# Candidate-progress comparison implementation

Scope implemented: new `scripts/candidate_progress_eval.py`, `scripts/candidate_progress_owner.py`, `tests/test_candidate_progress_screen.py`; additionally the small Root-authorized error-propagation change in `scripts/par_eval.py`. No core/config edits by this agent, no released checkpoint load, real engine game, commit or push.

## Behavior

- Two fixed evaluation copies preserve every V14 Q/target/ensemble tensor and the original 36-member order. Config uses historical values plus current defaults, `frozen=False`, and only the OFF/ON `cand_stall_rescue` flag. Original cand_rescue=True/rescue_after=30/zone_rescue=False is required. Strict existing tensor and actual-loader checks are reused.
- Exactly four technical games, OFF/ON each on9946007/player_0 and831006/player_1. One environment per worker; existing common.play_game controls both policies. Passive NativeTrace uses original targeting_probe.action_bytes for both players and v2 scoring after decisions. OFF must reproduce archive native hash, all three match results, total points/wins and counters exactly. ON must exhibit positive actual early unit-step exposure and native divergence on at least one matching key. Core diagnostics agreed with motion_impl: cand_stall_early_unit_steps/early_steps; no private state is passed to a policy. All actual model tensors checked again after every game.
- Historical configs are normalized through AgentConfig.from_dict().to_dict() before comparison. This handles later default-False fields absent from old manifests without suppressing genuine semantic differences. No historical admission is executed against current HEAD.
- Independent technical/performance admissions. Performance needs explicit Root PASS bound to same source and technical receipt. Fixed cohorts solution9948000–9948019 and direct9948100–9948119; three original par_eval --workers1 jobs in2+1 waves, exactly120 games. Existing ownership/source/input/protected-file/quota/STOP/battery helpers and bounded process cleanup reused; no retries or automatic phase transition.
- Three complete CSVs require40 unique exact games each, both sides,303 steps,v2 points, integer metrics and consistent game/point results. Gate uses actual ON wins against Solution>=OFF and24actual direct wins; draws are not victories. Existing paired whole-card5000draw/PCG64seed0 descriptive score bootstrap is reused. Only nomination, no promotion.
- Root-requested par_eval fix checks `caught_errors` on both agent and opponent immediately after each play_game. Any positive count raises RuntimeError before a row can become a successful CSV. Baselines without a counter retain existing behavior.

## Actual verification

Final targeted invocation:

`env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_candidate_progress_screen.py`

**26 passed in2.77s, exit0**, `/tmp/candidate-progress-implementation/green-2.log`. Synthetic data/Q states only. Archive loads forbidden except a single in-memory stub exercising the real par_eval worker control flow; that case replaces the engine/policy/game with minimal fakes and runs no game/model. Tests cover preservation of36members, malformed model rejection, archive key/passivity, OFF/ON technical gates, command/config bindings, win/draw thresholds, invalid CSVs, native action serialization/v2 reset accounting, fixed cohorts, default normalization and caught-error propagation through the actual worker.

Earlier evidence: `red.log`20 expected missing-runner failures; `green-1.log`20PASS; `integration-red.log` and `integration-red-2.log` demonstrate default-normalization and missing error-propagation failures, the latter5FAIL/21PASS. Final green is not a real-model/game qualification. Four changed Python files separately parsed with ast; no trailing whitespace; tracked par_eval diff check passed. No broad historical test suites were repeated.

## Admission interface

Common: schema_version1, profile candidate_progress_20261109, stage technical|performance, start_authorized=True, allow_battery=True, root/out/python/plans/source/protected/inputs/stop_file. Outputs exactly `experiments/analysis/candidate_progress_20261109/technical_v1` or `performance_v1`.

Technical additionally: v14_source and baseline_manifests mapping `9946007_player_0` and `831006_player_1` to bound archived manifest files. Root can use holder_oscillation_20261109/probe_v1/manifest.json and continuation_20261102/targeting/manifest.json respectively. Owner source must be included in inputs.

Performance additionally: models={off:...,on:...}, cohorts={solution:...,direct:...}, seed_acceptance, technical_receipt, technical_acceptance. The acceptance document requires statusPASS/profile/source/technical_receipt_sha256. Seed acceptance requires exact cohorts, no_observed_conflicts=True, nonempty limitations and bound evidence files.

Owner CLI: `python -B -m scripts.candidate_progress_owner technical|performance --admission ABS --admission-sha SHA --usage-file ABS`.

## Final bytes

- scripts/candidate_progress_eval.py: de13aa221a2e951689bd65a61461bb343a987efe8cb5a01215aa2962bd42c7b3
- scripts/candidate_progress_owner.py: 0027cd4d7859fc542e4a276eb3b5e752ac90628378ada096e3be411dc5ba8d3d
- scripts/par_eval.py: 93f6f98d2cf042c379f7d560b85934e4931cf6751997e021ae9364726a4e1cdd
- tests/test_candidate_progress_screen.py: 0240bf66a767086fdd785908c3edeb6747ba8ac9b5eecc151945c44ff52235de

Open: independent review underway, then Root source admission/commit and actual four-game qualification. No success or effect on real games is claimed.
