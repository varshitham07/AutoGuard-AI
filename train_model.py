#!/usr/bin/env python3
"""Train a cost-sensitive Scania APS failure classifier from the official UCI CSV.

Expected input:
  data/raw/aps_failure_training_set.csv

The script makes a stratified hold-out validation split, chooses a probability
threshold by the published challenge cost matrix, and saves the model plus
metrics. It never downloads or fabricates data.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "raw" / "aps_failure_training_set.csv"
MODEL_DIR = ROOT / "app" / "models"
MODEL_FILE = MODEL_DIR / "scania_aps_model.joblib"
METRICS_FILE = MODEL_DIR / "metrics.json"
RANDOM_STATE = 42


def main() -> None:
    if not DATA_FILE.exists():
        raise SystemExit(
            "Dataset not found. Download aps_failure_training_set.csv from "
            "https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks "
            f"and place it at: {DATA_FILE}"
        )

    data = pd.read_csv(DATA_FILE, na_values=["na", "NA", ""])
    if "class" not in data.columns:
        raise SystemExit("Expected target column named 'class' in UCI training CSV.")
    y = data.pop("class").astype(str).str.strip().str.lower().map({"neg": 0, "pos": 1})
    if y.isna().any():
        raise SystemExit("Unexpected target labels. Expected only 'neg' and 'pos'.")
    if set(y.unique()) != {0, 1}:
        raise SystemExit("Both negative and positive classes must be present.")
    X = data.apply(pd.to_numeric, errors="coerce")
    if X.shape[1] != 170:
        raise SystemExit(f"Expected 170 operational features, found {X.shape[1]}.")
    if X.isna().all(axis=1).any():
        raise SystemExit("Some rows contain no usable sensor values; inspect the source CSV.")

    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )

    # Weight the rare positive class; validation remains untouched by fitting.
    negatives = int((y_train == 0).sum())
    positives = int((y_train == 1).sum())
    weights = np.where(y_train.to_numpy() == 1, negatives / positives, 1.0)

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("classifier", HistGradientBoostingClassifier(
            learning_rate=0.08,
            max_iter=160,
            max_leaf_nodes=15,
            l2_regularization=2.0,
            early_stopping=True,
            random_state=RANDOM_STATE,
        )),
    ])
    model.fit(X_train, y_train, classifier__sample_weight=weights)

    probabilities = model.predict_proba(X_valid)[:, 1]
    # Published challenge costs: false positive = 10, false negative = 500.
    thresholds = np.unique(np.r_[np.linspace(0.01, 0.99, 99), 0.5])
    candidates = []
    for threshold in thresholds:
        predictions = (probabilities >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_valid, predictions, labels=[0, 1]).ravel()
        candidates.append((int(fp * 10 + fn * 500), float(threshold), tn, fp, fn, tp))
    cost, threshold, tn, fp, fn, tp = min(candidates, key=lambda row: (row[0], -row[1]))
    predictions = (probabilities >= threshold).astype(int)

    metrics = {
        "dataset": "UCI APS Failure at Scania Trucks (id 421)",
        "dataset_doi": "10.24432/C51S51",
        "target": "APS-related component failure (pos) vs non-APS failure (neg)",
        "rows": int(len(data)),
        "features": int(X.shape[1]),
        "train_rows": int(len(X_train)),
        "validation_rows": int(len(X_valid)),
        "positive_train": positives,
        "negative_train": negatives,
        "split": "stratified 80/20 hold-out; random_state=42",
        "model": "median imputation + HistGradientBoostingClassifier",
        "threshold": threshold,
        "score_interpretation": "Class-weighted model score used for ranking and cost-sensitive thresholding; not a calibrated real-world failure probability.",
        "validation": {
            "precision": float(precision_score(y_valid, predictions, zero_division=0)),
            "recall": float(recall_score(y_valid, predictions, zero_division=0)),
            "f1": float(f1_score(y_valid, predictions, zero_division=0)),
            "average_precision_pr_auc": float(average_precision_score(y_valid, probabilities)),
            "roc_auc": float(roc_auc_score(y_valid, probabilities)),
            "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
            "challenge_cost": int(cost),
            "cost_matrix": {"false_positive": 10, "false_negative": 500},
        },
        "limitations": [
            "Validation metrics are a single stratified hold-out estimate, not an independent external fleet trial.",
            "Feature names are anonymised by the data provider.",
            "This model predicts APS-related failure in the Scania dataset context only.",
            "It is not a passenger-car engine or tyre failure model.",
        ],
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": model,
        "features": list(X.columns),
        "threshold": threshold,
        "metrics": metrics,
    }
    joblib.dump(artifact, MODEL_FILE)
    METRICS_FILE.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"\nSaved model: {MODEL_FILE}")


if __name__ == "__main__":
    main()
