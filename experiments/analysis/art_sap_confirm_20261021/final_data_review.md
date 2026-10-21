# Independent final data review — fixed Art3 study

21 October 2026. Replacement reviewer `art_final_data_review`, covering all six
completed jobs and **2,208 new games** under frozen HEAD
`9c1efc7fe4e09e1738ff489292786fa535670174`.

**Verdict: the data and recorded execution pass this audit; the candidate fails
the fixed fresh acceptance gates and must not replace V3.** Development and course
requirements pass. Fresh Solution_92 improves by only **2.25 percentage points**,
with a paired whole-map 95% interval of **[−0.25, +4.75] percentage points**. Both
the required improvement of at least +5 pp and the strictly positive lower bound
fail. The conditional fresh direct comparison was correctly skipped. This study
ends without promotion, rerun, parameter adjustment, extension, or optional audit.

## Independent calculations and fixed gates

| Phase / opponent | V3 W/D/L | Candidate W/D/L | True-win difference | Paired whole-map 95% CI |
|---|---:|---:|---:|---:|
| Development / Solution_92 | 102/0/18 | 108/0/12 | +5.000 pp | [+0.833, +10.000] pp |
| Development / default | 120/0/0 | 120/0/0 | 0 pp | [0, 0] pp |
| Fresh / Solution_92 | 292/0/108 | 301/0/99 | +2.250 pp | [−0.250, +4.750] pp |
| Fresh / default | 399/0/1 | 399/0/1 | 0 pp | [0, 0] pp |

The candidate's fresh true-win rates are **75.25% versus Solution_92** and
**99.75% versus default**; V3 has 73.00% and 99.75%. On Solution_92, 19 individual
map/side outcomes change from non-win to win, and 10 change in the opposite
direction. The default win indicators are identical between the agents.

| Fixed fresh opponent condition | Observed value | Result |
|---|---:|---|
| Solution_92 true-win difference ≥ +5 pp | +2.25 pp | Fail |
| Solution_92 lower 95% bound strictly > 0 | −0.25 pp | Fail |
| Candidate default true-win rate ≥ 99% | 99.75% | Pass |
| default difference ≥ −1 pp | 0 pp | Pass |
| Fresh direct lower 95% bound strictly > 0.5 | Not evaluated | Correctly skipped after opponent-gate failure |

The separate direct development comparison is **80 wins, zero draws, 40 losses**:
mean result **0.6666666666666666**, whole-map 95% interval
**[0.5833333333333334, 0.75]**. It passes its development threshold of at least
0.5. Development opponent gates also pass: 108 candidate Solution wins, six more
than V3, and all 120 default wins. These known maps selected the historical
variant among related alternatives; their results remain development evidence
and are not pooled with the fresh estimate.

All figures were recomputed from keyed raw CSV rows using only stdlib and NumPy,
without importing or executing the supplied analyzer. Each opponent difference
uses true-win indicators, averages the two player sides within each map, and
resamples complete maps 5,000 times with `numpy.default_rng(0)`. Intervals use
the 2.5/97.5 percentiles with linear interpolation (NumPy 2.5.4). A second
construction from 200×2 binary win matrices and resampled map indices reproduces
both fresh intervals exactly. Direct development resamples map means of the
0/0.5/1 result. No draws occur here.

## Raw data and six completed jobs

Every comparison CSV has the exact ordered 24-column schema, finite nonnegative
numeric values, integral counters, fractions within [0,1], and exactly its
registered unique opponent/map/side key set. There are no missing, duplicate or
extra games. All 2,200 comparison rows have **303 steps**, point-counting version
**2**, and **`invalid_frac == 0`**. Result/game-win fields agree with integral
match-win counts (sum at most three); point-win agrees with total points.
Sap-hit counts do not exceed attempts, and attempts do not exceed unit steps.
All 23 non-time fields reproduce each historical development CSV exactly:
**5,520 equal values per agent**, with only elapsed seconds excluded.

| Registered job, in execution order | Games | Elapsed seconds | Fixed limit seconds |
|---|---:|---:|---:|
| `development_v3` | 240 | 170.768791 | 3,600 |
| `development_candidate` | 240 | 163.275224 | 3,600 |
| `direct_development` | 120 | 89.010932 | 1,200 |
| `course` | 8 | 23.822331 | 600 |
| `fresh_v3` | 800 | 509.511559 | 3,600 |
| `fresh_candidate` | 800 | 536.887604 | 3,600 |

All six recorded argument lists match the fixed checkpoint/output paths and
required modules, opponents, indices, counts, and two-worker setting exactly;
there are no config overrides. Jobs are sequential, return code 0, and have
no recorded job/cleanup errors. Each has its own recorded process group, a clear
group on completion, and no termination signals. Admission records report no
foreign model jobs and zero evaluation workers before launch. Their conservative
remaining-job estimates independently reproduce the frozen formula, including
the 20% reserve and 60-second startup allowances; both overall and individual
admission calculations fit before the deadline with the 300-second buffer.
All finish times precede **22 October 2026 03:15 UTC**.

Current output bytes match both completion-hash fields of every job:

| Output | SHA-256 |
|---|---|
| `development_v3.csv` | `a8527d4b19009a06f1fcadf7f148ae5e5f2ee8fd6958609dad4b29268b5a7b83` |
| `development_candidate.csv` | `a7c5f366e6b790e943b2d6fd83a61f414eca92319ec4948fe19d4c29e5d7e89c` |
| `direct_development.csv` | `9817c5feb5ad89d01858bcf5dd009d75102f1f116c37c597fd9e7648215c4aae` |
| `course.json` | `2170da1d780c73927f4f89c877293cc514078f4d7d3d69145948509e938de67d` |
| `fresh_v3.csv` | `0e3dd43635ee5cc83f3b31ffff01f176551be7786e154b71c22587a75395cdff` |
| `fresh_candidate.csv` | `0cad78af3707a799b36464dea87bbe238b4c35478dbdff26b866f89d76338b0b` |

