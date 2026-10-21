# Independent data audit: Mahmoud's art_sap development comparison

21 October 2026. Read-only review by delegated Codex agent `art_sap_data_review`.
Audited Git snapshot: `baef7a8025ea02b5f29a31a76a6f9a48e2e735a7`; the data and rule
originated in `f540da435af7fab208a211171611cb62fed906e6`. No checkout, source edits,
training, evaluation, model loading, merges, or pushes were performed. NumPy was used
only for bootstrap arithmetic. The ongoing CNN source freeze was not touched.

## Decision

The reported development result is numerically correct: **108/120 Solution wins
against V3's 102/120**, with 120/120 default wins. It reaches the previously used
development threshold, and is a reasonable candidate for **one independently
preregistered confirmation**, after technical review and reproduction. It is **not
evidence sufficient to replace V3**.

There are at least seven related variants in this batch, selected on heavily reused
development cards. The nominal confidence interval does not correct for that
selection. In particular, a positive lower bound on this selected comparison is not
an independent confirmation. Threshold 3 is promising but its neighboring variants
are weaker. No universal 100% claim is justified.

## Data checks and independent arithmetic

Reference: `experiments/analysis/enemy_tie_energy_20261021/development_v3.csv`,
SHA-256 `355f86af5be3f5f4dc755dad877af491a6b764cfce4d7c5db89ddf7dd1f52173`.
This is the reference explicitly named by the mechanism-probe README.

All eight files (reference plus seven A21 comparisons) contain exactly the expected
240 unique keys: cards 500720–500779, both `player_0`/`player_1`, opponents `default`
and `solution92`. Same 24-column schema, all numeric fields finite and nonnegative,
fraction columns in [0,1], `point_counting_version=2`, `steps=303`,
`invalid_frac=0` throughout. Match counts are integer and sum to at most three;
`result` and `game_win` agree with match wins, `point_win` agrees with total points.
There are no draws, so true win rate and mean result coincide here.

Bootstrap was recomputed independently from the raw Git blobs: pair by
opponent/card/side, average the two side differences per card, sample whole cards
with replacement 5,000 times using NumPy `default_rng(0)`, percentile 2.5/97.5.
Every file has both sides for every card; no exclusion or partial pairing occurred.

| Variant | Solution W/D/L | Difference vs V3 | Paired 95% CI |
|---|---:|---:|---:|
| V3 reference | 102/0/18 | — | — |
| art2 | 105/0/15 | +2.500 pp | [−1.667, +6.667] pp |
| art3 | **108/0/12** | **+5.000 pp** | **[+0.833, +10.000] pp** |
| art4 | 101/0/19 | −0.833 pp | [−3.333, +1.667] pp |
| art3, reserve20 | 103/0/17 | +0.833 pp | [−3.333, +5.000] pp |
| art3, unsafe | 103/0/17 | +0.833 pp | [−3.333, +5.000] pp |
| siege | 81/0/39 | −17.500 pp | [−25.833, −10.000] pp |
| siege + art3 | 85/0/35 | −14.167 pp | [−23.333, −5.833] pp |

Every variant and the reference wins 120/120 against default. The art3 result flips
seven V3 losses to wins and one V3 win to a loss, on eight different cards:

- Gain: 500735 p0, 500736 p1, 500744 p0, 500751 p1, 500753 p1,
  500758 p0, 500777 p1.
- Loss: 500775 p1.

The net +6 wins is therefore not entirely attributable to one exceptionally helpful
map, but is still selected from the same development block.

Both `probe_v3_720.json` and `probe_art3_720.json` contain the same 120 Solution
card/side keys, with match-win counts exactly matching their corresponding CSVs.
This is a useful cross-file consistency check, not an independent rerun by this
reviewer. The JSONs have fields `seed`, `side`, `params`, `wins`, `matches`, `secs`;
they do not contain source, checkpoint, CLI or full agent-config manifests.

