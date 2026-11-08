# Fog analysis provenance path fix — 2026-11-08

Completed the narrow path fix only. No commits/pushes, real model games, production/model/data/gate changes or historical reanalysis.

Changes:

- `scripts/fog_reward_eval.py`: `analyze` first rejects missing provenance, canonicalizes the provided provenance path once with the existing strict `safe_path`, and reuses that canonical path for location validation, loading, frozen input binding and hashing. Relative CLI/API inputs now use the same absolute frozen-input key as absolute inputs.
- `tests/test_fog_reward_compare.py`: two parametrized synthetic regressions exercise the actual API and argparse CLI entrypoint, comparing complete reports from relative and absolute jobs/results/provenance paths. CLI tests use the temporary synthetic checkout via the existing analyzer root default; no subprocess/model workers or game environments are launched.

TDD reproduction before the fix:

```
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_fog_reward_compare.py -k analysis_relative_and_absolute_paths_match -q --disable-warnings --maxfail=1
```

Observed expected failure: `ValueError: Missing frozen input binding` in the relative API case;1failed,45deselected in3.24s.

Verification after the fix:

```
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest tests/test_fog_reward_compare.py -k analysis_relative_and_absolute_paths_match -q --disable-warnings
```

**2passed,45deselected in3.44s.** Both relative/absolute API reports and relative/absolute CLI reports are identical. No broader suite was run for this narrow change. Diff reviewed: only the two authorized files,6 changed script lines and23 added test lines. No test process remains active. Root owns project handoff documentation and publication.

Root independently ran the two focused regressions:2passed,45deselected,3.69seconds. Historical440-game data/report remain unchanged. The actual report was successfully generated with absolute arguments under the original frozen source before this fix.
