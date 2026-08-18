"""
AgriTinyML Lab — Database Module (Supabase PostgreSQL)
TEAM TRONICS | Group B2

Uses psycopg2 with RealDictCursor so rows come back as plain dicts,
identical to the old SQLite row_factory behaviour.

DATABASE_URL must be set as an environment variable:
  postgresql://postgres:PASSWORD@db.XXXX.supabase.co:5432/postgres
"""

import os
import json
import csv
import io
import logging
from datetime import datetime, timezone
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

log = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    log.warning(
        "[DB] DATABASE_URL is not set. Database features will be unavailable "
        "until you set the environment variable and restart."
    )


# ── Connection helper ────────────────────────────────────────────────────────

@contextmanager
def get_conn():
    """Context manager: yields a psycopg2 connection, commits on success,
    rolls back on exception, always closes."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Set it to your Supabase connection string and restart the app."
        )
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()



# ── Schema ───────────────────────────────────────────────────────────────────

_CREATE_MODELS = """
CREATE TABLE IF NOT EXISTS models (
    id              SERIAL PRIMARY KEY,
    model_number    TEXT UNIQUE,
    name            TEXT,
    description     TEXT,
    architecture    TEXT,
    input_features  TEXT,
    output_classes  TEXT,
    accuracy        REAL,
    model_size_kb   REAL,
    tflite_url      TEXT,
    preprocessor_url TEXT,
    status          TEXT DEFAULT 'coming_soon',
    uploaded_at     TIMESTAMPTZ DEFAULT NOW(),
    uploaded_by     TEXT
);
"""

_CREATE_EXPERIMENTS = """
CREATE TABLE IF NOT EXISTS experiments (
    id               SERIAL PRIMARY KEY,
    timestamp        TIMESTAMPTZ DEFAULT NOW(),
    model_id         INTEGER,
    model_name       TEXT,
    crop_type        TEXT,
    crop_days        INTEGER,
    soil_moisture    REAL,
    temperature      REAL,
    humidity         REAL,
    prediction       TEXT,
    probability      REAL,
    engine           TEXT,
    inference_time_ms REAL,
    inputs           JSONB
);
"""

# Seed data for the models table
_SEED_MODELS = [
    {
        "model_number": "MODEL_01",
        "name": "Irrigation Prediction",
        "description": (
            "Binary classification TinyML model that predicts whether irrigation is required "
            "based on crop type, crop age, soil moisture, temperature and humidity. "
            "INT8 quantized for edge deployment."
        ),
        "architecture": "MLP 13→32→16→8→1 (Sigmoid)",
        "input_features": "CropType (one-hot 9), CropDays, SoilMoisture, temperature, Humidity",
        "output_classes": "0=No Irrigation Required, 1=Irrigation Required",
        "accuracy": 96.05,
        "model_size_kb": 5.50,
        "tflite_url": None,
        "preprocessor_url": None,
        "status": "ready",
        "uploaded_by": "TEAM TRONICS",
    },
    {
        "model_number": "MODEL_02",
        "name": "Crop Disease Detection",
        "description": (
            "Detect crop diseases from sensor readings or image features "
            "to enable early intervention and reduce crop loss."
        ),
        "architecture": "TBD",
        "input_features": "TBD",
        "output_classes": "Multi-class disease categories",
        "accuracy": None,
        "model_size_kb": None,
        "tflite_url": None,
        "preprocessor_url": None,
        "status": "coming_soon",
        "uploaded_by": "TEAM TRONICS",
    },
    {
        "model_number": "MODEL_03",
        "name": "Pest Identification",
        "description": (
            "Identify agricultural pests from field data or image-derived features, "
            "enabling precise and timely pest management."
        ),
        "architecture": "TBD",
        "input_features": "TBD",
        "output_classes": "Multi-class pest categories",
        "accuracy": None,
        "model_size_kb": None,
        "tflite_url": None,
        "preprocessor_url": None,
        "status": "coming_soon",
        "uploaded_by": "TEAM TRONICS",
    },
    {
        "model_number": "MODEL_04",
        "name": "Fertilizer Recommendation",
        "description": (
            "Recommend fertilizer type and quantity based on soil NPK levels, pH, and moisture. "
            "Outputs one of five classes — No Fertilizer, Apply Urea, Apply DAP, Apply MOP, Apply NPK Mix."
        ),
        "architecture": "TBD",
        "input_features": "Nitrogen (N), Phosphorus (P), Potassium (K), pH, Soil Moisture",
        "output_classes": "0=No Fertilizer, 1=Apply Urea, 2=Apply DAP, 3=Apply MOP, 4=Apply NPK Mix",
        "accuracy": None,
        "model_size_kb": None,
        "tflite_url": None,
        "preprocessor_url": None,
        "status": "coming_soon",
        "uploaded_by": "TEAM TRONICS",
    },
]


# ── init_db ──────────────────────────────────────────────────────────────────

def init_db():
    """
    Create tables and seed models on first run.
    Safe to call multiple times (uses IF NOT EXISTS + ON CONFLICT DO NOTHING).
    Called once at Flask startup in app.py.
    """
    with get_conn() as conn:
        cur = conn.cursor()

        # Create tables
        cur.execute(_CREATE_MODELS)
        cur.execute(_CREATE_EXPERIMENTS)

        # Seed model registry — INSERT or UPDATE so name/description changes take effect
        for m in _SEED_MODELS:
            cur.execute("""
                INSERT INTO models
                    (model_number, name, description, architecture, input_features,
                     output_classes, accuracy, model_size_kb, tflite_url,
                     preprocessor_url, status, uploaded_by)
                VALUES
                    (%(model_number)s, %(name)s, %(description)s, %(architecture)s,
                     %(input_features)s, %(output_classes)s, %(accuracy)s,
                     %(model_size_kb)s, %(tflite_url)s, %(preprocessor_url)s,
                     %(status)s, %(uploaded_by)s)
                ON CONFLICT (model_number) DO UPDATE SET
                    name          = EXCLUDED.name,
                    description   = EXCLUDED.description,
                    input_features = EXCLUDED.input_features,
                    output_classes = EXCLUDED.output_classes
            """, m)

        log.info("[DB] Tables ready. Model registry seeded/updated.")



# ── Models table helpers ─────────────────────────────────────────────────────

def get_all_models() -> list:
    """Return all rows from the models table ordered by model_number."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM models ORDER BY model_number")
        return [dict(r) for r in cur.fetchall()]


