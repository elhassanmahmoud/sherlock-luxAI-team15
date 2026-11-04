# Student/reward whole-branch review — final

**Verdict: PASS for the final code, completed experiment package and reviewed handoff documentation. No remaining actionable correctness or documentation findings in the bounded scope. The original P2 completion-publication race is addressed. This is not approval to promote any candidate or a claim that Git publication/operational cleanup has already completed.**

## Scope and review method

Reviewed the original `b06a77de86b6359426e886c582917361162e8ff0..5b9f8836fb94c21a9cdbe07f49fb091a19de8426` diff and the final publication fix through `cdb6e85a90612728dce54b6c32f7c334c8fbddfe`; authoritative amended spec, implementation plan/ledger, repository instructions, previous scoped reviews and directly relevant existing producer/consumer, learning, validation and action/reward audit helpers. Then reviewed the final German report, README/CLAUDE orientation, new work-log/protocol entries, analysis/candidate READMEs, candidate manifest, completed diagnostic protocol/evidence, independent student/RL/diagnostic reports, root statistical cross-check and final focused-test evidence.

No source edits, tests, checkpoint loads, models, games, training, commits or subagents were performed by this reviewer. Only scratch review artifacts were written. Existing same-code tests and independent statistical/model audits were not repeated without a concrete concern. Direct additional verification here used lightweight file hashing, manifest comparisons, link/path checks and `git diff --check`.

## Original P2 finding — ADDRESSED

Original location: `scripts/student_reward_train.py:491–497` at `5b9f883`.

A worker exposed `final_receipt.json` before persisting `status='done'`. A peer could observe the receipt, call `compare_prefill`, reject the still-running status, then incorrectly mark its own fully trained arm incomplete and delete its receipt. Unique staging filenames fixed the earlier rename collision but not this cross-file readiness window.

Final source persists completed status and unchanged audit evidence before atomically publishing the receipt. The receipt now serves as the readiness commit point for the specific observed race. The deterministic regression immediately calls real `validate_receipt` after publication and before the producer continues, covering both synthetic arms. Captured evidence shows the original incomplete-arm failure, followed by 21/21 covering tests passing after the correction. Exception cleanup remains intact. This does not claim fsync/crash durability or protection against unrelated external mutation.

The original actual RL jobs remained under their original source freeze. The coordinator recorded pausing only its SAP0 child from 13:34:02.352150 to 13:34:55.226684 UTC to stagger completion, followed by resume and full completion. Independent 94/94 artifact acceptance preceded the source change. Those original receipts and artifacts were not rewritten to claim the corrected code produced them. The scoped fix report is `/tmp/sherlock-student-20261104/publication-fix-review.md`.

## Code and integration conclusions

- Distillation reproduces the deployed arithmetic mean of all 36 pinned V14 raw Q vectors, holds labels fixed, performs all requested epochs and exports a final single 79/6/512 dueling network with separate supervised counters. Default three epochs and the explicitly amended S30 path remain distinct; there is no game-result checkpoint selection.
- Independent 80/20 splits and pooled exact feature overlap match the design. Raw, mean-value and centered-action errors decompose consistently; the absence of current masks is correctly disclosed.
- The producer/consumer boundary supports complete optional distillation provenance and sparse legacy config expansion. Explicit teacher overrides survive. Both RL arms preserve student source bytes and differ only in `w_sap_hit` after the same common training overrides.
- Initial proofs require one canonical learner, exact q/target initialization, fresh Adam and empty replay. Rollout hooks enforce map/side/opponent/config/epsilon chronology, step/update counts and emitted-action/replay agreement. Prefill comparison includes SAP coordinates and observed features; scalar rewards may differ by design.
- Counterfactual reward instrumentation evaluates identical transition inputs, checks removal of both hit bonus and miss penalty, returns the actual treatment reward, and does not alter RNG/state in the inspected reward implementation.
- Validation guards learning and replay operations, restores RNG/modes, and verifies identity/schedule. Final-save interception prevents best-validation selection; saved final tensors, optimizer and counters are checked against the live learner and actual reload proof.
- Source/output guards and the coordinator's freeze preserve the specified source weights. These are supported by actual hash evidence below, not static code alone. Local paths and runtime records aid reproduction but are not a portable environment lock.

## Completed data and provenance

