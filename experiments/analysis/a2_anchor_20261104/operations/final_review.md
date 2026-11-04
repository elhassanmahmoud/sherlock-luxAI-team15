# Final whole-branch review — A2 teacher anchor

Reviewed base `bb21f4c5cb14b239f920ba608a1d6d8fd7df5cb0` through head `7ba73806b6bc40895064afca537c4c4e7308496b`.

**Spec verdict: PASS. Quality verdict: PASS for publication of the completed experimental tools, evidence and report. No actionable P0/P1/P2/P3 finding remains in the reviewed branch. This is not approval of a replacement submission model: V14 correctly remains the release.**

## Scope and evidence

Read the whole-branch review package, project rules/current handoff, approved spec/plan and SDD ledger; inspected all three new public tools, their tests, the two historical-clock test changes, authored documentation, candidate manifest, archived implementation reviews, learning-completion and diagnostic audits, root crosscheck and relevant unmodified training/loss interfaces. Inspected the fixed diagnostic controller and the evaluator's key/completeness/statistics/selection implementation. Large data and model files were checked through recorded provenance and fresh byte hashes, rather than printing or re-executing them.

### Contract checks

- `scripts/student_anchor_train.py:64–111` reproduces the original replay sample, TD targets, Huber loss, clipping, optimizer and target-update schedule, adding exactly the existing legal-centered action loss at fixed weight 0.1 before a single backward/step. The original loss helper detaches teacher data, masks illegal coordinates, removes common value shifts and gives singleton legal masks zero action loss. `:128–138` calls the saved original update directly at weight zero. Reviewed tests cover exact parameter/optimizer/target/RNG equivalence and independent positive-anchor sampling.
- `scripts/student_anchor_train.py:41–61,225–245` copies only training rows and pins both original collections, counts and the A2 scale. Each arm uses the prescribed 256 draws with replacement and separate RNG. Completion validation independently recreates samples and rejects changed inputs, incomplete evidence or inconsistent combined loss. Restored constructor/instance adapters keep production source untouched. The prior CSV rounding defect is resolved at `:422–427`, with the real outer-publication boundary regression accepting producer precision and rejecting material discrepancies.
- `scripts/student_retention.py:143–172` evaluates only excluded rows, independently per model with no gradients, records clear metric definitions, and protects existing collector archives. The previously reported nested-output issue is resolved at `:130–133` with direct and symlink regressions.
- `scripts/student_failure_trace.py:103–114,116–202` captures actual forward inputs/outputs and the existing context without a second policy/belief computation. Copied raw outputs precede in-place masking. Terminal information stays external to decisions. `:302–355` compares full actions for both sides, results, match metrics and source/input pins on the ordinary play path. Overrides are not assigned invented rule causes. Tests and archived paired results cover these boundaries.
- The fixed four final models, two starts, 928 learning/prefill/known-validation executions, 96,000 updates and 920 fresh diagnostic games match the approved scope. The archived independent learning audit records 24,000 active gradients and 6,144,000 train-only draws per anchor, with paired actual prefill equality. The diagnostic audit groups both sides and all panel opponents by whole card, uses 5,000 draws/seed 0 and applies the predefined selection screen. Both anchors fail; there is no confirmation or promotion.
- The two existing test-file edits only move their local test clock into the future so STOP cleanup remains reachable; production deadlines are unchanged. The archived completed full-suite log reports 1,307 tests and 126 subtests passed. Source/tests/runtime paths have no changes between frozen `09c6934` and reviewed head.

### Fresh read-only checks performed in this review

- Verified all 90 preflight and 141 completion archive-manifest entries against their archived SHA-256; for every compressed entry also hashed decompressed bytes against the original source hash.
- Verified all six role files against the candidate manifest, the four new model copies against original final checkpoints, and all four original outer receipts against their recorded hashes.
- Verified all eleven diagnostic CSV hashes against the independent diagnostic report. Inspected machine-readable completion, diagnostic and root-crosscheck records; the controller reports eleven completed jobs and an empty running list.
- Rehashed all five protected files (four V14 copies across the two checkouts and existing ZIP), all five foreign files and all 87 original source files from initial-state evidence: every hash still matches.
- Confirmed the base-to-head diff contains no changes under `agents/` or `lux/`, or to original common, finetune and student-reward training files. Confirmed tracked checkout status clean and reviewed HEAD exact.

The first local archive-hash inspection stopped on a schema-key mismatch between the two manifest formats; it read no experimental code and changed nothing. The corrected read-only check above completed successfully. No test suite, model inference, training, games, replay simulation, source/index/HEAD mutation or subagent was run in this final review. The sole review artifact is this file outside the repository.

## Findings and limitations

**Findings: none.** Earlier P1 rounding and P2 archive-containment findings are resolved, not parked.

The report accurately distinguishes known-case observation, teacher-retention measurements and fresh game evidence. It records technical test incidents separately from the 1,872 study executions, discloses the private-NumPy-reader audit retry and does not claim universal 100% strength from V14's 40/40. Two training starts and twenty cards per evaluation population support the stated exploratory conclusions only; no general causal mechanism or globally superior method is established.

I did not independently rerun the 12-million-draw learning reconstruction, the 236 numerical calculations, engine scoring or historical test suite. Their archived independent audits, inspected implementations and freshly verified evidence hashes support this review. Prefill array equality is represented by runtime digests rather than separately saved raw prefill snapshots; gradient activity relies on recorded hooks from the shared backward. Historical operational helpers retain absolute original paths, as documented, and are not portable restart instructions. Full raw replay buffers remain local and are explicitly excluded from the published archive.

Remote reconciliation, actual push/main integration, updating the primary checkout, termination of any remaining owned monitor/awake process and the final operational handoff are outside this read-only review and remain root-owned publication/closure steps. No completed experiment needs rerunning for this verdict.
