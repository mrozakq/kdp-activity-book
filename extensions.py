import json
import sqlite3

from config import DB_PATH


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT NOT NULL,
            params_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'running',
            results_count INTEGER DEFAULT 0,
            output_log TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
        conn.commit()


def db_save(tool: str, params: dict) -> int:
    with get_db() as conn:
        cur = conn.execute(
            'INSERT INTO runs (tool_name, params_json) VALUES (?,?)',
            (tool, json.dumps(params, ensure_ascii=False))
        )
        conn.commit()
        return cur.lastrowid


def db_update(rid: int, status: str, count: int = 0, log: str = ''):
    with get_db() as conn:
        conn.execute(
            'UPDATE runs SET status=?, results_count=?, output_log=? WHERE id=?',
            (status, count, log[-5000:], rid)
        )
        conn.commit()


def db_last(tool: str):
    with get_db() as conn:
        return conn.execute(
            'SELECT * FROM runs WHERE tool_name=? ORDER BY id DESC LIMIT 1', (tool,)
        ).fetchone()


def db_all():
    with get_db() as conn:
        return conn.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 100').fetchall()
