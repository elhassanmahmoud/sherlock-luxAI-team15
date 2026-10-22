# V10 correctness-fix evaluation review

Read-only audit at `c78732f1cc0a7746268e644223692d146aa8f25e`, 22 October 2026. No model/engine imports, games, tests, repository edits, or Git mutations were performed. Requirements are the supplied protocol brief plus the controller's final narrowed selection rule.

## Recommended fixed design

All four selection arms use exactly the installed V10 checkpoint bytes (`03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`), differing only in the two Boolean overrides:

| Label | sap_overkill_recovery | nebula_infer_drift_safe |
|---|---:|---:|
| v10 | false | false |
| energy | true | false |
| drift | false | true |
| combined | true | true |

1. **Compatibility:** reserve 610000–610019; initially use only 610000–610001, both sides against Solution_92 (the controller’s final predeclaration narrows this technical check to one opponent). Compare original frozen code with patched code/flags false. Compare deterministic CSV fields excluding `secs`, and full action traces, rather than just outcomes. Eight games for these two code versions. Additional compatibility maps are technical diagnostics, never confirmation evidence.
2. **Selection:** 610100–610299, all four arms, both sides against Solution_92: 1,600 games. Choose exactly one arm with maximum Solution score improvement, requiring at least +1 percentage point over v10. Exact ties: combined, then energy, then drift. If no eligible arm, stop. Then run only v10 and that nominee on the same 200 maps/both sides against default: 800 games. Require default score ≥99%, as fixed by the controller. The Δ≥−1 pp condition remains mandatory in confirmation; it is not an additional selection gate. **No fallback to another arm after a failed default guard.** These are selection results, not a confirmed benefit.
3. **Confirmation, only after selection passes:** 611000–611799, nominee and v10, both sides against Solution_92 and default: 6,400 games. Frozen nominee, implementation, environment and inputs throughout.
4. **Direct gate:** 612000–612399, nominee against the byte-frozen V10 checkpoint, both sides: 800 games. Can be deferred until the opponent confirmation gates pass to save work; no expansion after a marginal result.
5. **Stronger-opponent information guard:** 613000–613099, nominee and v10, both sides against `sol92_sq`: 400 games, if promotion is otherwise justified. Report paired Δ/95% interval separately. Per controller instruction, no promotion if its Δ interval's upper endpoint is <0. No candidate switching or retuning from this block.

Confirmation gates remain: Solution_92 Δ≥2 pp and lower 95% bound >0; default score ≥99% and Δ≥−1 pp; direct lower 95% bound >50%. Bootstrap entire map pairs, 5,000 draws, NumPy `default_rng(0)`, percentiles 2.5/97.5. Do not round before gates. At 1,600 confirmation games/opponent, use half-result units: denominator 3,200; Solution difference ≥64, default total ≥3,168 and difference ≥−32. At 400 selection games/opponent, +1 pp is ≥8 half-result units and 99% is ≥792 of 800. Mean `result` counts a draw as 0.5: label it score rate or explicitly say ties count half; also report actual W/D/L.

Maximum competitive program: 2,400 selection + 6,400 confirmation + 800 direct + 400 stronger guard = **10,000 games**, plus the small technical compatibility/course checks. Complete each admitted fixed block; do not report a partial block as a failed or passed statistical gate. No 100% general-strength claim is supported.

## Seed freshness evidence

`seed-audit.json` records the checks. Across **730 committed CSVs with seed columns, 533,492 rows, and 82,770 distinct seeds**, there were no hits anywhere in 600000–619999. The original checkout's 730 local experiment seed CSVs also had no hits in 610000–613099. Thirty-seven tracked documentation Markdown files were checked for 600000–619999 mentions: none. Existing latest series occupy approximately 503220–509619; other known reservations include 510000–511399, 520000–520999 and 522000–523399. The proposed blocks avoid those.

Both original installed weight files were read and hash-checked against the required SHA. This is evidence about the current accessible state, not an assurance about unpublished work elsewhere. Controller should recheck newly changed remote/local evidence and commit the exclusive reservation/predeclaration before any match.

## Suitable commands and schema

`par_eval` is the supported batch evaluator. **`--first` is an offset from 500000**, not an absolute seed. It accepts repeated `--set`, which is safer for this four-arm experiment than producing four differently serialized checkpoints. Use one invocation at a time with `--workers 2`, globally no other model/game/pytest job. Explicitly constrain numerical-library threads to one. Run from the frozen mechanics checkout and use absolute paths for the interpreter, frozen reference, and outputs.

