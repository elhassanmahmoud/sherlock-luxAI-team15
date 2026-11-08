# Task 1 report — final Fog origin and optional reward

Status: implemented; focused synthetic verification PASS. Root integration review and original V14 reference proof remain separate.

## Changed files

- `agents/sherlock/config.py`: `fog_unknown_reward_neutral: bool = False`, including automatic old-checkpoint default via existing `from_dict`.
- `agents/sherlock/main.py`: initialize/reset `_sap_unknown`; clear it at entry to every `_act`, including empty/match-reset frames; remember each unit's actual Fog tuple object and record the canonical UID only at final SAP emission when `sap is fog_origin`. Every existing target/action rule and numeric SAP tuple remains intact. `_update` supplies `unknown_sap` only when the flag is true; false/missing flag keeps the original five-positional-argument reward call.
- `agents/sherlock/reward.py`: keyword-only optional `unknown_sap=None`; when opted in, omit only the SAP hit term for a marked final SAP. All other branches/terms remain intact.
- `tests/test_fog_unknown_reward.py`: 30 synthetic cases. Uses synthetic observations and the real agent action/replay/reward pipeline; narrow rule doubles exercise later replacement/cancellation paths. No engine games.

## Verification actually performed

Interpreter: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python` (this worktree has no local `.venv`).

1. RED before production edits: `-m pytest -q tests/test_fog_unknown_reward.py` — **29 failed, 1 passed**, 3.18 seconds. Failures were missing config field, missing provenance set/keyword, and the new reward contract. Historical five-argument auditor compatibility was already green.
2. GREEN after minimal production edits: same command — **30 passed**, 1.97 seconds.
3. Final permitted synthetic regression set: `-m pytest -q tests/test_fog_unknown_reward.py tests/test_fog_sap.py tests/test_terminal_death_potential.py tests/test_reward.py -k 'not match_boundary_transitions_in_real_game'` — **57 passed, 1 deselected**, 2.93 seconds. The excluded test runs a real full engine game and was intentionally not executed under this subtask's no-games contract.
4. `git diff --check` — clean.

Coverage includes known positive, zero and negative estimates; false/default/missing flag and missing provenance; zero hit weight and disabled shaping; death and match terminal potential terms; real Fog emission; mirrored emission; same-coordinate positive replacement and fully equal-value new-tuple replacement; smart-SAP cancellation; overkill and moving-target cancellation; later holder movement; provenance isolation across units/frames/empty frames/match reset/game reset; five-argument legacy reward auditor; paired synthetic training replay equal in native actions, canonical actions, masks, features, next features, done flags, numeric estimates and old statistics, with exactly +0.3 selected reward delta.

## Scope and remaining checks

- No commits, pushes, subagents, real games, gradients, trainer edits, model/weight/ZIP edits or historical-data changes.
- No full test suite or integration suite run: root explicitly serializes those and any real reference proof. The full suite contains real-game tests outside this subtask authorization.
- No strength claim follows from the reward arithmetic. Trainer provenance/audit integration and four-arm mechanical acceptance remain partner/root work.
- No known blocking issue in this diff. Existing `_prev_actions` and inference behavior deliberately unchanged.
- Root should update `docs/ARBEITSSTAND.md` after integrated work; it is outside this subtask's allowed write set.
