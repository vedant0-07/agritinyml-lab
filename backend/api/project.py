"""
Project Status API Blueprint
GET /api/project/status
GET /api/models
GET /api/models/<model_id>
"""

from flask import Blueprint, jsonify
from backend.models.registry import load_all_metadata, load_metadata
from backend.inference.manager import inference_manager

project_bp = Blueprint("project", __name__)

PROJECT_STATUS = {
    "name": "Design Adaptive Reconfigurable TinyML Edge Accelerator Using FPGA for Agriculture Applications",
    "team": "TEAM TRONICS",
    "group": "B2",
    "active_models": 1,
    "planned_models": 4,
    "fpga_status": "not_connected",
    "phases": [
        {"name": "Literature Review", "status": "completed"},
        {"name": "Dataset Collection", "status": "completed"},
        {"name": "Dataset Preprocessing", "status": "completed"},
        {"name": "Irrigation Model Training", "status": "completed"},
        {"name": "Model Evaluation", "status": "completed"},
        {"name": "Float32 TFLite Conversion", "status": "completed"},
        {"name": "INT8 Quantization", "status": "completed"},
        {"name": "Software Testing", "status": "completed"},
        {"name": "Web Demonstration Platform", "status": "completed"},
        {"name": "FPGA Accelerator Design", "status": "pending"},
        {"name": "FPGA Deployment", "status": "pending"},
        {"name": "Hardware Benchmarking", "status": "pending"},
        {"name": "Multi-Model Reconfiguration", "status": "pending"},
    ],
    "objectives": [
        "Develop an FPGA-based TinyML edge accelerator for agricultural AI applications.",
        "Enable real-time local inference with reduced dependency on cloud connectivity.",
        "Support multiple agricultural AI workloads through an adaptive/reconfigurable architecture.",
        "Reduce computational and memory requirements through TinyML and INT8 quantization.",
        "Evaluate the performance of software inference and eventually FPGA-based acceleration.",
        "Develop a scalable platform for agriculture applications such as irrigation prediction, disease detection, pest identification and soil monitoring."
    ],
    "tech_stack": {
        "ml": ["Python", "TensorFlow", "TensorFlow Lite"],
        "data": ["Pandas", "NumPy", "Scikit-learn"],
        "frontend": ["HTML", "CSS", "JavaScript"],
        "backend": ["Python", "Flask"],
        "future_hardware": ["FPGA / Zynq-based platform"]
    }
}


@project_bp.route("/api/project/status", methods=["GET"])
def get_project_status():
    backend_status = inference_manager.get_backend_status("irrigation")
    return jsonify({
        "success": True,
        "project": PROJECT_STATUS,
        "system": {
            "tflite_status": backend_status.get("tflite", {}).get("status", "unknown"),
            "fpga_status": "not_connected",
            "inference_active": "software"
        }
    })


@project_bp.route("/api/models", methods=["GET"])
def list_models():
    models = load_all_metadata()
    return jsonify({
        "success": True,
        "count": len(models),
        "models": models
    })


@project_bp.route("/api/models/<model_id>", methods=["GET"])
def get_model(model_id: str):
    meta = load_metadata(model_id)
    if not meta:
        return jsonify({
            "success": False,
            "error": f"Model '{model_id}' not found in registry."
        }), 404
    return jsonify({
        "success": True,
        "model": meta
    })
