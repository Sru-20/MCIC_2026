# Person B: Defender Pipeline

This folder contains the deterministic gate and ML detector for the agentic payment fraud
simulation.

## Files

- `features.py` - converts JSONL transcripts into numeric ML features
- `gate.py` - deterministic safety gate for payment attempts
- `train.py` - trains the Random Forest fraud detector
- `evaluate.py` - writes precision, recall, F1, AUC, and confusion matrix reports
- `breakdown.py` - compares gate coverage against ML detector coverage
- `classifier_model.pkl` - trained model artifact
- `feature_columns.json` - stable feature ordering for inference
- `evaluation_metrics.json` - machine-readable ML metrics
- `evaluation_report.md` - judge-facing evaluation summary
- `breakdown_report.json` - gate-vs-detector coverage report

## Run

From the repository root:

```bash
python defend/features.py
python defend/train.py
python defend/evaluate.py
python defend/breakdown.py
```

## Defense Design

The deterministic gate catches high-confidence provenance and payment-risk cases:

- payment instruction came from external content
- agent inferred payment details
- final payee came from tool output
- new payee with amount over `$500`
- amount over `$1000`
- recommendation flow suppresses competing options

The ML detector learns softer behavioral signals:

- payee planted earlier in a multi-turn conversation
- urgency language
- trust-building or romance language
- authority/compliance language
- recommendation steering
- payee introduction timing

The project argument is that neither layer is enough alone: the gate is reliable for hard policy
signals, while ML detects social-engineering trajectories where the final transfer may appear
`user_explicit`.