Example command structure, for the controller to execute only after predeclaration and checks (not executed by this audit):

```bash
PY=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python
D=/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics/experiments/analysis/v10_correctness_20261022
REF="$D/inputs/v10_frozen.pth"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1

"$PY" -m scripts.par_eval --weights "$REF" --first 110100 --n 200 --workers 2 --opponents solution92 --set sap_overkill_recovery=false --set nebula_infer_drift_safe=false --out "$D/selection_v10_sol.csv"
"$PY" -m scripts.par_eval --weights "$REF" --first 110100 --n 200 --workers 2 --opponents solution92 --set sap_overkill_recovery=true --set nebula_infer_drift_safe=false --out "$D/selection_energy_sol.csv"
"$PY" -m scripts.par_eval --weights "$REF" --first 110100 --n 200 --workers 2 --opponents solution92 --set sap_overkill_recovery=false --set nebula_infer_drift_safe=true --out "$D/selection_drift_sol.csv"
"$PY" -m scripts.par_eval --weights "$REF" --first 110100 --n 200 --workers 2 --opponents solution92 --set sap_overkill_recovery=true --set nebula_infer_drift_safe=true --out "$D/selection_combined_sol.csv"
"$PY" -m scripts.compare_report --ref "$D/selection_v10_sol.csv" "$D/selection_energy_sol.csv" "$D/selection_drift_sol.csv" "$D/selection_combined_sol.csv"
```

Bind one nominee and its two explicit flags in a selection JSON before default games. Remaining commands use the same options, reference checkpoint and immutable Boolean values, with these exact jobs:

| Output | first | n | opponents | arm |
|---|---:|---:|---|---|
| selection_v10_default.csv | 110100 | 200 | default | v10 |
| selection_nominee_default.csv | 110100 | 200 | default | nominee |
| confirm_v10.csv | 111000 | 800 | default,solution92 | v10 |
| confirm_nominee.csv | 111000 | 800 | default,solution92 | nominee |
| direct_nominee.csv | 112000 | 400 | self:/absolute/path/to/v10_frozen.pth | nominee |
| stronger_v10.csv | 113000 | 100 | sol92_sq | v10 |
| stronger_nominee.csv | 113000 | 100 | sol92_sq | nominee |

After **strict validation** of all full expected keys, existing display/confirmation commands are:

```bash
"$PY" -m scripts.compare_report --ref "$D/confirm_v10.csv" "$D/confirm_nominee.csv"
MIN_DELTA=0.02 "$PY" scripts/v5_gates.py confirm "$D/confirm_v10.csv" "$D/confirm_nominee.csv" "$D/direct_nominee.csv"
"$PY" -m scripts.compare_report --ref "$D/stronger_v10.csv" "$D/stronger_nominee.csv"
```

The existing selection CLI assumes both opponents in one CSV; do not apply it to the Solution-only stage. Either analyze that stage directly with the exact integer rule, or concatenate fully validated separate opponent files after the default guard into new combined files, retaining originals. Never silently reuse an old `V10_ref_*` CSV.

**CSV schema:** keep existing `GAME_FIELDS` unchanged: `seed,side,opponent,result,game_win,point_win,our_wins,opp_wins,our_points,opp_points,point_counting_version,wait_frac,invalid_frac,greedy_masked_frac,sap_attempts,sap_hits,stack_frac,relics_found,relics_seen,known_point_tiles,belief_contradictions,unit_steps,steps,secs`. Require exactly one row per planned `(opponent, seed, side)`, no extras/missing rows/duplicates; 303 steps, point-counting version 2, finite values, valid consistent result/match wins, and both sides for every map. `scripts.early_curriculum_analysis.validate_keys(rows, seeds, opponents)` is a usable pure-data validator for arbitrary specified blocks; its study-specific `direct_gate` must not be reused unchanged because its seeds are fixed to 511200–511399.

**Manifest/decision schema:** store `run_id`, `predeclaration_commit`, `source_commit`, absolute source hashes (agent/config/belief/rules/features + evaluator/opponents/scoring/protocol), Python/engine/environment identity and actual 3-match configuration, `reference_path`, `reference_sha256`, each arm's complete effective config and overrides, exact seed lists/opponents/sides, worker/thread limits, exact command arrays and cwd, expected CSV schema/keys, planned thresholds/tie order, phase state, command exit codes, elapsed time, CSV/log hashes, and protected-input hashes before/after each job. `selection.json` must bind the selected arm, source/config/checkpoint hashes, full selection evidence hashes and the reason; confirmation must consume that same frozen identity. Code commit alone does not describe dirty or ignored executable files.

