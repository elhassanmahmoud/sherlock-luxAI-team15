# Task 1 report — exact student-state collector

Status: implemented; no commits, production games, or training jobs started. Changes owned only `scripts/student_collect.py` and `tests/test_student_collect.py` (plus this required report). Existing shared files and runtime agent unchanged.

## Interface and integration contract

- Python: `collect(student: Path, out: Path, seed_start: int, maps: int, deadline: datetime) -> dict`.
- CLI: `python -m scripts.student_collect --student PATH --out DIR --seed-start 865100 --maps 30 --deadline-utc ISO`.
- `ExactCollector(agent, check=...)` is an instance-local context manager; `set_game(metadata)` sets attribution, `arrays()` returns collected arrays without teacher labels. The exact Q hook and instance `act` wrapper are restored on any exception.
- Outputs: `dataset.npz`, `manifest.json`, `games.jsonl`, `status.json`. Success schema is `schema_version=1`, `status='done'`, pinned `teacher_sha256`, `teacher_members=36`, `student_sha256`, exact integer-side `game_plan`, row counts, and `files_sha256` for both data files. `game_plan` entries contain `game_index/env_seed/side/side_name/opponent/is_train`. Game log uses normal `play_game` result keys plus attribution and retained row counts; optional nonfinite game-summary scalars become JSON null.
- NPZ contains exactly all 14 specified columns and dtypes. Q-hook input/output receive immediate independent numpy copies before the actual Agent_x CPU numpy masking mutation. Saved current `_prev_feats` must match network row order exactly; saved masks are copied only after the single normal `act`. Final returned world actions are authoritative; mirrored movement is converted back to canonical action IDs; late SAP outside the saved network mask is retained and counted.
- Whole-map diagnostic split is the last `max(1,maps//6)` maps; production is last five of 30. Technical map counts 2–30 supported, tagged technical unless 30. Fixed map-index modulo-five opponents are Solution/Solution/Solution/default/V13. Both sides of each map remain together.
- Strict existing student checkpoint contract: one 79→512→512 dueling six-action canonical network, no ensemble/CNN/optimizer/replay, equal q/target, exploration counters 60000/0; valid legacy distillation provenance accepted. An actual Agent_x is loaded, tensors are compared against validated checkpoint, frozen/learning/autosave disabled, evaluation mode enforced.
- Dependencies are pinned before/after, including 39 source files (agent/opponents/environment/default utility), Python executable and installed dependency versions. Student/teacher/V13 input hashes and all discovered protected weights/package/ZIP files in current, primary and historical workspaces are checked. V14 and V13 hashes are fixed. Network, target, optimizer, counters, replay length and losses are digested before and after each game. No update/save calls occur.
- Deadline checked before each normal act, games, teacher batches and publication. Only complete 303-step games accepted. Invalid/nonfinite rows fail the run rather than being dropped. Failure leaves explicit failed receipts and completed game logs, removes pending/final NPZ, and never claims done. Dataset serialization is reloaded and compared before final pinned-input/source check and publication.

## Verification actually executed

1. Initial test-first run: 11 expected failures because collector implementation did not exist.
2. Additional UID-boundary test failed because UID17 was initially accepted; tightened to course UID0..15. Additional legacy provenance test failed because zero updates were accepted; added strict validation.
3. Final focused run: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_student_collect.py tests/test_student_distill.py` — **56 passed in 4.30s** (27 collector + 29 existing distillation). Includes synthetic exact alias mutation, authoritative/mirrored final actions, late outside-mask SAP, no stale reset/empty rows, hook cleanup on exceptions, real Agent_x checkpoint load without gameplay, complete synthetic collection/hash/schema receipts, deadline/learning/source mutation rollback, incompatible checkpoints, nonfinite/empty/duplicate-forward decisions, occupied/protected/alias output guards.
4. CLI `--help` executed successfully.
5. Actual `_pins()` executed successfully after final dependency additions: 39 source files, 10 protected files; dependency versions recorded. No gameplay.
6. `git diff --check` clean for tracked changes at time checked; full repository suite is delegated to root for coordinated resource use, not claimed here.

## Remaining review / limits

- Root owns the requested real-production equivalence check and all actual Lux runs; synthetic end-to-end tests intentionally substitute `play_game`/environment/opponent creation. They do exercise real collector, serialization, teacher mean helper, checkpoint validation and learning digest.
- Teacher labels describe raw V14 Q values on the student's observed feature rows, not a reconstruction of the teacher's full final rule-driven action.
- Diagnostic maps are development data; no unseen-strength conclusion follows.
- No central `ARBEITSSTAND.md` update here because write ownership is restricted; root must integrate this implementation, actual verification and remaining limits into the shared handoff.
