# Task 1 — isolated fixed-artifact validation tool

Implemented and committed as `e5b6345` (`Add isolated fixed REPLACE36 prospective validation`). Only `scripts/replacement_validation.py` and `tests/test_replacement_validation.py` are in the commit. This report is intentionally ignored under `.superpowers/sdd/`.

## Delivered behavior

- Standalone `start`, `analyze`, `stop` CLI; exact 15-job/3200-game fixed matrix under profile `replacement20261108`, phase `confirmation`, nominee null. Existing NOMINABLE, controllers, analyzers, gates and archived data are unchanged.
- Reuses the shared resource lock, safe paths, origin-independent source identity, quota/power/process guard, queue, PID/PGID ownership, receipts, termination and reservation helper. Its small lifecycle wrapper changes only admission/output namespace; it calls shared `run_queue` directly.
- Fixed REPLACE36 SHA-256 `5ce350a86d4ed90b319af298e64b98e7f725ed253f5df89d504e98a73a54db6b`; origin SHA-256 `e63c06d87745120b7c7e46d4fc8dec264e178377c548cd0cd23a6c3dda85d02e`. Origin and all historical files are byte-bound; prior compact nominee must remain null and REPLACE36 nominable false. Historical source hashes are evidence, never compared as if they were current runtime sources.
- New single-use `validation_launch.json`; no restart or partial reuse. Old output namespaces are rejected. Existing STOP applies. Shared guard preserves max two workers, quota ceiling <=100, fresh known quota receipt, source/HEAD/protected weight/ZIP checks, power controls, process/test collision checks and shutdown behavior.
- Analysis validates complete state, reservation, provenance, origin, admission, source/HEAD, protected files, every input hash, exact plan/seed inventory, all commands/receipts and every real CSV field/key before statistics. Requires exactly 15 complete jobs and 3200 games, no missing/extra/duplicate/mixed rows.
- Calls shared `confirm_checks` directly, without sending REPLACE36 through the legacy nomination gate. Preserves seven score gates plus three strict-win safeguards. Reports all seven opponents' W/D/L and score/delta confidence intervals plus panel and direct intervals; labels the independent outcome-motivated validation, unadjusted interval limitation and no automatic promotion/successor/top-up.

## Actual verification

TDD observed missing-entrypoint failure before implementation. Complete synthetic pass/fail matrix and negative tests were written before implementation. Self-review added failing regression tests for omitted protected bindings and missing opponent intervals, then fixed both. All data are explicitly synthetic; no synthetic outcomes are claimed as new experimental results.

Command used:

```text
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_replacement_validation.py tests/test_ensemble_diversity_compare.py tests/test_ensemble_diversity_eval_supervisor.py tests/test_ensemble_diversity_supervisor.py tests/test_compare_report.py tests/test_league_gates.py -q
```

Result: **228 passed, 43 subtests passed in 10.23s**. Includes lifecycle failure/reservation/wake cleanup, CLI start/analyze/stop wiring, stale quota/source drift, fixed artifact/origin/admission and schedule refusals, rebound malformed CSV/receipt rejection, complete positive and inconclusive matrix, all unchanged strict gate edge cases, and existing helper/statistical/controller suites.

Read-only real-input check: origin_evidence validated **86 origin/archival paths**; validate_plan validated **15 jobs**; build_state returned prepared/profile replacement20261108/confirmation/nominee null/3200 expected games and correct validation_launch.json. It did **not** create an output directory or reservation. No model import/load, training, game execution, or launch was performed.

`git diff --cached --check` passed before commit. Full repository suite was **not** run because the assigned scope explicitly prohibits model loads and tests with actual games; relevant shared suites above passed.

## Self-review

Reviewed evidence ordering: every CSV/receipt/state binding and required field validates before validation_checks can run. Confirmed commands contain only fixed par_eval arguments, exact role weights and seed lists; no config overrides. Confirmed old modules remain unchanged and shared queue still owns max-two scheduling, STOP, guard checks and child cleanup. Fresh output and exclusive reservation remain irreversible-once-launched safeguards even after failure, while wake/signal cleanup is retained. Additional opponent intervals use the existing compare_results bootstrap, preserving whole-map sampling, 5000 draws and seed 0.

No unresolved implementation findings. Root still owns independent code review, final source freeze, documentation/publication, and any actual user-authorized execution; no strength claim or promotion is justified by these synthetic checks.
