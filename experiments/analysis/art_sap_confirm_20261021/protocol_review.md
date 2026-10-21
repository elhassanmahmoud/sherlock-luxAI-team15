# Independent review of the fixed Art3 experiment helpers

Reviewed on 21 October 2026, 18:16 UTC, by delegated Codex reviewer
`art_sap_protocol_review`. Initial checkout HEAD was
`47388d4c7196d3ef90714e23045164f9c80348bf`. Scope: the four helpers under
`.superpowers/sdd/2026-10-21-art-sap-confirmation/`, their archived mirrors,
the fixed plan, and the production evaluator/course-report interfaces.

**Current decision after scoped re-review: the reported process-guard blocker is
resolved for the fixed study's supported command forms.** All 11 synthetic
tests pass. No additional implementation blocker was found in this re-review;
Root's complete freeze inventory and manual inspection of unclassified Python
processes remain prelaunch requirements. The statistical protocol and report
checks match the plan and are unchanged. The original finding below is retained
as review history; its resolution and remaining guard limits follow it.
No candidate, execution state, source, weights, or experiment data were changed
by this reviewer. Only this report was written. No model or engine was imported,
and no games or training were run.

## Original blocking finding — resolved in round 1

### P1 — The process guard misses this Mac's Python processes and common model entry points

`job_launcher.py:53–63` recognizes only lowercase `python`, followed by a narrow
list of `-m scripts.*` invocations. Actual `ps` output on this machine identifies
the interpreter as
`/Library/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python`.
The capital `P` means even a normal competing `-m scripts.par_eval` or trainer is
invisible to the guard. During this review the independently authorized builder
test process was visible with that same capitalized executable name; it was not
an unauthorized run and this reviewer did not interfere with it.

Mocked `ps` listings, passed through the real `check_processes()` without
starting any model process, produced:

| Foreign process | Observed guard result |
|---|---|
| `/usr/bin/python3 -B -m scripts.par_eval --workers 2` | Rejected, as intended |
| Actual macOS `…/MacOS/Python -B -m scripts.par_eval --workers 2` | **Accepted** |
| `/usr/bin/python3 -m scripts.experiment --games 3000` | **Accepted** |
| `/usr/bin/python3 -m pytest -q tests/test_ensemble_dimensions.py` | **Accepted** |
| `/usr/bin/python3 scripts/train.py --games 3000` | **Accepted** |
| A foreign `multiprocessing.spawn` worker | **Accepted** |

The last five cases violate the intended no-other-model-compute protection.
The own-group worker counter does not detect foreign orphaned workers, and the
existing nine tests do not exercise this guard.

Required before launch: recognize the actual interpreter representation and
cover the repository's model-capable module/file/test entry points plus foreign
spawn workers. A fail-closed check of Python processes with explicit allowances
for this launcher's owned process group and separately identified harmless
analysis processes is a defensible alternative to an incomplete model allowlist.
Add mocked process-list regressions for these examples, allowing at most two
owned evaluation workers and rejecting three. Re-run the harmless cleanup test.
Root must also verify that all currently authorized model tests have completed
before launching the candidate.

## Scoped re-review, round 1 — 21 October 2026, 18:25 UTC

Checkout HEAD at re-review was
`e37da4d1a4e0abd9f20a0a528447da8bcd980cbf`. Inspected the new
`compute_process_kind()` and updated `check_processes()`, the two added tests,
and all four archived mirrors. This review did not edit implementation, commit,
push, import models, or run games.

The guard now normalizes the executable name, recognizes this machine's
capital-P Python, the supported model modules and file entry points,
pytest/unittest/test entry points, and foreign multiprocessing workers and
support processes. Only the actual current PID and the registered child process
group receive ownership exemptions; another test process in the launcher's
parent group is still rejected. Owned resource trackers are permitted without
being counted as evaluation workers. Two owned workers pass; three fail.

Independently repeated all five original false-negative examples through mocked
`ps` output: all now reject. Independently ran the complete supplied helper suite:
**11 tests passed in 2.508 s**, including the TERM-resistant-descendant cleanup
test, all prior statistical/provenance tests, the new foreign-process cases,
read-only command cases, and the two-versus-three-worker boundary. No Torch,
JAX or luxai_s3 import occurred in the additional probes.

Unrelated-change check: `protocol.py` and `analyze.py` retain their original
reviewed SHA-256 values. Reconstructing the original guard in memory yields
exactly the original full `job_launcher.py` hash; removing only the two new guard
tests and their mock import yields exactly the original `test_helpers.py` hash.
Thus no gates, seeds, counts, identity rules, budget arithmetic, deadline,
launch lifecycle or cleanup logic changed. All four archives match their
current implementation bytes.

