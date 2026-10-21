# Coordinated collision feasibility — 21 October 2026

**Verdict:** the mechanism is distinct and physically valid, and the archive contains concrete legal opportunities. It does **not** currently justify a new policy or new game-based probe. Most tightly gated opportunities were already taken by V3; the only missed example against an actually stationary opponent has a small energy margin and no preceding stationary observation. No improvement is established.

Scope: read-only source and existing diagnostic JSON/JSONL inspection in `/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint`; stdlib-only counting. No model/engine imports, tests, games, repository edits, weights/HEAD changes, network actions, or fresh/partial Art3 result reads. This file is the only output written.

## Missing decision and engine semantics

`agents/sherlock/rules.py:341–383` compares **one** ally's energy minus move cost against the visible enemy energy sum. `rammed` explicitly prevents a second ally from ramming the same tile. The rule therefore cannot select a pair whose individual members lose/tie but whose combined energy wins. Normal independent learned/rule actions can nevertheless happen to produce such a collision.

`agents/sherlock/joint_actions.py:45–87` requires changed movement sources and destinations to be more than Chebyshev distance one from every visible nonnegative-energy enemy. Its acceptance at line 116 requires a strict increase in **distinct** nominal known-point occupancy. Thus the failed pair coordinator deliberately excludes this combat mechanism. The missing decision is specifically: jointly commit two legal adjacent attackers to one currently occupied known point when their combined post-move energy beats the enemy aggregate despite neither doing so individually, accounting for allies already entering and the cost of vacating holders. It is not a need to rerun the occupancy coordinator.

Actual installed engine source checked at `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/lib/python3.13/site-packages/luxai_s3/env.py`: negative-energy units are removed before movement (228–232); movement is paid first (240–291); `original_unit_energy` is saved at 293; the aggregate maps receive that saved array at 462; strict aggregate comparison at486–499 chooses collision survivors. Ties remove both sides. Sap costs/damage, void and field gains do not change that collision comparison. Winning collision does not guarantee useful surviving energy/productivity after the rest of the step. No engine execution was performed.

## Archive count and concrete cases

Source: all 20 existing `experiments/analysis/continuous_20261021/loss_observation/*_player_*.jsonl.gz` files listed by its `manifest.json`: 6,060 records, of which 6,000 have a nonempty decision and nonzero `match_step_t` (20 games × 300 active decisions). `scripts/observe_loss_mechanisms.py:39–69,91–128` records legal visible enemy positions/energies, every friendly decision slot's position/energy, world-frame legal mask, move cost, known-point status and first-holder identity. These are sufficient for the following one-step **opportunity** count without truth inputs. All 20 compressed-input hashes match the existing manifest. This is an outcome-stratified historical diagnostic sample, not a general prevalence or strength estimate. Q-value arrays and full per-step terrain maps are not retained, so a learned-regret gate or complete alternative trajectory cannot be reconstructed.

Fixed counting definition: target is in `decision.known_point_tiles` and contains at least one visible nonnegative-energy opponent; attacker is one cardinal step away, has enough movement energy, and its recorded target-direction legal mask is true. Sum all visible active enemy energy at the target. Require at least two attackers, no available individual attacker with post-move energy strictly above that sum, and a pair whose sum is strictly above it. Exclude match-reset decisions. All coordinates below are world coordinates. A tile at one decision step is counted once, irrespective of alternative pair count.

- 2,040 visible enemy-occupied known-point tile-steps.
- 61 have at least two legal adjacent attackers.
- **10 joint-only tile-steps**, across 3 game files; every one has a winning pair (no case requires 3+ allies).
- **7** permit a pair that does not remove either recorded first holder of a known point.
- **6** additionally exceed enemy energy by **more than 10**, across 2 game files.
- Of those 6, **4 already have sufficient actual V3 incoming energy**, leaving only 2 missed nominal options. One opponent actually leaves; one stays. Requiring target enemies also to have been observed in the same position on the immediately preceding decision leaves **zero missed** tightly gated options.

