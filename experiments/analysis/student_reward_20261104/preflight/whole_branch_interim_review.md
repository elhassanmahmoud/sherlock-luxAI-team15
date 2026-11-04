# Student/reward whole-branch review — interim

Scope: frozen `b06a77de86b6359426e886c582917361162e8ff0..5b9f8836fb94c21a9cdbe07f49fb091a19de8426`, supplied whole-branch diff, authoritative amended spec, implementation plan, ledger, previous scoped reviews, and directly relevant existing producer/consumer, learning, validation and audit helpers. Repository instructions read. No source edits, tests, models, games, checkpoint loads, commits or heavy workloads performed. Only this report is written. Final data/documentation package is pending; this is not a completed experiment/data acceptance.

## Actionable code finding

### P2 — Publish readiness before exposing the final receipt

Location: `scripts/student_reward_train.py:491–497` (especially final receipt publication at line 492 before `persist()` at line 493).

The two arm workers use existence of the other worker's `final_receipt.json` as permission to call `compare_prefill`, but the receipt is exposed before that worker persists `status='done'`. A valid interleaving is: worker A atomically publishes its receipt and is descheduled; worker B completes its own persistence/validation, sees A's receipt and enters `compare_prefill`; `validate_receipt(A)` reads A's still-running `status.json` and raises `ValueError('Incomplete arm')`. B's enclosing exception handler then marks B incomplete and deletes B's otherwise valid final receipt. A can subsequently finish without a paired proof. Thus simultaneous valid completions can be incorrectly rejected even though no file is corrupt and both fixed learning budgets completed.

The prior unique-tempfile correction prevents staging-file collisions, but does not establish cross-file publication readiness. Make receipt publication the commit point after all required done-status/evidence files exist, or perform paired validation in a coordinator after both workers finish successfully. Add a deterministic publication-barrier regression after the active source freeze ends. A receipt reader must never treat the marker as ready before its required status is ready. No claim is made that this interleaving occurred in the actual experiment; final statuses and receipts must establish that separately.

## Other reviewed contracts

- Distillation computes the deployed arithmetic mean of all 36 pinned V14 raw Q vectors, holds labels fixed, performs the requested complete epochs, keeps the default at three, and exports only a final single 79/6/512 network with separate distillation counters. The explicit S30 amendment changes the complete epoch count without selecting a checkpoint on game outcomes.
- Independent 80/20 splits and pooled exact feature overlap are consistent with the specified historical diagnostic. Raw, mean-value and centered-action errors decompose correctly. Unmasked action agreement is not legal-action agreement or unseen-map evidence.
- The amended producer and consumer agree on optional all-or-none distillation provenance and sparse legacy config expansion. Full effective configs are carried into preparation and live learners; explicit teacher overrides survive. Both arms preserve source student bytes and differ only in `w_sap_hit`, after identical common training overrides.
- Initial learner proofs require fresh Adam/replay, exact equal q/target tensors and one canonical learner shared by both sides. Actual rollout hooks check schedule/config/epsilon, action-to-replay agreement, rewards, step and update counts. Prefill comparison includes full emitted actions/SAP coordinates and observed feature vectors. Different scalar rewards during prefill are expected.
- The reward counterfactual evaluates the same transition inputs, removes both hit bonuses and miss penalties, checks the signed algebra, and returns the actual arm's reward. No RNG/state mutation occurs in the inspected underlying reward function.
- Validation saves/restores RNG and mode, guards learning methods and replay writes, checks state identity and complete known-map schedules. This is separate from evidence of generalization. Final saving intercepts historical best-validation writes and accepts the final live state through matching tensor/optimizer/counter/reload proofs.
- Existing source/output guards and root-owned freeze protect the specified source weights. Final acceptance still depends on actual before/after hashes and source-freeze records, not static code alone. Reused helper source dependencies and runtime environment must remain under the coordinator's freeze; an absolute interpreter path is not a portable environment lock.

## Reviewed frozen hashes

- `scripts/student_distill.py`: `d79c07ba4df4dcd56f2784a4ad51201be5a1818c2a22a85b22b8cfea7095a6fa`
- `tests/test_student_distill.py`: `3b86de3b8b0ff771000aaff90b0f7aa10da4d28f62f4017dd8c7d688b8969b6f`
- `scripts/student_reward_train.py`: `b91a1149422273800c01cf7d65750d933c36dc8d7809e91ac8e264d3071c0213`
- `tests/test_student_reward_train.py`: `d2112d19fcb2e4b504db37c9de5fec1676226818445be2c4d7f7f7c361f25ada`

Previous focused test/review results were read as existing evidence and not rerun. Their scoped passes are not a guarantee against a different concurrent completion interleaving. Static review found no other material defect in this bounded scope.

## Pending completion package

Await actual S3/S30 audit records, both reward-arm completion/status/proof records, source/protected-hash reconciliation, phase-admission or explicit omission evidence for the 600-game diagnostic, and final shared documentation. The final review must reconcile counts and claims with those records and preserve all sampling limits. No promotion is authorized today.
