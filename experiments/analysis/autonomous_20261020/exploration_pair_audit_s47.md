# Exploration pair audit — seed 47

Technical audit passed: 3,000 training and 240 evaluation games per arm; current HEAD/source/interpreter/protected identities; equal fresh Q/target/RNG; exact decay-only config difference; final checkpoint identities and finite Q/target tensors.

| Opponent | Control | Slow | Slow − control | 95% map interval |
|---|---:|---:|---:|---:|
| default | 100.00% | 93.33% | -6.67 pp | [-13.33, -1.67] pp |
| solution92 | 71.67% | 47.50% | -24.17 pp | [-35.00, -13.33] pp |

Mean result counts draws as 0.5. Whole-map bootstrap: 5,000 draws, seed 0, both sides together. This interval measures map variability for one fixed start, not training-start uncertainty. No method verdict, best-start selection, job or promotion.