The probe's aggregate Sap counts per match are:

| | Match 1 | Match 2 | Match 3 |
|---|---:|---:|---:|
| V3 | 42.9417 | 46.3917 | 39.7167 |
| art3 | 44.9000 | 46.3333 | 42.1417 |
| Difference | +1.9583 | −0.0583 | +2.4250 |

The overall net difference is 1.4417 Saps per match. These changed-trajectory totals
are not a count of direct rule activations, and do not establish causally why a game
changed. The README's “roughly two additional Saps per match” is an approximate
description, not an activation audit. Engine-state diagnostic data must remain
measurement-only; this data audit does not certify the custom engine reconstruction.

## Candidate definition and provenance limitation

The documented candidate can be specified as:

- Start from the exact current `all18_v3` checkpoint, retaining all 18 network tensors
  and all existing V3 configuration fields.
- Set **`art_sap=true`, `art_min_hits=3`, `art_reserve=0`, `art_safe=true`**.
- Leave `siege=false`, `threat_feats=false`; do not combine with the rejected
  coordinator, siege, threat nets, or other rule/weight changes.
- All other newly introduced flags remain at their default-off values.

This definition is **inferred from the README plus source defaults**, not bound by a
saved A21 run manifest. The A21 CSVs save outcomes only; the repository snapshot has
no art3 checkpoint or command/config manifest. `par_eval.py` supports temporary
`--set` overrides but does not record them in its CSV. Consequently I cannot prove
from these files alone that those were the only actual overrides in Mahmoud's run.
The source commit carrying the results also does not prove its exact bytes were the
source used before the results were saved.

Both local submission files were independently SHA-256 checked without loading a
model and remain `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`.
An exact new candidate checkpoint/hash and tensor/config comparison must be made
after the current model job is finished; this reviewer did not create one.

## Required next steps before fresh confirmation

1. Finish the current frozen CNN experiment. Independently review and integrate the
   needed source at a safe boundary. Bind the next study to an exact source commit,
   environment/match-count identity, V3 hash, full candidate config, checkpoint hash,
   and equality of all learned V3 tensors. Verify no unintended threat/mixed-input
   or siege activation. Do not silently update source mid-study.
2. Before new result inspection, fix this one candidate, the map blocks, stop rules,
   and acceptance thresholds. Do not later substitute art2/art4 or change reserve
   based on fresh results. Root's 523000–523399 reservation does not overlap
   Mahmoud's declared 503220–503819 threat/PPO blocks, but check latest remote
   reservations and recorded data again at launch.
3. Reproduce the documented 240-game art3 development comparison using the explicit
   definition above, ideally with a new same-source 240-game V3 control because
   source/model-loading code changed. Compare **all 23 non-time fields**, not merely
   the final 108 count. If reproduction differs, diagnose before spending fresh
   cards; do not “repair” by tuning the rule to recover 108.
4. Run the preregistered direct V3 development comparison and the technical/course
   runner checks required by the chosen plan. The A21 files contain no direct V3
   results and no course-runner proof. Existing development gate: Solution at least
   108/120, default 120/120; direct result at least 0.5 if retaining the V4 protocol.
5. Only then use one fresh block: paired candidate/V3 versus Solution and default,
   plus a separate direct block. Retain the established thresholds: Solution
   improvement at least 5 pp with lower paired 95% bound above zero; default at least
   99% and no worse than V3 by more than 1 pp; direct lower bound above 0.5. Report
   W/D/L as well as mean result. A negative result ends this candidate without
   extending its sample or pooling the selected development advantage into the
   confirmation estimate.
6. Only a candidate satisfying those gates can proceed to release safeguards,
   current-V3 backup, packaging/reproduction and protected-weight replacement.

## Evidence hashes

Raw Git-blob SHA-256 values (not normalized text):

