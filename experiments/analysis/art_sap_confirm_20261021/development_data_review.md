# Independent development-data review

21 October 2026, delegated reviewer `art_sap_data_review`. Read-only audit of the
two completed opponent development comparisons and the completed direct comparison, under source freeze
`9c1efc7fe4e09e1738ff489292786fa535670174`. No model imports, model tests, games,
training, frozen-file changes, state edits, commits or pushes were performed.
The independent calculation imports only the Python standard library and NumPy;
neither the study analyzer nor the project's statistical code was imported.

**Verdict:** both opponent and direct development gates pass, and both historical comparisons
are reproduced exactly in all 23 non-time fields. This validates the selected
candidate's development result and its reproducible definition. It is **not fresh
confirmation**, does not finish the course gate, and does not authorize V3
replacement by itself.

| Opponent | V3 W/D/L | Candidate W/D/L | True-win difference | Whole-map 95% CI |
|---|---:|---:|---:|---:|
| Solution_92 | 102/0/18 | 108/0/12 | +5.000 pp | [+0.833, +10.000] pp |
| default | 120/0/0 | 120/0/0 | 0 pp | [0, 0] pp |

The separate direct comparison has **80 wins, zero draws, 40 losses** for the
candidate against V3: mean result **66.667%**, whole-map 95% interval
**[58.333%, 75.000%]**, on the same 60 known cards with both player sides. This
passes the fixed direct-development mean-result threshold of at least 0.5.

There are 60 known maps (500720–500779), both player sides, per opponent and agent.
Bootstrap: pair by opponent/map/side, convert outcomes to **true win indicators**,
average both side differences within each map, draw whole maps 5,000 times using
NumPy `default_rng(0)`, use 2.5/97.5 percentiles. These figures are independently
recomputed from raw CSVs; there are no draws, so mean result happens to equal win
rate here. The historical selection bias remains: these maps selected this variant
among seven related candidates and were reused before this audit.

## Integrity checks performed

- Both new CSVs contain exactly 240 unique expected opponent/map/side keys, with
  no missing or extra combinations and the same 24-column schema as the references.
- All numeric values are finite and nonnegative; fraction values are within [0,1].
  Every row has 303 steps, point-counting version 2 and `invalid_frac == 0`.
  Match-win counts are integral and sum to at most three. Result/game-win fields
  agree with match wins, and point-win fields agree with total points.
- V3: all **5,520 values** (240 × 23 non-time fields) equal the archived V3 reference.
  Candidate: all **5,520 values** equal Mahmoud's archived A21_art3 comparison.
  Only elapsed seconds were excluded; no tolerances or result-only matching.
- Both job records show the exact registered checkpoint path, 60 maps starting at
  validation index 720, two workers, both specified opponents, no config overrides,
  their own output path, return code 0, 240 rows and cleanup group cleared.
  Durations are 170.77 and 163.28 seconds, within 3,600-second limits and deadline.
  Current output hashes match both saved completion-hash fields in each job record.
- The direct job independently passes the same data-schema, exact-key, consistency,
  zero-invalid and output/hash checks for its 120 expected rows. Its exact command
  uses the frozen candidate versus `self:` plus the frozen V3 path; return code 0,
  elapsed time 89.01 seconds, within its 1,200-second limit, with freeze and cleanup
  records valid. Its interval resamples 60 whole-map means of direct 0/0.5/1 result,
  5,000 draws with seed 0, rather than pairing it to an opponent-reference CSV.
- Independently recomputed freeze ID:
  `561eef88a5c787431009720ad09a70e2900d1d0e25b1ad212d0310e67f942d43`.
  All three completed job records bind that ID. Actual HEAD matches the registered HEAD;
  all **83 source/runtime hashes, five input hashes and eight protected hashes**
  match actual file bytes. The protected V3 and previous backup pairs in both
  checkouts remain unchanged.
- Candidate file hash:
  `e392f20c60d51817591ee4c0061bc8150e7ec8aa312b42e704004538ead45497`.
  The frozen identity receipt binds this hash, the unchanged V3 hash, only the
  saved changes `art_sap=true` and `art_min_hits=3`, and 18 loaded networks.
  Effective flags are `art_reserve=0`, `art_safe=true`, `siege=false`,
  `threat_feats=false`, `joint_moves=false` as planned.
- Without importing Torch or unpickling, the reviewer independently compared all
  **264 serialized tensor-storage payloads** in the original and candidate ZIP
  checkpoints; every storage payload is byte-identical. Structured checkpoint
  equality and actual loaded-network checks are additionally supported by the
  frozen identity receipt and the statically inspected creation checker. This
  audit did not independently instantiate networks; identical storage bytes alone
  are not a substitute for verifying tensor-shape/metadata interpretation.

The historical CSV hashes remain:

- V3: `355f86af5be3f5f4dc755dad877af491a6b764cfce4d7c5db89ddf7dd1f52173`.
- A21_art3: `080488ca48aaf0a405d3b1a6bc70e699d7bcf71a12564ec7fdf5f058cd70687c`.

New output hashes:

- `development_v3.csv`:
  `a8527d4b19009a06f1fcadf7f148ae5e5f2ee8fd6958609dad4b29268b5a7b83`.
- `development_candidate.csv`:
  `a7c5f366e6b790e943b2d6fd83a61f414eca92319ec4948fe19d4c29e5d7e89c`.
- `direct_development.csv`:
  `9817c5feb5ad89d01858bcf5dd009d75102f1f116c37c597fd9e7648215c4aae`.

## Scope and next gate

This review covers the completed **480 opponent development games plus 120 direct
development games**. The direct job finished during the review and was added at
Root's request; no course or fresh results are certified here. Root must complete
the remaining fixed technical gates and recheck
remote/seed reservations before fresh testing. The current development figures
must not be pooled into the fresh estimate, used to adjust the candidate, or
reported as proof of general improvement. `invalid_frac == 0` is the existing
measurement, not a claim that this reviewer exhaustively checked every semantic
game rule. Historical process and intermediate hash checks are evidenced by the
launcher records; this audit independently verifies the resulting files and
present freeze, not a reconstructed process trace.

Reproducible independent calculation: `independent_development_audit.py` in this
directory. Its checked numeric output is `development_data_review.json`. Re-run
from the worktree while the recorded HEAD and frozen inputs remain available:

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B experiments/analysis/art_sap_confirm_20261021/independent_development_audit.py
```

The script completed successfully during this review. It writes only its own
review JSON and does not call study helpers or alter execution state.
