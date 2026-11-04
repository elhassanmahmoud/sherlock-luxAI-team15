# Exploratory student/reward diagnostic

Integrity: all 600 planned games complete, unique, finite, 303 steps and scoring v2. Outcomes agree with recorded team win counts.

Scores count each draw as half. Intervals are unadjusted 95% paired whole-card percentile bootstraps (20 cards, 5,000 samples, seed 0).

| Role | Opponent | W–D–L | Score | Paired score difference vs V14 | 95% interval |
|---|---|---:|---:|---:|---:|
| V14 | pooled | 99–0–21 | 0.8250 | +0.00 pp | [+0.00, +0.00] pp |
| V14 | solution92 | 36–0–4 | 0.9000 | +0.00 pp | [+0.00, +0.00] pp |
| V14 | default | 40–0–0 | 1.0000 | +0.00 pp | [+0.00, +0.00] pp |
| V14 | V13 | 23–0–17 | 0.5750 | +0.00 pp | [+0.00, +0.00] pp |
| S3 | pooled | 33–0–87 | 0.2750 | -55.00 pp | [-60.83, -49.17] pp |
| S3 | solution92 | 0–0–40 | 0.0000 | -90.00 pp | [-100.00, -77.50] pp |
| S3 | default | 33–0–7 | 0.8250 | -17.50 pp | [-32.50, -5.00] pp |
| S3 | V13 | 0–0–40 | 0.0000 | -57.50 pp | [-67.50, -50.00] pp |
| S30 | pooled | 62–0–58 | 0.5167 | -30.83 pp | [-38.33, -22.50] pp |
| S30 | solution92 | 18–0–22 | 0.4500 | -45.00 pp | [-62.50, -27.50] pp |
| S30 | default | 40–0–0 | 1.0000 | +0.00 pp | [+0.00, +0.00] pp |
| S30 | V13 | 4–0–36 | 0.1000 | -47.50 pp | [-60.00, -32.50] pp |
| CONTROL30 | pooled | 58–0–62 | 0.4833 | -34.17 pp | [-42.50, -25.83] pp |
| CONTROL30 | solution92 | 16–0–24 | 0.4000 | -50.00 pp | [-67.50, -32.50] pp |
| CONTROL30 | default | 40–0–0 | 1.0000 | +0.00 pp | [+0.00, +0.00] pp |
| CONTROL30 | V13 | 2–0–38 | 0.0500 | -52.50 pp | [-65.00, -37.50] pp |
| SAP0_30 | pooled | 66–0–54 | 0.5500 | -27.50 pp | [-35.00, -18.33] pp |
| SAP0_30 | solution92 | 22–0–18 | 0.5500 | -35.00 pp | [-52.50, -17.50] pp |
| SAP0_30 | default | 40–0–0 | 1.0000 | +0.00 pp | [+0.00, +0.00] pp |
| SAP0_30 | V13 | 4–0–36 | 0.1000 | -47.50 pp | [-60.00, -35.00] pp |

Primary reward comparison: SAP0_30 minus CONTROL30 (same S30 initialization and one training seed).

| Panel | Score difference | 95% interval |
|---|---:|---:|
| pooled | +6.67 pp | [-0.83, +14.17] pp |
| solution92 | +15.00 pp | [+0.00, +30.00] pp |
| default | +0.00 pp | [+0.00, +0.00] pp |
| V13 | +5.00 pp | [-10.00, +20.00] pp |

Interpretation limits:

- Exploratory diagnostic on 20 locally reserved cards; not a strength confirmation or submission decision.
- One training seed; card bootstrap quantifies card variation conditional on these trained checkpoints, not variation over training seeds.
- Multiple role/opponent comparisons; percentile intervals are unadjusted and do not control simultaneous error.
- Whole cards are paired across roles and resampled with both sides together; pooled panels additionally keep all three opponents together.
- A score of 1 on these games describes this sample only and does not imply a population guarantee.
- CSV consistency cannot independently reconstruct engine scoring; v2 is required and outcome/win/point fields are cross-checked.
