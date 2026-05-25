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