**Guard limits:** this remains recognition of supported process command lines,
not proof that arbitrary Python is harmless. Mocked `python -c` model code,
an unknown custom script name, and the valid combined mode flag
`python -Bm scripts.par_eval` are still unclassified and accepted. The fixed
study itself emits separate `-B -m` arguments, so the latter is outside its
supported launch form; do not interpret the passing guard as a general Python
isolation guarantee. Standard string splitting also cannot reliably parse
executable or script paths containing spaces. Conversely, all foreign pytest
and multiprocessing helper processes are conservatively rejected even if their
actual workload would be harmless.

Root must inspect unclassified Python/inline/custom processes at admission,
ensure all model tests have finished, and retain exclusive model-compute
ownership during the run. Do not start a new custom model command while a study
job is running. These stated operational limits do not require changing the
fixed experiment or expanding this narrow repair. The separate exhaustive
freeze inventory remains Root's responsibility, as described below.

Current re-reviewed changed-file hashes:

| Helper | SHA-256 |
|---|---|
| job_launcher.py | `3c99dd53a3a547bc604fe5eb5614df30d70c423643e1a9c68aee699981efc84e` |
| test_helpers.py | `f6e916df777fbfb50f38bc4e201b2e4484fd1c4a844268bfd5e385782a477694` |

## Verified protocol behavior

- CLI is fixed: no `--set` overrides; 60 known maps 500720–500779 for each
  reproduction and direct development block; fresh opponent maps
  523000–523199; fresh direct maps 523200–523399; both sides; exactly two
  evaluation workers. `scripts.protocol.VAL_SEED_BASE` and the evaluator mapping
  supply the 500000 offset. The course command uses the candidate alone and its
  production checker fixes the two known maps and both opponents/sides.
- Counts are 240 + 240 reproduction, 120 direct development, 8 course,
  800 + 800 fresh opponent games, and conditional 400 direct fresh games:
  **2,608 total**, excluding any separately admitted optional audit. The helper
  does not add another candidate, extension, training run, or optional audit.
- CSV validation requires the exact 24-column schema, exact unique
  opponent/map/side key set, finite nonnegative measurements, integral count
  columns, valid fractions, 303 steps, point-counting version 2, and
  `invalid_frac == 0` in every row. Match results, `game_win`, and `point_win`
  must agree with their counts; action/map counters have sensible bounds.
- Reproduction compares all 23 non-time fields per row, not merely aggregate
  wins. Both historical file hashes are pinned. All reproduction differences
  prevent advancement, as do fewer than 108 candidate Solution wins, fewer
  than six additional wins, or fewer than 120 default wins.
- Against fixed opponents, wins are `result == 1`; draws are counted separately
  and contribute zero to true win rate. Direct result uses 0/0.5/1 and requires
  mean result >=0.5 in development.
- Bootstrap sampling is paired by whole map, retaining both sides together;
  candidate-minus-reference map differences use 5,000 draws with
  `numpy.default_rng(0)` and 2.5/97.5 percentiles. Fresh Solution gates are
  >=5 percentage points and lower bound strictly >0. Default gates are >=99%
  and difference >=−1 percentage point. Direct fresh requires lower result
  bound strictly >0.5. Integer cross-products correctly handle exact 5%, 99%,
  and −1% boundaries.
- Analyzer phase reports recompute prior gates, validate phase chronology,
  require completed hash-bound jobs, and return advancement/release-review
  booleans. They do not silently declare adoption. Launcher phase selection and
  remote/seed checks are explicitly Root's responsibility; it is not an
  autonomous gate-enforcing scheduler.

## Timing and process cleanup

The admitted historical V3 file has 240 positive timings, maximum **4.94 s**.
The helper calculates `ceil(games * 4.94 / workers * 1.2 + 60)`, uses one worker
for the serial eight-game course run, and sums every still-unattempted job,
including both fresh opponent blocks and conditional direct fresh. Initial
projections are:

| Job | Projected seconds | Fixed cap seconds |
|---|---:|---:|
| Each known-opponent reproduction | 772 | 3,600 |
| Direct development | 416 | 1,200 |
| Course | 108 | 600 |
| Each fresh opponent block | 2,432 | 3,600 |
| Direct fresh | 1,246 | 2,400 |

Total is **8,178 s**, plus a separate 300 s closing buffer. The `/2` is
appropriate for the two balanced evaluation workers: `secs` measures each
worker's whole-game wall time and these fixed map counts split evenly. It is
not accidentally applied to the course runner. As a separate plausibility
check, the recent V4 direct-development file contains 120 games with maximum
3.65 s, below the chosen 4.94 s envelope; its opponent block maximum is 4.69 s.
No evidence here warrants declaring the division itself a defect. This remains
a conservative empirical projection, not a guarantee that an unseen candidate
or thermal slowdown cannot exceed it. Per-job caps and repeated admission are
the fallback; Root should inspect actual completed timings before continuing.

