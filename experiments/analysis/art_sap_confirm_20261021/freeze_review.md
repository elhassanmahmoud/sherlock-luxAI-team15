# Independent prelaunch freeze inventory audit

21 October 2026, 18:29–18:30 UTC (20:29–20:30 Berlin).
Reviewer: delegated Codex agent `art_sap_protocol_review`.

**Decision: the prepared freeze passes this independent inventory audit.** No
missing scoped source, changed frozen file, protected-weight alias, identity
binding discrepancy, or competing model process was found. This clears the
inventory prerequisite for the fixed known-map reproduction; it is not a
statistical qualification or permission to bypass any later gate.

Only this report was written. The reviewer used Python's standard library and
read-only shell/Git inspection: no NumPy, Torch, JAX or luxai_s3 import, model
reload, test suite, training, game, source edit, state edit, commit, or push.

## Frozen state and complete source coverage

- Actual and registered HEAD:
  `9c1efc7fe4e09e1738ff489292786fa535670174`.
- Registered root: `/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint`.
- Execution state: `prepared`, `jobs=[]`, `active=null`.
- Execution-state SHA-256:
  `049835d9df7012bddd0799a420d8e200c93940d660a4e60ac1af5f3ce1c9b09e`.
- Independently recomputed immutable freeze identifier:
  `561eef88a5c787431009720ad09a70e2900d1d0e25b1ad212d0310e67f942d43`.
- All **96 registered files** have the recorded current SHA-256:
  **83 source/runtime files, 8 protected weights, 5 fixed inputs**.

The source inventory is exactly the independently enumerated union below;
there are no missing or extra entries relative to that scope:

| Scope | Files |
|---|---:|
| All Python files under `agents/`, including both opponents | 23 |
| All Python files under `scripts/` | 32 |
| All Python files under `lux/` | 4 |
| All Python files in the installed `luxai_s3` package | 10 |
| All five study helpers and their five `.py.txt` archives | 10 |
| `Paths.csv`, `requirements.txt`, configured Python, `pyvenv.cfg` | 4 |

Each of the five helper/archive pairs is byte-identical. The reviewed launcher,
protocol, analyzer and synthetic-test hashes remain those approved in round 1
of `protocol_review.md`; the separately reviewed candidate creator is also
included. The frozen plan and both historical reference CSVs are present among
the five fixed inputs with their expected hashes.

The configured interpreter is the intended shared virtual-environment path,
which resolves through its normal executable symlink to
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13`; hashing the
configured path verifies its target bytes. `pyvenv.cfg` records Python 3.13.13
and excludes system site packages. The installed engine's parsed
`match_count_per_episode` is **3**. This inventory freezes the stated project,
engine and interpreter scope; it does not claim a hermetic hash inventory of
every transitive third-party binary/library. Do not change dependencies during
the freeze.

## Protected weights and candidate identity

For **each** checkout (`sherlock-v4-joint` and `sherlock-luxAI-team15`), checked
the exact four intended paths:

| Relative paths, per checkout | Expected SHA-256 |
|---|---|
| `agents/sherlock/weights/agent_p0.pth` and `agent_p1.pth` | `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935` |
| `experiments/releases/20261020_old3_sym3/agent_p0.pth` and `agent_p1.pth` | `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158` |

All eight hashes match: four V3 and four historical backup files. These are
eight distinct canonical resolved paths and eight distinct device/inode pairs;
the multiplicity is not produced by aliases. The candidate is also a separate
path and inode from every protected file.

Candidate `experiments/candidates/v3_art3_20261021.pth` hashes to
`e392f20c60d51817591ee4c0061bc8150e7ec8aa312b42e704004538ead45497`.
Its frozen identity receipt hashes to
`5d234b66eeaf19e2346f89b1ad2b1ede96fa8c1cb23ea0dc48d1c020cd904aa8`
and binds the same exact source/candidate paths and hashes. It records exactly
`art_sap=True`, `art_min_hits=3`, unchanged other checkpoint fields,
18 loaded networks and identical loaded inference tensors. Required effective
flags are correct: reserve 0, safe true, siege/threat/joint false; smart sap is
also false and action masking true.

As an additional model-free check, opened both checkpoint ZIP containers using
`zipfile`, without unpickling. All **264 raw tensor-storage members** have the
same relative member names and byte hashes between V3 and candidate. This
independently corroborates storage preservation; it does not replace the
semantic recursive comparison and actual reload performed by Root's reviewed
creator. The latter's result is bound by the frozen receipt. No claim is made
that this reviewer independently reran the 18-network model load.

## Process, time and untouched outputs

The manually inspected process snapshot contained only:

- This audit's short-lived standard-library Python process.
- PID/PGID **81327**, the existing remote watcher at
  `/tmp/sherlock-v4-remote-watch-20261021/watch.py`.
- PID/PGID **46418**, `/usr/bin/caffeinate -is`.

Read the watcher's source: it fetches remote refs, inspects Git metadata/diffs,
and writes its own `/tmp` logs/state. It does not run models, check out or merge
code, or write frozen project inputs. No trainer, evaluator, model test,
foreign multiprocessing worker, or unclassified Python workload was present.
These PIDs are a timestamped observation, not permanent identities. The
launcher's repeated guard and Root's exclusive compute ownership remain needed
throughout execution; command-recognition limits are documented in the protocol
review.

All seven fixed output paths are unique, inside the study directory, have the
correct CSV/JSON suffixes, and are absent. Their seven logs are also absent.
There are no attempted jobs. Nothing in this audit started a reproduction or
consumed a seed.

Per-job caps and the deadline exactly match the fixed plan: **22 October
03:15 UTC / 05:15 Berlin**, leaving the user's later 06:00 Berlin deadline as
the closing reserve. Independently recomputed the initial estimate using all
240 historical V3 timings, maximum 4.94 s, the 20% reserve, 60 s per job and
one serial course worker: **8,178 s**, or **8,478 s including the closing
buffer**. Every individual estimate fits its cap, and the complete remaining
plan fits the deadline at this audit time (about 31,500 s remained).

Root's documented integrated suite reports **531 tests plus 14 subtests**, and
the separate helper suite has **11 passing tests**. This inventory audit did
not repeat model tests. The earlier independent synthetic-helper review and
static creator review remain applicable to the exact frozen helper bytes.

## Continuing conditions

Keep the registered HEAD, all frozen sources/runtime/inputs and the eight
protected weights unchanged during the fixed study. Root still owns gate
selection, exact development reproduction, direct/course admission, and the
fresh remote/seed audit immediately before any fresh games. This audit neither
checks fresh-seed availability nor waives that later check. No replacement of
V3 is justified until all predefined statistical, technical and release gates
are completed.

Final verification after this verdict was communicated: Root had registered
`development_v3` (owner PID 331, child PID/PGID 344), so the operational state
bytes had advanced from the prelaunch snapshot above. The immutable freeze
identifier, actual HEAD and all 96 frozen file hashes were rechecked and remain
unchanged. This is an expected Root-controlled transition; the reviewer did not
launch or control that process.
