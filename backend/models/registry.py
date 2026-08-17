"""
Model Registry
Discovers and loads model metadata from the models/ directory.
"""

import os
import json
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")

MODEL_IDS = ["irrigation", "disease", "pest", "soil"]


def load_all_metadata() -> list:
    """Load metadata for all registered models."""
    result = []
    for model_id in MODEL_IDS:
        meta = load_metadata(model_id)
        if meta:
            result.append(meta)
    return result


def load_metadata(model_id: str) -> Optional[dict]:
    """Load metadata for a specific model."""
    meta_path = os.path.join(MODELS_DIR, model_id, "metadata.json")
    if not os.path.exists(meta_path):
        return None
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_model_file_path(model_id: str, model_type: str = "int8") -> Optional[str]:
    """
    Get the absolute path to a model file.
    model_type: 'int8', 'float32', or 'keras'
    """
    meta = load_metadata(model_id)
    if not meta:
        return None

    models_dict = meta.get("models", {})
    rel_path = models_dict.get(model_type)
    if not rel_path:
        return None

    abs_path = os.path.join(BASE_DIR, rel_path)
    if os.path.exists(abs_path):
        return abs_path
    return None
