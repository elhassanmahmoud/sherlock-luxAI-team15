# Full-suite diagnosis and bounded test fix — 2026-11-03

**Finding:** all 11 failures in root's default-discovery suite were archived-test import-isolation defects. They were not failures of the new runtime, training, builder, statistics, fixed-date admission or source artifacts. Root's red evidence: **11 failed, 1064 passed, 126 subtests passed in205.87s**, exit1, `/tmp/sherlock-final-20261103/full_suite.log`.

Every final traceback failed an assertion inspecting the entire pytest process's `sys.modules`. Root discovery collects model-oriented tests before executing these archived tests, so Torch and agents were already legitimately imported. The archived test bodies had otherwise reached their intended final import check. No missing historical path, stale-deadline or changed-configuration failure occurred in this run.

## Exact affected contracts

- `backup_adaptation_20261102/test_study_driver.py`: CSV invalid/missing/duplicate key rejection.
- `backup_adaptation_20261102/test_study_stats.py`: complete two-phase summary chain.
- `continuation_20261102/performance/test_build_targeting_candidates.py`: invalid component rejection, mutually exclusive P-only/audit mode, P-only preservation (three tests).
- `continuation_20261102/performance/test_targeting_eval_driver.py`: complete synthetic phase and shared-freeze confirmation.
- `continuation_20261102/performance/test_targeting_stats.py`: complete selection/confirmation and P-only chain (two tests).
- `continuation_20261102/release_tools/test_install_qualified_P.py`: model/environment stack import boundary.
- `continuation_20261102/release_tools/test_verify_P_package.py`: valid package and incomplete-confirmation rejection (two tests).

Paths above are relative to `experiments/analysis/`. Only those seven archived **test** files and the new `tests/archive_import_isolation.py` helper were edited after root confirmed the original suite exited. Runtime/statistical helpers, historical plans/results, model files and new experiment implementations were not changed by this fix.

## Bounded fix

Each import assertion now calls a shared test helper which reruns that exact real unittest class/method, including setUp/setUpClass/body/cleanup, in the current Python with `-I -B`, explicit repository/sibling paths and a30-second bound. A process-local marker prevents recursion. The original import boundary is asserted inside the clean child, checking forbidden prefixes including submodules. The installer retains Torch/agents/LuxAI exclusions. The parent requires child success and reports child diagnostics on failure. No loaded-module deletion, parent-module subtraction, skip, xfail or weakened statistical assertion was introduced.

## Actual verification

Interpreter: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B`, single BLAS/Torch thread environment where applicable.

1. All seven affected archived test files: **110 passed,107 subtests passed in11.92s**, exit0. Log: `archived_focused.log` in this report directory.
2. Exactly the original11 failed node IDs, with Torch deliberately imported in the parent pytest process before collection: **11 passed,10 subtests passed in5.66s**, exit0. This verifies the original contamination trigger without constructing/loading any model. Log: `archived_contaminated.log`.
3. A disposable synthetic stdlib import contract checked the helper itself: clean child accepted; an actual forbidden `fractions` import in the child rejected with the expected boundary assertion. No repository fixture file was added. Log: `archived_boundary_probe.log`.
4. `git diff --check`: exit0, no findings.

No actual games, model construction/checkpoint loading, training, installation, commits or historical study execution occurred. The child tests use existing synthetic dictionaries/files/CSV fixtures. Root independently reviewed the seven diffs and helper and reported PASS, then requested no further worker tests because root owns the final full-suite rerun. **No final full-suite-green claim is made here.**
