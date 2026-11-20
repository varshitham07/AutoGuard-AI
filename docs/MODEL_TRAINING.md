# Train and use the Scania APS failure model

AutoGuard AI includes a reproducible training pipeline for the official **UCI APS Failure at Scania Trucks** dataset (UCI ID 421; DOI 10.24432/C51S51).

## 1. Obtain the real dataset

1. Double-click `DOWNLOAD_SCANIA_DATA_WINDOWS.bat` on Windows. It downloads and extracts the official archive.
2. Alternatively, use the [official UCI dataset page](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks) and place `aps_failure_training_set.csv` at `data/raw/aps_failure_training_set.csv`.

Do not create substitute rows or rename columns. The original target column must be `class`, with labels `neg` and `pos`. Keep the raw data out of Git because it is a large source file.

## 2. Install modelling dependencies

From the repository root:

```bash
python -m pip install -r requirements-ml.txt
```

## 3. Train and evaluate

```bash
python train_model.py
```

The script:
- checks that the original target and 170 operational feature columns exist;
- parses `na` as missing and applies median imputation;
- uses a stratified 70/15/15 split for model fitting, threshold calibration and final testing;
- trains a gradient-boosting classifier with positive-class sample weighting;
- selects the operating threshold on the calibration partition using the published challenge cost matrix (false positive = 10; false negative = 500);
- reports precision, recall, F1, PR-AUC, ROC-AUC, confusion matrix and challenge cost on the untouched test partition.

Separating threshold calibration from final testing avoids reporting performance on the same records used to tune the decision threshold. The final metrics are still an internal hold-out estimate, not an independent fleet trial.

The trained artifact and measured metrics are written to `app/models/`. Those generated files are ignored by Git. **Do not report metrics until training has completed successfully on the downloaded dataset.**

## 4. Run the application

```bash
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`, sign in, then use **EngineGuard → Upload Scania sensor CSV**. Prediction input must contain the same 170 feature headers from the official training file; it must not contain the `class` label. Upload a small CSV with no more than 500 rows.

## 5. Scope and safety

The output is a class-weighted ranking score, not a calibrated real-world probability. This is a dataset-specific classifier for APS-related component failure in the Scania heavy-truck dataset. It is not a passenger-car engine diagnostic tool, tyre failure detector, real-time telematics system or proof of a vehicle's current roadworthiness. A high-risk output is a recommendation for professional inspection, not a diagnosis. A low-risk output does not guarantee safety.

The official dataset uses anonymised sensor attributes, so model explanations are limited to the source feature identifiers unless additional licensed engineering documentation is available.
