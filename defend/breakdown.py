#!/usr/bin/env python3
"""Compare deterministic gate coverage with ML detector coverage."""

from __future__ import annotations

import json
from pathlib import Path

import joblib

try:
    from .features import build_feature_table, load_default_datasets
    from .gate import BLOCK, STEP_UP, DeterministicGate
except ImportError:
    from features import build_feature_table, load_default_datasets
    from gate import BLOCK, STEP_UP, DeterministicGate


DEFEND_DIR = Path(__file__).resolve().parent
MODEL_PATH = DEFEND_DIR / "classifier_model.pkl"
FEATURE_COLUMNS_PATH = DEFEND_DIR / "feature_columns.json"
BREAKDOWN_PATH = DEFEND_DIR / "breakdown_report.json"
BREAKDOWN_MD_PATH = DEFEND_DIR / "breakdown_report.md"


def analyze(data_dir: str | Path = "generate/data", threshold: float = 0.5) -> dict:
    transcripts = load_default_datasets(data_dir)
    fraud_transcripts = [row for row in transcripts if row.get("ground_truth_label") == "fraud"]
    x_table, _, _ = build_feature_table(fraud_transcripts)
    feature_columns = json.loads(FEATURE_COLUMNS_PATH.read_text(encoding="utf-8"))
    x_table = x_table.reindex(columns=feature_columns, fill_value=0)

    model = joblib.load(MODEL_PATH)
    gate = DeterministicGate()
    probabilities = model.predict_proba(x_table)[:, 1]

    counts = {"gate_only": 0, "detector_only": 0, "both_caught": 0, "missed": 0}
    details = []

    for transcript, probability in zip(fraud_transcripts, probabilities):
        gate_result = gate.evaluate(transcript)
        gate_caught = gate_result["verdict"] in {STEP_UP, BLOCK}
        detector_caught = probability >= threshold

        if gate_caught and detector_caught:
            counts["both_caught"] += 1
            category = "both_caught"
        elif gate_caught:
            counts["gate_only"] += 1
            category = "gate_only"
        elif detector_caught:
            counts["detector_only"] += 1
            category = "detector_only"
        else:
            counts["missed"] += 1
            category = "missed"

        details.append(
            {
                "conversation_id": transcript.get("conversation_id"),
                "attack_type": transcript.get("attack_type"),
                "category": category,
                "gate_verdict": gate_result["verdict"],
                "gate_reasons": gate_result["reasons"],
                "detector_fraud_probability": float(probability),
            }
        )

    total = len(fraud_transcripts)
    gate_caught_total = counts["gate_only"] + counts["both_caught"]
    detector_caught_total = counts["detector_only"] + counts["both_caught"]
    combined_caught = total - counts["missed"]
    summary = {
        "total_attacks": total,
        **counts,
        "gate_caught": gate_caught_total,
        "detector_caught": detector_caught_total,
        "gate_caught_rate": pct(gate_caught_total, total),
        "detector_caught_rate": pct(detector_caught_total, total),
        "gate_only_rate": pct(counts["gate_only"], total),
        "detector_only_rate": pct(counts["detector_only"], total),
        "both_caught_rate": pct(counts["both_caught"], total),
        "missed_rate": pct(counts["missed"], total),
        "combined_defense_rate": pct(combined_caught, total),
        "threshold": threshold,
    }

    report = {"summary": summary, "details": details}
    BREAKDOWN_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    BREAKDOWN_MD_PATH.write_text(render_markdown(summary), encoding="utf-8")
    return report


def pct(count: int, total: int) -> float:
    return float(count / total) if total else 0.0


def render_markdown(summary: dict) -> str:
    return f"""# Gate vs ML Detector Breakdown

Evaluated on {summary['total_attacks']} simulated fraud attacks.

| Defense Result | Count | Percentage |
|---|---:|---:|
| Gate caught | {summary['gate_caught']} | {summary['gate_caught_rate']:.1%} |
| Detector caught | {summary['detector_caught']} | {summary['detector_caught_rate']:.1%} |
| Both caught | {summary['both_caught']} | {summary['both_caught_rate']:.1%} |
| Gate only | {summary['gate_only']} | {summary['gate_only_rate']:.1%} |
| Detector only | {summary['detector_only']} | {summary['detector_only_rate']:.1%} |
| Missed | {summary['missed']} | {summary['missed_rate']:.1%} |
| **Combined defense** | **{summary['total_attacks'] - summary['missed']}** | **{summary['combined_defense_rate']:.1%}** |

The deterministic gate catches high-confidence policy/provenance issues. The ML detector adds
coverage for behavioral attacks, especially lower-amount trust poisoning where the transfer appears
to be explicitly requested by the user.
"""


def main() -> None:
    report = analyze()
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved breakdown to {BREAKDOWN_PATH}")


if __name__ == "__main__":
    main()
