"""Loading and inference helpers for the trained Scania APS model."""
from pathlib import Path
import joblib

ROOT = Path(__file__).resolve().parent.parent
MODEL_FILE = ROOT / "app" / "models" / "scania_aps_model.joblib"
METRICS_FILE = ROOT / "app" / "models" / "metrics.json"


def load_artifact():
    if not MODEL_FILE.exists():
        return None
    return joblib.load(MODEL_FILE)


def model_status():
    if not MODEL_FILE.exists():
        return {
            "available": False,
            "model": "Scania APS failure classifier",
            "message": "Model not trained on this installation. Follow docs/MODEL_TRAINING.md.",
        }
    artifact = load_artifact()
    return {
        "available": True,
        "model": "Scania APS failure classifier",
        "threshold": float(artifact["threshold"]),
        "metrics": artifact["metrics"],
        "message": "Trained model loaded. Predictions apply only to the Scania APS dataset context.",
    }


def predict_frame(frame):
    import pandas as pd
    artifact = load_artifact()
    if artifact is None:
        raise RuntimeError("Model is not trained. Follow docs/MODEL_TRAINING.md.")
    features = artifact["features"]
    missing = [name for name in features if name not in frame.columns]
    if missing:
        raise ValueError(f"CSV is missing {len(missing)} required feature columns; first missing: {missing[:5]}")
    X = frame[features].apply(pd.to_numeric, errors="coerce")
    if X.isna().all(axis=1).any():
        raise ValueError("At least one row has no usable numeric sensor values.")
    probabilities = artifact["model"].predict_proba(X)[:, 1]
    threshold = float(artifact["threshold"])
    return [
        {
            "row": index + 1,
            "aps_failure_probability": round(float(probability), 6),
            "threshold": round(threshold, 6),
            "prediction": "APS failure risk — inspection recommended" if probability >= threshold else "No APS alert at selected threshold",
            "flagged": bool(probability >= threshold),
        }
        for index, probability in enumerate(probabilities)
    ]
