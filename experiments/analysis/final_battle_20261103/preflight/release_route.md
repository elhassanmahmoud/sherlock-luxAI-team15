# Final release route — read-only source audit, 03 November

No commands below were executed. This audit loaded no models, started no games/tests and changed no repository files. Actual existing scripts were inspected.

## Decision and fallback

- New release requires the single nominated PAIR18/PAIR24/FT18/Z36/R36 to pass all seven **400-map /12,000-game** confirmation gates, independent complete-data review, unchanged study identities and independent technical acceptance. C36 is never releasable. No fallback nominee or team waiver after failure.
- If any required stage is incomplete/unqualified: retain unchanged V14. The primary checkout already contains `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/Gruppe15.zip`,22,228,404 bytes, hash verified during this audit: `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. The current followup worktree has **no** root `Gruppe15.zip`.
- V14 raw weights/source baseline remain `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. The existing ZIP has a separately frozen checkpoint and older verified runtime; its weight-file hash is not the raw-weight hash. Historical 03-Nov preflight applies to that exact ZIP, not to a fresh rebuild.

## Safe package preparation without replacing active weights

`build_submission` accepts `--from-run DIRECTORY`, not a direct `.pth`. It looks for `DIRECTORY/weights/agent.pth`, or separate agent_p0/p1 files. The new builder outputs `<FIXED_BUILD>/<ROLE>.pth`; create a **new staging directory**, clearly recorded as package input rather than a training run.

