"""
Preprocessing wrapper for the Irrigation model.
Uses the saved preprocessor.pkl (ColumnTransformer) from training.
Never refits — uses the original fitted object only.
"""

import os
import numpy as np
import pandas as pd
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PREPROCESSOR_PATH = os.path.join(BASE_DIR, "preprocessing", "preprocessor.pkl")

VALID_CROP_TYPES = [
    "Coffee", "Garden Flowers", "Groundnuts", "Maize",
    "Paddy", "Potato", "Pulse", "Sugarcane", "Wheat"
]

# Feature column names expected by the ColumnTransformer
FEATURE_COLUMNS = ["CropType", "CropDays", "SoilMoisture", "temperature", "Humidity"]


class IrrigationPreprocessor:
    """
    Wraps the saved ColumnTransformer to preprocess raw user inputs
    using the exact same pipeline as during training.
    """

    def __init__(self):
        self._preprocessor = None
        self.status = "unloaded"
        self.error_message = None
        self._load()

    def _load(self):
        if not os.path.exists(PREPROCESSOR_PATH):
            self.status = "error"
            self.error_message = f"Preprocessor file not found."
            return
        try:
            self._preprocessor = joblib.load(PREPROCESSOR_PATH)
            self.status = "ready"
        except Exception as e:
            self.status = "error"
            self.error_message = str(e)

    def validate(self, crop_type: str, crop_days, soil_moisture, temperature, humidity) -> tuple:
        """
        Validate raw inputs. Returns (is_valid: bool, error_message: str | None)
        """
        errors = []

        if crop_type not in VALID_CROP_TYPES:
            errors.append(f"Invalid crop type '{crop_type}'. Must be one of: {', '.join(VALID_CROP_TYPES)}")

        for name, value in [("Crop Days", crop_days), ("Soil Moisture", soil_moisture),
                             ("Temperature", temperature), ("Humidity", humidity)]:
            try:
                v = float(value)
                if np.isnan(v) or np.isinf(v):
                    errors.append(f"{name} must be a finite number.")
                elif v < 0:
                    errors.append(f"{name} cannot be negative.")
            except (TypeError, ValueError):
                errors.append(f"{name} must be a valid number.")

        if errors:
            return False, "; ".join(errors)
        return True, None

    def preprocess(self, crop_type: str, crop_days: float, soil_moisture: float,
                   temperature: float, humidity: float) -> np.ndarray:
        """
        Transform raw inputs into 13 preprocessed features.
        Returns numpy array of shape (1, 13) as float32.
        """
        if self.status != "ready":
            raise RuntimeError(self.error_message or "Preprocessor not loaded.")

        # Build DataFrame with the exact column names the ColumnTransformer expects
        df = pd.DataFrame([[crop_type, float(crop_days), float(soil_moisture),
                            float(temperature), float(humidity)]],
                          columns=FEATURE_COLUMNS)

        transformed = self._preprocessor.transform(df)
        return transformed.astype(np.float32)


# Global singleton
irrigation_preprocessor = IrrigationPreprocessor()