Historical execution, intermediate checks and cleanup are evidenced by launcher
records, not an independent reconstruction of a live process trace. The present
files, exact argument lists, counters, ordering, timestamps and final integrity
were independently checked. `execution_state.json` still says `prepared` with
`active: null`; this review did not invent or write a closed-state marker.

## Course integration and its limits

The course report has the exact expected top-level and per-game schemas and all
eight unique combinations: seeds 500720/500721, both opponents and both sides.
All eight records report `fresh_belief: true`, `loaded_model_verified: true`, and
303 actions. Every median/p95/maximum is finite, nonnegative and ordered. The
largest per-game p95 is **2.3259874898940325 ms** and largest action maximum is
**10.945542016997933 ms**. Thus the fixed study limits p95 ≤50 ms and maximum
≤250 ms pass. All five course `unchanged_sha256` paths and actual hashes match:
both V3 submission files, candidate, `Paths.csv`, and `lux/runner.py`.

Static inspection of the frozen checker confirms it uses the unchanged real
course runner in a temporary workspace, verifies loaded configuration/tensors,
creates a fresh Sherlock instance per game, and checks action shape, finite
integer values and action types 0–5. The report contains summaries and flags;
this reviewer did not rerun those actions or instantiate the agent. These checks
do not establish every semantic game rule, official course timing compliance,
or a general guarantee of legal actions. The report itself states the official
time limit is unknown. `invalid_frac == 0` is the existing evaluator metric, not
an exhaustive legality proof. Solution_92 class-global state remains as in the
course runner. Eight reused development games are an integration probe, not a
strength estimate.

## Source, checkpoint and seed integrity

Actual HEAD matches the frozen HEAD above. The independently recomputed freeze
ID is `561eef88a5c787431009720ad09a70e2900d1d0e25b1ad212d0310e67f942d43`,
and every job binds it. **All 83 source/runtime, five input and eight protected
hashes match actual bytes**, checked at the start and end of the audit. The
source/runtime set includes the agent, evaluation/launcher code, course runner
and environment files. Execution-state bytes also stayed identical during the
audit (SHA-256 `e17830430e5e1ce03ff2a3c977847009758597153eb6d7aba95d63cbe76b4098`).

Both submission pairs, in the study and main checkouts, retain V3 SHA-256
`aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`.
Both older six-network backup pairs retain
`3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.
The experimental candidate retains
`e392f20c60d51817591ee4c0061bc8150e7ec8aa312b42e704004538ead45497`.

The frozen identity receipt binds those baseline/candidate hashes, exactly the
two saved changes `art_sap=true`, `art_min_hits=3`, 18 loaded networks, and
unchanged remaining checkpoint fields. Effective defaults are `art_reserve=0`,
`art_safe=true`; `siege`, `threat_feats`, and `joint_moves` are false. The creation
checker was statically inspected. Independently comparing all **264 serialized
tensor-storage payloads** in the two ZIP checkpoints finds identical bytes,
without unpickling or Torch imports. Actual loading and recursive metadata/config
equality are supported by the frozen receipt and separately reviewed creation
code; this reviewer did not independently load a model. Storage equality alone
does not prove tensor metadata interpretation.

Fresh opponent maps **523000–523199 are consumed**. No `direct_fresh` job or output
exists; **523200–523399 remain unused by this study**. The pre-fresh seed audit
records 2,109 accessible CSVs / 1,485,640 records with no hits or errors for the
reserved block, and Mahmoud's separate reservation 503220–503819. Its timestamp
falls after course completion and before fresh launch; its recorded origin/main
is `4e1bdb301fb805bbba3252ef7c11988114f90582`. This review checks that record and
the exact study keys; it does not repeat a remote fetch or certify inaccessible
external seed use. No pooling, alternate candidate, fresh direct game or optional
2,000-game audit is authorized by this failed result.

## Review provenance and reproduction

The unavailable predecessor had left `independent_final_audit.py` and
`independent_results.json` before this reviewer began, but no final review. Both
were inspected, not presumed finished. Their pre-review hashes are retained in
the JSON. The companion extends the earlier independent development audit; this
reviewer strengthened exact schemas/counters, all-job ownership/cleanup/admission
checks, final freeze/state rechecks, provenance and the separate index-resampling
calculation, then ran it successfully. File contents alone do not authenticate
the predecessor's authorship; that attribution comes from the handoff.

Only this report and the two designated final-audit artifacts were written.
No frozen source, state, HEAD or checkpoint was changed; no model/engine imports,
games, tests, training, fetches or Git mutations occurred. Reproduction from the
study checkout, while the frozen files and HEAD remain available:

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B experiments/analysis/art_sap_confirm_20261021/independent_final_audit.py
```

The companion writes only `independent_results.json`, containing complete frozen
hash maps, job evidence, checked calculations and limits. Its SHA-256 at this
review is `bc8113c103a140074c3986eb49cde648e12d929ddc710c89460e29a7b10e31d4`;
the resulting JSON SHA-256 is
`1f9b79e6904ee9c78e611e412daf9ed820eff9c33e25b3323f217f8987d2f411`.

This is a **run-time evidence companion** tied to the original frozen HEAD and
absolute local paths. It intentionally fails its integrity checks after a later
reporting commit changes HEAD, or if the checkout paths/frozen files change; that
is not evidence that the saved game results changed. The CSV counts and bootstrap
statistics remain reproducible directly from the archived raw rows using the
method above, independently of a later reporting HEAD.
