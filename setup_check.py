"""
AgriTinyML Lab — Setup Verification Script
Run this to verify all dependencies and files are ready.

Usage: python setup_check.py
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def check(label, condition, detail=""):
    mark = "✓" if condition else "✗"
    color_ok  = "\033[32m"
    color_err = "\033[31m"
    color_end = "\033[0m"
    color = color_ok if condition else color_err
    print(f"  {color}{mark}{color_end} {label}", end="")
    if detail: print(f"  ({detail})", end="")
    print()
    return condition

print()
print("=" * 58)
print("  AgriTinyML Lab — Setup Check")
print("  TEAM TRONICS | Group B2")
print("=" * 58)

all_ok = True

print("\n[1] Python Version")
ok = sys.version_info >= (3, 9)
check(f"Python {sys.version_info.major}.{sys.version_info.minor}", ok, "requires >= 3.9")
all_ok &= ok

print("\n[2] Required Packages")
packages = {
    "flask":        "Flask",
    "flask_cors":   "Flask-CORS",
    "numpy":        "NumPy",
    "pandas":       "Pandas",
    "joblib":       "joblib",
    "sklearn":      "scikit-learn",
}
for mod, name in packages.items():
    try:
        m = __import__(mod)
        ver = getattr(m, "__version__", "?")
        ok = check(name, True, ver)
    except ImportError:
        ok = check(name, False, "NOT INSTALLED — run: pip install -r requirements.txt")
        all_ok = False

# Check TFLite
tflite_ok = False
try:
    import tflite_runtime.interpreter as tflite
    check("tflite-runtime", True, "Lightweight TFLite")
    tflite_ok = True
except ImportError:
    try:
        import tensorflow as tf
        check("tensorflow", True, f"v{tf.__version__}")
        tflite_ok = True
    except ImportError:
        check("tensorflow / tflite-runtime", False,
              "NOT INSTALLED — run: pip install tensorflow-cpu")
        all_ok = False

print("\n[3] Model Files")
model_files = [
    ("models/irrigation/model_int8.tflite",    "INT8 TFLite model (primary inference)"),
    ("models/irrigation/model_float32.tflite", "Float32 TFLite model"),
    ("models/irrigation/metadata.json",        "Model metadata"),
]
for rel, desc in model_files:
    path = os.path.join(BASE_DIR, rel)
    exists = os.path.exists(path)
    size = f"{os.path.getsize(path)/1024:.1f} KB" if exists else ""
    ok = check(desc, exists, size if size else "MISSING")
    all_ok &= ok

print("\n[4] Preprocessing Files")
preproc_files = [
    ("preprocessing/preprocessor.pkl", "Original ColumnTransformer pipeline"),
    ("preprocessing/X_test.csv",       "Test features (76 samples)"),
    ("preprocessing/y_test.csv",       "Test labels"),
]
for rel, desc in preproc_files:
    path = os.path.join(BASE_DIR, rel)
    exists = os.path.exists(path)
    ok = check(desc, exists, "MISSING" if not exists else "")
    all_ok &= ok

print("\n[5] Preprocessor Load Test")
try:
    import joblib
    pp = joblib.load(os.path.join(BASE_DIR, "preprocessing", "preprocessor.pkl"))
    check("preprocessor.pkl loads correctly", True, type(pp).__name__)
except Exception as e:
    check("preprocessor.pkl loads correctly", False, str(e))
    all_ok = False

print("\n" + "=" * 58)
if all_ok:
    print("  ✓ All checks passed! Run: python app.py")
    print("  ✓ Then open: http://127.0.0.1:5000")
else:
    print("  ✗ Some checks failed. Fix issues above, then run app.py")
print("=" * 58)
print()