After all evaluation workers stop and the study/data audit closes, set these task-specific variables, replacing only the two explicit placeholders:

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
release_root=/Users/moayedshawesh/Desktop/KI/sherlock-november-followup
release_py313=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python
release_py310=/tmp/sherlock-continue-20261102/venv310/bin/python
release_raw="$release_root/experiments/ensembles/<FIXED_BUILD>/<ROLE>.pth"
release_evidence="$release_root/experiments/analysis/<NEW_RELEASE_DIRECTORY>"
mkdir "$release_evidence"
release_stage="$release_evidence/package_input"
mkdir -p "$release_stage/weights"
cp -n "$release_raw" "$release_stage/weights/agent.pth"
shasum -a 256 "$release_raw" "$release_stage/weights/agent.pth"
```

Run all subsequent commands from `release_root`, with the established one-thread environment (OMP/OPENBLAS/MKL/VECLIB/NUMEXPR=1), sequentially and without concurrent model/suite jobs. Keep before/after source, candidate, active-weight and existing-ZIP hashes; save actual argv,cwd,start/end,exit codes and logs in the new evidence directory.

```sh
"$release_py313" -B -m scripts.check_candidate_runner --weights "$release_raw" --out "$release_evidence/runner313.json"
"$release_py313" -B -m scripts.build_submission --battle --group 15 --from-run "$release_stage" --out "$release_evidence/Gruppe15.zip"
```

The default builder check is mandatory; do not use `--no-check`. `check_candidate_runner` plays eight complete course-runner games on consumed seeds500720/500721 against default/Solution, both sides. It verifies actual loaded member count/config/tensors,303 steps, fresh belief, action shape/type, preserved sources/weights and reports act timing/RSS. These are technical games, not new winrate evidence.

The builder writes `Gruppe15.main.Agent_x`, one `Gruppe15/agent.pth` for identical side inputs, `agents.yaml`,empty `__init__.py`, valid runtime `.py` modules and `LIESMICH.txt`. It checks the extracted package under **both** `agents/` and the project root, including `train=True`: frozen flag, evaluation mode,epsilon0 and no checkpoint mutation.

It can overwrite its chosen ZIP destination: use an explicitly new evidence path, never the existing primary ZIP during preparation. The invalid-module-name filter excludes local `config 2.py` copies; internal README/worklogs/plans/manifests/CSVs are not packaged. New source includes `assignment.py`, so do not impose the historical18-entry ZIP count on a new package.

## Independent payload and Python3.10 acceptance

Require a passing full suite for the exact release source and independent review of the actual technical logs; never overlap the suite and model jobs. Before installation, independently inspect the actual ZIP and compare its embedded checkpoint against **the exact confirmed raw candidate**: all ordered member tensor bytes/dtypes/shapes, target_q,other fields and config must be identical except `cfg.frozen=True`. Expected member count is18(PAIR18/FT18),24(PAIR24),36(Z36/R36). Check the saved candidate manifest and index18 replacement provenance; Z36 alone changes zone_rescue. Do not require old P checkpoint keys/optimizer fields: new artifacts deliberately omit optimizer/replay and normalize inference counters.

The builder's `frozen_bytes` normally changes only `cfg.frozen`; it reserializes the checkpoint, so whole-file hashes differ. `--half` also changes tensor dtype and removes optimizer state, and is **not** an exact payload-equivalence route for this float32 study. Do not select it merely to reduce file size.

The separately repaired3.10 interpreter exists at the path above. Existing evidence records Python3.10.22,Torch2.2.2,NumPy1.26.4 and three-match course parameters; verify actual current environment identity before relying on it. No reinstall is implied. Safe existing checks:

```sh
"$release_py310" -B -m scripts.check_candidate_runner --weights "$release_raw" --out "$release_evidence/runner310.json"
"$release_py310" -I -B -c 'import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); from scripts.build_submission import check_battle,battle_paths; check_battle(Path(sys.argv[2]),battle_paths(15,True))' "$release_root" "$release_evidence/Gruppe15.zip"
"$release_py313" -B "$release_root/scripts/xversion_replay.py" record "$release_evidence/Gruppe15.zip" "$release_evidence/selected_4242.pkl" --seed 4242
"$release_py310" -I -B "$release_root/scripts/xversion_replay.py" replay "$release_evidence/Gruppe15.zip" "$release_evidence/selected_4242.pkl"
```

Require303 recorded steps and zero differing actions on replay, with `frozen=True` and correct network count. Record plays one new self-play game; replay reuses its observations and is not another game. These scripts support the required single `agent.pth` layout. Replay pickle must be locally generated/trusted. Preserve ZIP/raw/source hashes around every stage. Record time/memory honestly; these checks establish neither Windows certification nor an unknown course time limit.

## Installation boundary: historical tools are incompatible

There is **no ready existing structured one-command installer for these new roles**:

- `experiments/analysis/continuation_20261102/release_tools/install_qualified_P.py` and `verify_P_package.py` pin old P SHA `dbb15222…`,source03e,36 members,PflagsTrue,old preflight/schema and the9,000-game P confirmation. Their Solution lower-bound comparison also differs from the new strict gate. Do not rename a new role to P, rewrite historical receipts or loosen those tools.
- `scripts/release_candidate.py` accepts legacy text PASS logs/optional team waiver; it does not consume the new structured12,000-game evidence. It copies active weights **before** runner QC, has no automatic rollback, does not back up the existing ZIP and skips rechecking an already existing backup directory. Do not fabricate a PASS log or use `--team-decision` to bypass this plan.

Thus build and fully verify the candidate ZIP with `--from-run` while active V14 stays intact. Only after independent actual data/payload/technical acceptance should root use a newly reviewed evidence-bound publication procedure or an explicitly journaled controlled file transaction: back up/hash **both** active `.pth` files **and** existing primary ZIP; publish both identical selected raw weights and the exact verified ZIP; verify all destinations; roll back all three on any failure. Preserve existing release directories and foreign files. This memo does not supply an unreviewed shortcut installer.

If a new release helper is needed, implement/review it before the performance source freeze, or outside the frozen checkout after the study is formally closed. Never change source/HEAD inside an active screen-to-confirmation freeze merely to add release tooling.

## Final handoff

The upload artifact must be named **Gruppe15.zip**, containing class`Gruppe15.main.Agent_x` and weight`Gruppe15/agent.pth`, for Moodle by **04 November2026,23:59 Berlin**. Final root jobs end by16:00; public upload still needs the user's concrete upload authorization. Keep source/candidate/confirmation/technical manifests,logs,CSV provenance and final decision in the repository; exclude these internal documents from the runtime archive. Final report should name the actual released role/hash or unchanged V14 and distinguish historical strength measurements from new study results.
