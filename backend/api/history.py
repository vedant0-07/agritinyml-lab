"""
Experiments API Blueprint
GET    /api/experiments          — list all experiments (newest first)
POST   /api/experiments          — insert a new experiment row
DELETE /api/experiments          — delete all experiments
GET    /api/experiments/export   — download all experiments as CSV

Legacy aliases kept for backwards compatibility:
GET    /api/history              → /api/experiments
POST   /api/history/clear        → DELETE /api/experiments
GET    /api/history/export       → /api/experiments/export
"""

from flask import Blueprint, jsonify, request, make_response
from backend.database.db import (
    get_experiments, save_experiment, delete_experiments, experiments_to_csv
)

history_bp = Blueprint("history", __name__)


# ── Primary endpoints ────────────────────────────────────────────────────────

@history_bp.route("/api/experiments", methods=["GET"])
def list_experiments():
    """Return all experiments ordered by timestamp DESC."""
    limit    = int(request.args.get("limit", 200))
    model_id = request.args.get("model_id", type=int)
    try:
        rows = get_experiments(limit=limit, model_id=model_id)
        return jsonify({"success": True, "count": len(rows), "experiments": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "experiments": []}), 503


@history_bp.route("/api/experiments", methods=["POST"])
def create_experiment():
    """Insert a new experiment row. Body is JSON matching the experiments schema."""
    data = request.get_json(silent=True) or {}
    try:
        row_id = save_experiment(data)
        return jsonify({"success": True, "id": row_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@history_bp.route("/api/experiments", methods=["DELETE"])
def remove_experiments():
    """Delete all experiments (or filter by model_id query param)."""
    model_id = request.args.get("model_id", type=int)
    try:
        count = delete_experiments(model_id=model_id)
        return jsonify({"success": True, "deleted": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@history_bp.route("/api/experiments/export", methods=["GET"])
def export_experiments_csv():
    """Download all experiments as a CSV file."""
    model_id = request.args.get("model_id", type=int)
    csv_data = experiments_to_csv(model_id=model_id)
    resp = make_response(csv_data)
    resp.headers["Content-Disposition"] = "attachment; filename=agritinyml_experiments.csv"
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    return resp


# ── Legacy aliases (frontend JS still uses /api/history/*) ───────────────────

@history_bp.route("/api/history", methods=["GET"])
def legacy_history():
    limit    = int(request.args.get("limit", 200))
    model_id = request.args.get("model_id", type=int)
    rows = get_experiments(limit=limit, model_id=model_id)
    # Keep old key name "history" so existing JS doesn't break
    return jsonify({"success": True, "count": len(rows), "history": rows})


@history_bp.route("/api/history/clear", methods=["POST"])
def legacy_clear():
    model_id = request.args.get("model_id", type=int)
    count = delete_experiments(model_id=model_id)
    return jsonify({"success": True, "deleted": count,
                    "message": f"Cleared {count} experiment records."})


@history_bp.route("/api/history/export", methods=["GET"])
def legacy_export():
    model_id = request.args.get("model_id", type=int)
    csv_data = experiments_to_csv(model_id=model_id)
    resp = make_response(csv_data)
    resp.headers["Content-Disposition"] = "attachment; filename=experiment_history.csv"
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    return resp
