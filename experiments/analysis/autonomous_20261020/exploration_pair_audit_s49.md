# Exploration pair audit — seed 49

Technical audit passed: 3,000 training and 240 evaluation games per arm; current HEAD/source/interpreter/protected identities; equal fresh Q/target/RNG; exact decay-only config difference; final checkpoint identities and finite Q/target tensors.

| Opponent | Control | Slow | Slow − control | 95% map interval |
|---|---:|---:|---:|---:|
| default | 95.00% | 95.00% | +0.00 pp | [-6.67, +5.83] pp |
| solution92 | 55.00% | 47.50% | -7.50 pp | [-19.17, +4.17] pp |

Mean result counts draws as 0.5. Whole-map bootstrap: 5,000 draws, seed 0, both sides together. This interval measures map variability for one fixed start, not training-start uncertainty. No method verdict, best-start selection, job or promotion.
