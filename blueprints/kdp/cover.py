import os
import threading
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request

from config import (
    COVER_DIR, COVER_PALETTES, COVER_KIDS_PALETTES, COVER_KIDS_THEMES,
    RESULTS_DIR, UPLOAD_DIR,
)
from extensions import db_save, db_update
from jobs import active_jobs, create_job, jdone, jerror, jlog, jobs_lock

bp = Blueprint('cover', __name__)

# Map a preset mix (n_* counts) to the canonical back-cover blurb type ids,
# ordered to match the "How to Use" / TOC sequence for consistency.
_MIX_TO_TYPE = {
    'n_mazes': 'maze', 'n_pattern': 'pattern', 'n_symmetry': 'symmetry',
    'n_mathmaze': 'math_maze', 'n_pathsum': 'path_sums', 'n_sudoku': 'sudoku',
    'n_magic': 'magic_square', 'n_counting': 'counting',
    'n_wordsearch': 'wordsearch', 'n_dotgrid': 'dot_grid',
}
_TYPE_ORDER = ['maze', 'pattern', 'symmetry', 'math_maze', 'path_sums',
               'sudoku', 'magic_square', 'counting', 'wordsearch', 'dot_grid']


def _types_from_mix(mix):
    """Ordered list of activity types actually present in a preset's mix."""
    present = {_MIX_TO_TYPE[k] for k, v in (mix or {}).items()
              if k in _MIX_TO_TYPE and v}
    return [t for t in _TYPE_ORDER if t in present]


@bp.route('/cover')
def cover():
    return render_template(
        'cover.html',
        palettes=COVER_PALETTES,
        kids_palettes=COVER_KIDS_PALETTES,
        kids_themes=COVER_KIDS_THEMES,
    )


@bp.route('/cover/run', methods=['POST'])
def cover_run():
    title    = request.form.get('title', '').strip()
    subtitle = request.form.get('subtitle', '').strip()
    author   = request.form.get('author', '').strip()
    pages    = int(request.form.get('pages', 48))
    hook     = request.form.get('hook', '').strip()
    tagline  = request.form.get('tagline', '').strip()
    bio      = request.form.get('author_bio', '').strip()
    palette  = request.form.get('palette', 'lavender')
    paper    = request.form.get('paper', 'white')
    seed     = int(request.form.get('seed', 42))
    bullets_raw = request.form.get('bullets', '')
    bullets = [b.strip() for b in bullets_raw.splitlines() if b.strip()]

    # Kids-mode params (no-op when cover_mode == "adult")
    cover_mode = request.form.get('cover_mode', 'adult').strip().lower()
    if cover_mode not in ('adult', 'kids'):
        cover_mode = 'adult'
    bg_theme   = request.form.get('bg_theme', 'city').strip()
    badge_text = request.form.get('badge_text', '').strip()
    cta_text   = request.form.get('cta_text', '').strip()
    # Activity types present in the volume (comma-separated) → procedural blurb.
    activity_types = [t.strip() for t in
                      request.form.get('activity_types', '').split(',') if t.strip()]

    if not title:
        return jsonify({'error': 'Podaj tytuł książki'}), 400
    if not subtitle:
        return jsonify({'error': 'Podaj podtytuł'}), 400

    # Optional background image upload
    bg_file = request.files.get('background')
    deco_file = request.files.get('decorative')
    mascot_file = request.files.get('mascot')
    up_dir = UPLOAD_DIR / str(uuid.uuid4())

    bg_path   = None
    deco_path = None
    mascot_path = None
    if bg_file and bg_file.filename:
        up_dir.mkdir(parents=True, exist_ok=True)
        bg_path = str(up_dir / os.path.basename(bg_file.filename))
        bg_file.save(bg_path)
    if deco_file and deco_file.filename:
        up_dir.mkdir(parents=True, exist_ok=True)
        deco_path = str(up_dir / os.path.basename(deco_file.filename))
        deco_file.save(deco_path)
    if mascot_file and mascot_file.filename:
        up_dir.mkdir(parents=True, exist_ok=True)
        mascot_path = str(up_dir / os.path.basename(mascot_file.filename))
        mascot_file.save(mascot_path)

    jid = create_job()
    rid = db_save('cover', {'title': title, 'pages': pages, 'palette': palette})

    def run():
        try:
            import sys as _sys
            cover_dir = str(COVER_DIR)
            if cover_dir not in _sys.path:
                _sys.path.insert(0, cover_dir)

            from cover_builder import build_cover

            out_pdf = str(RESULTS_DIR / f'{jid}_cover.pdf')

            result = build_cover(
                title=title,
                subtitle=subtitle,
                author=author,
                description_bullets=bullets,   # may be empty — no bullets drawn
                page_count=pages,
                background_image_path=bg_path,
                output_pdf=out_pdf,
                palette_name=palette,
                hook=hook,
                tagline=tagline,
                author_bio=bio,
                decorative_image_path=deco_path,
                paper=paper,
                seed=seed,
                cover_mode=cover_mode,
                bg_theme=bg_theme,
                badge_text=badge_text,
                cta_text=cta_text,
                mascot_image_path=mascot_path,
                activity_types=activity_types,
                log=lambda m: jlog(jid, m),
            )

            failed = result.get('failed', [])
            if failed:
                jlog(jid, f'⚠️  {len(failed)} problem(ów) walidacji')
            jdone(jid, out_pdf, 1)
            db_update(rid, 'done', 1)
        except Exception as e:
            import traceback
            jlog(jid, traceback.format_exc())
            jerror(jid, str(e))
            db_update(rid, 'error')

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': jid})


