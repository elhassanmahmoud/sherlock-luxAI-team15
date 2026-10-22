# Independent V10 mechanics review — 22 October 2026

**Verdict: clean for the requested scope, both specification compliance and code quality. No important actionable defect found.** This approves the implementation for the planned compatibility and performance checks; it does not establish that either enabled correction improves win rate or authorize promotion from test results not yet observed.

Reviewed `c78732f1cc0a7746268e644223692d146aa8f25e..9e5206be4daafeb0553e854a1f0ef38130c3a939`, the implementation brief/report, red/green logs, installed `luxai_s3` engine source, the controller's two untracked helpers and current `selection_jobs.json`, and `docs/superpowers/plans/2026-10-22-v10-mechanics.md`. I performed no test/model imports, games, training, source edits, pushes or agent delegation. Only read-only checks and this requested report were written/performed.

## Specification and engine semantics

- **Recovery correction:** `_overkill` adds a nonnegative maximum field gain only when `sap_overkill_recovery` is true. The public default 20 agrees with `EnvParams.max_energy_per_tile`, and the engine clips computed fields to this upper bound. An explicit supplied public bound is respected. Using the maximum instead of the observed tile field is justified: energy nodes can drift after the previous field computation, and the next `step_env` recomputes the field before actions. No hidden state or engine dependency is introduced in production.
- The strict negative cancellation threshold is correct. Engine `env.py:525–550` applies field recovery after sap/void, clips a recovered/nonnegative result to at least zero, but preserves a still-negative pre-field energy instead of removing it immediately. Removal occurs at the next step's start. Thus the recorded +5 legacy outcome and -45 corrected outcome are correct; -35 would be the wrong expected engine value for the second case. Zero survives. Nonpositive maximum recovery correctly adds zero.
- Existing conservative splash bookkeeping remains unchanged. The sum of per-shot nonnegative integer floors at at most the minimum allowed dropoff does not overestimate the engine's integer conversion after aggregate splash damage. This preserves the intended conservative bound under the existing predicted-hit assumption.
- **Drift correction:** `observe` samples the drift counter before calling the unchanged detector, preserves visible-map updates, and skips hidden-nebula inference only if that observation detects drift. Engine `env.py:644–692` computes visibility before rolling terrain, then exposes the rolled terrain through that old mask. The corrected branch therefore avoids overwriting the correctly rolled hidden asteroid from stale visibility evidence. Subsequent no-drift inference and canonical player/direction handling remain intact.
- The explicitly allowed narrow limitation is documented accurately: a missed drift, or disabled `drift_track`, is not repaired. The existing hit/target-position assumptions in sap planning are also retained and disclosed. These are scope limits, not newly introduced defects.

## Compatibility and quality

- Both independent flags default to false in `AgentConfig`. `from_dict` preserves those defaults for old checkpoint dictionaries. The new `Belief` parameter is appended and wired from the agent constructor; `reset_game` does not discard it, including game/player resets.
- With both flags false, the sap arithmetic and inference behavior are unchanged. The extra drift counter read has no map side effect. No tensor layout, feature dimension, runner, simulator, engine, dependency, artillery rule or unrelated strategy changed.
- The production changes are small and localized; comments explain the temporal and recovery constraints. Test assertions cover consumer-visible actions/map outcomes, not just the new arithmetic. The synthetic real-engine step independently checks the surprising negative-energy behavior.
- `git diff --check c78732f..9e5206b` returned exit 0 with empty output. The committed diff contains only the three authorized production files and the focused test file, in the requested two logical commits (`75e71c0`, `9e5206b`).
- Independently read and SHA-256 checked both installed weight files and both frozen baseline copies. All four equal `03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`.

## Test evidence read, not rerun

- Recovery RED: expected action/cancellation failures, including the actual engine target remaining at +5 when the enabled case requires -45. Final recovery red log records 9 failed / 11 passed.
- Drift RED: 5 expected failures / 5 passed; the detector already recognizes drift, while the hidden asteroid is wrongly relabeled nebula.
- Focused final GREEN: **33 passed, 49 deselected in 7.34s**, including all 30 new cases and three affected existing cases. Covers omitted/false/true flags, strict zero boundary, missing/stale fields, public maximum overrides, adjacent surviving targets, integer splash planning, engine outcomes, both drift directions/player orientations, reset handling, visible terrain, normal inference and resumed inference.
- Controller full-suite log completed during this review: **527 passed, 14 subtests passed in 97.54s**. This matches the stated baseline 497 plus 30 new cases. I did not launch another suite.

## Experiment helpers and predeclaration

No concrete execution/integrity error found in the current declared commands.

- `capture_compatibility.py` prepends the requested checkout before importing project code, loads the frozen V10 checkpoint with both flags checked false, disables training/autosave, uses the existing reset-safe opponent/game path, and hashes every returned action for both players on the two declared seeds/both sides. Captures are made before any subsequent action-array mutation, and action counts must match played steps. It excludes only elapsed time from game metrics and refuses an existing receipt.
- `run_jobs.py` uses the correct repository root, invokes the existing evaluator sequentially, and the current four selection jobs each specify exactly two workers, frozen reference weights, the correct `500000 + 110100` seed offset, 200 cards, Solution_92 and the intended explicit Boolean pair. Output paths are new paths in the study directory. It records command/phase evidence, checks failure exit codes, and compares persistent source/plan/engine/interpreter/protected-weight identity before and after jobs and across phases. It contains no choice or promotion step.
- The predeclaration fixes one nominee, complete fresh blocks, tie handling, exact unrounded gates, card-paired bootstrap parameters, the stronger-opponent veto and unchanged behavior across phases. It does not turn correctness tests or selection results into a performance claim.
- **Controller responsibilities remain as already stated in the plan:** admit only one evaluation batch globally; compare the two compatibility receipts' game data; audit complete expected CSV keys/results; bind the nominee's effective configuration; and apply the predeclared decision gates. These small execution helpers do not themselves implement statistical selection, global cross-process admission or promotion, and should not be described as doing so. With the current reviewed job manifest and the controller's stated single-batch use, that separation introduces no blocker.

Remaining prerequisite before performance claims: complete the disabled-path compatibility comparison and then the predeclared evaluations. Keep both flags off in the active submission unless those independent gates pass.
