# Task 1 report — DONE

Implemented only `scripts/student_distill.py` and `tests/test_student_distill.py`; no commits, no production training or games, and no runtime-agent/default changes.

## Contract and implementation

- CLI: `python -m scripts.student_distill --teacher PATH --buffers PATH PATH --out PATH --deadline-utc ISO`; optional explicit `--row-cap` marks both manifest and status `technical_test_only=true` and records the cap. Production requires exactly two distinct full 300,000-row float32/79-column `s` matrices; all source rows are checked for finiteness even with a technical cap.
- Pinned V14 SHA256, guarded `torch.load(weights_only=True)`, exactly 36 homogeneous 79-input/6-output dueling QNets, shape/config checks and finite tensors. Targets match deployed `torch.stack(...).mean(dim=0)` bit for bit on a nontrivial 36-net synthetic case. Teacher models are eval/frozen and prediction runs under no_grad; teacher construction preserves RNG state.
- Single dueling QNet hidden 512; seed 20261104; Adam 1e-4; batch 1024; exactly three full independently shuffled epochs. Full production extent is 480,000 training rows, 1,407 updates, and 1,440,000 training-row visits. No epoch selection.
- First 80% / last 20% independently per file. Per-buffer train/diagnostic metrics before and after: raw Q-MSE, mean-value MSE, centered-action MSE and unmasked argmax agreement. Exact pooled feature-row overlap counts include unique overlap and matching row multiplicities, with signed zeros normalized. Metrics state the historical-row/absent-mask limitations explicitly.
- Input hashes before/after cover entire checkpoint and both complete replay files. Source hashes before/after cover entire distiller, model, config and path-protection source files. Manifest also records Python executable/version, Torch/NumPy versions, Git HEAD, actual row counts, progress, epoch/update counts, training-row visits and wall time.
- Protected and occupied outputs refused, including aliases and output ancestors containing sources/submission roots. A pending checkpoint is verified before final rename. Deadline checks occur between load/label/prediction/training batches. Deadline/error paths retain truthful incomplete status/manifest, remove pending/final checkpoint, and never report a complete candidate.
- Export contains one `q`, cloned identical `target_q`, empty `ensemble`/`ensemble_dims`, teacher cfg with only hidden changed to512, feature_dim79/n_actions6/env_steps60000/learn_steps0; no optimizer/replay. Separate `distillation_updates`, epochs and seed record actual supervised learning. Exact reload predictions are checked before export. Torch deterministic-mode flags are restored on exit.

## Actual verification

All Python execution used the existing primary `.venv`, with OMP/OPENBLAS/MKL thread count1 and torch thread count1 for synthetic fits.

1. Initial TDD run: **12 failures**, all intentional missing-implementation assertions.
2. First implementation: 11passed/1failed; the analytic argmax fixture accidentally tied all six outputs and was corrected to express its intended disagreement.
3. Additional failure-path coverage passed for deadline after one actual update, source mutation refusing export, fixed-seed exact repeatability, signed-zero equality and unchanged input arrays.
4. Two further tests first failed for global deterministic-mode leakage and float32 reduction-order differences from deployed stack-mean. Both fixes then passed.
5. Final focused command: `python -m pytest tests/test_student_distill.py -q`: **18 passed in2.47s**.
6. Read-only real-V14 preflight: **36 networks, hidden256, duelingtrue; finite output shape[2,6]; entire checkpoint hash unchanged** (`98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`). This only loaded/predicted two zero feature rows; no training or games.
7. Synthetic integration uses 36 real small QNets, two20-row buffers, the real512-wide student and three actual Adam updates. `Agent_x` loads the exported checkpoint with zero extra networks and exactly identical predictions; cfg preservation, finite outputs, cloned target, unchanged full source/input hashes and update counters asserted.

Root owns full-suite/integration checks, production runtime admission and subsequent experiment execution. No production runtime or strength claim is made here. No unresolved Task1 concern identified; independent review is still required by the plan.
