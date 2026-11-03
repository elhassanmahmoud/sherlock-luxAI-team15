# Final Battle performance study implementation

Date: 03 November 2026. Workspace: `/Users/moayedshawesh/Desktop/KI/sherlock-november-followup`.

## Scope

Only these assigned new files were authored for this task:

- `scripts/final_battle_study.py`
- `tests/test_final_battle_study.py`

No existing P/PT implementation was edited. No commits, subagents, models, games, training, server, package build, weight change, full suite or live freeze were performed by this worker. The only launched test child was a bounded standard-library sleeping process, terminated to verify ownership/STOP cleanup. Other agents' files were left alone. Independent review and integration are root-owned.

## CLI

Run from the project root with the shared interpreter and `-B -m scripts.final_battle_study`:

```text
freeze --root ROOT --out NEW_FREEZE.json --weights ROLE_MAPPING.json --python PYTHON --expected-head FULL_REVIEWED_SHA
prepare --freeze FREEZE.json --out NEW_SELECTION_DIRECTORY --phase selection
run --plan SELECTION_DIRECTORY/plan.json --start
summarize --plan SELECTION_DIRECTORY/plan.json --state SELECTION_DIRECTORY/state.json --out NEW_SELECTION_SUMMARY.json
prepare --freeze FREEZE.json --out NEW_CONFIRMATION_DIRECTORY --phase confirmation --candidate ROLE --selection-state SELECTION_DIRECTORY/state.json --selection-summary SELECTION_SUMMARY.json
run --plan CONFIRMATION_DIRECTORY/plan.json --start
summarize --plan CONFIRMATION_DIRECTORY/plan.json --state CONFIRMATION_DIRECTORY/state.json --out NEW_CONFIRMATION_SUMMARY.json
```

`ROLE_MAPPING.json` is a JSON object mapping role names to actual weight-file paths. Relative weight paths resolve against `--root`. The required roster is `baseline`, `PAIR18`, `PAIR24`, `FT18`, `Z36`; `C36` and `R36` are permitted only together. The reduced roster additionally requires `--training-omission-reason 'technical reason'`, recorded before outcomes. Optional repeatable `--protocol` inputs augment the mandatory final plan and role-mapping manifest.

Preparation/import/statistics never execute model jobs. Only `run --start` does. Every output path must be new. The runner never installs/promotes weights.

## Fixed behavior

- Screen: exactly 80 maps 851000–851079, two sides, combined six-opponent panel plus default for baseline and every frozen role; direct comparisons for each nonbaseline role against fixed V14. Totals 6,240 or 8,800.
- Confirmation: exactly baseline and one eligible nominee, 400 comparison maps 852000–852399, plus 400 separate direct maps 853000–853399; 12,000 games.
- Uses committed checkpoint configs without inherited P overrides. Each job has two `par_eval` workers and explicit empty override lists.
- `C36` remains in the full screen for methodological comparison and can never be nominated. `R36` requires panel and Solution point deltas at least those of `C36`, in addition to all screen gates.
- Nomination: highest panel delta, highest Solution delta, fewer networks, alphabetical name. No direct-score tie breaker inherited from an old study.
- Confirmation gates exactly follow the final plan: panel delta >=1pp, panel lower >0, Solution delta >=0, Solution lower **strictly >−1pp**, default >=99%, default delta >=−1pp, direct lower >50%. All seven required. Numerical EPS follows existing gate practice.
- Existing `compare_report` and `league_gates` helpers calculate statistics: 5,000 PCG64 seed-0 whole-map bootstrap draws, paired sides and panel opponents. Strict complete expected CSV-key/schema/303-step/v2 checks happen before these helpers can form intersections.
- A confirmation must consume the complete original selection state and summary from this freeze. Every plan/job/output/CSV hash/source identity is validated and the entire selection summary is recomputed; arbitrary JSON claiming passed/nominee cannot admit a phase.
- Each freeze reserves one selection and one possible confirmation via exclusive sibling `*.selection.reservation.json` and `*.confirmation.reservation.json` files. This prevents phase duplication in a second output directory. Partial preparation or execution deliberately remains reserved; no resume or implicit restart exists.

