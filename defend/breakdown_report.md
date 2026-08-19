# Gate vs ML Detector Breakdown

Evaluated on 300 simulated fraud attacks.

| Defense Result | Count | Percentage |
|---|---:|---:|
| Gate caught | 247 | 82.3% |
| Detector caught | 300 | 100.0% |
| Both caught | 247 | 82.3% |
| Gate only | 0 | 0.0% |
| Detector only | 53 | 17.7% |
| Missed | 0 | 0.0% |
| **Combined defense** | **300** | **100.0%** |

The deterministic gate catches high-confidence policy/provenance issues. The ML detector adds
coverage for behavioral attacks, especially lower-amount trust poisoning where the transfer appears
to be explicitly requested by the user.
