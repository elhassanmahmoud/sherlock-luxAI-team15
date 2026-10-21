# Independent development-data audit and passive-probe review

**Verdict: ready within the reviewed scope; no blocking findings.** The fixed prototype fails its Solution development gate. The recorded decision not to advance to fresh confirmation or replace V3 is supported.

Audit snapshot: 392 completed new games, before the separately proposed four-game passive funnel follow-up. Reviewed frozen source commit `e84b9928f20d24fcfe18d1ccf1d1db5a59cf78f5`, `results.json`, `analyze.py`, README, raw CSVs, state/identity/reproduction records, course-runner output, activation output and reference source comparison. Only this audit file was written. No source, index, refs, checkpoint, existing output or state file was changed. No Torch/model import, game, probe execution or test-suite run was performed.

## Independently reproduced results

Used a fresh lightweight Python calculation with only stdlib and NumPy; did not execute `analyze.py` or import its comparison helper. Parsed CSVs by `(seed, side, opponent)`, asserted exact Cartesian key sets and uniqueness, then paired both sides within each sorted card.

| Comparison | Candidate W/D/L | Reference W/D/L | Recomputed estimate and 95% card interval |
|---|---:|---:|---|
| Default | 120/0/0 | 120/0/0 | Win-rate difference 0 pp [0; 0] |
| Solution_92 | 101/0/19 | 102/0/18 | Win-rate difference −0.833333 pp [−2.5; 0] |
| Direct against V3 | 62/0/58 | — | Mean result 0.5166667 [0.5; 0.5416667] |

- Candidate and reused reference each contain exactly 240 distinct keys: cards 500720–500779 × both sides × both named opponents. Direct comparison has exactly 120 distinct keys over the same cards/sides and the protected V3 checkpoint as its sole opponent.
- Every raw result matches the comparison of recorded match-win totals; `game_win` matches actual wins. All numeric fields are finite, every game has 303 steps and point-counting version 2, and all `invalid_frac` values are zero. There are no draws or excluded rows.
- Bootstrap recomputation used 5,000 draws of 60 whole-card means/differences, `np.random.default_rng(0)`, and 2.5/97.5 percentiles. All estimates and interval endpoints match the saved output within 1e-15. Only one Solution game changes its win/loss outcome between candidate and reference; this is consistent with the narrow paired interval, not an arithmetic error.
- Gate arithmetic agrees: Solution 101 < 108 fails, Default 120 = 120 passes, direct mean ≥ 0.5 passes. The failed Solution gate is sufficient to reject advancement. Saved technical timing is also comfortably within the prototype's 50 ms p95 / 250 ms maximum budgets: highest per-game p95 2.342875 ms, maximum 5.239 ms.
- Recorded game accounting reconciles: 240 opponent + 120 direct + 16 disabled smoke + 8 course-runner + 8 activation = **392 new games**. The 240 reused V3 games are correctly reported separately. Activation records sum to 2,400 helper calls and zero changed units in those eight games only.

## Provenance and reference reuse

- Current HEAD equals the full frozen `e84b992` commit. Independently rehashed all **115 saved inputs** (source/interpreter/engine files, protected release and backup files, candidate and baseline CSV); all match. The **98 tracked source files** in the freeze also match the corresponding Git blobs at that commit. Current candidate hash is `8301c9fdae44a511c91d21946f4ac66536260e6836358fbc300726b801ae8acc`; V3 and old backup hashes remain the recorded values.
- All three result-input CSV hashes match `results.json`; recorded job CSV output hashes also match. Recorded jobs finish successfully, report post-job input verification, are sequential without overlap, and leave `active=null` / `remaining_games=0`. The audit independently verifies current bytes, rather than claiming to have observed historical process execution.
- Independently matched all **62 listed shared reference sources** to the historical reference manifest, including evaluation/opponent code and engine files. Inspected the three documented source differences: the old default-off enemy-energy feature is absent, while the approved default-off joint decoder and counters are present. No unexplained active-baseline change was found.
- Independently compared all **368 non-time fields** across the exact 16 smoke keys against the reused baseline; every numeric field agrees within 1e-9 and categorical fields agree exactly. This supports the specifically authorized reference-reuse check. It is not a claim that all 240 reference games were replayed.
- The saved candidate-identity record reports only `joint_moves` changed and all other checkpoint fields identical. This audit verifies checkpoint byte hashes and provenance, but deliberately does not reload tensors; tensor identity relies on the recorded earlier check.

The README faithfully describes known development cards, actual-win versus direct-result metrics, paired uncertainty, the null-interval limitation, reuse and the failed fixed candidate. It does not claim a general improvement, fresh confirmation, or 100% general win probability. No material wording correction is required.

## Pre-execution review of passive funnel probe

Reviewed `.superpowers/sdd/2026-10-21-v4-joint-prototype/funnel_probe.py`, SHA-256 `17dd6c3cce53350014ba33481418999023ea45aa6a08ebfcaef7d3608cfecf09`. **Approved to run as the bounded passive diagnostic.** This is source review only, not a claim that the four games have run.

- The wrapper calls the original decoder exactly once with unchanged arguments, records counters, and returns that exact `changed` object. The funnel only builds local collections and reads arrays; it neither selects replacement actions nor mutates inputs. Hook restoration occurs in `finally`.
- The sampled values are the actual helper inputs after final action overrides, in the existing canonical coordinate frame. The funnel reads observed friendly positions/energy, known point tiles, visible enemies, masks and Q values. It has no engine-truth/future/opponent-action input. Existing `play_game` resets team/side through `new_game` for each game.
- Eligible units and destination/occupancy rules reproduce the helper's contract. The nested stages are all finite legal movement options, baseline plus top two, regret bound, current/destination enemy guard, then shared-known-point pair eligibility. Initial distance ≤2 applies throughout. Numeric fallback and baseline retention agree with the helper.
- Gains are intentionally measured against the unchanged full baseline plan before pair reservations; the module docstring states that distinction. Thus stage-five gain counts are opportunities, not predicted numbers of accepted pairs or changed units.
- The `no_change_stage5_discrepancies` invariant is sound: if the real helper returns no changes, no strict-gain pair was accepted, so its plan and used-unit set stayed at baseline throughout. Any valid stage-five gain pair would therefore remain available and force an accepted change when reached. A nonzero discrepancy should be investigated before interpreting funnel results.
- Four known-card games on 500724–500725, both sides, sampled every tenth helper call, constitute a limited descriptive diagnostic. They do not estimate population-wide activation or establish a cause of the failed win-rate gate. These limitations are consistent with the current README.

No additional experiment, parameter change, release decision or broader audit is implied by this approval.
