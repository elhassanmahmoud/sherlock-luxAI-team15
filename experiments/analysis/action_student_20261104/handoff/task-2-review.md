# Independent Task 2 review

Verdict: **request changes for one P2 output-boundary issue**. The numerical objective, training/calibration schedule, dataset split handling and final checkpoint contract otherwise pass specification and code-quality review.

## Finding

**[P2] Protect the packaged submission directory in the trainer output guard.** `scripts/student_action_distill.py:20-21,254` imports and uses `student_distill.reserve_output` directly. That helper protects `agents/sherlock/weights` and root-level `Gruppe15`, but omits `agents/Gruppe15` in the current, primary and historical checkouts. The Task 1 producer explicitly adds those packaged-submission boundaries in `student_collect.reserve_output`. Thus a fresh output such as `ROOT/agents/Gruppe15/action-fit` is accepted by the trainer and writes training artifacts into the submission packaging tree. Add the same guards locally or through a stable shared helper (without importing mutable collector internals), plus a targeted guard regression. Existing files are not overwritten because occupied outputs are refused; this is a protection-boundary gap.

Evidence: one bounded, non-mutating probe used `unittest.mock.patch.object(Path, 'mkdir', side_effect=ReachedCreation)` around the actual imported trainer `reserve_output`. `agents/Gruppe15/task2-review-probe` reached directory creation; `agents/sherlock/weights/task2-review-probe` and root `Gruppe15/task2-review-probe` were rejected before creation. No directories, training jobs or games were created. Interpreter: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`.

## Specification review

- `action_loss` implements mean over rows of legal-centered MSE divided by the fixed scale squared plus KL(teacher || student), with the teacher detached. Illegal log-probability entries are masked before subtraction, avoiding `-inf - -inf`; single-legal rows give exact zero loss/gradient. No instability found for the intended finite Q range.
- `teacher_scale` uses float64 legal-centered teacher entries from train rows only, pooled across all legal entries with floor .001. No student or per-row normalization.
- Exactly 30 action epochs and five value-only epochs, Adam 1e-4, batch 1024, seed 20261104. Only `train_index` enters either optimizer phase. Diagnostic predictions and metrics never feed training or scale. Whole-seed split assignment is checked across dataset rounds.
- Calibration minimizes squared raw legal-Q means against teacher legal means. Body/adv gradients are disabled, a new optimizer contains only value parameters, body/adv tensors must remain exact, and numerical legal pair-ranking changes are checked with an explicit near-tie tolerance.
- Actual `student_reward_train._student` accepts the exported existing metadata contract: one 512-wide network, exact q/target, no optimizer/replay/ensemble, env_steps 60000 and learn_steps 0. `Agent_x` reload is verified against actual predictions with no extra networks.
- Completed phases are required and timeout/exception paths remove pending/final artifacts. Sidecars retain cumulative real update counts, input/source hashes, split, objective/scale, phase counts and before/after metrics. Collector final-action metrics are explicitly labeled as recorded collecting-policy behavior.
- Producer contract was reviewed read-only: array names/dtypes/shapes match `student_collect.py`, including teacher labels added before package completion. Dataset manifests/status and array hashes are validated; actual games.jsonl semantic/game-completeness and fixed production seed/S30 provenance checks remain the parent integration boundary as explicitly agreed in the implementer report.

## Evidence and scope

Read Task 2 brief/report, task diff, complete trainer/test source, fixed design/plan, producer schema and the real `_student`/QNet/output helper implementations. Reviewed the supplied 28 focused tests and earlier 104-test evidence; did not rerun those green tests. The only new executable check was the concrete output-boundary probe above. No code edits, production runs, gameplay, commits or subagents. Task 1 producer source unchanged by this review.