## Critical implementation/evaluation pitfalls

- **Old checkpoints load new defaults.** `AgentConfig.from_dict` and `Agent_x._cfg_from_checkpoint` must preserve both new defaults false. The reference in `self:<path>` loads the same current `Agent_x` code, so byte-frozen checkpoint alone is insufficient to prove legacy behavior. Leave the old branches literally intact when false and verify original-versus-patched traces. Guard each correction by its own flag; preserve all pre-existing rule/training guards and action/state ordering in the false path.
- **Pairing can silently lose evidence.** `compare_report` deliberately uses intersections; assert exact planned keys first and require zero excluded maps. `v5_gates.direct_interval` merely groups rows by seed and has no completeness/result/opponent validation: validate the direct CSV against its one exact frozen opponent label before calling it.
- **Wrong defaults are substantial.** `par_eval` defaults to 14 workers; old `pipeline_v10.sh` defaults to 12 and the V3 reference, uses consumed 507xxx/508xxx blocks and hardcoded shared output/log names. It is unsuitable here without a separate bounded controller. Its shell pipelines do not reliably propagate evaluator failure. `v5_gates` defaults are +3 pp selection/+5 pp confirmation unless explicitly overridden.
- **Output protection is partial.** `par_eval` refuses an existing output before launch, but reserves no atomic run/output ownership and writes the full CSV only at completion. A crash leaves no complete CSV, and concurrent launches can race. Create a new exclusively owned run directory, retain logs/exit status, audit any resume from immutable evidence, and never count absent rows as losses. `set_cfg` and `record_replay` can overwrite their outputs; guard their destinations externally.
- **Batching:** current `par_eval` uses one persistent candidate/environment per worker and strided seed chunks; use that rather than spawning Python per seed. It already resets Solution class globals per game and `new_game` per side. Direct evaluation rebuilds the reference agent every game, which is slower; do not change this just for speed without a separately verified compatibility check. A single two-worker batch is the resource cap, not two two-worker launches.
- **Replay/config mismatch:** `record_replay` has no `--set`, so replaying a true-flag arm from the original checkpoint silently gives baseline behavior. Use a temporary config-persisted candidate with identical tensor hashes and verified effective flags, or the controller's trace capture with explicit overrides. Its output is under presentation/replays and has overwrite risk. I found no `eval_seed` script in the inspected repository or `/tmp`; do not assume an unreviewed helper shares batch/reset/config semantics.
- **Promotion packaging:** serialize only the winning config after gates, verify all 18 model tensors exactly equal V10 and its behavior equals the tested overrides, then run the existing unchanged course-runner check with protected-input hashes. The serialized candidate byte SHA changes even though tensors do not. Keep the original checkpoint and tests/results; do not describe these config changes as additional training.

No statistical outcome has been observed in this audit. The strongest recommendation is the narrowed one-nominee design above, with exact-key validation and a demonstrably identical disabled path before new strength claims.


## Final pass on the controller predeclaration

Read `docs/superpowers/plans/2026-10-22-v10-mechanics.md` after it was created. Its blocks, offset example, selection threshold/order/ties, no-fallback rule, confirmation sizes/gates, stronger-opponent veto, and global two-worker cap agree with this review. The final plan deliberately uses Solution only for the two-seed technical compatibility check (8 games across the two code versions), and default ≥99% as the selection guard.

Before commit/start, recommended corrections sent to controller:

1. Freeze the same behavior-affecting implementation and effective nominee configuration across selection, confirmation, direct and stronger guard, not only within each individual phase. A behavioral edit between phases invalidates that nomination and stops this program; do not quietly carry its selection forward.
2. Compare complete disabled-path action traces as well as deterministic final metrics on the compatibility seeds. Matching final metrics alone does not establish identical behavior.
3. State percentile endpoints 2.5/97.5 and exact, unrounded gate arithmetic explicitly.

No further audit expansion is needed before the controller finalizes the predeclaration. Freshness JSON is a point-in-time read-only result; controller owns its final reservation and source freeze.
