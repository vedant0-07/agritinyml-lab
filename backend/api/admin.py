"""
Admin Blueprint — /admin
TEAM TRONICS | Group B2

Protected by Flask session-based authentication.
Credentials read from ADMIN_USERNAME and ADMIN_PASSWORD env vars (never hardcoded).
Supabase Storage used for file uploads (SUPABASE_URL + SUPABASE_KEY env vars).
"""

import os
from functools import wraps
from datetime import datetime, timedelta

from werkzeug.utils import secure_filename
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, make_response, get_flashed_messages)

from backend.database.db import (
    get_all_models, get_model_by_number,
    update_model_metadata, reset_model_to_seed,
    toggle_model_status, set_model_files,
    get_experiment_stats, get_experiments_page,
    delete_experiments, experiments_to_csv,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

STORAGE_BUCKET = "tinyml-models"
ALLOWED_TFLITE = {"tflite"}
ALLOWED_PKL    = {"pkl"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ext_ok(filename: str, allowed: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _get_supabase():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY environment variables must be set "
            "to enable file uploads."
        )
    try:
        from supabase import create_client
    except ImportError:
        raise RuntimeError(
            "supabase package is not installed. Run: pip install supabase>=2.3.0"
        )
    return create_client(url, key)


def admin_required(f):
    """Decorator — redirects to /admin/login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


# ── Auth routes ───────────────────────────────────────────────────────────────

@admin_bp.route("/")
def index():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("admin.login"))


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        env_user = os.environ.get("ADMIN_USERNAME", "")
        env_pass = os.environ.get("ADMIN_PASSWORD", "")

        if not env_user or not env_pass:
            error = ("Admin credentials are not configured on the server. "
                     "Set ADMIN_USERNAME and ADMIN_PASSWORD in environment variables.")
        elif username == env_user and password == env_pass:
            session.permanent = True
            session["admin_logged_in"] = True
            session["admin_user"] = username
            flash("Logged in successfully.", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@admin_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin.login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    active_tab  = request.args.get("tab", "overview")
    page        = max(1, int(request.args.get("page", 1)))
    pred_filter = request.args.get("pred", "")

    models    = []
    stats     = {}
    exp_rows  = []
    total_pages = 1
    total_exp   = 0
    db_error    = None

    try:
        models    = get_all_models()
        stats     = get_experiment_stats()
        exp_data  = get_experiments_page(page=page, per_page=20,
                                         pred_filter=pred_filter or None)
        exp_rows    = exp_data["rows"]
        total_pages = exp_data["total_pages"]
        total_exp   = exp_data["total"]
    except Exception as exc:
        db_error = str(exc)

    messages = get_flashed_messages(with_categories=True)

    return render_template(
        "admin_dashboard.html",
        models      = models,
        stats       = stats,
        experiments = exp_rows,
        total_pages = total_pages,
        total_exp   = total_exp,
        current_page = page,
        pred_filter = pred_filter,
        active_tab  = active_tab,
        db_error    = db_error,
        admin_user  = session.get("admin_user", "Admin"),
        messages    = messages,
    )


# ── Model Upload ──────────────────────────────────────────────────────────────

@admin_bp.route("/upload", methods=["POST"])
@admin_required
def upload_model():
    model_number   = request.form.get("model_number", "").strip()
    model_name     = request.form.get("model_name", "").strip()
    description    = request.form.get("description", "").strip()
    architecture   = request.form.get("architecture", "").strip()
    input_features = request.form.get("input_features", "").strip()
    output_classes = request.form.get("output_classes", "").strip()
    accuracy_raw   = request.form.get("accuracy", "").strip()
    tflite_file    = request.files.get("tflite_file")
    pkl_file       = request.files.get("pkl_file")

    # ── Validation ────────────────────────────────────────────────────────────
    if not model_number:
        flash("Model number is required.", "error")
        return redirect(url_for("admin.dashboard", tab="upload"))

    if not tflite_file or not tflite_file.filename:
        flash("TFLite model file is required.", "error")
        return redirect(url_for("admin.dashboard", tab="upload"))

    if not _ext_ok(tflite_file.filename, ALLOWED_TFLITE):
        flash("TFLite file must have a .tflite extension.", "error")
        return redirect(url_for("admin.dashboard", tab="upload"))

    if pkl_file and pkl_file.filename and not _ext_ok(pkl_file.filename, ALLOWED_PKL):
        flash("Preprocessor file must have a .pkl extension.", "error")
        return redirect(url_for("admin.dashboard", tab="upload"))

    try:
        accuracy = float(accuracy_raw) if accuracy_raw else None
    except ValueError:
        flash("Accuracy must be a number between 0 and 100.", "error")
        return redirect(url_for("admin.dashboard", tab="upload"))

    # ── Upload to Supabase Storage ────────────────────────────────────────────
    try:
        sb = _get_supabase()

        # Create bucket if it doesn't exist (public = True for CDN URLs)
        try:
            sb.storage.create_bucket(STORAGE_BUCKET, options={"public": True})
        except Exception:
            pass  # Bucket already exists

        folder      = model_number.lower().replace("_", "-")
        tflite_path = f"{folder}/model_int8.tflite"
        tflite_bytes = tflite_file.read()

        sb.storage.from_(STORAGE_BUCKET).upload(
            path=tflite_path,
            file=tflite_bytes,
            file_options={"content-type": "application/octet-stream", "upsert": "true"},
        )
        tflite_url = sb.storage.from_(STORAGE_BUCKET).get_public_url(tflite_path)

        pkl_url = None
        if pkl_file and pkl_file.filename:
            pkl_path  = f"{folder}/preprocessor.pkl"
            pkl_bytes = pkl_file.read()
            sb.storage.from_(STORAGE_BUCKET).upload(
                path=pkl_path,
                file=pkl_bytes,
                file_options={"content-type": "application/octet-stream", "upsert": "true"},
            )
            pkl_url = sb.storage.from_(STORAGE_BUCKET).get_public_url(pkl_path)

    except Exception as exc:
        flash(f"Storage upload failed: {exc}", "error")
        return redirect(url_for("admin.dashboard", tab="upload"))

    # ── Update database ───────────────────────────────────────────────────────
    try:
        update_model_metadata(model_number, {
            "name":          model_name,
            "description":   description,
            "architecture":  architecture,
            "input_features": input_features,
            "output_classes": output_classes,
            "accuracy":      accuracy,
        })
        set_model_files(model_number, tflite_url=tflite_url, preprocessor_url=pkl_url)
        flash(f"✓ {model_name or model_number} uploaded and marked as READY.", "success")
    except Exception as exc:
        flash(f"Database update failed: {exc}", "error")

    return redirect(url_for("admin.dashboard", tab="models"))


# ── Model Management ──────────────────────────────────────────────────────────

@admin_bp.route("/model/<model_number>/toggle", methods=["POST"])
@admin_required
def toggle_model(model_number):
    try:
        new_status = toggle_model_status(model_number)
        label = "READY" if new_status == "ready" else "COMING SOON"
        flash(f"{model_number} status set to {label}.", "success")
    except Exception as exc:
        flash(f"Toggle failed: {exc}", "error")
    return redirect(url_for("admin.dashboard", tab="models"))


@admin_bp.route("/model/<model_number>/edit", methods=["POST"])
@admin_required
def edit_model(model_number):
    try:
        acc_raw  = request.form.get("accuracy", "").strip()
        accuracy = float(acc_raw) if acc_raw else None
        update_model_metadata(model_number, {
            "name":        request.form.get("name", "").strip(),
            "description": request.form.get("description", "").strip(),
            "accuracy":    accuracy,
        })
        flash(f"{model_number} updated successfully.", "success")
    except Exception as exc:
        flash(f"Edit failed: {exc}", "error")
    return redirect(url_for("admin.dashboard", tab="models"))


@admin_bp.route("/model/<model_number>/reset", methods=["POST"])
@admin_required
def reset_model(model_number):
    try:
        reset_model_to_seed(model_number)
        flash(f"{model_number} has been reset to defaults (coming_soon).", "info")
    except Exception as exc:
        flash(f"Reset failed: {exc}", "error")
    return redirect(url_for("admin.dashboard", tab="models"))


# ── Experiment Management ─────────────────────────────────────────────────────

@admin_bp.route("/experiments/clear", methods=["POST"])
@admin_required
def clear_experiments():
    try:
        count = delete_experiments()
        flash(f"Cleared {count} experiment records.", "info")
    except Exception as exc:
        flash(f"Clear failed: {exc}", "error")
    return redirect(url_for("admin.dashboard", tab="experiments"))


@admin_bp.route("/experiments/export")
@admin_required
def export_experiments():
    try:
        csv_data = experiments_to_csv()
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        resp = make_response(csv_data)
        resp.headers["Content-Disposition"] = (
            f"attachment; filename=agritinyml_experiments_{ts}.csv"
        )
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        return resp
    except Exception as exc:
        flash(f"Export failed: {exc}", "error")
        return redirect(url_for("admin.dashboard", tab="experiments"))
