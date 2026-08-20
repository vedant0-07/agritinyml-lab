"""
Fertilizer Models Preprocessing
Supports MODEL_05 (Test 1 — 9 features → 33 encoded) and
         MODEL_06 (Test 2 — 8 features → 22 encoded)

Loads saved preprocessor.pkl (ColumnTransformer / Pipeline) from training.
Never refits — uses the original fitted object only.
If the pkl cannot be loaded (e.g. Python/sklearn version mismatch),
status is set to 'error' and the API returns a clear message.
"""

import os
import numpy as np
import pandas as pd
import logging

log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_pkl(path: str):
    """Try joblib first, then pickle. Returns object or raises."""
    # joblib is the standard for sklearn objects
    try:
        import joblib
        return joblib.load(path)
    except Exception as e1:
        log.warning(f"joblib.load failed ({e1}), trying pickle...")

    # pickle fallback
    import pickle
    with open(path, "rb") as f:
        return pickle.load(f)


# ── MODEL_05 — Test 1 ─────────────────────────────────────────────────────────

MODEL05_PKL  = os.path.join(BASE_DIR, "models", "model05", "preprocessor.pkl")

# Feature columns in the ORDER the ColumnTransformer expects
MODEL05_COLUMNS = [
    "Temperature", "Humidity", "Moisture",
    "Nitrogen", "Potassium", "Phosphorous",
    "Soil Type", "Crop Type", "pH"
]

MODEL05_CLASSES = [
    "10:10:10 NPK", "10:26:26 NPK", "12:32:16 NPK", "13:32:26 NPK",
    "18:46:00 NPK", "19:19:19 NPK", "20:20:20 NPK", "50:26:26 NPK",
    "Ammonium Sulphate", "Chilated Micronutrient", "DAP",
    "Ferrous Sulphate", "Hydrated Lime", "MOP",
    "Magnesium Sulphate", "SSP", "Sulphur", "Urea", "White Potash",
]


# ── MODEL_06 — Test 2 ─────────────────────────────────────────────────────────

MODEL06_PKL  = os.path.join(BASE_DIR, "models", "model06", "preprocessor.pkl")

MODEL06_COLUMNS = [
    "Temperature", "Humidity", "Moisture",
    "Soil Type", "Crop Type",
    "Nitrogen", "Potassium", "Phosphorous"
]

MODEL06_CLASSES = [
    "10-26-26", "14-35-14", "17-17-17",
    "20-20", "28-28", "DAP", "Urea",
]


# ── Generic preprocessor class ────────────────────────────────────────────────

class FertilizerPreprocessor:
    """
    Loads a saved sklearn ColumnTransformer/Pipeline and wraps it for inference.
    """

    def __init__(self, model_id: str, pkl_path: str, columns: list, classes: list):
        self.model_id  = model_id
        self.pkl_path  = pkl_path
        self.columns   = columns
        self.classes   = classes
        self._preprocessor = None
        self.status    = "unloaded"
        self.error_message = None
        self._load()

    def _load(self):
        if not os.path.exists(self.pkl_path):
            self.status = "error"
            self.error_message = (
                f"Preprocessor file not found: {os.path.basename(self.pkl_path)}"
            )
            log.warning(f"[{self.model_id}] {self.error_message}")
            return
        try:
            self._preprocessor = _load_pkl(self.pkl_path)
            self.status = "ready"
            log.info(f"[{self.model_id}] Preprocessor loaded OK")
        except Exception as e:
            self.status = "error"
            self.error_message = (
                f"Cannot load preprocessor (Python/sklearn version mismatch?): {e}"
            )
            log.warning(f"[{self.model_id}] {self.error_message}")

    def validate(self, inputs: dict) -> tuple:
        """Basic validation. Returns (is_valid, error_str | None)."""
        errors = []
        numeric_fields = [c for c in self.columns if c not in ("Soil Type", "Crop Type")]
        for field in numeric_fields:
            val = inputs.get(field)
            if val is None:
                errors.append(f"'{field}' is required.")
                continue
            try:
                v = float(val)
                if not np.isfinite(v):
                    errors.append(f"'{field}' must be a finite number.")
                elif v < 0:
                    errors.append(f"'{field}' cannot be negative.")
            except (TypeError, ValueError):
                errors.append(f"'{field}' must be a valid number.")

        for cat in ("Soil Type", "Crop Type"):
            if cat in self.columns and not inputs.get(cat):
                errors.append(f"'{cat}' is required.")

        return (len(errors) == 0), ("; ".join(errors) if errors else None)

    def preprocess(self, inputs: dict) -> np.ndarray:
        """
        Transform raw input dict into a numpy array for inference.
        Column order is fixed by self.columns to match what the pkl expects.
        """
        if self.status != "ready":
            raise RuntimeError(self.error_message or "Preprocessor not loaded.")

        row = []
        for col in self.columns:
            val = inputs.get(col)
            if col in ("Soil Type", "Crop Type"):
                row.append(str(val))
            else:
                row.append(float(val))

        df = pd.DataFrame([row], columns=self.columns)
        transformed = self._preprocessor.transform(df)
        return transformed.astype(np.float32)

    def class_label(self, index: int) -> str:
        """Return class label for a predicted index."""
        if 0 <= index < len(self.classes):
            return self.classes[index]
        return f"Class_{index}"


# ── Singletons ────────────────────────────────────────────────────────────────

fertilizer1_preprocessor = FertilizerPreprocessor(
    model_id  = "MODEL_05",
    pkl_path  = MODEL05_PKL,
    columns   = MODEL05_COLUMNS,
    classes   = MODEL05_CLASSES,
)

fertilizer2_preprocessor = FertilizerPreprocessor(
    model_id  = "MODEL_06",
    pkl_path  = MODEL06_PKL,
    columns   = MODEL06_COLUMNS,
    classes   = MODEL06_CLASSES,
)
