import queue
import threading
import uuid

active_jobs: dict = {}
jobs_lock = threading.Lock()


def create_job() -> str:
    jid = str(uuid.uuid4())
    with jobs_lock:
        active_jobs[jid] = {
            'q': queue.Queue(),
            'status': 'running',
            'result_path': None,
            'results_count': 0,
            'data': None,
            'preview_b64': None,
        }
    return jid


def jlog(jid: str, msg: str):
    with jobs_lock:
        if jid in active_jobs:
            active_jobs[jid]['q'].put(msg)


def jdone(jid: str, result_path=None, count=0, data=None, preview_b64=None):
    with jobs_lock:
        if jid in active_jobs:
            j = active_jobs[jid]
            j['status'] = 'done'
            j['result_path'] = result_path
            j['results_count'] = count
            j['data'] = data
            j['preview_b64'] = preview_b64
            j['q'].put('__DONE__')


def jerror(jid: str, msg: str):
    with jobs_lock:
        if jid in active_jobs:
            active_jobs[jid]['status'] = 'error'
            active_jobs[jid]['q'].put(f'❌ BŁĄD: {msg}')
            active_jobs[jid]['q'].put('__DONE__')
