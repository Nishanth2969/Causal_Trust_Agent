import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import Optional
from .constants import RUNS_DIR, SQLITE_PATH

def _get_db():
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            mode TEXT NOT NULL,
            mttr_human_s REAL,
            mttr_cta_s REAL,
            status TEXT,
            fail_reason TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            run_id TEXT NOT NULL,
            idx INTEGER NOT NULL,
            json_blob TEXT NOT NULL,
            PRIMARY KEY (run_id, idx),
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)
    conn.commit()
    conn.close()

def start_run(mode: str) -> str:
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    started_at = datetime.utcnow().isoformat()
    
    conn = _get_db()
    conn.execute(
        "INSERT INTO runs (id, started_at, mode, status) VALUES (?, ?, ?, ?)",
        (run_id, started_at, mode, "running")
    )
    conn.commit()
    conn.close()
    
    os.makedirs(RUNS_DIR, exist_ok=True)
    jsonl_path = os.path.join(RUNS_DIR, f"{run_id}.jsonl")
    open(jsonl_path, 'w').close()
    
    return run_id

def append_event(run_id: str, event: dict) -> int:
    conn = _get_db()
    cursor = conn.execute(
        "SELECT COALESCE(MAX(idx), -1) FROM events WHERE run_id = ?",
        (run_id,)
    )
    max_idx = cursor.fetchone()[0]
    idx = max_idx + 1
    
    event_copy = event.copy()
    event_copy["idx"] = idx
    
    json_blob = json.dumps(event_copy)
    conn.execute(
        "INSERT INTO events (run_id, idx, json_blob) VALUES (?, ?, ?)",
        (run_id, idx, json_blob)
    )
    conn.commit()
    conn.close()
    
    jsonl_path = os.path.join(RUNS_DIR, f"{run_id}.jsonl")
    with open(jsonl_path, 'a') as f:
        f.write(json_blob + '\n')
    
    return idx

def list_runs() -> list[dict]:
    conn = _get_db()
    cursor = conn.execute(
        "SELECT * FROM runs ORDER BY started_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def load_events(run_id: str) -> list[dict]:
    conn = _get_db()
    cursor = conn.execute(
        "SELECT json_blob FROM events WHERE run_id = ? ORDER BY idx",
        (run_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    return [json.loads(row[0]) for row in rows]

def save_metric(run_id: str, key: str, value):
    allowed_keys = {"mttr_human_s", "mttr_cta_s", "status", "fail_reason"}
    if key not in allowed_keys:
        raise ValueError(f"Invalid metric key: {key}")
    
    conn = _get_db()
    conn.execute(
        f"UPDATE runs SET {key} = ? WHERE id = ?",
        (value, run_id)
    )
    conn.commit()
    conn.close()

def get_run(run_id: str) -> Optional[dict]:
    conn = _get_db()
    cursor = conn.execute(
        "SELECT * FROM runs WHERE id = ?",
        (run_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

init_db()

