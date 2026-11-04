# Task 1 independent review: PASS

Scope: static review of `scripts/student_distill.py` and `tests/test_student_distill.py` against the Task 1 brief, implementation report, student/reward spec and implementation-plan global constraints. Read relevant current QNet, Agent_x load/inference and output-path protection code to validate integration. No repository files changed; no training, games, model loads, commits or additional tests run during this review. Reported 18 focused passes and root's 35 baseline passes are prior evidence, not independently rerun results.

No material correctness or specification defect found for this bounded prototype. No remediation required before the root's separate runtime admission and production-artifact verification.

## Reviewed evidence

- Teacher pin and load: lines 85–109 require the exact V14 SHA256, safe weights-only load, 36 homogeneous 79-input/6-output models, valid dueling configuration and finite state. Strict state loading validates architecture. Frozen eval teachers are constructed under saved RNG state. Lines 112–125 reproduce the current deployed `torch.stack(...).mean(dim=0)` reduction including float32 order; current Agent_x inference uses that operation at main.py:339–341.
- Data and diagnostics: lines 128–156 load only float32 79-column `s`, validate every source row for finiteness, require 300,000 rows without a technical cap, and split each file independently at 80%. Lines 159–177 count exact pooled feature equality including multiplicity and signed-zero normalization without altering inputs. Lines 180–211 calculate the requested raw/mean/centered MSE and unmasked argmax metrics per buffer and split. Lines 335–338 clearly limit interpretation to historical rows without current masks.
- Genuine fixed learning: lines 273–305 create one 512-wide dueling QNet, deterministic seed 20261104, Adam 1e-4, batch 1024, and three full shuffled epochs. Each batch performs backward and optimizer.step, checks finite gradients/parameters, and records actual update/row counts. Full inputs imply 480,000 training rows, 469 batches/epoch, 1,407 updates and 1,440,000 row visits. Lines 309–312 reject wholly unchanged student tensors.
- Export: lines 313–329 preserve the teacher cfg except hidden=512, export one q with an identical cloned target_q, empty ensemble metadata, 79/6 dimensions, specified env_steps/learn_steps, and separate supervised-learning counters without optimizer/replay state. Saved predictions are reloaded and checked. The integration test at tests/test_student_distill.py:115–146 additionally loads through actual Agent_x and verifies zero extras and identical predictions; this agrees with the existing loader's semantics.
- Guards/provenance: lines 67–82 reject occupied/protected/aliased outputs and ancestors containing inputs/protected directories. Lines 251–252 and 330–334 hash complete input files and relevant implementation sources and reject mutation before promotion. Lines 239–241, 265, 289 and prediction/data loops check the deadline between batches; lines 347–363 retain incomplete status and remove pending/final checkpoint on handled failure. Successful export follows all three epochs, post-training diagnostics, source/input checks and a final deadline check.
- Tests cover arithmetic and exact deployed mean, analytic metrics, independent splits and overlap, shape/dtype/nonfinite errors, protected/occupied outputs, safe export and actual Agent_x reload, timeout before and after an update, mutation refusal, deterministic repeatability/config preservation, signed zeros/input nonmutation, and deterministic-mode restoration. Synthetic-only scope is explicit.

## Boundaries

This review is code acceptance for the planned diagnostic, not runtime admission, a performance finding, or submission approval. Root still owns exact production replay selection/hash capture, full-run counts and changed-tensor checks, deadline/resource admission, broader protected-file snapshots and subsequent experiment decisions as assigned in Task 3. The script's technical row-cap mode is explicitly marked non-production; such fixtures must not be treated as the production student.

Reviewed SHA256:
- scripts/student_distill.py: `a9f262aca9ec0f2c752fd676b483e706df2677ccd7b99fd4bf98549ddbf6b504`
- tests/test_student_distill.py: `0e2d394b068cbf5261c5a8790953a4f4dd38343faa123743dd314518c3031bab`
