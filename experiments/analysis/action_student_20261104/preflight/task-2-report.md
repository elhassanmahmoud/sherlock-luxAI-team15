# Task 2 implementation report

Implemented only `scripts/student_action_distill.py` and `tests/test_student_action_distill.py`; no commits, production jobs, shared documentation edits, runtime changes or subagents.

API: `run_distillation(student, datasets, out, deadline)` (aware datetime). CLI: `python -m scripts.student_action_distill --student PATH --datasets DIR [DIR ...] --out DIR --deadline-utc ISO`. Final checkpoint: `OUT/weights/agent.pth`; provenance/status/metrics remain JSON sidecars. No configurable epoch shortcut: exactly 30 action and five value-head-only epochs, Adam 1e-4, batch 1024, seed 20261104, one CPU thread.

Objective: row-averaged legal-centered MSE divided by one teacher-only scale² plus KL(teacher || student) on masked softmaxes using that same scale. Scale is legal-centered teacher RMS across *all legal train entries*, floor .001; root explicitly confirmed the centered RMS interpretation. Illegal actions and per-row offsets cannot affect the action objective; one-legal-action rows contribute exactly zero. No teacher gradient. Calibration targets teacher legal-Q means with body/adv frozen, byte-equality checked and pairwise legal rankings checked with recorded float32 near-tie tolerance.

Validation: exact NPZ columns/shapes/dtypes/finiteness, nonempty masks, game/step/unit row uniqueness, manifest schema 1/status done plus status.json done, exact dataset/games hashes, pinned V14 SHA/36 members, contiguous full plan indices, both sides per seed, per-row identifier/split agreement and whole-seed split consistency across rounds. Latest collector student SHA must equal supplied starting student. Occupied/protected/input-containing outputs refused. Hashes pin inputs, relevant source files and protected submission files before/after. Parent owns the additional production schedule/game-completeness/starting-S30 provenance checks.

Exports preserve the existing nine checkpoint fields plus the three already-supported distillation metadata fields. q=target exactly; no optimizer/replay/ensemble; env_steps60000/learn_steps0. Distillation update metadata is prior actual updates plus all current action/value optimizer steps. Sidecars separately retain phase counts, split, starting hash, source pins, objective/scale and cumulative counts. Actual Agent_x reload must reproduce Q exactly and have no extra_q. Initial, after-action and after-calibration metrics distinguish legal agreement/regret/Q error and explicitly label recorded collector rule overrides as belonging to the collecting policy, not replayed new final-policy actions. Any deadline/exception removes pending/final checkpoints; an interrupted value phase is tested.

Evidence (real 512-wide QNet, tiny synthetic datasets, no games):

- Initial seven helper tests failed due to missing implementation, then passed.
- New validation/training tests failed before their implementation; exact objective and duplicate row guard have explicit observed red/green evidence.
- `python -m pytest -q tests/test_student_action_distill.py`: **28 passed in 3.87s**, final run.
- Previous adjacent run of action/distill/reward tests: **104 passed in 23.80s** (before adding the final duplicate-ID case).
- `git diff --check`: exit 0 (new files currently untracked, so the test runs are the primary verification).
- Diagnostic-only target changes produce bit-identical final training tensors and identical scale; calibration lowers train legal-mean Q error on the fixture. Deadline after all30 action epochs and one value epoch exports nothing. Frozen-body mutation and non-tie legal ranking changes are rejected.

Limits: no production collection/training/strength evaluation; no whole-suite run by this implementer (root owns integrated verification). Source hashes intentionally require a source freeze during real fitting. Completed package status/hash is trusted for games.jsonl contents; parent is independently checking actual completed-game counts and production seed provenance.

## Review fix round 1/5

Addressed independent review P2: local `reserve_output` now checks `agents/Gruppe15` in current, primary and historical checkouts, plus ancestors and filesystem aliases, before delegating to the stable existing raw-weight/input guard. It does not import collector internals. Before editing, copied both owned source/test files to `/tmp/sherlock-action-student-20261104/task2-before-fix/` for scoped review.

Observed red: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_student_action_distill.py -k 'packaged_submission_paths'` yielded **3 failed, 29 deselected in 2.57s**; all three protected checkout paths reached the mocked creation boundary. No directories were created. Added a temporary repository-symlink-alias regression as well.

Final covering command: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -m pytest -q tests/test_student_action_distill.py` yielded **32 passed in 3.89s**, exit 0. `git diff --check -- scripts/student_action_distill.py tests/test_student_action_distill.py` exited 0. Only the two owned files and this report changed; no production fitting or adjacent/full-suite run in this fix round.