def get_model_by_number(model_number: str) -> dict | None:
    """Return a single model row by model_number, or None if not found."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM models WHERE model_number = %s", (model_number,))
        row = cur.fetchone()
        return dict(row) if row else None


# ── Experiments table helpers ────────────────────────────────────────────────

def save_experiment(entry: dict) -> int:
    """
    Insert one experiment row.
    Returns the new row id.

    Expected keys in `entry`:
        model_id, model_name, crop_type, crop_days, soil_moisture,
        temperature, humidity, prediction, probability,
        engine, inference_time_ms, inputs (dict → stored as JSONB)
    """
    inputs_json = json.dumps(entry.get("inputs", {}))
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO experiments
                (model_id, model_name, crop_type, crop_days, soil_moisture,
                 temperature, humidity, prediction, probability,
                 engine, inference_time_ms, inputs)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            entry.get("model_id"),
            entry.get("model_name", ""),
            entry.get("crop_type", ""),
            entry.get("crop_days"),
            entry.get("soil_moisture"),
            entry.get("temperature"),
            entry.get("humidity"),
            entry.get("prediction", ""),
            entry.get("probability"),
            entry.get("engine", "TFLite"),
            entry.get("inference_time_ms"),
            inputs_json,
        ))
        row = cur.fetchone()
        return row["id"] if row else -1


def get_experiments(limit: int = 200, model_id: int = None) -> list:
    """Return experiments ordered by timestamp DESC."""
    with get_conn() as conn:
        cur = conn.cursor()
        if model_id is not None:
            cur.execute("""
                SELECT * FROM experiments
                WHERE model_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (model_id, limit))
        else:
            cur.execute("""
                SELECT * FROM experiments
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            # Timestamp → ISO string for JSON serialisation
            if d.get("timestamp") and hasattr(d["timestamp"], "isoformat"):
                d["timestamp"] = d["timestamp"].isoformat()
            # inputs JSONB → already a dict from psycopg2, ensure it's serialisable
            if isinstance(d.get("inputs"), str):
                try:
                    d["inputs"] = json.loads(d["inputs"])
                except Exception:
                    pass
            result.append(d)
        return result


def delete_experiments(model_id: int = None) -> int:
    """Delete experiments. Returns number of rows deleted."""
    with get_conn() as conn:
        cur = conn.cursor()
        if model_id is not None:
            cur.execute("DELETE FROM experiments WHERE model_id = %s", (model_id,))
        else:
            cur.execute("DELETE FROM experiments")
        return cur.rowcount


def experiments_to_csv(model_id: int = None) -> str:
    """Return all experiments as a CSV string."""
    rows = get_experiments(limit=100000, model_id=model_id)
    if not rows:
        return "No experiment data available.\n"
    output = io.StringIO()
    fields = ["id", "timestamp", "model_id", "model_name", "crop_type",
              "crop_days", "soil_moisture", "temperature", "humidity",
              "prediction", "probability", "engine", "inference_time_ms"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


# ── Admin helpers ─────────────────────────────────────────────────────────────

def update_model_metadata(model_number: str, fields: dict) -> bool:
    """Update editable metadata fields for a model. Ignores unknown keys."""
    allowed = {"name", "description", "accuracy", "architecture",
               "input_features", "output_classes"}
    safe = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not safe:
        return False
    set_clause = ", ".join(f"{k} = %s" for k in safe)
    vals = list(safe.values()) + [model_number]
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE models SET {set_clause} WHERE model_number = %s", vals)
        return cur.rowcount > 0


def reset_model_to_seed(model_number: str) -> bool:
    """Reset a model row to its original seed defaults (coming_soon, no files)."""
    seed = next((m for m in _SEED_MODELS if m["model_number"] == model_number), None)
    if not seed:
        return False
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE models SET
                name = %(name)s,
                description = %(description)s,
                architecture = %(architecture)s,
                input_features = %(input_features)s,
                output_classes = %(output_classes)s,
                accuracy = %(accuracy)s,
                model_size_kb = %(model_size_kb)s,
                tflite_url = NULL,
                preprocessor_url = NULL,
                status = 'coming_soon'
            WHERE model_number = %(model_number)s
        """, {**seed, "model_number": model_number})
        return cur.rowcount > 0