## Freeze/resource/deadline safety

The source identity reuses the reviewed generic `early_curriculum_study.source_identity` helper: all repository Python sources, ignored executable-tree Python files, engine sources, interpreter executable/config, requirements, protocols, and HEAD. It binds actual candidate/opponent/active V14 weight files and this driver. The mandatory final plan and supplied mapping are also hashed. Actual missing model input is rejected; no random fallback is allowed. V14 baseline/direct/active weight SHA must equal the prescribed source SHA.

Generic reviewed driver helpers are reused for hashing, safe paths/atomic JSON, power parsing, class-rate calculations, input validation, output CSV validation, job arguments and owned-group infrastructure. Old P/PT role/gate/phase/deadline functions are **not** reused or mutated. Source identity is checked before jobs, during monitoring, and after completion.

Historical 2.22 panel / 3.0 direct seconds per game are already two-worker wall throughput. Projection never divides by workers. It applies class maxima and a shared slowdown factor, 20% margin and 3,600 seconds for internal transitions. Each admission includes the entire remaining current phase plus all 11,200 panel and 800 direct future confirmation games when screening.

The hard game cutoff is **04 November 2026, 12:30 UTC / 13:30 Berlin**, with no inherited old deadline. Runtime checks STOP `/tmp/sherlock-final-20261103/STOP`, power and the hard cutoff, using ten-second waits to leave hashing headroom below the requested fifteen-second monitoring cadence. Below35% battery prevents a new job; <=25% stops owned jobs unless AC is present. Quota is intentionally external: root/heartbeat can create STOP, with no invented quota API.

The repository-common `resource_lock` coordinates other cooperating supervisors. A fresh process snapshot rejects active model jobs and actual Python final-training/final-study commands, including `final_rescue_train` and the temporary `train_supervisor.py`. The additional parser ignores shell snippets, `python -c` text, preparation commands and its own PID. Launched groups are registered while signals are blocked; runtime/STOP/signal/failure cleanup terminates only the registered owned group and clears ownership. State remains incomplete on failures.

## Actual validation

Interpreter: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B`.

- Initial red: test collection failed because the new `final_battle_study` module did not exist.
- First implementation: 14 synthetic tests passed.
- Added phase-duplication/process-parser regressions: observed red (2 failed, 16 passed), then 18 passed after implementing the missing safeguards.
- Expanded final focused run: **22 passed in 3.04s** using `-m pytest -q -p no:cacheprovider tests/test_final_battle_study.py`.
- `-m scripts.final_battle_study --help`: exit0, exposes freeze/prepare/run/summarize.
- Fresh import probe: no torch, agents, luxai_s3, lux.runner, scripts.experiment or scripts.finetune imports.
- `git diff --check`: no findings in tracked changes; the new files were also inspected for trailing whitespace.

Synthetic coverage includes full/reduced schedules and totals; wrong/missing/unpaired roles; C36 exclusion; R36 control comparisons; all gate boundaries; nomination tie breaks; no double division; shared slowdown; deadline/reserve admission; STOP/battery/hard cutoff; complete keys/schema/steps/v2; source/head/freeze tampering; rate/future-work/deadline/role plan tampering; incomplete/tampered outputs; selection summary tampering/recomputation; single-plan reservations; all12,000 synthetic confirmation rows; and real owned standard-library child cleanup.

## Review/owner follow-up

Independent review should focus on statistical/role semantics, the freeze and selection recomputation boundaries, one-phase reservations, process ownership and wall-time admission. Root should then run the agreed combined/full verification while no model jobs are active, commit explicit paths, and only afterward create the actual immutable study freeze. The runner's numerical `promotion_qualified` field does not replace independent data/technical review or authorize an automatic installation. No performance claim is made by these synthetic checks.
