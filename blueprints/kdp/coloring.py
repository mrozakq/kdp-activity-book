import csv
import io
import os
import threading
import uuid
import zipfile

from flask import Blueprint, jsonify, render_template, request

from config import (COLORING_DIR, FONT_MAP, KDP_BLEED_IN, KDP_BLEED_PX,
                    KDP_DPI, KDP_MIN_PAGES, KDP_PAGE_H_IN, KDP_PAGE_H_PT,
                    KDP_PAGE_H_PX, KDP_PAGE_W_IN, KDP_PAGE_W_PT,
                    KDP_PAGE_W_PX, KDP_TRIM_H_IN, KDP_TRIM_W_IN,
                    RESULTS_DIR, UPLOAD_DIR)
from extensions import db_last, db_save, db_update
from helpers.kdp import kdp_convert_grayscale, kdp_create_pdf, kdp_validate
from jobs import create_job, jdone, jerror, jlog

bp = Blueprint('coloring', __name__)


def _validate_coloring_output(png_paths: list, pw: int, ph: int,
                              book_mode_50: bool, jid: str):
    """
    Validate generated coloring PNGs against KDP requirements.
    Checks: page count, dimensions, grayscale mode, all images have content.
    """
    from PIL import Image as _Image
    issues, passed = [], []
    n = len(png_paths)
    expected = 50 if book_mode_50 else None

    # Page count
    if expected and n != expected:
        issues.append(f'Liczba projektów: {n} (oczekiwano {expected})')
    else:
        passed.append(f'✅ Liczba projektów: {n} {"(50 ✓)" if book_mode_50 else ""}')

    # Check each file
    bad_size, bad_mode, blank = 0, 0, 0
    for p in png_paths:
        try:
            with _Image.open(p) as img:
                if img.size != (pw, ph):
                    bad_size += 1
                if img.mode not in ('L', '1', 'RGB'):
                    bad_mode += 1
                # Blank check: mean pixel value ≥ 253 → treat as blank
                import statistics
                sample = list(img.convert('L').getdata())[::200]
                if statistics.mean(sample) >= 253:
                    blank += 1
        except Exception as e:
            issues.append(f'Błąd odczytu {os.path.basename(p)}: {e}')

    if bad_size:
        issues.append(f'{bad_size} plików ma złe wymiary (oczekiwano {pw}×{ph})')
    else:
        passed.append(f'✅ Wymiary: {pw}×{ph}px — wszystkie OK')

    if bad_mode:
        issues.append(f'{bad_mode} plików w niewłaściwym trybie koloru')
    else:
        passed.append('✅ Tryb koloru: grayscale — wszystkie OK')

    if blank:
        issues.append(f'{blank} plików wygląda na puste (brak treści)')
    else:
        passed.append('✅ Wszystkie strony zawierają treść (nie puste)')

    if book_mode_50:
        jlog(jid, f'   Walidacja 50-Design Book:')
    for m in passed:
        jlog(jid, f'   {m}')
    for m in issues:
        jlog(jid, f'   ⚠️  {m}')
    if not issues:
        jlog(jid, '   ✅ Walidacja przeszła pomyślnie — 0 problemów')

    return {'ok': len(issues) == 0, 'issues': issues, 'passed': passed}


@bp.route('/coloring')
def coloring():
    return render_template('coloring.html', fonts=list(FONT_MAP.keys()), last=db_last('coloring'))