| File basename | SHA-256 |
|---|---|
| A21_art2_720.csv | `3cc4bdb5c8c675dada1132fbedd46381e43b92b63fb411e4ed2831f32dfe4485` |
| A21_art3_720.csv | `080488ca48aaf0a405d3b1a6bc70e699d7bcf71a12564ec7fdf5f058cd70687c` |
| A21_art3r20_720.csv | `1c77b518321eb34c595f2e2040220a5adcca2d642367b1236a11fa9e1853760c` |
| A21_art3unsafe_720.csv | `3c4ca1e692fcc85b124932f2a8cc1bad07e938c348e6a50298b88b9d95714aae` |
| A21_art4_720.csv | `8023a83901e3f60312f18b177c8cee885769e2ce5f680ff8b1161a1a8cb0c360` |
| A21_siege_720.csv | `e973b040d24970fbf679121426964d8fa2c76ac8324ed888be9676ed3fe5910c` |
| A21_siege_art3_720.csv | `28cb9b155e4ba0035a695ec171c25df0c213a0083678e18c17e025160ccc9e32` |
| probe_v3_720.json | `ee0ba249c6fb12fae8f9569c87619913537bcb6e09d0a34bce29f013ef1cbead` |
| probe_art3_720.json | `f2a8f52afccdcf21b18798d99a725703d75076a5f1ceba3c852b64c9a097d8c9` |

Machine-readable independently calculated results:
`/tmp/sherlock-art-sap-data-audit-20261021.json`.

Limits: no new games, no learned tensor equality audit, no course tests, no
independent simulator-reconstruction audit, and no fresh-card results in this
review. All strength statements are conditional on the fixed selected agents and
the observed reused development cards.


## Follow-up review of Root's prospective plan

Plan reviewed before new art_sap games:
`docs/superpowers/plans/2026-10-21-art-sap-confirmation.md` in the V4 worktree.
Reviewed draft SHA-256: `cae394b81a66898abe8fd1b8ae4a48f6daed8f22ba0e60e840f332d9f13ad506`.

No statistical/design blocker in this draft. It fixes one candidate, exact
reproduction against all non-time fields (480 games), a direct development gate
(120 games), and eight course games. Only then it spends the distinct fresh
523000–523199 opponent block (1,600 games); the 523200–523399 direct block
(400 games) is used only if the fixed opponent gates pass. It explicitly prevents
sharing these fresh cards with a qualified CNN candidate and reserves Mahmoud's
503220–503819 block. The maximum 2,608 pre-audit games is correctly summed. The
03:15 UTC / 05:15 Berlin admission deadline leaves 45 minutes before the user's
06:00 completion boundary. No sample extension or tuning after fresh results is
allowed. Source/config/tensor binding resolves the historical provenance gap if
actually executed and independently checked.

Three clarifications requested before freezing that plan:

1. Specify that `art_min_hits` uses the number of **currently visible enemy
   entries around the existing Sap target**, which can include negative-energy
   enemies. It is not a guarantee of three surviving enemies or three actual
   future hits. This describes the fixed existing implementation; changing the
   filter now would create a different candidate and invalidate exact A21
   reproduction as its provenance.
2. `art_safe` checks currently visible, sufficiently energized enemies' Manhattan
   **direct-target** range. It does not prove safety from adjacent splash,
   unobserved enemies, enemy movement, or general Chebyshev-capable opponents.
3. Require `invalid_frac == 0` for every comparison CSV, and explicitly construct
   the candidate by directly copying V3 plus the two config fields, without the
   unrelated ensemble builder. The separate code review identified stale
   `ensemble_dims` metadata in that builder; the plan's already-required check of
   18 actually loaded networks and exact tensors is essential. This data reviewer
   has not independently reproduced or fixed that code bug.

The fixed true-win indicators (rather than mean result when draws occur) for
Solution/default are appropriate. Direct comparisons use mean 0/0.5/1. Metadata,
source, loading, malformed data, or reproduction failures are technical stops;
none should be reinterpreted as ordinary strength failures or worked around by
changing candidate parameters after results.
