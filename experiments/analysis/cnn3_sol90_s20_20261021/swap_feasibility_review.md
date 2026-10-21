# Read-only assessment: swapping already assigned V3 point targets

21 October 2026. Requested frozen source: `47388d4`, `/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint`. No repository edits, games, model imports, checkpoint loads or tests. Only this report is written. The archive calculations used Python standard-library JSON/gzip and geometry.

## Recommendation

Finish the fixed CNN3 continuation and its planned evaluation. Do **not** start another overnight swap implementation by default. A swap is a genuinely different assignment mechanism from the stopped unassigned-target pilot, and existing legal records contain a few geometrically better swaps. However, there is no demonstrated path improvement, altered action or added point from them. The opportunities under the existing eight-decision cadence are sparse. This supports a later narrow diagnostic, not a new strength claim or blind rule.

If CNN3 fails its development gate, retain V3 and finish the night's report/reproducibility checks. Do not spend the remaining hours successively broadening filters, cadence or rewards to obtain a positive-looking candidate. The coordination hypotheses are not disproved; evidence sufficient to justify another full development loop is missing.

## What the source establishes

`features.assign_targets` chooses the globally smallest remaining unit-target cost, then removes that unit row and target column. This produces unique targets but does not minimize total assignment cost; a two-target exchange can reduce total cost. On own known point targets, current V3's far-opponent penalties do not explain the geometric examples below. A swap keeps the same two point targets and uniqueness, unlike the stopped pilot's demand for an unassigned point target.

Swapping is nevertheless not a solution to blocked target tiles: the same set of targets remains assigned. It is also not automatically better to reduce total distance. Delaying an almost-arrived harvester can reduce early scoring, energy/threat can dominate travel distance, and targets can be reassigned next step.

For V3, point-target changes affect assigned-target feature slots 30–33. `pt_walk`, `pt_hold` and `contest_sap` are off. `scripted_explore` does not apply because both targets remain known point tiles. `pt_sap` can overwrite STAY at a currently held point, so exclude existing point holders. The network can still choose the same action after a swap, or switch to SAP; real final-action comparison is necessary. SAP geometry is chosen separately and a changed target can affect whether SAP is selected even though it does not directly choose its target.

Both assignments and both feature rows must be replaced atomically before inference; `_decide` caches them by step. Altering only `ctx['assigned']` after features exist is inert. Rebuild only the two unit rows and retain all other features/actions. A one-step swap is not a commitment policy. Adding commitment later would be another hypothesis.

## Bounded evidence from existing records

Source: `experiments/analysis/autonomous_20261020/post_exploration_point_flow/v3_observations.jsonl.gz`, SHA-256 `527e2f4124240c45704e268efd6040037af2bccd286b6152712a99b3ba4116ec`. This contains 20 historical V3 games on ten known maps 500720–500729, both sides. It is a selected development archive, not fresh evidence or an independent strength sample. Companion observer source confirms that rows cover known own-half/diagonal point tiles and their current assigned owner.

Exploratory calculation, defined once for this read-only pass:

- Group rows by game, match index and match step; retain matches 1 and 2 (human matches 2/3).
- An eligible recorded owner is live, has energy at least movement cost, stands in the own half including diagonal, is not currently on any recorded known point, and owns a known point target recorded as unoccupied and not blocked.
- Enumerate distinct owner pairs; compare summed baseline and swapped Manhattan distances. Count a geometric opportunity only when swapping saves at least two distance units. The local subset additionally requires both swapped Manhattan distances at most six.
- Do not filter using lifecycle outcomes, hidden information, or future recorded actions. Visible-threat flags are descriptive only. The calculation does not know cross-target BFS distances.

| Recorded state category | Count |
|---|---:|
| All represented M2/M3 states | 3,908 |
| At least two eligible owners | 1,299 |
| At least one distance-saving swap | 101 (2.58%) |
| Distance-saving swap with both cross distances <=6 | 39 (1.00%) |
| Represented states at steps 25/45/65/85 | 157 |
| Scheduled states with two eligible owners | 43 |
| Scheduled states with any distance-saving swap | 4 |
| Scheduled states in the local subset | 2 (1.27%) |

