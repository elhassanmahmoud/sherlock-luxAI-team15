# Task 1: explicit authorized quota ceiling

Status: implemented and self-reviewed. Commit: `9c103a1` (`Allow explicit quota ceiling for ensemble comparison supervisor`). Only the two owned controller/test files were committed; other team changes and untracked artifacts were preserved.

The controller accepts keyword `max_used_percent=65` through `check_usage`, `build_state`, and `run_supervisor`. CLI `--max-used-percent` parses a float and defaults to 65. Explicit 100 admits known usage below 100, including 65 and 99, and rejects exhaustion at 100. Cap validation rejects bool, zero, negative, nonfinite, nonnumeric and above-100 values. The selected cap is stored in state and the input-hashed launch reservation. Live guards read this state field; legacy absent fields default to 65. Receipt freshness, ordinary-use permission, known usage, source/model/protected-file/CSV checks, power and process ownership remain unchanged.

TDD evidence: wrote tests first, then ran the specified interpreter against `tests/test_ensemble_diversity_eval_supervisor.py`. Before implementation: 25 failures (including subtest failures), 19 tests passed and 16 subtests passed; failures showed the absent API/CLI/state field and old hardcoded threshold. After implementation: **23 tests and 43 subtests passed in 1.22 seconds**, exit 0. Command:

```
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_ensemble_diversity_eval_supervisor.py -q
```

`git diff --check` passed. Self-review checked forwarding CLI → supervisor → state, persistent launch record and guard default, fail-closed invalid caps, 65/99/100 boundaries, and unchanged checks outside quota policy. Controller tests use temporary files and synthetic analysis fixtures; no games or model children were launched. Full suite intentionally not run under the task's explicit no-games restriction. No statistics, model weights, job plans, agent code or trained artifacts were changed. Root owns shared docs, independent review and actual launch.
