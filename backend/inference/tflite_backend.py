"""
TFLite Inference Backend
Loads and runs the INT8 TFLite model for real inference.
Supports: tflite_runtime, ai_edge_litert, tensorflow (tries in this order)
"""

import os
import time
import numpy as np

# Try importers in order of preference
_Interpreter = None
_RUNTIME = None

# 1. tflite_runtime (lightweight, classic)
try:
    import tflite_runtime.interpreter as _tflite_rt
    _Interpreter = _tflite_rt.Interpreter
    _RUNTIME = "tflite_runtime"
except ImportError:
    pass

# 2. ai_edge_litert (new official runtime, Python 3.12/3.13 compatible)
if _Interpreter is None:
    try:
        from ai_edge_litert.interpreter import Interpreter as _litert_interp
        _Interpreter = _litert_interp
        _RUNTIME = "ai_edge_litert"
    except ImportError:
        pass

# 3. tensorflow.lite (full TF, Python <= 3.12)
if _Interpreter is None:
    try:
        import tensorflow as tf
        _Interpreter = tf.lite.Interpreter
        _RUNTIME = "tensorflow"
    except (ImportError, AttributeError):
        pass


class TFLiteBackend:
    """
    Manages TFLite model loading and inference.
    Loads model once at startup and reuses the interpreter.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.input_scale = None
        self.input_zero_point = None
        self.output_scale = None
        self.output_zero_point = None
        self.is_quantized = False
        self.status = "unloaded"
        self.error_message = None
        self._load()

    def _load(self):
        if _Interpreter is None:
            self.status = "error"
            self.error_message = "TFLite runtime not available. Install tensorflow or tflite-runtime."
            return

        if not os.path.exists(self.model_path):
            self.status = "error"
            self.error_message = f"Model file not found: {os.path.basename(self.model_path)}"
            return

        try:
            self.interpreter = _Interpreter(model_path=self.model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()

            # Check if INT8 quantized
            input_dtype = self.input_details[0]['dtype']
            if input_dtype == np.int8:
                self.is_quantized = True
                quant_params = self.input_details[0].get('quantization_parameters', {})
                scales = quant_params.get('scales', [1.0])
                zero_points = quant_params.get('zero_points', [0])
                self.input_scale = float(scales[0]) if len(scales) > 0 else 1.0
                self.input_zero_point = int(zero_points[0]) if len(zero_points) > 0 else 0

                out_quant = self.output_details[0].get('quantization_parameters', {})
                out_scales = out_quant.get('scales', [1.0])
                out_zero_points = out_quant.get('zero_points', [0])
                self.output_scale = float(out_scales[0]) if len(out_scales) > 0 else 1.0
                self.output_zero_point = int(out_zero_points[0]) if len(out_zero_points) > 0 else 0

            self.status = "ready"
        except Exception as e:
            self.status = "error"
            self.error_message = str(e)

    def predict(self, features: np.ndarray) -> dict:
        """
        Run inference on preprocessed feature array.
        features: numpy array of shape (1, 13) — already scaled/encoded
        Returns dict with prediction, probability, inference_time_ms
        """
        if self.status != "ready":
            return {
                "success": False,
                "error": self.error_message or "Model not ready",
                "backend": "tflite"
            }

        try:
            features = features.astype(np.float32)
            start = time.perf_counter()

            if self.is_quantized:
                # Quantize input: q = round(x / scale) + zero_point, clamp to int8
                q_input = np.round(features / self.input_scale + self.input_zero_point)
                q_input = np.clip(q_input, -128, 127).astype(np.int8)
                self.interpreter.set_tensor(self.input_details[0]['index'], q_input)
                self.interpreter.invoke()
                q_output = self.interpreter.get_tensor(self.output_details[0]['index'])
                # Dequantize output
                raw_output = (q_output.astype(np.float32) - self.output_zero_point) * self.output_scale
            else:
                self.interpreter.set_tensor(self.input_details[0]['index'], features)
                self.interpreter.invoke()
                raw_output = self.interpreter.get_tensor(self.output_details[0]['index'])

            elapsed_ms = (time.perf_counter() - start) * 1000
            output_squeezed = np.squeeze(raw_output)

            if output_squeezed.ndim == 0:
                # ── Binary classification (single scalar output) ──────────
                probability = float(output_squeezed)
                prediction  = 1 if probability >= 0.5 else 0
                probabilities = None
            else:
                # ── Multi-class (vector output — argmax) ──────────────────
                prediction    = int(np.argmax(output_squeezed))
                probability   = float(output_squeezed[prediction])
                # Normalise to [0,1] for reporting
                total = float(np.sum(np.abs(output_squeezed))) or 1.0
                probabilities = [round(float(v) / total, 4) for v in output_squeezed]

            return {
                "success": True,
                "prediction": prediction,
                "probability": round(probability, 6),
                "probabilities": probabilities,   # None for binary, list for multi-class
                "inference_time_ms": round(elapsed_ms, 3),
                "backend": "tflite",
                "runtime": _RUNTIME,
                "is_quantized": self.is_quantized
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "backend": "tflite"
            }

    def get_status(self) -> dict:
        return {
            "backend": "tflite",
            "status": self.status,
            "runtime": _RUNTIME,
            "model_path": os.path.basename(self.model_path),
            "is_quantized": self.is_quantized,
            "error": self.error_message
        }
