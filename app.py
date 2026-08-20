"""
AgriTinyML Lab — Flask Application
TEAM TRONICS | Group B2
Run: python app.py
URL: http://127.0.0.1:5000
"""

import os
import sys
from datetime import timedelta

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# --- App Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static"),
    static_url_path="/static"
)
CORS(app)
app.config["JSON_SORT_KEYS"] = False

# Secret key for admin sessions (MUST be set as env var in production)
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY",
    os.urandom(32)  # fallback: sessions reset on restart — acceptable for local dev
)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)

# --- Register API Blueprints ---
from backend.api.predict import predict_bp
from backend.api.evaluate import evaluate_bp
from backend.api.history import history_bp
from backend.api.project import project_bp
from backend.api.admin import admin_bp

app.register_blueprint(predict_bp)
app.register_blueprint(evaluate_bp)
app.register_blueprint(history_bp)
app.register_blueprint(project_bp)
app.register_blueprint(admin_bp)

# --- Initialize Database (Supabase PostgreSQL) ---
try:
    from backend.database.db import init_db
    init_db()
    print("[AgriTinyML] Database: connected and tables ready (Supabase PostgreSQL)")
except Exception as _db_err:
    print(f"[AgriTinyML] WARNING: Database init failed — {_db_err}")
    print("[AgriTinyML] Ensure DATABASE_URL environment variable is set correctly.")


# --- Load Models at Startup ---
from backend.inference.manager import inference_manager
from backend.models.registry import get_model_file_path

def _load_models():
    int8_path = get_model_file_path("irrigation", "int8")
    if int8_path:
        status = inference_manager.load_model("irrigation", os.path.relpath(int8_path, BASE_DIR))
        print(f"[AgriTinyML] Irrigation INT8 model: {status.get('status', 'unknown')}")
    else:
        print("[AgriTinyML] WARNING: irrigation_model_int8.tflite not found.")

    # MODEL_05 — Test 1 (Fertilizer, 19 classes)
    f1_path = os.path.join(BASE_DIR, "models", "model05", "model_int8.tflite")
    if os.path.exists(f1_path):
        s = inference_manager.load_model("fertilizer1", os.path.relpath(f1_path, BASE_DIR))
        print(f"[AgriTinyML] Fertilizer1 (Test 1) model: {s.get('status', 'unknown')}")
    else:
        print("[AgriTinyML] WARNING: models/model05/model_int8.tflite not found.")

    # MODEL_06 — Test 2 (Fertilizer, 7 classes)
    f2_path = os.path.join(BASE_DIR, "models", "model06", "model_int8.tflite")
    if os.path.exists(f2_path):
        s = inference_manager.load_model("fertilizer2", os.path.relpath(f2_path, BASE_DIR))
        print(f"[AgriTinyML] Fertilizer2 (Test 2) model: {s.get('status', 'unknown')}")
    else:
        print("[AgriTinyML] WARNING: models/model06/model_int8.tflite not found.")

_load_models()

# --- Verify Preprocessors ---
from backend.preprocessing.irrigation import irrigation_preprocessor
from backend.preprocessing.fertilizer import fertilizer1_preprocessor, fertilizer2_preprocessor
print(f"[AgriTinyML] Preprocessor — Irrigation:   {irrigation_preprocessor.status}")
print(f"[AgriTinyML] Preprocessor — Fertilizer1:  {fertilizer1_preprocessor.status}")
print(f"[AgriTinyML] Preprocessor — Fertilizer2:  {fertilizer2_preprocessor.status}")
if fertilizer1_preprocessor.status == "error":
    print(f"[AgriTinyML]   Fertilizer1 error: {fertilizer1_preprocessor.error_message}")
if fertilizer2_preprocessor.status == "error":
    print(f"[AgriTinyML]   Fertilizer2 error: {fertilizer2_preprocessor.error_message}")

# --- Frontend Routes ---
@app.route("/")
def index():
    return send_from_directory(
        os.path.join(BASE_DIR, "frontend", "templates"), "index.html"
    )

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found."}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"success": False, "error": "Internal server error."}), 500

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "error": "Method not allowed."}), 405

# --- Health Check ---
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "project": "AgriTinyML Lab",
        "team": "TEAM TRONICS",
        "group": "B2",
        "inference_model": "Irrigation TinyML INT8",
        "fpga": "not_connected"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = "127.0.0.1" if port == 5000 else "0.0.0.0"
    debug = port == 5000  # Debug only in local dev
    print("=" * 60)
    print("  AgriTinyML Lab — TEAM TRONICS | Group B2")
    print("  Design Adaptive Reconfigurable TinyML Edge Accelerator")
    print("=" * 60)
    print(f"  Starting server at http://{host}:{port}")
    print(f"  Press Ctrl+C to stop")
    print("=" * 60)
    app.run(host=host, port=port, debug=debug, use_reloader=False)