Exact locations are decompressed JSONL line numbers under the loss_observation directory. M is one-based; t is recorded `match_step_t`. Energy is summed after movement cost, before Sap. “H” marks opportunities requiring at least one first holder; “N” passes the nonholder plus >10-margin restriction.

| File | Line | M/t | Target | Ally post-move energies available | Enemy sum | Actual V3 incoming sum | Gate |
|---|---:|---|---|---|---:|---:|---|
| `510858_player_1.jsonl.gz` |73|1/72|(12,19)|62,49|109|0|H|
| `510930_player_0.jsonl.gz` |168|2/66|(15,5)|138,118|138|118|H|
| `510930_player_0.jsonl.gz` |174|2/72|(14,3)|58,147|191|205|N|
| `510930_player_1.jsonl.gz` |66|1/65|(20,9)|88,88,30|108|206|N|
| `510930_player_1.jsonl.gz` |155|2/53|(17,8)|155,151,148|163|155|N|
| `510930_player_1.jsonl.gz` |166|2/64|(18,9)|69,75,57,150,150|165|300|N|
| `510930_player_1.jsonl.gz` |169|2/67|(18,8)|154,154|220|0|H|
| `510930_player_1.jsonl.gz` |174|2/72|(20,9)|67,155,49|216|204|nonholder, margin 8|
| `510930_player_1.jsonl.gz` |258|3/55|(20,7)|68,143|199|0|N|
| `510930_player_1.jsonl.gz` |261|3/58|(20,7)|82,150|168|232|N|

At line155, the admissible nonholder pair is UID 7/8 (155+151); UID 10 is a holder. The target enemy's actual action is DOWN and it vacates the target. Thus 306>163 is an observable possibility, not an actual collision improvement.

At **line258**, own UID 6/8 are both at(20,8), energies 69/144, move cost 1, both UP masks true, neither on a known point. They actually both move DOWN. UP+UP would contribute **211 against 199**, whereas neither 68 nor 143 wins alone. Enemy UID 9 is visibly at(20,7) and actually SAPs `[5,0,1]`; recorded truth after preserves its position there. This is one concrete missed joint collision opportunity under the opponent's recorded action. It is only a 12-energy margin, the enemy was not observed in that same position at the prior decision, and the archive does not establish a beneficial alternative trajectory. Enemy arrivals/reactions, later Sap/void/field damage, concentration and future point coverage remain material limitations. Truth/actions are offline diagnosis only and cannot be policy inputs.

`mechanism_probe_20261021/probe_v3_720.json` contains 120 per-game aggregate match summaries, not full legal observations. Its fortress images/aggregates identify a combat problem but cannot count this gate. The former pair coordinator's activation/funnel artifacts likewise retain aggregate stages/counters and cannot reconstruct collision opportunities; its recorded zero/rare activation does not reject or support this mechanism. The loss archive is the usable concrete input source.

## Overlap and next-step decision

The historical `ram` variant was negative (EXPERIMENT_PROTOKOLL line 165: −1.5pp on development). It uses the same stationary-target assumption, movement override and energy comparison, but excludes the new joint-only threshold by construction. `smart_sap` coordinates expected damage allocation rather than moving allied energy into one collision; because collision uses pre-Sap energy, simultaneous smart Sap cannot supply this missing threshold. `siege` relocates/waits at firing positions and lost point occupancy; its negative result warns against sacrificing productive holders, but is not a test of pair collision selection. None of these differences imply strength gain.

**No additional live passive probe is recommended from this bounded review.** The fixed existing 20-game sample has already supplied the useful passive feasibility count: only 2 missed nonholder/>10-margin nominal options, only 1 against an actually stationary target, and 0 missed if prior observed stationarity is required. Relaxing the gate or starting new games to find more examples would be speculative at this stage. Do not retune margins from these examples or replace the current study. This verdict is limited to the evidence and this mechanism; it does not claim coordinated collision attacks can never help.
