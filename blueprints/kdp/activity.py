import glob as _glob
import os
import threading
import uuid
import zipfile

from flask import Blueprint, jsonify, render_template, request

from config import (KDP_BLEED_PX, KDP_DPI, KDP_MIN_PAGES,
                    KDP_PAGE_H_IN, KDP_PAGE_H_PT, KDP_PAGE_H_PX,
                    KDP_PAGE_W_IN, KDP_PAGE_W_PT, KDP_PAGE_W_PX,
                    KDP_TRIM_H_IN, KDP_TRIM_W_IN, RESULTS_DIR, TOOLS_DIR,
                    UPLOAD_DIR)
from extensions import db_last, db_save, db_update
from helpers.kdp import kdp_create_pdf, kdp_validate
from jobs import create_job, jdone, jerror, jlog

bp = Blueprint('kdp_activity', __name__)

ACTIVITY_DIR = TOOLS_DIR / 'activity_bot'


@bp.route('/activity')
def activity():
    return render_template('activity.html', last=db_last('activity'))


@bp.route('/activity/run', methods=['POST'])
def activity_run():
    try:
        n_mazes      = max(0, min(50, int(request.form.get('n_mazes', 10))))
        n_sudoku     = max(0, min(50, int(request.form.get('n_sudoku', 0))))
        n_wordsearch = max(0, min(50, int(request.form.get('n_wordsearch', 0))))
        n_tictactoe  = max(0, min(50, int(request.form.get('n_tictactoe', 0))))
        n_magic      = max(0, min(50, int(request.form.get('n_magic', 0))))
        n_dotgrid    = max(0, min(50, int(request.form.get('n_dotgrid', 0))))
        n_counting   = max(0, min(50, int(request.form.get('n_counting', 0))))
        n_pattern    = max(0, min(50, int(request.form.get('n_pattern', 0))))
        n_symmetry   = max(0, min(50, int(request.form.get('n_symmetry', 0))))
        n_cbn        = max(0, min(50, int(request.form.get('n_cbn', 0))))
        n_pathsum    = max(0, min(50, int(request.form.get('n_pathsum', 0))))
        n_mathmaze   = max(0, min(50, int(request.form.get('n_mathmaze', 0))))
    except ValueError:
        return jsonify({'error': 'Counts muszą być liczbami całkowitymi'}), 400

    difficulty = request.form.get('difficulty', 'medium')
    if difficulty not in ('easy', 'medium', 'hard'):
        difficulty = 'medium'

    sudoku_size = request.form.get('sudoku_size', '4x4')
    sudoku_difficulty = request.form.get('sudoku_difficulty', 'medium')

    wordsearch_theme = request.form.get('wordsearch_theme', 'animals_en')
    wordsearch_difficulty = request.form.get('wordsearch_difficulty', 'medium')

    tictactoe_difficulty = request.form.get('tictactoe_difficulty', 'medium')
    magic_difficulty     = request.form.get('magic_difficulty',     'medium')
    dotgrid_difficulty   = request.form.get('dotgrid_difficulty',   'medium')
    counting_difficulty  = request.form.get('counting_difficulty',  'medium')
    pattern_difficulty   = request.form.get('pattern_difficulty',   'medium')
    symmetry_difficulty  = request.form.get('symmetry_difficulty',  'medium')
    cbn_difficulty       = request.form.get('cbn_difficulty',       'medium')
    pathsum_difficulty   = request.form.get('pathsum_difficulty',   'medium')
    mathmaze_difficulty  = request.form.get('mathmaze_difficulty',  'medium')

    kdp_mode = request.form.get('kdp_mode', 'true') == 'true'
    seed_base = int(request.form.get('seed', 42))

    if (n_mazes == 0 and n_sudoku == 0 and n_wordsearch == 0
            and n_magic == 0 and n_dotgrid == 0
            and n_counting == 0 and n_pattern == 0 and n_symmetry == 0
            and n_pathsum == 0 and n_mathmaze == 0):
        return jsonify({'error': 'Wybierz co najmniej jedną aktywność'}), 400

    jid = create_job()
    rid = db_save('activity', {
        'n_mazes': n_mazes, 'n_sudoku': n_sudoku, 'n_wordsearch': n_wordsearch,
        'n_tictactoe': n_tictactoe, 'n_magic': n_magic, 'n_dotgrid': n_dotgrid,
        'n_counting': n_counting, 'n_pattern': n_pattern,
        'n_symmetry': n_symmetry, 'n_cbn': n_cbn,
        'n_pathsum': n_pathsum, 'n_mathmaze': n_mathmaze,
        'difficulty': difficulty,
        'sudoku_size': sudoku_size, 'sudoku_difficulty': sudoku_difficulty,
        'wordsearch_theme': wordsearch_theme,
        'wordsearch_difficulty': wordsearch_difficulty,
        'tictactoe_difficulty': tictactoe_difficulty,
        'magic_difficulty': magic_difficulty,
        'dotgrid_difficulty': dotgrid_difficulty,
        'counting_difficulty': counting_difficulty,
        'pattern_difficulty': pattern_difficulty,
        'symmetry_difficulty': symmetry_difficulty,
        'cbn_difficulty': cbn_difficulty,
        'pathsum_difficulty': pathsum_difficulty,
        'mathmaze_difficulty': mathmaze_difficulty,
        'kdp': kdp_mode,
    })

    def run():
        try:
            from tools.activity_bot.maze            import generate_maze_image
            from tools.activity_bot.sudoku          import generate_sudoku_image
            from tools.activity_bot.wordsearch      import generate_wordsearch_image
            from tools.activity_bot.tictactoe       import generate_tictactoe_image
            from tools.activity_bot.magic_square    import generate_magic_square_image
            from tools.activity_bot.dot_grid        import generate_dot_grid_image
            from tools.activity_bot.counting        import generate_counting_image
            from tools.activity_bot.pattern         import generate_pattern_image
            from tools.activity_bot.symmetry        import generate_symmetry_image
            from tools.activity_bot.color_by_number import generate_color_by_number_image
            from tools.activity_bot.path_sums       import generate_path_sums_image
            from tools.activity_bot.math_maze       import generate_math_maze_image

            # Generate at the book's live-area size so build_activity_book can
            # place pages with KDP mirrored margins (8.5x11, no bleed).
            from tools.activity_bot.book_builder import CONTENT_W, CONTENT_H
            canvas = (CONTENT_W, CONTENT_H)
            jlog(jid, f'📐 Canvas: {canvas[0]}×{canvas[1]} px @ {KDP_DPI} DPI'
                       ' (live area, KDP no-bleed)')
            jlog(jid, f'🎯 Mazes: {n_mazes} ({difficulty}) · '
                       f'Sudoku: {n_sudoku} ({sudoku_size}/{sudoku_difficulty}) · '
                       f'WordSearch: {n_wordsearch} ({wordsearch_theme}/{wordsearch_difficulty})')
            jlog(jid, f'   TicTacToe: {n_tictactoe} ({tictactoe_difficulty}) · '
                       f'Magic: {n_magic} ({magic_difficulty}) · '
                       f'DotGrid: {n_dotgrid} ({dotgrid_difficulty})')
            jlog(jid, f'   Counting: {n_counting} · Pattern: {n_pattern} · '
                       f'Symmetry: {n_symmetry} · ColorByNum: {n_cbn} · '
                       f'PathSum: {n_pathsum} · MathMaze: {n_mathmaze}')

            res_dir = RESULTS_DIR / jid
            res_dir.mkdir(exist_ok=True)
            generated = []

            # Spread each kind evenly across the page sequence (Bresenham-style).
            # Each item gets a fractional position (i+0.5)/n; we sort all items
            # by position so kinds interleave even when their counts differ.
            buckets = []
            if n_mazes:      buckets.append(('maze',       [(i + 1,) for i in range(n_mazes)]))
            if n_sudoku:     buckets.append(('sudoku',     [(i + 1,) for i in range(n_sudoku)]))
            if n_wordsearch: buckets.append(('wordsearch', [(i + 1,) for i in range(n_wordsearch)]))
            if n_tictactoe:  buckets.append(('tictactoe',  [(i + 1,) for i in range(n_tictactoe)]))
            if n_magic:      buckets.append(('magic',      [(i + 1,) for i in range(n_magic)]))
            if n_dotgrid:    buckets.append(('dotgrid',    [(i + 1,) for i in range(n_dotgrid)]))
            if n_counting:   buckets.append(('counting',   [(i + 1,) for i in range(n_counting)]))
            if n_pattern:    buckets.append(('pattern',    [(i + 1,) for i in range(n_pattern)]))
            if n_symmetry:   buckets.append(('symmetry',   [(i + 1,) for i in range(n_symmetry)]))
            if n_cbn:        buckets.append(('cbn',        [(i + 1,) for i in range(n_cbn)]))
            if n_pathsum:    buckets.append(('pathsum',    [(i + 1,) for i in range(n_pathsum)]))
            if n_mathmaze:   buckets.append(('mathmaze',   [(i + 1,) for i in range(n_mathmaze)]))

            total = sum(len(items) for _, items in buckets)
            tagged = []
            for kind, items in buckets:
                n = len(items)
                for i, payload in enumerate(items):
                    pos = (i + 0.5) / n * total
                    tagged.append((pos, kind, payload[0]))
            # Stable sort by position; ties break on kind name for determinism.
            tagged.sort(key=lambda t: (t[0], t[1]))
            order = [(kind, payload) for (_, kind, payload) in tagged]

            from PIL import Image as _Image

            for idx, (kind, payload) in enumerate(order, 1):
                out = res_dir / f'{idx:03d}_{kind}.png'
                if kind == 'maze':
                    n = payload
                    img = generate_maze_image(
                        difficulty=difficulty,
                        seed=seed_base + n,
                        title=f'Maze {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   🧩 [{idx:03d}] Maze {n} zapisany')
                elif kind == 'sudoku':
                    n = payload
                    img = generate_sudoku_image(
                        size_key=sudoku_size,
                        difficulty=sudoku_difficulty,
                        seed=seed_base + 2000 + n,
                        title=f'Sudoku {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   🔢 [{idx:03d}] Sudoku {n} ({sudoku_size}) zapisany')
                elif kind == 'wordsearch':
                    n = payload
                    img = generate_wordsearch_image(
                        theme=wordsearch_theme,
                        difficulty=wordsearch_difficulty,
                        seed=seed_base + 3000 + n,
                        title=f'Word Search {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   📝 [{idx:03d}] WordSearch {n} ({wordsearch_theme}) zapisany')
                elif kind == 'tictactoe':
                    n = payload
                    img = generate_tictactoe_image(
                        difficulty=tictactoe_difficulty,
                        title=f'Tic-Tac-Toe {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   ⭕ [{idx:03d}] Tic-Tac-Toe {n} ({tictactoe_difficulty}) zapisany')
                elif kind == 'magic':
                    n = payload
                    img = generate_magic_square_image(
                        difficulty=magic_difficulty,
                        seed=seed_base + 4000 + n,
                        title=f'Magic Square {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   ✨ [{idx:03d}] Magic Square {n} ({magic_difficulty}) zapisany')
                elif kind == 'dotgrid':
                    n = payload
                    img = generate_dot_grid_image(
                        difficulty=dotgrid_difficulty,
                        seed=seed_base + 4000 + n,
                        title=f'Drawing Grid {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   • [{idx:03d}] Dot Grid {n} ({dotgrid_difficulty}) zapisany')
                elif kind == 'counting':
                    n = payload
                    img = generate_counting_image(
                        difficulty=counting_difficulty,
                        seed=seed_base + 5000 + n,
                        title=f'How Many? {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   🔢 [{idx:03d}] Counting {n} ({counting_difficulty}) zapisany')
                elif kind == 'pattern':
                    n = payload
                    img = generate_pattern_image(
                        difficulty=pattern_difficulty,
                        seed=seed_base + 6000 + n,
                        title=f'What Comes Next? {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   🔁 [{idx:03d}] Pattern {n} ({pattern_difficulty}) zapisany')
                elif kind == 'symmetry':
                    n = payload
                    img = generate_symmetry_image(
                        difficulty=symmetry_difficulty,
                        seed=seed_base + 7000 + n,
                        title=f'Symmetry {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   🪞 [{idx:03d}] Symmetry {n} ({symmetry_difficulty}) zapisany')
                elif kind == 'cbn':
                    n = payload
                    img = generate_color_by_number_image(
                        difficulty=cbn_difficulty,
                        seed=seed_base + 8000 + n,
                        title=f'Color by Number {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   🎨 [{idx:03d}] Color by Number {n} ({cbn_difficulty}) zapisany')
                elif kind == 'pathsum':
                    n = payload
                    img = generate_path_sums_image(
                        difficulty=pathsum_difficulty,
                        seed=seed_base + 9000 + n,
                        title=f'Path Sum {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   ➕ [{idx:03d}] Path Sum {n} ({pathsum_difficulty}) zapisany')
                elif kind == 'mathmaze':
                    n = payload
                    img = generate_math_maze_image(
                        difficulty=mathmaze_difficulty,
                        seed=seed_base + 10000 + n,
                        title=f'Math Maze {n}',
                        canvas_size=canvas,
                    )
                    img.save(str(out), dpi=(KDP_DPI, KDP_DPI))
                    jlog(jid, f'   ➗ [{idx:03d}] Math Maze {n} ({mathmaze_difficulty}) zapisany')
                generated.append(str(out))

            jlog(jid, f'✅ Wygenerowano łącznie {len(generated)} stron')

            zip_path = RESULTS_DIR / f'{jid}_activity.zip'
            with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
                for p in generated:
                    zf.write(p, os.path.basename(p))
            jlog(jid, f'📦 ZIP: {len(generated)} stron')

            jdone(jid, str(zip_path), len(generated))
            db_update(rid, 'done', len(generated))

        except Exception as e:
            import traceback
            jlog(jid, traceback.format_exc())
            jerror(jid, str(e))
            db_update(rid, 'error')

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': jid})


