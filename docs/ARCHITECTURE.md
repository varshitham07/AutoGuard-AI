# Architecture

```text
Browser UI (web/index.html)
        |
        | HTTPS/HTTP JSON + CSV multipart
        v
FastAPI application (app/main.py)
        |-- Account registration/login (PBKDF2 + signed bearer token)
        |-- Fleet vehicles -----------------------+
        |-- Tyre rule screening + history         |
        |-- Maintenance work orders               |--> SQLite (local autoguard.db)
        |-- Scania APS prediction API             |
        |                                          |
        +--> Model service (app/model_service.py) |
                 |                                |
                 +--> joblib model artifact <-----+
                         ^
                         |
              train_model.py
                         ^
                         |
        Official UCI Scania APS training CSV
```

## Main data flows

- User accounts own their vehicle, tyre-check, model-prediction and work-order records.
- Tyre screening is rule-based and records the input evidence, flags and follow-up suggestions.
- Scania APS inference is available only when a local model artifact exists. Prediction CSVs must contain the official 170 feature columns.
- Model training is a reproducible offline command after the user downloads the official UCI dataset. Raw dataset files and generated model artifacts are excluded from Git.
- GitHub Pages serves only static HTML and browser-local preview data; it cannot host the FastAPI process or share the SQLite database.
