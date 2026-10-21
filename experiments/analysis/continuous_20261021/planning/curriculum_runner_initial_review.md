### Spec Compliance

- ❌ Issues found: Task 2's incomplete-CSV rejection and exclusive heavy-job admission are not fully implemented (`scripts/early_curriculum_study.py:207`, `:412`, `:595`). These should be fixed before starting the study.
- ✅ Both requested files are present; requested public interfaces and explicit start/resume CLI are implemented. Commands fix the six 3000-game arms, seeds, validation settings and isolate-validation flag; only opponent plan and output location differ between arms (`scripts/early_curriculum_study.py:170`, `:547`).
- ⚠️ Cross-task requirements remain intentionally unverified: Task 3 statistical gates and Task 4 conditional candidate/confirmation work do not exist in this diff. Root must preserve the 2080 ensemble-game / 400 direct-game reservation in `remaining_work` until completed jobs or failed gates justify reducing it (`scripts/early_curriculum_study.py:181`). Freeze final HEAD/source/plan/interpreter/weights and record the fresh-block collision check only after all remaining implementation/review changes. This is not a Task 2 defect.

### Strengths

- Audits enforce exact training sequence, five validation timepoints, 160 validation keys, ten reproducible aggregates and 240 final evaluation keys; pair audit compares actual initial identities and checks output-hash coverage (`scripts/early_curriculum_study.py:286`, `:345`, `:351`).
- Checkpoint loading is isolated into an owned child, validates finite q/target tensors and final counters, and final evaluation reads the final 3000-game checkpoint (`scripts/early_curriculum_study.py:267`, `:516`).
- Admission reserves all specified game counts using maxima, factor 1.25, and 900 seconds; phase completion is published only after the child exits and output audit/hash capture succeeds. Resume retains the original deadline and rejects incomplete phases (`scripts/early_curriculum_study.py:157`, `:181`, `:189`, `:470`).
- Tests exercise real short processes for deadline/signals and preserve a foreign process, rather than mocking all lifecycle behavior (`tests/test_early_curriculum_study.py:304`, `:324`). Reported 47-test run was not rerun.

### Issues

#### Critical (Must Fix)

- None found within the Task 2 scope.

#### Important (Should Fix)

1. **[P1] Resource admission does not exclude every heavy child or atomically reserve the shared resource.** `scripts/early_curriculum_study.py:412-417`, `:420-436`, `:595-596`. The process-name pattern excludes this runner's own `scripts.early_curriculum_study --checkpoint-audit` process, although that command imports Torch and loads the checkpoint. A second study can therefore begin a trainer/evaluation while that audit is active. The lock lives inside each study directory, so different run IDs have independent locks; two supervisors can also both pass the process snapshot before either launches a training child. Both cases violate the global one-trainer OR two-evalworker limit and the prohibition on concurrent model audits. Use a shared resource lock across cooperating study supervisors, held throughout the heavy execution/audit interval (or the entire managed study), retain best-effort foreign-process detection, and include the explicit checkpoint-audit command among heavy jobs. Such a lock cannot prevent an unrelated manually launched tool that does not cooperate from starting later; this finding requires deterministic exclusion across our own supervisors, not an impossible system-wide promise. Add a lightweight two-supervisor or lock-contention regression plus an audit-process admission case. Focused evidence: `check_resources()` returned successfully for a mocked `ps` line containing `/python -B -m scripts.early_curriculum_study --checkpoint-audit state.json 47 control`.

2. **[P2] Incomplete CSV schemas are accepted as complete evidence.** `scripts/early_curriculum_study.py:207-218`, `:345-348`; fixture at `tests/test_early_curriculum_study.py:130-134`. Header validation only rejects empty/duplicate names, then checks values for columns that happen to exist. Neither it nor the callers require the complete production schema. A final table with the correct 240 keys and only 12 core fields passes despite omitting all 12 remaining `GAME_FIELDS`, including timing and diagnostics. The synthetic success fixture already omits these fields, so the existing tests normalize the gap. The same design allows required training diagnostics such as `epsilon` or `winrate_50` to disappear without rejection. Require explicit per-table schemas (complete GAME_FIELDS, TRAIN_FIELDS, VAL_FIELDS, and after_games for raw validation) without introducing heavyweight supervisor imports. Test deletion of required columns as well as deletion of rows, and make success fixtures schema-complete. Focused evidence: `audit_evaluation()` returned `{'evaluation_rows': 240}` for a CSV missing 12 production GAME_FIELDS.

#### Minor (Nice to Have)

1. **[P3] Signal masking leaks into the child.** `scripts/early_curriculum_study.py:433-442`. Blocking HUP/INT/TERM protects the Popen/ownership-registration window in the supervisor, but the child inherits that mask across exec; restoring it in the parent does not restore it in the child. A real lightweight child reported blocked signals `[1, 2, 15]`. Consequently `stop_group`'s SIGTERM stage cannot gracefully terminate these children; cleanup normally falls through to SIGKILL. Preserve the parent's race protection while restoring the intended signal mask in the launched child using a safe launch mechanism, and test the child's mask or a TERM handler. This does not invalidate the demonstrated bounded hard-kill cleanup, so it is not a blocking finding by itself.

### Verification and Scope

- Reviewed package `review-99ba956..4332d6b.diff` (BASE `99ba956`, HEAD `4332d6b`) and the task brief/report. The initial tool output truncated the middle; the missing lifecycle/CLI portion was retrieved from the diff package. No changed source file was separately read, no Git state commands were run, and no checkout files were modified.
- Concrete integration risk checked: mismatch between audit/command assumptions and production output. Inspected only relevant `scripts/experiment.py` schema, manifest, validation-timing and training-write sections, `scripts/par_eval.py` CLI/output/worker behavior, and `scripts/common.py` result/steps generation. These support the manifest argv slicing, validation timing interpretation, final seed offset, two-worker invocation and three-match result assumptions; they also establish the missing-column finding.
- Focused counterexamples used `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B`, temporary CSV/state files, a mocked process listing and one short non-model child. No model was loaded; no training/evaluation job or package-wide test suite was run. The signal-check harness initially used macOS's symlinked temporary-directory spelling and was correctly rejected by input-path safety; resolving that temporary root allowed the narrow child-mask check.
- Reported verification remains 47 passing scoped tests in the implementer's report. The new findings are cases that report and its tests did not cover.

### Assessment

**Task quality:** Needs fixes.

**Reasoning:** The orchestration and data audits are thoughtfully bounded and the main experiment contract is represented, but shared resource exclusion and schema completeness do not yet satisfy the fail-closed guarantees needed before an expensive study. Fix the two Important issues and run focused regressions before proceeding to the later task gates.
