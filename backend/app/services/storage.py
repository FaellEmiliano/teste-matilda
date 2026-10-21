import json
import os
import sqlite3
import time
from pathlib import Path
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'data'

def database_path():
    return Path(os.getenv('MATILDA_DB', str(ROOT / '.runtime/matilda.db')))

@contextmanager
def connection():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path, timeout=10) as db:
        db.execute('CREATE TABLE IF NOT EXISTS cache (doi TEXT PRIMARY KEY, payload TEXT NOT NULL, retrieved_at TEXT NOT NULL, stored_at REAL NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS analyses (id TEXT PRIMARY KEY, payload TEXT NOT NULL, stored_at REAL NOT NULL)')
        db.execute('DELETE FROM analyses WHERE stored_at < ?', (time.time() - 7 * 86400,))
        yield db

def load_json(name):
    return json.loads((DATA / name).read_text())

def cached(doi):
    with connection() as db:
        row = db.execute('SELECT payload, retrieved_at, stored_at FROM cache WHERE doi = ?', (doi,)).fetchone()
    if row:
        return json.loads(row[0]), row[1], time.time() - row[2]
    path = DATA / 'openalex_snapshots' / (doi.replace('/', '_') + '.json')
    if path.exists():
        from datetime import datetime
        snapshot = json.loads(path.read_text())
        return snapshot['data'], snapshot['retrieved_at'], time.time() - datetime.fromisoformat(snapshot['retrieved_at']).timestamp()
    return None

def save_cache(doi, raw, retrieved_at):
    with connection() as db:
        db.execute('INSERT OR REPLACE INTO cache VALUES (?, ?, ?, ?)', (doi, json.dumps(raw), retrieved_at, time.time()))

def save_analysis(analysis):
    with connection() as db:
        db.execute('INSERT INTO analyses VALUES (?, ?, ?)', (analysis.id, analysis.model_dump_json(), time.time()))

def get_analysis(identifier):
    with connection() as db:
        row = db.execute('SELECT payload FROM analyses WHERE id = ?', (identifier,)).fetchone()
    return json.loads(row[0]) if row else None