Local examples occur on five of the ten maps across all times. Three of the nominal 160 scheduled states are absent from this field-row archive and are not silently counted as zero. The two local scheduled states contain three qualifying pairs. Counts are state-level; consecutive occurrences are correlated and do not constitute independent samples.

Concrete legal example: **500722, player_1, match index 2, step 65**, canonical coordinates. UID5 at (3,12), E131, assigned (2,16), baseline Manhattan/BFS 5/5. UID12 at (2,11), E94, assigned (3,17), baseline Manhattan/BFS 7/7. A swap changes Manhattan distances from 5+7 to 5+5. Both targets are unoccupied by our team, unblocked in belief, with no visible threat or visible enemy on target recorded. Actual baseline actions are DOWN and RIGHT. Those actions can already progress toward their swapped targets too; this is specifically not proof that the swap changes behavior.

Second scheduled state: **500724, player_1, match index 1, step 45**. One pair changes 1+7 to 4+2, but has visible threats and delays the unit one move from its current target. Another changes 3+7 to 4+4 with a visible enemy on one target. These illustrate why a geometric score alone is insufficient.

The newer target-pilot records retain observation digests, not full observations/terrain/assignments. Their 0/32 eligible alternatives cannot be retrospectively reclassified into swap opportunities. The loss-observation archive lacks assignments and cross paths too. None of these records can establish counterfactual action or point gain.

## Optional smallest independent feasibility probe, if root chooses one later

This is a separate proposed experiment, not an extension/relabeling of the stopped pilot. Do not start it during CNN training. It should cost only four V3 games after a small helper change, not create a learner, branch simulator or general infrastructure.

1. Before execution, freeze two unused development maps and both sides, eight times/game (M2/M3 steps 25/45/65/85), V3 weights/config, and one deterministic pair selector. Do not reuse the two hand-picked archive examples as evidence of general frequency.
2. Require two distinct movable units, neither currently harvesting a known point, each assigned a different unoccupied own-half known point; preserve both targets. Both targets must be passable in current belief. Compute all four known-map BFS distances, not just Manhattan. Each swapped distance must be <=6 and the summed BFS reduction >=2. Require finite baseline paths. Select greatest summed reduction, then sorted unit IDs. No threat-weight tuning.
3. On a cloned pre-act V3, simultaneously swap the two assignments and rebuild their four assigned-target features; run ordinary final `act`. Live V3 remains unchanged. Compare complete final action arrays; log eligible-pair count, all four BFS distances, chosen IDs/targets, original/changed final actions and exclusion counts. Record compact legal context needed to audit a chosen pair, not hidden state.
4. Fixed admission gate: at least eight of the 32 scheduled states must have an eligible swap that changes an actual emitted action, with at least one such state on each map. Stop after four games or 15 minutes, whichever comes first. Preserve a partial result as incomplete; do not add maps or relax BFS/cadence/eligibility to reach the threshold.
5. A pass would establish only actionable frequency. Before any policy/learner experiment, a separately bounded causal comparison must show a point benefit. A failed frequency gate ends swap work for this night.

The historical sparse rates make this gate unlikely to pass, although two new maps could differ. That is precisely why I recommend **not implementing this probe tonight by default**. Its expected information value is lower than completing CNN3's already authorized clean test and preserving a clear negative result if necessary.

## Scope and uncertainty

No new production bug was found. Greedy assignment's failure to guarantee minimum total distance is a known algorithmic property, not proof that the game objective is mishandled. Baseline BFS values are available only for recorded assignments; cross paths, full legal model inputs and alternative Q-values are unavailable. Belief terrain can be stale. The geometric counts are exploratory prioritization evidence only. No claim of 100% performance or a stronger V4 follows.
