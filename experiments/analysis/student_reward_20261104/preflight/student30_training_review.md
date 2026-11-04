# S30 production student artifact audit: PASS

No training, games or repository edits. One CPU thread. No strength or submission-readiness claim.

Student SHA256: `3104596d5527d644d0c3f2cfc98189ec166e6e8e4a1f0ae9a4166f27a934b11b`.

Production run: two complete 300,000 × 79 float32 buffers; 480,000 training and 120,000 diagnostic rows; seed 20261104; Adam 0.0001; batch 1024; 30 complete epochs; 14,070 updates and 14,400,000 training row visits. No row cap. Guard exited 0; manifest/status agree.

Strict 79→512→512 dueling QNet; 12/12 tensors differ from deterministic initial state; finite tensors; target_q equals q. Actual Agent_x loads one net with exact checkpoint parameters/predictions, no extras. Config equals actual V14 cfg except hidden=512. No optimizer/replay payload. Export metadata: env_steps=60000 (inference exploration schedule), learn_steps=0; supervised updates/epochs/seed recorded separately.

All manifest teacher/buffer/source before/after hashes and current hashes agree. All five recorded protected weights/ZIP hashes remain unchanged.

Independently recomputed every before/after train/diagnostic metric from actual rows and direct arithmetic mean of the 36 teacher constituent networks. Agreement with recorded metrics within 1e-10.

| Buffer | Diagnostic Q-MSE before → after | Mean-value MSE after | Centered action MSE after | Unmasked argmax before → after |
|---|---:|---:|---:|---:|
| control18 (60,000 rows) | 369.486700987377 → 2.977447363950 | 2.638414075850 | 0.339033288100 | 0.128533333333 → 0.680883333333 |
| adapt18 (60,000 rows) | 367.822117761835 → 3.111383232460 | 2.779182289532 | 0.332200942928 | 0.121266666667 → 0.687150000000 |

Exact pooled feature overlap independently agrees: 18 shared unique rows; 18 train and 18 diagnostic row occurrences. Unique train/diagnostic rows: 471,229/118,118.

The finite changed checkpoint, deterministic initialization contrast, full-source metrics, pinned reviewed training code and completed guard support genuine learning. Epoch/update/row-visit counts are contemporaneous run records plus verified source-loop arithmetic; training was not rerun. No game strength, legal-action or independent-map/episode claim is made. The protected check covers the five paths captured by preflight; additional backup files have no before snapshot in the supplied evidence.

Blockers: none.