@bp.route('/activity/kdp_pdf/<jid>', methods=['POST'])
def activity_kdp_pdf(jid):
    """Build a KDP-compliant PDF from previously generated PNG files."""
    res_dir = RESULTS_DIR / jid
    if not res_dir.exists():
        return jsonify({'error': 'Brak wyników — najpierw wygeneruj strony'}), 404

    jid2 = create_job()

    def run():
        try:
            from natsort import natsorted

            pngs = natsorted(_glob.glob(str(res_dir / '*.png')))
            if not pngs:
                jerror(jid2, 'Brak plików PNG w folderze wyników')
                return

            jlog(jid2, f'📚 Znaleziono {len(pngs)} stron PNG')
            jlog(jid2, '🔍 Walidacja KDP...')
            val = kdp_validate(pngs)
            if val['ok']:
                jlog(jid2, '   ✅ Walidacja OK')
            else:
                for issue in val['issues']:
                    jlog(jid2, f'   ⚠️  {issue}')
                if len(pngs) < KDP_MIN_PAGES // 2:
                    jlog(jid2, f'   ℹ️  Strony będą powtórzone do min. {KDP_MIN_PAGES}')

            pdf_path = RESULTS_DIR / f'{jid}_activity_KDP.pdf'
            jlog(jid2, f'⚙️  Generuję PDF KDP ({KDP_PAGE_W_IN}" × {KDP_PAGE_H_IN}" z bleedem)...')

            result = kdp_create_pdf(pngs, str(pdf_path), jlog_fn=lambda m: jlog(jid2, m))
            size_mb = os.path.getsize(str(pdf_path)) / 1024 / 1024
            jlog(jid2, f'✅ PDF gotowy: {result["pages"]} stron, {size_mb:.1f} MB')
            jlog(jid2, f'   MediaBox: {KDP_PAGE_W_IN}" × {KDP_PAGE_H_IN}" '
                       f'({KDP_PAGE_W_PT:.0f}×{KDP_PAGE_H_PT:.0f} pt)')
            jlog(jid2, f'   TrimBox:  {KDP_TRIM_W_IN}" × {KDP_TRIM_H_IN}"')

            for iss in result.get('issues', []):
                jlog(jid2, f'   ⚠️  {iss}')

            jdone(jid2, str(pdf_path), result['pages'])

        except Exception as e:
            import traceback
            jlog(jid2, traceback.format_exc())
            jerror(jid2, str(e))

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': jid2})