@bp.route('/cover/run_series', methods=['POST'])
def cover_run_series():
    """Build all 5 Little Vibe Coders covers in one job and zip the PDFs.
    Each cover uses its preset's cover block (kids mode); spine follows the
    exact interior page count baked into the preset."""
    import zipfile

    seed = int(request.form.get('seed', 42))
    jid = create_job()

    def run():
        try:
            import sys as _sys
            cover_dir = str(COVER_DIR)
            if cover_dir not in _sys.path:
                _sys.path.insert(0, cover_dir)
            from cover_builder import build_cover
            from tools.activity_bot.series_presets import (
                list_preset_keys, get_preset)

            out_dir = RESULTS_DIR / jid
            out_dir.mkdir(parents=True, exist_ok=True)
            pdfs, total_fail = [], 0

            for key in list_preset_keys():
                p = get_preset(key)
                c = p.get('cover')
                if not c:
                    jlog(jid, f'⚠️  {key}: brak bloku cover — pomijam')
                    continue
                jlog(jid, f'📕 Vol.{p["volume"]} — {key} ({c["pages"]} stron)...')
                out_pdf = out_dir / f'vol{p["volume"]}_{key}_cover.pdf'
                res = build_cover(
                    title=p['title'], subtitle=p['subtitle'], author=p['author'],
                    description_bullets=c.get('bullets', []),
                    page_count=c['pages'], output_pdf=str(out_pdf),
                    palette_name=c['palette'], hook=c['hook'],
                    tagline=c['tagline'], author_bio='', paper='white', seed=seed,
                    cover_mode='kids', bg_theme=c['bg_theme'],
                    badge_text=c['badge_text'], cta_text=c['cta'],
                    activity_types=_types_from_mix(p.get('mix')),
                    log=lambda m: None,
                )
                nf = len(res.get('failed', []))
                total_fail += nf
                jlog(jid, f'   {"✅" if nf == 0 else "⚠️  " + str(nf) + " fail"} '
                          f'Vol.{p["volume"]} gotowy')
                pdfs.append(str(out_pdf))

            zip_path = RESULTS_DIR / f'{jid}_covers.zip'
            with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
                for pf in pdfs:
                    zf.write(pf, os.path.basename(pf))
            jlog(jid, f'📦 Spakowano {len(pdfs)} okładek do ZIP '
                      f'(walidacja: {total_fail} fail łącznie)')
            jdone(jid, str(zip_path), len(pdfs))
        except Exception as e:
            import traceback
            jlog(jid, traceback.format_exc())
            jerror(jid, str(e))

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': jid})


@bp.route('/cover/preset/<key>', methods=['GET'])
def cover_preset_detail(key):
    """Return the cover block of a series preset (plus identifying fields) for
    UI auto-fill. Analogous to /activity/preset/<key>."""
    from tools.activity_bot.series_presets import get_preset
    p = get_preset(key)
    if not p:
        return jsonify({'error': f'Unknown preset: {key}'}), 404
    if 'cover' not in p:
        return jsonify({'error': f'Preset has no cover block: {key}'}), 404
    return jsonify({
        'key': key,
        'volume': p.get('volume'),
        'title': p.get('title'),
        'subtitle': p.get('subtitle'),
        'author': p.get('author'),
        'cover': p['cover'],
        'activity_types': _types_from_mix(p.get('mix')),
    })


@bp.route('/cover/preview/<jid>')
def cover_preview(jid):
    """Return the PNG preview as base64 for inline display."""
    with jobs_lock:
        if jid not in active_jobs:
            return jsonify({'error': 'not found'}), 404
        result_path = active_jobs[jid].get('result_path')
    if not result_path:
        return jsonify({'error': 'no result'}), 404
    png_path = Path(result_path).with_suffix('.png')
    if not png_path.exists():
        return jsonify({'error': 'no preview'}), 404
    import base64 as b64
    data = b64.b64encode(png_path.read_bytes()).decode()
    return jsonify({'b64': data})
