# Person B Defense Evaluation

## ML Detector Metrics

| Metric | Value |
|---|---:|
| Precision | 1.000 |
| Recall | 1.000 |
| F1 | 1.000 |
| AUC | 1.000 |
| Threshold | 0.50 |

## Confusion Matrix

|  | Predicted Legitimate | Predicted Fraud |
|---|---:|---:|
| Actual Legitimate | 20 | 0 |
| Actual Fraud | 0 | 60 |

## Top Model Features

- `payee_by_user`: 0.2549
- `payee_lag_turns`: 0.1522
- `trust_word_count`: 0.1071
- `turn_count`: 0.1000
- `authority_word_count`: 0.0884
- `tool_result_turns`: 0.0641
- `payee_by_attacker`: 0.0469
- `payee_by_tool_result`: 0.0415
- `attacker_turns`: 0.0381
- `agent_tool_call_turns`: 0.0353
- `urgency_word_count`: 0.0260
- `source_user_explicit`: 0.0164

## Interpretation

The ML detector learns behavioral signals that deterministic rules can miss, especially
multi-turn trust poisoning where the final tool call may appear to be `user_explicit`.
The deterministic gate remains important because it catches provenance risks immediately,
such as payment instructions sourced from external merchant or recommendation content.