The supplied independent S3/S30 audits recomputed diagnostics over all 600,000 source rows with the direct 36-network teacher mean and checked actual Agent_x loading. Counts are consistent with 480,000 learning rows, 120,000 historical diagnostic rows, 1,407/14,070 Adam updates and 1,440,000/14,400,000 row visits. Both finite student states changed from initialization; 18 shared unique feature rows and 18 occurrences in each split are explicitly reported. Parameter arithmetic agrees with 435,847.

Independent RL audit accepts both arms: each 40 prefill + 160 learning + 32 known validation games, 24,000 Adam updates and final env_steps 120,600. Paired prefill action/feature transcripts match; SAP0's 898.2 lower prefill aggregate reward equals the signed removed term. Later reward-exposure tables agree with the audit and are not interpreted as strength estimates. Total new game accounting is 464 RL-related + 600 diagnostic = 1,064.

The completed diagnostic contains the full fixed five-role × 20-map × two-side × three-opponent grid. All five guards record exit 0 and 120 games each; the supplied independent audit validates unique keys, finite complete 303-step v2 rows and outcome consistency with recorded wins. The independent auditor and existing `scripts.compare_report` cross-check agree on 54 estimate/interval values and all W/D/L values with no dropped games. No second sample or promotion is claimed.

Direct checks by this reviewer confirmed:

- All 89 source hashes are identical between protocol/completion records and current files at `cdb6e85`.
- All five protected snapshots match before/after records and current files, including V14 and the existing ZIP.
- All five role snapshots and the V13 opponent match pinned hashes; all four candidate sizes match their manifest.
- Every completed CSV hash matches both its completion record and independent audit record.
- Original student/RL guard files exist in the durable archive; links in the final report and analysis/candidate READMEs resolve.
- Current source/test hashes match reviewed versions; `git diff --check` passes. Final captured log records **50 focused tests passed in 9.94s**. The report correctly distinguishes this from 35 earlier baseline tests and does not claim a rerun of the full historical suite.

These checks bind the reviewed summaries to current durable files. They do not independently replay the environment or recreate training; learning chronology and runtime action/isolation proofs are supported by recorded evidence plus reviewed implementation and separate artifact audits.

## Findings and interpretation in the handoff

Final documentation matches the data: Solution wins are V14 36/40, S3 0/40, S30 18/40, CONTROL30 16/40, SAP0_30 22/40. Three-opponent totals are 99, 33, 62, 58 and 66 out of 120, with no draws. The primary SAP0−CONTROL contrast is +6.67 percentage points, paired 95% interval [−0.83, +14.17]; SAP0−V14 is −27.50 points [−35.00, −18.33]. The cautious claim of an uncertain positive SAP signal within this student pair, alongside clearly inferior student results in this sample and unchanged V14 submission, is supported.

The report explicitly states 20 maps, one training start, whole-map pairing, 5,000 bootstrap replicates/seed0, multiple unadjusted exploratory comparisons and no independent confirmation. Card resampling describes map variation conditional on these particular trained models, not training-seed uncertainty. Local freshness is limited to scanned readable seed fields/ranges in eight working copies; seedless/undocumented/external trials remain unknown. Historical replay row diagnostics do not establish episode/map independence or legal-action agreement. Sample win rates do not promise universal outcomes, and historical 95.4% Solution results on different cards are not treated as a longitudinal drop.

The retained rule layer, injected env_steps schedule counter, separate supervised/RL updates, S30 amendment timing, original source commits, publication-race mitigation/fix and local-only replay requirements are explained accurately. All four archived checkpoints are clearly marked experimental and not approved submissions. Suggested action-aware losses, new masked student-state data, multiple starts and other features remain proposals, not completed work.

## Final reviewed hashes

- `scripts/student_distill.py`: `d79c07ba4df4dcd56f2784a4ad51201be5a1818c2a22a85b22b8cfea7095a6fa`
- `tests/test_student_distill.py`: `3b86de3b8b0ff771000aaff90b0f7aa10da4d28f62f4017dd8c7d688b8969b6f`
- `scripts/student_reward_train.py`: `011dd1b5612755fc5117ec9d3fbb8e32de86365624d4f948e57174c3d013e5f5`
- `tests/test_student_reward_train.py`: `a7445354cb3f43fd03d0d09e591871f1ea8d002b0be014e3b49daa2d1baa72b6`

At this review boundary, operational cleanup, the promised `operations_closed.json` and final main-branch publication remain coordinator work. The final package does not yet prove those actions occurred; create and reconcile the closure record before publication as planned. This is an explicitly outstanding delivery action, not a remaining code/data/documentation defect. No promotion is authorized today.
