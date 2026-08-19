#!/usr/bin/env python3
"""Evaluate the trained ML detector and write judge-facing reports."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split

try:
    from .features import build_feature_table, load_default_datasets
except ImportError:
    from features import build_feature_table, load_default_datasets


DEFEND_DIR = Path(__file__).resolve().parent
MODEL_PATH = DEFEND_DIR / "classifier_model.pkl"
FEATURE_COLUMNS_PATH = DEFEND_DIR / "feature_columns.json"
METRICS_PATH = DEFEND_DIR / "evaluation_metrics.json"
REPORT_PATH = DEFEND_DIR / "evaluation_report.md"


def evaluate_model(data_dir: str | Path = "generate/data", threshold: float = 0.5, random_state: int = 42) -> dict:
    transcripts = load_default_datasets(data_dir)
    x_table, y, _ = build_feature_table(transcripts)
    feature_columns = json.loads(FEATURE_COLUMNS_PATH.read_text(encoding="utf-8"))
    x_table = x_table.reindex(columns=feature_columns, fill_value=0)

    _, x_test, _, y_test = train_test_split(
        x_table,
        y,
        test_size=0.2,
        random_state=random_state,
        stratify=y,
    )

    model = joblib.load(MODEL_PATH)
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= threshold).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        predictions,
        average="binary",
        zero_division=0,
    )
    tn, fp, fn, tp = confusion_matrix(y_test, predictions).ravel()

    metrics = {
        "threshold": threshold,
        "test_size": int(len(y_test)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "auc": float(roc_auc_score(y_test, probabilities)),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
        "top_features": top_features(model, feature_columns),
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(render_report(metrics), encoding="utf-8")
    return metrics


def top_features(model, feature_columns: list[str], limit: int = 12) -> list[dict[str, float]]:
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return []
    ranked = sorted(zip(feature_columns, importances), key=lambda item: item[1], reverse=True)
    return [{"feature": name, "importance": float(score)} for name, score in ranked[:limit]]


def render_report(metrics: dict) -> str:
    matrix = metrics["confusion_matrix"]
    top = "\n".join(
        f"- `{item['feature']}`: {item['importance']:.4f}" for item in metrics.get("top_features", [])
    )
    return f"""# Person B Defense Evaluation

## ML Detector Metrics

| Metric | Value |
|---|---:|
| Precision | {metrics['precision']:.3f} |
| Recall | {metrics['recall']:.3f} |
| F1 | {metrics['f1']:.3f} |
| AUC | {metrics['auc']:.3f} |
| Threshold | {metrics['threshold']:.2f} |

## Confusion Matrix

|  | Predicted Legitimate | Predicted Fraud |
|---|---:|---:|
| Actual Legitimate | {matrix['true_negative']} | {matrix['false_positive']} |
| Actual Fraud | {matrix['false_negative']} | {matrix['true_positive']} |

## Top Model Features

{top}

## Interpretation

The ML detector learns behavioral signals that deterministic rules can miss, especially
multi-turn trust poisoning where the final tool call may appear to be `user_explicit`.
The deterministic gate remains important because it catches provenance risks immediately,
such as payment instructions sourced from external merchant or recommendation content.
"""


def main() -> None:
    metrics = evaluate_model()
    print(json.dumps(metrics, indent=2))
    print(f"Saved metrics to {METRICS_PATH}")
    print(f"Saved report to {REPORT_PATH}")


if __name__ == "__main__":
    main()
