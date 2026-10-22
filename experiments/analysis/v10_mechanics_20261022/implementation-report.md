# V10 mechanics implementation report — 22 October 2026

Status: two bounded corrections implemented and committed; focused tests pass. Both flags default to false. Full-suite verification, compatibility replay checks, experiments and any integration/promotion remain with the controller. No full games, training, model jobs, pushes, merges or weight changes were performed by this implementer.

## Scope and commits

Worktree: `/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics`
Branch: `fix/v10-mechanics-20261022`
Base: `c78732f1cc0a7746268e644223692d146aa8f25e`

1. `75e71c0a5b90939ed37764ac1ed187b1bc8128db` — `fix: optionally account for field recovery in sap coordination`
   - `agents/sherlock/config.py`, `agents/sherlock/main.py`, `tests/test_v10_mechanics.py`.
2. `9e5206be4daafeb0553e854a1f0ef38130c3a939` — `fix: optionally skip stale sensor inference on detected terrain drift`
   - `agents/sherlock/config.py`, `agents/sherlock/main.py`, `agents/sherlock/belief.py`, `tests/test_v10_mechanics.py`.

No model tensors, feature dimensions, dependency, engine, runner, simulator or artillery changes. Controller-owned untracked plan, analysis and baseline-backup artifacts were left untouched. Repository workstand/protocol updates are controller-owned under the explicit file ownership in the implementation brief.

## Recovery accounting decision

`sap_overkill_recovery=True` modifies the existing `_overkill` condition to keep a shot unless every covered enemy's remaining energy is strictly negative even after adding the maximum possible positive field gain. Existing direct/splash coverage and integer planned-damage accumulation remain unchanged. Zero energy survives. A nonpositive field bound adds zero, since negative energy cannot recover from nonpositive gain and the engine clips a nonnegative unit's field result at zero.

The bound is `max(0, env_cfg.get("max_energy_per_tile", MAX_TILE_ENERGY))`; the existing `features.MAX_TILE_ENERGY` is 20, matching installed `luxai_s3.params.EnvParams.max_energy_per_tile`. `compute_energy_features` clips fields to that fixed upper bound; the parameter is not randomized. Normal wrapper observations do not expose it, hence the documented default. An explicitly supplied public override is honored. No engine imports or full-state access were added to production.

Ruling: use the public maximum, not the observed tile's positive field value — engine `step_env` recomputes field energy before actions, while energy nodes may already have drifted after the prior field/observation computation — cost: more shots may be retained than necessary on weak or negative fields. The controller agreed with this conservative choice. Nebula reduction, void and opponent action costs cannot increase recovery, so ignoring them preserves the upper bound.

Cancellation remains conditional on the existing predicted hits and target positions. This correction does not guarantee that enemies remain still or that every planned hit lands. Existing splash bookkeeping uses `floor(cost * min(dropoff, .25))` per shot; for nonnegative damage, the sum of these floors does not overestimate the engine's aggregate floor. The focused cost-31 fixture checks that conservative 7-per-shot behavior and the exact-zero recovery boundary.

## Drift ordering decision

`nebula_infer_drift_safe=True` is passed from `AgentConfig` into `Belief` and preserved across game/player resets. `observe` records the prior drift count, calls the unchanged detector, updates current visible terrain as before, then suppresses hidden-in-range nebula inference only if this observation actually caused a detected drift. Inference resumes on subsequent observations without detected drift. This avoids overwriting an asteroid correctly rolled into a hidden cell with an inference about pre-drift terrain.

Ruling: conservatively skip invalid inference on a detected drift observation instead of relocating/rolling newly inferred cells — avoids altering detector evidence, visible map ordering or expanding the inferred area — cost: useful old-terrain information on that observation is not propagated.

Limit: undetected drift can still produce an invalid inference, including when `drift_track=False`. The existing detector is heuristic and unchanged. This flag does not claim to solve missed drifts. It also does not introduce any global hidden-state inference.

## Compatibility

