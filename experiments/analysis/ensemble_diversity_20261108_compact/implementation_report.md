# Task 1 implementation report

Commit: `f903de9` (four assigned source/test files only).

Implemented immutable `full20261107` and explicit `compact20261108` experiment profiles in the existing analysis/controller pipeline. Compact selection fixes 39 jobs / 1,560 games with panel 1700000–1700019 and direct 1701000–1701019. Compact confirmation fixes 15 jobs / 3,200 games with panel 1800000–1800099 and direct 1900000–1900199. Role paths, model/opponent pins, ranking, score and strict-win safeguards, bootstrap implementation and ten confirmation checks remain shared and unchanged.

The controller's `--profile` defaults to legacy full and must match the plan. Profile controls analysis directory, protocol source identity, phase reservation and expected completed selection. It persists in state and launch records. Compact provenance, receipts and analysis reports also bind the profile. Legacy full records without profile remain valid and keep the original report shape for deterministic historical recomputation.

Confirmation admission recomputes all 39 matching-profile selection jobs and the exact saved nominee before validating/opening confirmation seed files. Source/model/receipt/hash binding, fresh quota checks (including authorized ceiling 100), resource limits, STOP, exclusive reservation and no-resume logic are retained.

Verification actually performed:

- RED: compact analysis initially failed on unsupported protocol/profile and helper arguments (6 failures); compact controller evidence/CLI failed on missing profile support (2 failures); compact build_state failed on missing profile argument (1 failure).
- Final command: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest tests/test_ensemble_diversity_compare.py tests/test_ensemble_diversity_eval_supervisor.py -q --tb=short`.
- Result: **113 passed, 43 subtests passed in 5.46s**. Includes all original tests in these two files, complete bound synthetic 1,560/3,200-row blocks, exact seeds/counts, cross-profile protocol/path/provenance/receipt failures, nominee tampering and deterministic recomputation, strict default boundaries 40/40 and 198/200, controller CLI/state/reservation, and pre-confirmation seed ordering.
- `git diff --check` passed before commit.
- No model jobs, real games, weight changes, old incomplete outcome reads or changes outside the four assigned files by this implementer. Root owns documentation, plan generation, seed audit and overall-suite coordination. A whole-repository suite was not run here because this task explicitly prohibited games and restricted verification to synthetic/source tests.

Open: independent review and root-owned prelaunch work. No measured performance conclusion; no model start by implementer.
