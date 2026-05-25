import glob
import os
import queue
import re
import shutil

from flask import (Blueprint, Response, jsonify, render_template,
                   send_file, stream_with_context)

from config import RESULTS_DIR
from extensions import db_all, db_last
from jobs import active_jobs, jobs_lock

bp = Blueprint('main', __name__)


# ── Tool catalog (used by index) — KDP-only standalone instance ──────────────
TOOLS_META = [
    {'id': 'kdp',        'name': 'KDP Builder',           'icon': '📘',
     'color': 'purple',  'url': '/kdp',
     'desc': 'Komplet narzędzi pod Amazon KDP — kolorowanki, fiszki, okładki, kompletne książki'},
]


# ── Sample CSV downloads ──────────────────────────────────────────────────────
SAMPLES = {
    'coloring': ('coloring_quotes.csv',
                 'quote\n"Be the change you wish to see in the world"\n'
                 '"In every walk with nature one receives far more than he seeks"\n'
                 '"The secret of getting ahead is getting started"\n'
                 '"Life is what happens when you\'re busy making other plans"'),
    'flashcard': ('flashcard_data.csv',
                  'text_top,text_bottom,image_path\n'
                  'Hello,Cześć,\nGoodbye,Do widzenia,\nThank you,Dziękuję,\n'
                  'Please,Proszę,\nYes,Tak,\nNo,Nie,\nGood morning,Dzień dobry,\n'
                  'Good night,Dobranoc,'),
}


# ── SSE stream ────────────────────────────────────────────────────────────────
@bp.route('/stream/<jid>')
def stream(jid):
    def generate():
        with jobs_lock:
            if jid not in active_jobs:
                yield 'data: Nie znaleziono zadania\n\n'
                yield 'event: done\ndata: done\n\n'
                return
            q = active_jobs[jid]['q']
        while True:
            try:
                msg = q.get(timeout=30)
            except queue.Empty:
                yield 'data: ⏳ czekam...\n\n'
                continue
            if msg == '__DONE__':
                yield 'data: ✅ Zadanie zakończone\n\n'
                yield 'event: done\ndata: done\n\n'
                break
            yield f'data: {msg}\n\n'

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )


@bp.route('/job/<jid>')
def job_info(jid):
    with jobs_lock:
        if jid not in active_jobs:
            return jsonify({'status': 'not_found'})
        j = active_jobs[jid]
        return jsonify({
            'status': j['status'],
            'results_count': j['results_count'],
            'has_result': j['result_path'] is not None,
            'data': j['data'],
            'preview_b64': j['preview_b64'],
        })


@bp.route('/download/<jid>')
def download_result(jid):
    with jobs_lock:
        if jid not in active_jobs:
            return 'Nie znaleziono', 404
        path = active_jobs[jid].get('result_path')
    if not path or not os.path.exists(path):
        return 'Plik niedostępny', 404
    return send_file(path, as_attachment=True)


_JID_RE = re.compile(r'[a-f0-9-]{36}')


@bp.route('/cleanup/<jid>', methods=['POST'])
def cleanup_result(jid):
    """Remove all files generated for a given job from results/."""
    if not _JID_RE.fullmatch(jid):
        return jsonify({'error': 'Niepoprawny job id'}), 400

    removed = []
    folder = RESULTS_DIR / jid
    if folder.is_dir():
        shutil.rmtree(folder, ignore_errors=True)
        removed.append(folder.name)

    for p in glob.glob(str(RESULTS_DIR / f'{jid}_*')):
        try:
            os.remove(p)
            removed.append(os.path.basename(p))
        except OSError:
            pass

    with jobs_lock:
        active_jobs.pop(jid, None)

    return jsonify({'ok': True, 'removed': len(removed), 'files': removed})


# ── Index ─────────────────────────────────────────────────────────────────────
@bp.route('/')
def index():
    last_runs = {t['id']: dict(db_last(t['id'])) if db_last(t['id']) else None
                 for t in TOOLS_META}
    return render_template('index.html', tools=TOOLS_META, last_runs=last_runs)


# ── History ───────────────────────────────────────────────────────────────────
@bp.route('/history')
def history():
    runs = db_all()
    return render_template('history.html', runs=runs)


# ── Sample CSV downloads ──────────────────────────────────────────────────────
@bp.route('/sample/<name>')
def sample_csv(name):
    if name not in SAMPLES:
        return 'Not found', 404
    filename, content = SAMPLES[name]
    return Response(content, mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={filename}'})
