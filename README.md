# AgriTinyML Lab — TEAM TRONICS | Group B2

> **Design Adaptive Reconfigurable TinyML Edge Accelerator Using FPGA for Agriculture Applications**

A professional, research-grade web application for demonstrating, testing, and evaluating TinyML models for agricultural applications. Built as a functional ML model testing and demonstration platform.

---

## Team

**TEAM TRONICS — Group B2**

| Name              | Roll No. |
|-------------------|----------|
| Ritesh Kawale     | J-41     |
| Rutuj Adakane     | J-42     |
| Sahil Sadawarti   | J-43     |
| Sameer Khonde     | J-44     |
| Trisha Kanade     | J-56     |
| Vedant Khorgade   | J-61     |

---

## Project Status

| Stage | Status |
|-------|--------|
| Dataset Preparation | ✅ Completed |
| Data Preprocessing | ✅ Completed |
| Irrigation Model Training | ✅ Completed |
| Model Evaluation | ✅ Completed |
| Float32 TFLite Conversion | ✅ Completed |
| INT8 Quantization | ✅ Completed |
| Software Testing | ✅ Completed |
| Web Platform | ✅ Completed |
| FPGA Accelerator Design | ⏳ Pending |
| FPGA Deployment | ⏳ Pending |
| Hardware Benchmarking | ⏳ Pending |

---

## Requirements

- Python 3.9+
- TensorFlow (for TFLite interpreter)
- scikit-learn >= 1.9.0 (must match version used to create preprocessor.pkl)
- Flask, Flask-CORS
- NumPy, Pandas, joblib

---

## Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify project files

Ensure the following files exist:

```
models/irrigation/model_int8.tflite
models/irrigation/model_float32.tflite
models/irrigation/metadata.json
preprocessing/preprocessor.pkl
preprocessing/X_test.csv
preprocessing/y_test.csv
```

### 3. Run the application

```bash
python app.py
```

### 4. Open browser

```
http://127.0.0.1:5000
```

---

## Project Structure

```
testing website/
├── app.py                          # Flask entry point
├── requirements.txt
├── README.md
├── experiments.db                  # SQLite (auto-created)
│
├── models/
│   ├── irrigation/
│   │   ├── model_int8.tflite
│   │   ├── model_float32.tflite
│   │   └── metadata.json
│   ├── disease/metadata.json
│   ├── pest/metadata.json
│   └── soil/metadata.json
│
├── preprocessing/
│   ├── preprocessor.pkl            # Original training pipeline (do not modify)
│   ├── X_test.csv                  # Preprocessed test features
│   └── y_test.csv                  # Test labels
│
├── backend/
│   ├── inference/
│   │   ├── manager.py              # InferenceManager (TFLite + FPGA abstraction)
│   │   ├── tflite_backend.py       # TFLite inference (ACTIVE)
│   │   └── fpga_backend.py         # FPGA stub (NOT CONNECTED)
│   ├── models/registry.py          # Model registry loader
│   ├── preprocessing/irrigation.py # Preprocessing wrapper
│   ├── api/
│   │   ├── predict.py              # POST /api/predict/<model_id>
│   │   ├── evaluate.py             # POST /api/evaluate/<model_id>
│   │   ├── history.py              # GET/POST /api/history
│   │   └── project.py              # GET /api/project/status
│   └── database/db.py              # SQLite experiment log
│
└── frontend/
    ├── templates/index.html        # SPA shell
    └── static/
        ├── css/main.css            # Design system
        └── js/
            ├── main.js             # Navigation
            ├── playground.js       # Model inference UI
            ├── evaluation.js       # Test set evaluation
            ├── comparison.js       # Float32 vs INT8 charts
            ├── architecture.js     # Architecture diagrams
            └── experiments.js      # History table
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System health check |
| GET | `/api/models` | List all registered models |
| GET | `/api/models/<model_id>` | Get model metadata |
| POST | `/api/predict/<model_id>` | Run inference (actual INT8 model) |
| POST | `/api/evaluate/<model_id>` | Evaluate on test set |
| GET | `/api/history` | Get experiment history |
| POST | `/api/history/clear` | Clear history |
| GET | `/api/history/export` | Export as CSV |
| GET | `/api/project/status` | Project status |

### Example Prediction Request

```bash
curl -X POST http://127.0.0.1:5000/api/predict/irrigation \
  -H "Content-Type: application/json" \
  -d '{"crop_type": "Wheat", "crop_days": 45, "soil_moisture": 200, "temperature": 35, "humidity": 25}'
```

---

## Important Notes

- **Predictions are real** — all inference uses the actual `irrigation_model_int8.tflite` via TFLite
- **Preprocessing is the original** — `preprocessor.pkl` is loaded via joblib, never refit
- **FPGA results are TBD** — no fabricated hardware metrics are shown
- **scikit-learn version must be >= 1.9.0** — the preprocessor.pkl was saved with sklearn 1.9.0

---

## © 2026 TEAM TRONICS — Group B2
