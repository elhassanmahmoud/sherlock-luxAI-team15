# Task 1 implementation report

Implemented `scripts/student_retention.py` and `tests/test_student_retention.py` only. No commits, existing data runs, model training, protected file writes, or runtime-agent changes.

CLI: `python -m scripts.student_retention --datasets DIR [DIR ...] --model NAME=PATH [--model NAME=PATH ...] --out NEW_DIR [--batch-size 1024]`. Evaluates checkpoint `q` only as scoped; no target/replay/TD audit.

Reuses validated `student_action_distill.load_datasets`, `action_metrics`, QNet, and the existing submission/input/occupied-output guards. Inference sees only `~is_train`, is batched/no-grad/eval/CPU, and preserves the torch RNG across model construction. Architecture is inferred from state and checked against supplied config; ensembles, malformed states, invalid masks and nonfinite states/outputs fail. Metrics include masked agreement, legal teacher regret, legal/centered/mean-Q errors, pooled legal Q mean/population std, mean per-row legal spread, and top-two gap mean/std/tie rate on rows with at least two legal actions. Singleton masks produce null gap summaries. Recorded collector overrides remain explicitly labeled.

`report.json` is published only on success, with per-role checkpoint hashes, per-dataset excluded counts, diagnostic seeds, before/after complete package/model/source hashes, HEAD, runtime versions, metric definitions, and development-data/causality limits. Existing outputs and protected destinations are rejected before creation. Complete reports are rejected if inputs or direct source files change during evaluation.

Test-first: initial 21 tests failed because the module did not exist, then passed after implementation. Three additional CLI/provenance/gap cases passed. Final scoped verification: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_student_retention.py` → **24 passed in 1.81s**. `git diff --check` returned exit 0; CLI `--help` checked separately. Fixtures are tiny 8-row packages and real 8-hidden QNets. No actual collection corpus read by inference.

Ready for independent review, root verification, and the root-coordinated full five-model corpus diagnostic. Remaining: independent review and actual-corpus report, then root documentation/commit. Root owns ARBEITSSTAND updates.

## P2 review correction

Verified the reviewer finding: the individual-file guard accepted `COLLECTOR/retention-report`. Added an explicit resolved-output/collector-directory containment check before `reserve_output` can create anything. The check also rejects symlinked ancestor aliases. Only `scripts/student_retention.py` and its scoped tests changed.

Test-first proof: the new direct-path and symlink-alias cases both failed with “DID NOT RAISE” before the fix. Each case snapshots every archive entry/hash, then requires rejection, no output creation and identical contents. Final requested verification: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_student_retention.py` → **26 passed in 1.75s**. No other suites, corpus inference, training or commits run. Ready for reviewer/root recheck.
