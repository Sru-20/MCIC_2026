#!/usr/bin/env python3
"""Train the behavioral ML fraud detector."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split

try:
    from .features import build_feature_table, load_default_datasets
except ImportError:
    from features import build_feature_table, load_default_datasets


DEFEND_DIR = Path(__file__).resolve().parent
MODEL_PATH = DEFEND_DIR / "classifier_model.pkl"
FEATURE_COLUMNS_PATH = DEFEND_DIR / "feature_columns.json"
TRAINING_METRICS_PATH = DEFEND_DIR / "training_metrics.json"


def train_model(data_dir: str | Path = "generate/data", random_state: int = 42) -> dict:
    transcripts = load_default_datasets(data_dir)
    x_table, y, feature_columns = build_feature_table(transcripts)

    x_train, x_test, y_train, y_test = train_test_split(
        x_table,
        y,
        test_size=0.2,
        random_state=random_state,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=8,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=random_state,
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        predictions,
        average="binary",
        zero_division=0,
    )

    metrics = {
        "model": "RandomForestClassifier",
        "total_transcripts": len(transcripts),
        "train_size": int(len(x_train)),
        "test_size": int(len(x_test)),
        "fraud_count": int(y.sum()),
        "legitimate_count": int((y == 0).sum()),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "auc": float(roc_auc_score(y_test, probabilities)),
    }

    DEFEND_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    FEATURE_COLUMNS_PATH.write_text(json.dumps(feature_columns, indent=2), encoding="utf-8")
    TRAINING_METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    metrics = train_model()
    print(json.dumps(metrics, indent=2))
    print(f"Saved model to {MODEL_PATH}")
    print(f"Saved feature columns to {FEATURE_COLUMNS_PATH}")


if __name__ == "__main__":
    main()