@bp.route('/coloring/run', methods=['POST'])
def coloring_run():
    quotes_text = request.form.get('quotes', '').strip()
    quotes_csv_file = request.files.get('quotes_csv')
    font_name = request.form.get('font', 'random')
    font_size = int(request.form.get('font_size', 350))
    text_color = request.form.get('text_color', '#ffffff')
    stroke_color = request.form.get('stroke_color', '#000000')
    stroke_width = int(request.form.get('stroke_width', 20))
    kdp_mode = request.form.get('kdp_mode', 'false') == 'true'
    bw_mode = request.form.get('bw_mode', 'L')
    book_mode_50 = request.form.get('book_mode_50', 'false') == 'true'
    images = request.files.getlist('images')

    # In book_mode_50, user images are optional (procedural generation fills in)
    has_user_images = any(img.filename for img in images)
    if not has_user_images and not book_mode_50:
        return jsonify({'error': 'Prześlij co najmniej jeden obraz mandali'}), 400

    # ── Parse quotes ──────────────────────────────────────────────────────────
    quotes_meta = []   # list of dicts with 'text' and 'lines'
    if book_mode_50:
        # Optional override: inline JSON from the auto-quotes flow (Claude-generated).
        custom_quotes_json = request.form.get('custom_quotes_json', '').strip()
        if custom_quotes_json:
            import json as _json
            try:
                quotes_meta = _json.loads(custom_quotes_json)
            except Exception as e:
                return jsonify({'error': f'Nieprawidłowy custom_quotes_json: {e}'}), 400
            if not isinstance(quotes_meta, list) or not quotes_meta:
                return jsonify({'error': 'custom_quotes_json musi być niepustą listą obiektów'}), 400
        else:
            quotes_path = COLORING_DIR / 'data' / 'quotes_50.json'
            if quotes_path.exists():
                import json as _json
                with open(str(quotes_path), encoding='utf-8') as f:
                    quotes_meta = _json.load(f)
            if not quotes_meta:
                return jsonify({'error': 'Brak pliku quotes_50.json w tools/coloring_bot/data/'}), 400
        kdp_mode = True  # book mode always forces KDP
    else:
        raw_quotes = []
        if quotes_csv_file and quotes_csv_file.filename:
            txt = quotes_csv_file.read().decode('utf-8-sig')
            delim = ',' if ',' in txt.split('\n')[0] else ';'
            rdr = csv.DictReader(io.StringIO(txt), delimiter=delim)
            for row in rdr:
                q = (row.get('quote') or row.get('Quote') or next(iter(row.values()), '')).strip()
                if q:
                    raw_quotes.append(q)
        for line in quotes_text.splitlines():
            line = line.strip()
            if line:
                raw_quotes.append(line)
        if not raw_quotes:
            return jsonify({'error': 'Podaj cytaty (w polu tekstowym lub pliku CSV)'}), 400
        quotes_meta = [{'text': q, 'lines': len(q.split()) // 5 + 1} for q in raw_quotes]

    # ── Save uploaded images ──────────────────────────────────────────────────
    up_dir = UPLOAD_DIR / str(uuid.uuid4())
    img_paths = []
    if has_user_images:
        up_dir.mkdir(parents=True)
        for img in images:
            if img.filename:
                p = up_dir / os.path.basename(img.filename)
                img.save(str(p))
                img_paths.append(str(p))

    jid = create_job()
    rid = db_save('coloring', {
        'quotes': len(quotes_meta),
        'font': font_name,
        'kdp': kdp_mode,
        'book50': book_mode_50,
    })

    def run():
        try:
            from PIL import Image, ImageDraw, ImageFont as PILFont
            import random as _rnd

            fonts_dir = COLORING_DIR / 'data' / 'fonts'
            all_font_paths = [fonts_dir / v for v in FONT_MAP.values()]

            res_dir = RESULTS_DIR / jid
            res_dir.mkdir(exist_ok=True)
            generated = []

            # ── Canvas / safe zone setup ──────────────────────────────────────
            if kdp_mode:
                pw, ph = KDP_PAGE_W_PX, KDP_PAGE_H_PX   # 2625 × 3375

                if book_mode_50:
                    # 100-page book: gutter 0.625" from trim edge
                    safe_left  = KDP_BLEED_PX + int(0.625 * 300)   # 37 + 187 = 224 px
                    safe_right = KDP_BLEED_PX + int(0.375 * 300)   # 37 + 112 = 149 px from right
                    safe_top   = KDP_BLEED_PX + int(0.375 * 300)   # 37 + 112 = 149 px
                    safe_bot   = KDP_BLEED_PX + int(0.375 * 300)
                    jlog(jid, f'📐 Tryb 50-Design Book: {pw}×{ph}px')
                    jlog(jid, f'   Gutter left: 0.625" | Margins: 0.375" | Bleed: 0.125"')
                else:
                    # Standard KDP: symmetric 0.375" from trim on all sides
                    safe_left  = KDP_BLEED_PX + int(0.375 * 300)
                    safe_right = KDP_BLEED_PX + int(0.375 * 300)
                    safe_top   = KDP_BLEED_PX + int(0.375 * 300)
                    safe_bot   = KDP_BLEED_PX + int(0.375 * 300)
                    jlog(jid, f'📐 Tryb KDP: {pw}×{ph}px (8.75"×11.25" z bleedem 0.125")')

                # Text anchor = centre of safe rectangle
                text_cx = (safe_left + (pw - safe_right)) // 2
                text_cy = (safe_top  + (ph - safe_bot))   // 2
                text_max_w = pw - safe_left - safe_right   # usable text width in px
            else:
                pw, ph = 2550, 3300
                text_cx, text_cy = pw // 2, ph // 2
                text_max_w = pw - 2 * int(0.375 * 300)

            # ── Procedural background cache for book mode ─────────────────────
            # Priority: user-uploaded images > procedural/folder backgrounds.
            # If user provided images, skip the cache build (we'll cycle through theirs).
            bg_cache = {}
            CATEGORY_NAMES = []
            if book_mode_50:
                import sys as _sys
                if str(COLORING_DIR) not in _sys.path:
                    _sys.path.insert(0, str(COLORING_DIR))
                from pattern_gen import generate_background as _gen_bg, CATEGORY_NAMES

                if img_paths:
                    jlog(jid, f'🖼️  Używam {len(img_paths)} własnych teł (cykl po stronach)')
                else:
                    jlog(jid, '🎨 Generuję tła proceduralne (5 kategorii × 5 wariantów)...')
                    for cat in range(5):
                        bg_cache[cat] = []
                        for seed_i in range(5):
                            bg_img = _gen_bg(cat, (pw, ph), seed=cat * 100 + seed_i)
                            bg_cache[cat].append(bg_img)
                        jlog(jid, f'   ✅ Kategoria {CATEGORY_NAMES[cat]}: 5 teł gotowych')

            # ── Text-wrap helper (pixel-aware) ────────────────────────────────
            def wrap_text(text: str, font, max_w: int) -> str:
                words = text.split()
                lines, cur = [], ''
                for word in words:
                    test = (cur + ' ' + word).strip()
                    bb = font.getbbox(test)
                    if bb[2] - bb[0] > max_w and cur:
                        lines.append(cur)
                        cur = word
                    else:
                        cur = test
                if cur:
                    lines.append(cur)
                return '\n'.join(lines)

            # ── Generate designs ──────────────────────────────────────────────
            rng = _rnd.Random(42)

            for i, q_meta in enumerate(quotes_meta):
                quote = q_meta['text'] if isinstance(q_meta, dict) else q_meta
                q_lines = q_meta.get('lines', 2) if isinstance(q_meta, dict) else 2
                n = i + 1
                cat = (i // 10) % 5   # 0-9→cat0, 10-19→cat1, …

                if book_mode_50:
                    cat_name = CATEGORY_NAMES[cat]
                    jlog(jid, f'🎨 [{n}/50] Cat {cat+1} ({cat_name}) — "{quote[:45]}"')
                else:
                    jlog(jid, f'🎨 [{n}/{len(quotes_meta)}] "{quote[:50]}"')

                # ── Font selection ────────────────────────────────────────────
                if font_name == 'random':
                    fp = all_font_paths[rng.randint(0, len(all_font_paths) - 1)]
                else:
                    fp = fonts_dir / FONT_MAP.get(font_name, list(FONT_MAP.values())[0])
                font = PILFont.truetype(str(fp), font_size)

                # ── Wrap text to pixel width ──────────────────────────────────
                q_br = wrap_text(quote, font, int(text_max_w * 0.92))

                # ── Build canvas ──────────────────────────────────────────────
                im = Image.new('RGBA', (pw, ph), 'white')

                if img_paths:
                    # User-uploaded image — cycle through provided files.
                    bg = Image.open(img_paths[i % len(img_paths)]).convert('RGBA')
                    fill_w = pw
                    wp = fill_w / float(bg.size[0])
                    bg = bg.resize((fill_w, int(bg.size[1] * wp)), Image.LANCZOS)
                    ow = (pw - bg.size[0]) // 2
                    oh = (ph - bg.size[1]) // 2
                    im.alpha_composite(bg, (ow, oh))
                elif book_mode_50 and bg_cache:
                    # Pick procedural/folder background — long quotes get simpler patterns
                    options = bg_cache[cat]
                    if q_lines >= 3:
                        bg_idx = i % max(1, len(options) // 2)
                    else:
                        bg_idx = i % len(options)
                    bg = options[bg_idx].convert('RGBA')
                    # Scale to canvas (should already be pw×ph)
                    if bg.size != (pw, ph):
                        bg = bg.resize((pw, ph), Image.LANCZOS)
                    im.alpha_composite(bg)

                # ── Draw text ─────────────────────────────────────────────────
                draw = ImageDraw.Draw(im)
                draw.text(
                    (text_cx, text_cy), q_br,
                    align='center', anchor='mm',
                    font=font,
                    fill=text_color,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_color,
                    spacing=int(font_size * 0.15),
                )

                # ── KDP grayscale conversion ──────────────────────────────────
                if kdp_mode:
                    im = kdp_convert_grayscale(im.convert('RGB'), bw_mode)

                out = res_dir / f'{n}.png'
                im.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                generated.append(str(out))
                if n % 10 == 0 or n == len(quotes_meta):
                    jlog(jid, f'   ✅ {n}.png saved')

            # ── Validation ────────────────────────────────────────────────────
            if kdp_mode:
                jlog(jid, '🔍 Walidacja KDP...')
                val = _validate_coloring_output(generated, pw, ph, book_mode_50, jid)

            # ── ZIP ───────────────────────────────────────────────────────────
            zip_path = RESULTS_DIR / f'{jid}_coloring.zip'
            with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
                for p in generated:
                    zf.write(p, os.path.basename(p))

            suffix = f' — {len(generated)} projektów, gotowe do KDP PDF' if kdp_mode else ''
            jlog(jid, f'📦 ZIP: {len(generated)} obrazów{suffix}')
            jdone(jid, str(zip_path), len(generated))
            db_update(rid, 'done', len(generated))

        except Exception as e:
            import traceback
            jlog(jid, traceback.format_exc())
            jerror(jid, str(e))
            db_update(rid, 'error')

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': jid})


@bp.route('/coloring/merge_pdf/<jid>', methods=['POST'])
def coloring_merge_pdf(jid):
    res_dir = RESULTS_DIR / jid
    if not res_dir.exists():
        return jsonify({'error': 'Brak wyników'}), 404
    jid2 = create_job()

    def run():
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas as rl_canvas
            from natsort import natsorted
            import glob as g

            pngs = natsorted(g.glob(str(res_dir / '*.png')))
            pdf_path = RESULTS_DIR / f'{jid}_coloring.pdf'
            c = rl_canvas.Canvas(str(pdf_path), pagesize=letter)
            w, h = letter
            for p in pngs:
                c.drawImage(p, 0, 0, width=w, height=h)
                c.showPage()
            c.save()
            jlog(jid2, f'📄 PDF z {len(pngs)} stron zapisany')
            jdone(jid2, str(pdf_path), len(pngs))
        except Exception as e:
            jerror(jid2, str(e))

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': jid2})


@bp.route('/coloring/kdp_pdf/<jid>', methods=['POST'])
def coloring_kdp_pdf(jid):
    """Generate a full KDP-compliant PDF from previously generated PNG files."""
    res_dir = RESULTS_DIR / jid
    if not res_dir.exists():
        return jsonify({'error': 'Brak wyników — najpierw wygeneruj obrazy'}), 404

    jid2 = create_job()

    def run():
        try:
            from natsort import natsorted
            import glob as g

            pngs = natsorted(g.glob(str(res_dir / '*.png')))
            if not pngs:
                jerror(jid2, 'Brak plików PNG w folderze wyników')
                return

            is_50_book = len(pngs) >= 50
            jlog(jid2, f'📚 Znaleziono {len(pngs)} obrazów PNG'
                       + (' (50-Design Book Mode)' if is_50_book else ''))

            # Validate
            jlog(jid2, '🔍 Walidacja KDP...')
            val = kdp_validate(pngs)
            if val['ok']:
                jlog(jid2, '   ✅ Walidacja OK')
            else:
                for issue in val['issues']:
                    jlog(jid2, f'   ⚠️  {issue}')
                if len(pngs) < KDP_MIN_PAGES // 2:
                    jlog(jid2, f'   ℹ️  Strony będą powtórzone do min. {KDP_MIN_PAGES} stron')
            if is_50_book:
                expected_pdf_pages = len(pngs) * 2   # 50 designs × 2 = 100
                jlog(jid2, f'   📄 PDF będzie miał {expected_pdf_pages} stron (50 projektów + 50 pustych)')

            pdf_path = RESULTS_DIR / f'{jid}_KDP.pdf'
            jlog(jid2, f'⚙️  Generuję PDF KDP ({KDP_PAGE_W_IN}" × {KDP_PAGE_H_IN}" z bleedem)...')

            result = kdp_create_pdf(pngs, str(pdf_path), jlog_fn=lambda m: jlog(jid2, m))

            size_mb = os.path.getsize(str(pdf_path)) / 1024 / 1024
            jlog(jid2, f'✅ PDF gotowy: {result["pages"]} stron, {size_mb:.1f} MB')
            jlog(jid2, f'   Strony z projektem: {result["pages"]//2}')
            jlog(jid2, f'   Puste strony (separator): {result["pages"]//2}')
            jlog(jid2, f'   MediaBox: {KDP_PAGE_W_IN}" × {KDP_PAGE_H_IN}" ({KDP_PAGE_W_PT:.0f}×{KDP_PAGE_H_PT:.0f} pt)')
            jlog(jid2, f'   TrimBox:  {KDP_TRIM_W_IN}" × {KDP_TRIM_H_IN}"')
            jlog(jid2, f'   Bleed:    {KDP_BLEED_IN}" na każdej stronie')

            if result['issues']:
                for iss in result['issues']:
                    jlog(jid2, f'   ⚠️  {iss}')

            jdone(jid2, str(pdf_path), result['pages'])

        except Exception as e:
            import traceback
            jlog(jid2, traceback.format_exc())
            jerror(jid2, str(e))

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': jid2})
