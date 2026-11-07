# Fix round 1 — comparison admission and training cleanup

Implemented in the primary checkout on 07.11.2026 after Root confirmed there were no active model jobs and authorized tests. No training-worktree writes, real children, games, commits, or change to the foreign-process guard policy.

## Confirmation admission

`selection_evidence` now reruns `ensemble_diversity_compare.analyze` on the complete saved selection plan/results/provenance before any confirmation seed files are opened. The saved summary must equal the deterministic recomputation in full, and its nominee must equal the requested nominee. This revalidates the fixed 39-job inventory, receipts, all 7800 rows, and selection ranking instead of trusting a hash-bearing summary.

Regression evidence: the former 39 arbitrary `job_N` files with an empty plan/receipts are rejected. A real complete synthetic selection is accepted; changing only its saved nominee from A39 to B39 is rejected. Both new rejection tests failed before the change and passed afterward. The existing confirmation-seed ordering test remains passing.

## Training cleanup

Added a local conservative `group_alive` probe to `ensemble_diversity_supervisor`. Permission failure is considered disappearance only when a successful independent `ps -axo pgid=` snapshot contains no matching group. A present group or failed snapshot still raises. Shutdown polls/reaps leaders before each group probe and tolerates `ProcessLookupError` if a group disappears between probe and TERM/KILL. The normal post-exit descendant check uses the same probe.

Seven new simulated-race cases failed before the fix and pass afterward: absent/present/failed independent snapshots, reap-before-probe order, disappearance during TERM and KILL, and successful completion after an exited-group permission race. The original incident's precise EPERM cause was not reproduced; these are deterministic mocks of the reported failure modes.

Root's run-prefix work and foreign-process policy were preserved. An AST comparison before/after the edit confirmed identical `run_name`, `training_command`, `build_state`, `run_supervisor`, `main`, `check_model_processes`, and `guard` functions. Existing run-prefix tests remain passing.

## Executed validation

With all numeric thread limits set to one and bytecode writes disabled:

```
.venv/bin/python -B -m pytest -q tests/test_ensemble_diversity_supervisor.py tests/test_ensemble_diversity_eval_supervisor.py
......................................................   [100%]
54 passed, 16 subtests passed in 1.34s
```

Earlier focused check after the admission change: `19 passed, 16 subtests passed in 1.16s` for the evaluation-supervisor test file. No full project suite or actual model execution was run for this fix. Independent re-review remains with Root.
