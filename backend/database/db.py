"""
Database module for experiment history.
- Local development: SQLite (auto-created as experiments.db)
- Production (Render/Railway): PostgreSQL via DATABASE_URL environment variable
"""

import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_URL = os.environ.get("DATABASE_URL")  # Set by Render/Railway for PostgreSQL

# ---- Backend Selection ----
if DATABASE_URL:
    # Production: PostgreSQL
    try:
        import psycopg2
        import psycopg2.extras
        _DB_BACKEND = "postgresql"
    except ImportError:
        DATABASE_URL = None  # Fall back to SQLite if psycopg2 not installed
        _DB_BACKEND = "sqlite"
else:
    _DB_BACKEND = "sqlite"

if _DB_BACKEND == "sqlite":
    import sqlite3
    DB_PATH = os.path.join(BASE_DIR, "experiments.db")


def get_connection():
    if _DB_BACKEND == "postgresql":
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS experiment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model_id TEXT NOT NULL,
            crop_type TEXT,
            crop_days REAL,
            soil_moisture REAL,
            temperature REAL,
            humidity REAL,
            prediction INTEGER,
            label TEXT,
            probability REAL,
            inference_engine TEXT,
            inference_time_ms REAL,
            backend TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_experiment(entry: dict) -> int:
    """Save a prediction to experiment history. Returns inserted row id."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO experiment_history
        (timestamp, model_id, crop_type, crop_days, soil_moisture, temperature,
         humidity, prediction, label, probability, inference_engine, inference_time_ms, backend)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entry.get("timestamp", datetime.utcnow().isoformat()),
        entry.get("model_id", ""),
        entry.get("crop_type", ""),
        entry.get("crop_days"),
        entry.get("soil_moisture"),
        entry.get("temperature"),
        entry.get("humidity"),
        entry.get("prediction"),
        entry.get("label", ""),
        entry.get("probability"),
        entry.get("inference_engine", "TFLite"),
        entry.get("inference_time_ms"),
        entry.get("backend", "tflite"),
    ))
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_history(limit: int = 200, model_id: str = None) -> list:
    """Retrieve experiment history, most recent first."""
    conn = get_connection()
    c = conn.cursor()
    if model_id:
        c.execute("""
            SELECT * FROM experiment_history
            WHERE model_id = ?
            ORDER BY id DESC LIMIT ?
        """, (model_id, limit))
    else:
        c.execute("""
            SELECT * FROM experiment_history
            ORDER BY id DESC LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def clear_history(model_id: str = None) -> int:
    """Clear experiment history. Returns number of rows deleted."""
    conn = get_connection()
    c = conn.cursor()
    if model_id:
        c.execute("DELETE FROM experiment_history WHERE model_id = ?", (model_id,))
    else:
        c.execute("DELETE FROM experiment_history")
    count = c.rowcount
    conn.commit()
    conn.close()
    return count