@bp.route('/activity/build_book', methods=['POST'])
def activity_build_book():
    """Assemble a full activity book PDF (title, copyright, intro, TOC,
    activities, Great Job! closing) from previously generated PNG pages.

    Form params:
      job_id, title, subtitle, author, age_range, year, description (optional)
    """
    job_id = (request.form.get('job_id') or '').strip()
    if not job_id:
        return jsonify({'error': 'job_id is required'}), 400
    res_dir = RESULTS_DIR / job_id
    if not res_dir.exists():
        return jsonify({'error': f'No results for job_id={job_id}'}), 404

    author = (request.form.get('author') or '').strip()
    if not author:
        return jsonify({'error': 'Author is required — enter the author '
                                 'name before building the book'}), 400

    try:
        year = int(request.form.get('year') or 2026)
    except ValueError:
        year = 2026

    metadata = {
        'title':       (request.form.get('title') or 'Activity Book').strip(),
        'subtitle':    (request.form.get('subtitle') or '').strip(),
        'author':      author,
        'age_range':   (request.form.get('age_range') or '3-5').strip(),
        'year':        year,
        'description': (request.form.get('description') or '').strip(),
    }

    jid2 = create_job()

    def run():
        try:
            from natsort import natsorted
            from tools.activity_bot.book_builder import build_activity_book

            pngs = natsorted(_glob.glob(str(res_dir / '*.png')))
            if not pngs:
                jerror(jid2, 'No PNG files in results folder')
                return

            jlog(jid2, f'📚 Building book from {len(pngs)} pages')
            jlog(jid2, f'   Title:    {metadata["title"]}')
            jlog(jid2, f'   Author:   {metadata["author"]}')
            jlog(jid2, f'   Age:      {metadata["age_range"]}')

            pdf_path = res_dir / 'book.pdf'
            result = build_activity_book(pngs, metadata, str(pdf_path),
                                         jlog_fn=lambda m: jlog(jid2, m))

            jlog(jid2, f'✅ Book PDF: {result["total_pages"]} pages, '
                       f'{result["file_size_mb"]:.2f} MB')
            jlog(jid2, f'   Validation OK: {result["validation"]["ok"]}')
            for iss in result['validation']['issues']:
                jlog(jid2, f'   ⚠️  {iss}')

            jdone(jid2, str(pdf_path), result['total_pages'],
                  data=result)

        except Exception as e:
            import traceback
            jlog(jid2, traceback.format_exc())
            jerror(jid2, str(e))

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': jid2})


@bp.route('/activity/presets', methods=['GET'])
def activity_presets_list():
    """Return list of available series presets for UI dropdown."""
    from tools.activity_bot.series_presets import (
        list_preset_keys, preset_display_name, get_preset
    )
    out = []
    for k in list_preset_keys():
        p = get_preset(k)
        out.append({
            'key': k,
            'label': preset_display_name(k),
            'volume': p['volume'],
            'subtitle': p['subtitle'],
        })
    return jsonify({'presets': out})


@bp.route('/activity/preset/<key>', methods=['GET'])
def activity_preset_detail(key):
    """Return full config dict for a single preset (for JS auto-fill)."""
    from tools.activity_bot.series_presets import get_preset
    p = get_preset(key)
    if not p:
        return jsonify({'error': f'Unknown preset: {key}'}), 404
    return jsonify(p)