def toggle_model_status(model_number: str) -> str:
    """Toggle model status between ready and coming_soon. Returns new status."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE models
            SET status = CASE WHEN status = 'ready' THEN 'coming_soon' ELSE 'ready' END
            WHERE model_number = %s
            RETURNING status
        """, (model_number,))
        row = cur.fetchone()
        return row["status"] if row else "unknown"


def set_model_files(model_number: str, tflite_url: str = None,
                    preprocessor_url: str = None) -> bool:
    """Update file URLs and mark model as ready when tflite_url is provided."""
    updates, vals = [], []
    if tflite_url is not None:
        updates.append("tflite_url = %s")
        vals.append(tflite_url)
        updates.append("status = 'ready'")
    if preprocessor_url is not None:
        updates.append("preprocessor_url = %s")
        vals.append(preprocessor_url)
    if not updates:
        return False
    vals.append(model_number)
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE models SET {', '.join(updates)} WHERE model_number = %s",
            vals
        )
        return cur.rowcount > 0


def get_experiment_stats() -> dict:
    """Return quick stats for the admin dashboard."""
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) AS total FROM experiments")
        total = cur.fetchone()["total"] or 0

        cur.execute(
            "SELECT COUNT(*) AS today FROM experiments "
            "WHERE timestamp::date = CURRENT_DATE"
        )
        today = cur.fetchone()["today"] or 0

        cur.execute(
            "SELECT prediction, COUNT(*) AS cnt FROM experiments "
            "GROUP BY prediction ORDER BY cnt DESC LIMIT 1"
        )
        row = cur.fetchone()
        most_common = row["prediction"] if row else "N/A"

        cur.execute(
            "SELECT ROUND(AVG(inference_time_ms)::numeric, 3) AS avg_ms "
            "FROM experiments WHERE inference_time_ms IS NOT NULL"
        )
        row = cur.fetchone()
        avg_ms = float(row["avg_ms"]) if row and row["avg_ms"] else 0.0

        cur.execute(
            "SELECT model_name, COUNT(*) AS cnt FROM experiments "
            "GROUP BY model_name ORDER BY cnt DESC LIMIT 1"
        )
        row = cur.fetchone()
        top_model = row["model_name"] if row else "N/A"

        return {
            "total":       total,
            "today":       today,
            "most_common": most_common,
            "avg_ms":      avg_ms,
            "top_model":   top_model,
        }


def get_experiments_page(page: int = 1, per_page: int = 20,
                         pred_filter: str = None) -> dict:
    """Return paginated experiments with total count and page info."""
    offset = (page - 1) * per_page
    with get_conn() as conn:
        cur = conn.cursor()

        if pred_filter:
            where      = "WHERE prediction ILIKE %s"
            count_args = (f"%{pred_filter}%",)
            data_args  = (f"%{pred_filter}%", per_page, offset)
        else:
            where      = ""
            count_args = ()
            data_args  = (per_page, offset)

        cur.execute(f"SELECT COUNT(*) AS total FROM experiments {where}", count_args)
        total = cur.fetchone()["total"] or 0

        cur.execute(f"""
            SELECT id, timestamp, model_name, crop_type, crop_days,
                   soil_moisture, temperature, humidity, prediction,
                   probability, engine, inference_time_ms
            FROM experiments {where}
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """, data_args)

        rows = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("timestamp") and hasattr(d["timestamp"], "isoformat"):
                d["timestamp"] = d["timestamp"].isoformat()
            rows.append(d)

        total_pages = max(1, (total + per_page - 1) // per_page)
        return {
            "rows":        rows,
            "total":       total,
            "page":        page,
            "per_page":    per_page,
            "total_pages": total_pages,
        }

