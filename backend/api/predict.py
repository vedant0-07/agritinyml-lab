"""
Predict API Blueprint
POST /api/predict/<model_id>
"""

import time
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

from backend.inference.manager import inference_manager
from backend.preprocessing.irrigation import irrigation_preprocessor, VALID_CROP_TYPES
from backend.database.db import save_experiment

predict_bp = Blueprint("predict", __name__)

LABEL_MAP = {0: "No Irrigation Required", 1: "Irrigation Required"}


@predict_bp.route("/api/predict/<model_id>", methods=["POST"])
def predict(model_id: str):
    if model_id != "irrigation":
        return jsonify({
            "success": False,
            "error": f"Model '{model_id}' is not available. Only 'irrigation' is currently deployed."
        }), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body must be valid JSON."
        }), 400

    # Extract inputs
    crop_type = data.get("crop_type", "")
    crop_days = data.get("crop_days")
    soil_moisture = data.get("soil_moisture")
    temperature = data.get("temperature")
    humidity = data.get("humidity")
    backend_type = data.get("backend", "tflite")

    # Validate
    is_valid, validation_error = irrigation_preprocessor.validate(
        crop_type, crop_days, soil_moisture, temperature, humidity
    )
    if not is_valid:
        return jsonify({
            "success": False,
            "error": validation_error,
            "valid_crop_types": VALID_CROP_TYPES
        }), 422

    # Preprocess
    try:
        features = irrigation_preprocessor.preprocess(
            crop_type, float(crop_days), float(soil_moisture),
            float(temperature), float(humidity)
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Preprocessing error: {str(e)}"
        }), 500

    # Run inference
    result = inference_manager.predict("irrigation", features, backend_type=backend_type)

    if not result.get("success"):
        return jsonify({
            "success": False,
            "error": result.get("error", "Inference failed."),
            "fpga_status": "not_connected" if backend_type == "fpga" else None
        }), 503

    prediction = result["prediction"]
    probability = result["probability"]
    label = LABEL_MAP.get(prediction, "Unknown")
    ts = datetime.now(timezone.utc).isoformat()

    # Save to experiment history (PostgreSQL via Supabase)
    try:
        save_experiment({
            "model_id":         1,                    # MODEL_01 row id in models table
            "model_name":       "Irrigation Prediction",
            "crop_type":        crop_type,
            "crop_days":        int(float(crop_days)),
            "soil_moisture":    float(soil_moisture),
            "temperature":      float(temperature),
            "humidity":         float(humidity),
            "prediction":       label,                # store label string e.g. "Irrigation Required"
            "probability":      probability,
            "engine":           "TFLite INT8",
            "inference_time_ms": result.get("inference_time_ms"),
            "inputs": {
                "crop_type":     crop_type,
                "crop_days":     float(crop_days),
                "soil_moisture": float(soil_moisture),
                "temperature":   float(temperature),
                "humidity":      float(humidity),
            },
        })
    except Exception:
        pass  # History save failure must not break the prediction response

    return jsonify({
        "success": True,
        "model": "Irrigation TinyML INT8",
        "model_id": model_id,
        "prediction": prediction,
        "label": label,
        "probability": probability,
        "probability_pct": round(probability * 100, 2),
        "inference_engine": "TensorFlow Lite",
        "inference_time_ms": result.get("inference_time_ms"),
        "backend": result.get("backend", "tflite"),
        "execution": "Software / CPU",
        "fpga_status": "Not Connected",
        "timestamp": ts,
        "inputs": {
            "crop_type": crop_type,
            "crop_days": float(crop_days),
            "soil_moisture": float(soil_moisture),
            "temperature": float(temperature),
            "humidity": float(humidity)
        }
    })
