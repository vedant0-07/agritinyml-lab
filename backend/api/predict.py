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


# ── Fertilizer Routes ─────────────────────────────────────────────────────────

from backend.preprocessing.fertilizer import (
    fertilizer1_preprocessor, fertilizer2_preprocessor,
    MODEL05_CLASSES, MODEL06_CLASSES,
)


def _fertilizer_predict(model_key: str, preprocessor, classes: list, model_label: str,
                         model_db_id: int, raw_inputs: dict) -> tuple:
    """
    Shared helper for fertilizer1 and fertilizer2 predictions.
    Returns (response_dict, http_status_code).
    """
    # Validate
    is_valid, validation_error = preprocessor.validate(raw_inputs)
    if not is_valid:
        return {"success": False, "error": validation_error}, 422

    if preprocessor.status != "ready":
        return {
            "success": False,
            "error": f"Preprocessor unavailable: {preprocessor.error_message}",
            "hint": "This model's preprocessor could not be loaded. Check server logs."
        }, 503

    # Preprocess
    try:
        features = preprocessor.preprocess(raw_inputs)
    except Exception as e:
        return {"success": False, "error": f"Preprocessing error: {e}"}, 500

    # Infer
    result = inference_manager.predict(model_key, features, backend_type="tflite")
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Inference failed.")}, 503

    prediction  = result["prediction"]
    probability = result["probability"]
    label       = preprocessor.class_label(prediction)
    ts          = datetime.now(timezone.utc).isoformat()

    # Save to experiment history
    try:
        save_experiment({
            "model_id":          model_db_id,
            "model_name":        model_label,
            "prediction":        label,
            "probability":       probability,
            "engine":            "TFLite INT8",
            "inference_time_ms": result.get("inference_time_ms"),
            "inputs":            raw_inputs,
        })
    except Exception:
        pass

    return {
        "success":          True,
        "model":            model_label,
        "model_id":         model_key,
        "prediction":       prediction,
        "label":            label,
        "probability":      probability,
        "probability_pct":  round(probability * 100, 2),
        "probabilities":    result.get("probabilities"),
        "classes":          classes,
        "inference_engine": "TensorFlow Lite",
        "inference_time_ms": result.get("inference_time_ms"),
        "backend":          result.get("backend", "tflite"),
        "execution":        "Software / CPU",
        "fpga_status":      "Not Connected",
        "timestamp":        ts,
        "inputs":           raw_inputs,
    }, 200


@predict_bp.route("/api/predict/fertilizer1", methods=["POST"])
def predict_fertilizer1():
    """MODEL_05 — Test 1: 9 inputs → 19 fertilizer classes."""
    data = request.get_json(silent=True) or {}
    raw_inputs = {
        "Temperature": data.get("temperature") or data.get("Temperature"),
        "Humidity":    data.get("humidity")    or data.get("Humidity"),
        "Moisture":    data.get("moisture")    or data.get("Moisture"),
        "Nitrogen":    data.get("nitrogen")    or data.get("Nitrogen"),
        "Potassium":   data.get("potassium")   or data.get("Potassium"),
        "Phosphorous": data.get("phosphorous") or data.get("Phosphorous"),
        "Soil Type":   data.get("soil_type")   or data.get("Soil Type"),
        "Crop Type":   data.get("crop_type")   or data.get("Crop Type"),
        "pH":          data.get("ph")          or data.get("pH"),
    }
    resp, code = _fertilizer_predict(
        model_key    = "fertilizer1",
        preprocessor = fertilizer1_preprocessor,
        classes      = MODEL05_CLASSES,
        model_label  = "Test 1 — Fertilizer Recommendation",
        model_db_id  = 5,
        raw_inputs   = raw_inputs,
    )
    return jsonify(resp), code


@predict_bp.route("/api/predict/fertilizer2", methods=["POST"])
def predict_fertilizer2():
    """MODEL_06 — Test 2: 8 inputs → 7 fertilizer classes."""
    data = request.get_json(silent=True) or {}
    raw_inputs = {
        "Temperature": data.get("temperature") or data.get("Temperature"),
        "Humidity":    data.get("humidity")    or data.get("Humidity"),
        "Moisture":    data.get("moisture")    or data.get("Moisture"),
        "Soil Type":   data.get("soil_type")   or data.get("Soil Type"),
        "Crop Type":   data.get("crop_type")   or data.get("Crop Type"),
        "Nitrogen":    data.get("nitrogen")    or data.get("Nitrogen"),
        "Potassium":   data.get("potassium")   or data.get("Potassium"),
        "Phosphorous": data.get("phosphorous") or data.get("Phosphorous"),
    }
    resp, code = _fertilizer_predict(
        model_key    = "fertilizer2",
        preprocessor = fertilizer2_preprocessor,
        classes      = MODEL06_CLASSES,
        model_label  = "Test 2 — Fertilizer Recommendation",
        model_db_id  = 6,
        raw_inputs   = raw_inputs,
    )
    return jsonify(resp), code
