# Independent Task 2 code review

Reviewed only `scripts/student_reward_train.py`, `tests/test_student_reward_train.py`, the supplied Task 2 brief/spec/design/report, and their existing finetune/audit/validation integration. No production models, games, training, source edits, commits or subagents.

Review snapshot:
- Script SHA256 `0ae5920b8f93c661f8b243bccaabecdb9b3639bd54a872ded0578335495240fb`
- Tests SHA256 `49b8839971fb5d5b293c86cc23ff4474ce77b417b6ed67cd0849ce1983005dd5`

## Material findings

**[P1] Accept the actual distilled checkpoint provenance fields.** Root identified, and this review statically confirmed, a producer/consumer mismatch at `scripts/student_reward_train.py:87–92`: `_student` requires exactly nine fields. The Task1 producer `scripts/student_distill.py:318–319` additionally exports `distillation_updates`, `distillation_epochs`, and `distillation_seed`, recording genuine distillation training separately from RL counters. Consequently every actual Task1 checkpoint is rejected before reward prepare, although the synthetic Task2 fixture passes because it omits all three fields. Admit these explicitly known metadata fields with appropriate integer/finite validation and preserve provenance, while continuing to reject optimizer/replay/unknown fields. Add an actual producer-contract fixture or integration regression. No production model load was necessary to establish the mismatch.

**[P2] Use a unique temporary file for concurrent paired receipt publication.** `scripts/student_reward_train.py:45–49`, called by `compare_prefill` at lines608–615 and by both completing workers at lines473–475. Each arm may see the other's completed receipt and concurrently execute `compare_prefill`. `_write` chooses the identical `paired_prefill.json.tmp` pathname in both processes. If both write before either rename, the first replace removes that temporary pathname; the second replace raises `FileNotFoundError`. That error propagates into run_arm's lines476–480 failure handler, marks a fully completed arm incomplete and deletes its success receipt. The already-published paired file then remains despite the revoked arm. This conflicts with the intended two-worker execution. Use unique same-directory temporary files with atomic replace, or make pairing publication single-owner.

Reproduced without importing or loading models: extracted the current `_write` AST, ran two threads against a disposable paired JSON file, and synchronized both immediately before `Path.replace`. Observed outcomes `['FileNotFoundError', 'success']`; the final JSON was valid. The same pathname race applies to two independent workers. The reproduction changed no repository files.

## Passing review checks

- Config treatment: `_config` preserves the complete student config, applying identical frozen/lr/training-rule overrides and changing only `w_sap_hit` between arms. Student checkpoint rejects optimizer/extra fields and verifies identical finite q/target with the single hidden512 QNet contract.
- Start and prefill: exact copied student tensors, no source replay copied, fresh Adam/empty replay verified on the actual canonical learner through `prove_initial`; fixed common seed/opponent plan; prefill disables learning and checks unchanged q/target/optimizer. Full world actions/SAP coordinates and feature vectors join the audited replay-action transcript for paired comparison.
- Fixed budget: actual calls must match 40 prefill plus160 training games,303 steps each,150 updates per learning game, and32 validation games on known500000–500003 against two opponents/both sides. This yields env_steps120600 and learn_steps24000. Existing Agent_x skips the three match-reset update opportunities, supporting150 updates per303-step game. Actual CSV and persisted chronology are independently cross-checked.
- Validation: uses the reviewed `run_validation(..., isolate=True)` guards, disables learning and replay writes/sampling/optimizer steps, sets eval mode/epsilon0, preserves gameplay config, restores RNG and bindings even on failure, and compares before/after learning identities. No model training occurs during validation.
- Replay actions: reused `action_audit` checks emitted final actions against canonical recorded actions and every actual buffer write. Additional digest includes full SAP aim and features. Reward transition count must equal checked replay transitions.
- Reward diagnostic: wraps the actual main.unit_rewards binding; original/zero/actual calls use the same arguments and pure existing reward implementation. Signed hit and miss contribution identity is checked; actual arm reward alone is returned. Binding restores in finally. Per-game signed/absolute exposure, attempts, flips and occupancy are logged.
- Final-only acceptance: intermediate saves suppressed; final save/reload is checked against live tensors, optimizer and counters. Historical weights_best cleanup is present in this frozen snapshot. Exceptions/deadlines remove success receipt and persist incomplete status; fixed extent and evidence are required by the new receipt validator, not the old1200-game receipt.
- Protection/provenance: existing/protected output paths and aliases refused; both init files/source hash/config/plans revalidated, primary and worktree protected weight/ZIP hashes checked, and training/opponent/runtime source pins checked before/after. No runtime defaults or submission files changed.

## Verification

Independent focused run with primary existing venv and OMP/MKL/OpenBLAS threads set to1:
`python -m pytest -q tests/test_student_reward_train.py`

**11 passed in6.68s**, exit0. Synthetic orchestration checks do not establish real gradient learning or gameplay quality; no such claim is made. Implementer report additionally records19 focused/reward/parser tests passing in9.44s. No broader tests were needed for this review.

Assessment: resolve the producer/consumer contract mismatch and paired-publication race before admitting the reward phase. Other reviewed protocol behavior is satisfactory. The Task2-only synthetic tests did not expose the Task1 metadata mismatch.
