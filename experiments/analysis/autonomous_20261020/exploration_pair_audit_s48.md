# Exploration pair audit — seed 48

Technical audit passed: 3,000 training and 240 evaluation games per arm; current HEAD/source/interpreter/protected identities; equal fresh Q/target/RNG; exact decay-only config difference; final checkpoint identities and finite Q/target tensors.

| Opponent | Control | Slow | Slow − control | 95% map interval |
|---|---:|---:|---:|---:|
| default | 98.33% | 93.33% | -5.00 pp | [-11.67, +0.83] pp |
| solution92 | 56.67% | 49.17% | -7.50 pp | [-16.67, +0.83] pp |

Mean result counts draws as 0.5. Whole-map bootstrap: 5,000 draws, seed 0, both sides together. This interval measures map variability for one fixed start, not training-start uncertainty. No method verdict, best-start selection, job or promotion.
