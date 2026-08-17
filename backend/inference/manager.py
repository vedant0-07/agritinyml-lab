"""
Inference Manager
Abstraction layer that routes inference requests to the active backend.
Currently: TFLiteBackend is ACTIVE, FPGABackend is NOT AVAILABLE.
Future: Switch to FPGABackend when hardware is connected.
"""

import os
from backend.inference.tflite_backend import TFLiteBackend
from backend.inference.fpga_backend import FPGABackend

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class InferenceManager:
    """
    Manages inference backends per model.
    Routes predictions to active backend (TFLite or FPGA).
    """

    def __init__(self):
        self._backends = {}   # model_id -> TFLiteBackend instance
        self._fpga = FPGABackend()

    def load_model(self, model_id: str, model_path: str):
        """Load a TFLite model and cache the backend instance."""
        abs_path = os.path.join(BASE_DIR, model_path)
        backend = TFLiteBackend(abs_path)
        self._backends[model_id] = backend
        return backend.get_status()

    def predict(self, model_id: str, features, backend_type: str = "tflite") -> dict:
        """
        Run prediction using the specified backend.
        backend_type: 'tflite' (active) or 'fpga' (not connected)
        """
        if backend_type == "fpga":
            return self._fpga.predict(features)

        if model_id not in self._backends:
            return {
                "success": False,
                "error": f"Model '{model_id}' is not loaded.",
                "backend": "tflite"
            }

        return self._backends[model_id].predict(features)

    def get_backend_status(self, model_id: str = None) -> dict:
        status = {
            "tflite": {},
            "fpga": self._fpga.get_status()
        }
        if model_id and model_id in self._backends:
            status["tflite"] = self._backends[model_id].get_status()
        elif self._backends:
            status["tflite"] = {k: v.get_status() for k, v in self._backends.items()}
        return status

    def is_model_loaded(self, model_id: str) -> bool:
        return model_id in self._backends and self._backends[model_id].status == "ready"


# Global singleton
inference_manager = InferenceManager()