The deadline constant is 22 October 03:15 UTC / 05:15 Berlin. Per-label caps
match the plan. A 10-second shutdown allowance precedes the per-job stop time;
polling checks source/weight hashes and the clock, and terminal job timing is
validated by the analyzer. A nonblocking study lock prevents two copies of this
launcher from racing. Output/log reuse and attempted-label retries are refused.

Each child receives a new session/process group. Cleanup sends TERM, then KILL,
to that owned group, checks for remaining non-zombie members, and retains the
active ownership marker when cleanup cannot be established. The harmless
TERM-resistant-descendant test passed and confirms cleanup after the group
leader terminates. Ordinary signals are handled; an uncatchable kill of the
launcher still requires Root to inspect and clear its recorded process group.

## Freeze-state checks still required from Root

There was **no Art3 execution_state.json** at the initial review, by design. Therefore
this report does not certify candidate identity, completed integration tests,
fresh seed availability, final HEAD, or complete source/runtime provenance.

`freeze_id` binds the immutable state fields; the launcher records it and exact
argv/output hashes for every attempt. Analyzer rejects failed/incomplete jobs,
changed outputs, mismatched freezes, wrong counts, excess timing, or missing
ownership. The identity receipt must bind the pinned V3 hash, candidate hash,
exactly the two saved config changes, unchanged other checkpoint fields,
18 loaded networks, and tensor identity. Effective art3/default-off flags are
checked. These are sound bindings to Root's separate model check, not an
independent re-execution of that check.

The validator enforces a minimum source list, not exhaustive enumeration of all
agent/script/engine dependencies. It checks protected hash multiplicities, not
the semantic identity of all eight paths, and `.absolute()` does not enforce
the documented canonical/symlink-free form. Before launch, Root's state audit
must therefore explicitly check:

1. All final agent, opponent, script, course, engine and runtime inputs required
   by the plan are present, including the actual helpers and their archives.
2. Both current V3 files and both historical backup files in **each** checkout
   are the intended distinct paths with the correct hashes; no aliases are
   counted as additional protection.
3. The candidate is a separate experimental file, the recursive comparison
   receipt includes all non-config checkpoint fields and the actual reload,
   and source HEAD is registered only after integration and tests.
4. Advancement uses the analyzer's true gate result, and a current remote/seed
   audit precedes any fresh game. The helpers intentionally do not perform
   these ownership decisions.

These are explicit operator responsibilities, not evidence of a bad state
already created. If the state omits them, that omission is a prelaunch blocker.

## Course-check scope and test evidence

Read `scripts/check_candidate_runner.py` and the existing
`v4_joint_pairs_v1_20261021/course_runner.json`. The analyzer uses their actual
fields: status, eight game records, exact keys, 303 steps, fresh belief,
verified model load, per-game median/p95/max action times, and the five unchanged
file hashes. Timing gate uses the greatest per-game p95 <=50 ms and absolute
maximum <=250 ms, a conservative interpretation of the fixed timing rule.

The production checker actually compares config and every loaded tensor/count,
uses fresh Sherlock instances, selects evaluation mode, and validates finite
integral `(max_units, 3)` actions with action types 0–5. Its `status=passed`
alone does not certify timing limits; the new analyzer supplies those limits.
It does not validate every semantic rule, and the existing `invalid_frac`
metric does not check sap target bounds. The separate artillery code review
is needed for range/energy/mask legality. That limitation is correctly retained
in the new report's scope. Course Solution class-global state is intentionally
not reset, matching the course runner, and is disclosed in the raw report.

Executed the supplied `test_helpers.py -v` under the shared Python environment:
**9 tests passed in 2.443 s**, including synthetic CSV rejection, true wins,
whole-map intervals, boundary gates, every non-time reproduction field,
job/freeze/output binding, actual course fields, fixed argv, descendant cleanup,
and the no-model-import assertion. Additional mocked process checks reproduced
the blocker above. All four `.py.txt` mirrors were byte-identical. Neither the
tests nor the additional probes imported Torch, JAX or luxai_s3.

Initial reviewed helper SHA-256 values (changed-file replacements above):

| Helper | SHA-256 |
|---|---|
| analyze.py | `6f83448f726f49328b1a730885177155412ed5e4ba07fa17487b45f4c83b3d34` |
| job_launcher.py | `ca00fb3857220b53802bb0d92389d2ad5054bdc43f4f1b8a25aa69bb9dcdef57` |
| protocol.py | `b64b54ee5dd6a27336db3c331b22c888ad26a04e6c18383b05669b72d18a8678` |
| test_helpers.py | `102e8c7836d18c846c120a148b85c9f846e6a77a1384db232b61315ffa731e60` |
