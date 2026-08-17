"""
Evaluate API Blueprint
POST /api/evaluate/<model_id>
Runs the complete test set through the actual model and returns real metrics.
"""

import os
import time
import numpy as np
import pandas as pd
from flask import Blueprint, jsonify

from backend.inference.manager import inference_manager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

evaluate_bp = Blueprint("evaluate", __name__)

LABEL_MAP = {0: "No Irrigation Required", 1: "Irrigation Required"}


def _load_test_data():
    """Load the preprocessed test set saved during training."""
    x_path = os.path.join(BASE_DIR, "preprocessing", "X_test.csv")
    y_path = os.path.join(BASE_DIR, "preprocessing", "y_test.csv")
    X_test = pd.read_csv(x_path).values.astype(np.float32)
    y_test = pd.read_csv(y_path).values.flatten().astype(int)
    return X_test, y_test


def _compute_metrics(y_true, y_pred):
    TP = int(np.sum((y_pred == 1) & (y_true == 1)))
    TN = int(np.sum((y_pred == 0) & (y_true == 0)))
    FP = int(np.sum((y_pred == 1) & (y_true == 0)))
    FN = int(np.sum((y_pred == 0) & (y_true == 1)))

    accuracy = (TP + TN) / len(y_true) * 100 if len(y_true) > 0 else 0
    precision = TP / (TP + FP) * 100 if (TP + FP) > 0 else 0
    recall = TP / (TP + FN) * 100 if (TP + FN) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "accuracy": round(accuracy, 2),
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "f1_score": round(f1, 2),
        "confusion_matrix": {"TP": TP, "TN": TN, "FP": FP, "FN": FN},
        "correct": TP + TN,
        "incorrect": FP + FN,
        "total": len(y_true)
    }


@evaluate_bp.route("/api/evaluate/<model_id>", methods=["POST"])
def evaluate(model_id: str):
    if model_id != "irrigation":
        return jsonify({
            "success": False,
            "error": f"Model '{model_id}' is not available for evaluation."
        }), 404

    if not inference_manager.is_model_loaded("irrigation"):
        return jsonify({
            "success": False,
            "error": "Irrigation model is not loaded."
        }), 503

    try:
        X_test, y_test = _load_test_data()
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to load test data: {str(e)}"
        }), 500

    predictions = []
    probabilities = []
    inference_times = []

    for i in range(len(X_test)):
        sample = X_test[i:i+1]
        result = inference_manager.predict("irrigation", sample, backend_type="tflite")
        if not result.get("success"):
            return jsonify({
                "success": False,
                "error": f"Inference failed on sample {i}: {result.get('error')}"
            }), 500
        predictions.append(result["prediction"])
        probabilities.append(result["probability"])
        inference_times.append(result.get("inference_time_ms", 0))

    y_pred = np.array(predictions)
    metrics = _compute_metrics(y_test, y_pred)

    # Build per-sample results
    sample_results = []
    for i in range(len(X_test)):
        sample_results.append({
            "index": i,
            "true_label": int(y_test[i]),
            "true_label_name": LABEL_MAP.get(int(y_test[i]), "Unknown"),
            "predicted": int(y_pred[i]),
            "predicted_name": LABEL_MAP.get(int(y_pred[i]), "Unknown"),
            "probability": round(float(probabilities[i]), 4),
            "correct": bool(y_test[i] == y_pred[i])
        })

    return jsonify({
        "success": True,
        "model": "Irrigation TinyML INT8",
        "model_id": model_id,
        "inference_engine": "TensorFlow Lite",
        "execution": "Software / CPU",
        "fpga_status": "Not Connected",
        "test_samples": len(X_test),
        "metrics": metrics,
        "avg_inference_time_ms": round(float(np.mean(inference_times)), 3),
        "total_inference_time_ms": round(float(np.sum(inference_times)), 3),
        "samples": sample_results
    })
