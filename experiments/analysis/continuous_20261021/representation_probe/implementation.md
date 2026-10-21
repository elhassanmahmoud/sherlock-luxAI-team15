# Optional enemy energy tie selection — implementation handoff, 21 October 2026

Implemented and committed in isolated `/Users/moayedshawesh/Desktop/KI/sherlock-enemy-tie`, branch `improvement/enemy-tie-20261021`.

- Base: `d93d4d5e9f59e8a8aea0c0879eb28bd4991d70a8`.
- Commit: `1b3f6a79d576725329784b4d51cbfbc96e603beb` (`feat: add optional energy tie selection for nearest enemy features`).
- Only owned files changed: `agents/sherlock/config.py`, `agents/sherlock/features.py`, `tests/test_enemy_tie_features.py`.
- Working tree clean after commit. No merge or push.

## Behavior

`AgentConfig.enemy_tie_energy` defaults to False. Old `from_dict` payloads therefore keep False; both explicit values serialize and roundtrip normally. `make_context` carries the option into the context, defaulting False if a config object lacks the attribute. A missing context option likewise preserves the existing `np.argmin` choice.

When enabled, the nearest Manhattan distance is still the primary criterion. Among only the enemies at that minimum distance, choose the highest observed energy; equal-energy ties retain the first original index. Negative-energy visible enemies are retained. No enemy ordering, targeting, action logic, distance calculation, count calculation, network shape or weights were changed. The vector still has 79 values. Only indices 69, 70 and 72 (enemy dx, dy and relative energy) can differ for this tie-only change.

This is an experimental inference candidate. These checks establish implementation behavior and compatibility for the covered fixtures, not playing strength or a causal interpretation of the archived observations.

## Actual verification and TDD

Read repository AGENTS/CLAUDE, newest work handoff, experiment notes, the bounded probe, and the TDD/testing/verification skill instructions.

Tests were written before production changes. Initial test authoring exposed an oracle rounding mismatch (Python float64 tanh versus existing float32 arithmetic); corrected the expected-value arithmetic before implementing. Corrected RED run against unchanged production files: **9 intended failures, 25 passes in 0.06 seconds**, saved at `/tmp/sherlock-enemy-tie-red-20261021.txt`. Failures were missing config option, missing context wiring, and still-first-index selection where higher energy should win. Legacy full-vector tests passed before the change.

After the minimal eight-line production addition: **34 passed in 0.03 seconds**. Final focused rerun also **34 passed in 0.03 seconds**, with the same Python process checking `sys.modules` after `pytest.main`: **no Torch, JAX or luxai_s3 modules loaded**. Plugin autoload was disabled. Both ordinary and staged `git diff --check` passed.

Coverage:

- Old serialized config missing the option, default False, true roundtrip.
- Missing/false context flag reproduces hand-derived full legacy vectors exactly on both canonical sides, including negative energy and equal energy.
- Enabled selection: higher-energy nearest tie, stable equal-energy tie, all-negative tie, nearer negative-energy opponent over farther strong opponent, noncontiguous nearest candidates, singleton and empty arrays.
- Actual `AgentConfig` → actual `make_context` → actual `build_features`, using real lightweight `Belief` plus synthetic observation and an agent namespace; no Agent_x or model.
- Only allowed feature subset changes; fixed vector length; all other context arrays/scalars/assignments unchanged.

The top-level `agents/__init__.py` eagerly imports all agents. Tests bypass that initializer by loading the actual empty sherlock package under a private importlib package name. Config, geometry, belief and features are loaded as real source modules, with normal relative imports; no AST extraction or production function replacement. The test module's import-delta assertion is compatible with future full-suite runs that already loaded other backends; the separate final process-wide import audit confirms none loaded in this actual focused run.

Reproduction from the isolated worktree:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_enemy_tie_features.py
```

The final process-wide audit used the same command prefix and this Python body:

```python
import os
import sys
import pytest
assert os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] == '1'
status = pytest.main(['-q', 'tests/test_enemy_tie_features.py'])
loaded = sorted(name for name in sys.modules if name.split('.')[0] in {'torch', 'jax', 'luxai_s3'})
assert not loaded, loaded
print('Backend import audit: no Torch, JAX or luxai_s3 modules loaded; plugin autoload disabled.')
raise SystemExit(status)
```

## Explicitly pending / not performed

No models loaded, no games or training launched, no weights read or written. No dependency installation or venv changes. No edits to the frozen curriculum checkout, shared documentation, main branch or plans. The current authorization explicitly limits verification during active training to focused lightweight tests, so no full-suite or game test was run despite the skills' general full-suite recommendation. Full integration checks, actual model/game tests, and all scientific evaluation remain pending for Root's controlled follow-up. No performance claim. Root owns the separate preregistration and documentation integration; root reported plan commit `eaf6b50` after implementation began.
