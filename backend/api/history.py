"""
History API Blueprint
GET  /api/history
POST /api/history/clear
"""

import csv
import io
from flask import Blueprint, jsonify, request, make_response
from backend.database.db import get_history, clear_history

history_bp = Blueprint("history", __name__)


@history_bp.route("/api/history", methods=["GET"])
def get_experiment_history():
    model_id = request.args.get("model_id")
    limit = int(request.args.get("limit", 200))
    rows = get_history(limit=limit, model_id=model_id)
    return jsonify({
        "success": True,
        "count": len(rows),
        "history": rows
    })


@history_bp.route("/api/history/clear", methods=["POST"])
def clear_experiment_history():
    model_id = request.args.get("model_id")
    count = clear_history(model_id=model_id)
    return jsonify({
        "success": True,
        "deleted": count,
        "message": f"Cleared {count} experiment records."
    })


@history_bp.route("/api/history/export", methods=["GET"])
def export_history_csv():
    model_id = request.args.get("model_id")
    rows = get_history(limit=10000, model_id=model_id)

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        output.write("No experiment data available.\n")

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=experiment_history.csv"
    response.headers["Content-Type"] = "text/csv"
    return response