- Both flags are separate, default-off fields accepted by `AgentConfig.from_dict`; old checkpoint dictionaries omit them and retain legacy behavior.
- Regression cases explicitly exercise omitted flags and false flags. Recovery still cancels the second shot for the original 35-energy/+10 case when disabled; drift inference still overwrites the rolled asteroid when disabled.
- The legacy sap branch performs its original comparisons without an added recovery term. The legacy belief path performs its original inference; the extra counter comparison has no map effect when the new flag is false.
- Direct constructors and existing consumers keep their existing defaults; the new Belief constructor parameter is appended. No saved tensor or feature layout changes.
- Tests exercise the consumer-visible behavior through AgentConfig parsing, Agent construction, game/player reset, actual `act` or `Belief.observe`. Full V10 trace equivalence is for the controller's independent compatibility check, not claimed here.

## Red/green evidence

All pytest calls were sequential from the worktree with:

`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest`

1. Before recovery production edits: `-q tests/test_v10_mechanics.py -k 'not engine'` → exit 1; **7 failed, 6 passed, 2 deselected in 4.23s**. Primary failure: second action was STAY (0), expected SAP (5). Log: `overkill-red.log`.
2. Before recovery production edits, controlled engine characterization: `-q tests/test_v10_mechanics.py -k engine` → exit 1; **1 failed, 1 passed, 13 deselected in 6.03s**. Actual engine target energy +5 instead of required -45 for the enabled flag. Initial synthetic input dtypes caused two JAX casting warnings; fixture was corrected to use the actual state's integer dtypes, with no production changes. Log: `overkill-engine-red.log`.
3. Final recovery RED with added adjacent-survivor/nonpositive-bound cases and corrected dtypes: `-q tests/test_v10_mechanics.py` → exit 1; **9 failed, 11 passed in 6.91s**, no warnings. Failures are the expected cancellation assertions and engine +5 versus -45 result. Log: `overkill-final-red.log`.
4. Recovery GREEN after minimal correction: `-q tests/test_v10_mechanics.py tests/test_rules_2110.py -k 'recovery or nonpositive or overkill'` → exit 0; **21 passed, 51 deselected in 6.87s**, no warnings. Log: `overkill-green.log`.
5. Before drift production edits: `-q tests/test_v10_mechanics.py -k drift` → exit 1; **5 failed, 5 passed, 20 deselected in 3.34s**. Drift detection already succeeds; corrected-path tests observe NEBULA (1), expected ASTEROID (2). Both canonical drift directions/player orientations fail for the intended reason. Log: `drift-red.log`.
6. Drift GREEN: `-q tests/test_v10_mechanics.py tests/test_rules_2110.py -k 'drift or nebula_infer'` → exit 0; **12 passed, 70 deselected in 3.49s**, no warnings. Log: `drift-green.log`.
7. Final combined focused check after improving the normal/no-new-drift observation fixtures: `-q tests/test_v10_mechanics.py tests/test_rules_2110.py -k 'recovery or nonpositive or overkill or drift or nebula_infer'` → exit 0; **33 passed, 49 deselected in 7.34s**, no warnings. This includes all **30 new cases** and **3 existing affected regression cases**. Log: `focused-final-green.log`.
8. `git diff --check` passed before each commit (exit 0; empty output). No owned files remained uncommitted after the second commit.

All logs above are under `/tmp/sherlock-v10-fixes-20261022/`. The real-engine regression executes one deterministic synthetic step per flag case, with the same rules and fixed +10 field; it is not a match, benchmark or training run. Expected outcomes are literal hand-derived +5 (one sap) and -45 (two saps; engine preserves negative energy when field cannot recover it).

## Coverage and remaining work

Recovery: original visible-positive counterexample; omitted/false/true configuration; strict negative/zero threshold; more damage than maximum recovery; observed zero/negative field uncertainty; missing map context; public maximum override including nonpositive bounds; adjacent-only survivor; conservative integer splash planning; real-engine resulting energy.

Drift: old sensor/new terrain counterexample; omitted/false/true configuration; drift count/votes unchanged; both directions and both player orientations after reset; current visible terrain preserved; normal hidden-in-range inference retained; disabled nebula inference retained; distant unknown terrain retained; inference resumes after the detected drift.

No full-suite or strength claim is made. The controller owns the full suite and independent V10 measurements. The conservative recovery bound may spend more energy; the drift guard sacrifices one observation's hidden inference and does not repair missed detections. Both flags remain off until separate evidence supports enabling them.
