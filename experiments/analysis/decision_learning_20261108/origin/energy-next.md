# SAP energy and learning-contract fallback

08 November 2026; read-only source review and standard-library analysis of existing records. No tests, models, new games, or repository edits. Files: `/tmp/sherlock-energy-next.py` and `.json` contain calculation,1053 holder-SAP records,324 off-mask records, and12 source hashes.

## Decision

The most useful next energy diagnostic is an **exact one-transition automatic-holder-SAP cancellation probe**, measuring both teams' point occupancy and the actual energy phases. It should precede another reserve/reward training variant. The current data do not support calling low holder energy self-inflicted SAP waste. The action-mask mismatch is real but is not by itself a demonstrated broken optimizer or invalid-action bug. A separate, narrower reward-semantic inconsistency exists: unknown fog-hit outcomes are always treated as estimated misses.

## What the old V14 traces actually show

Sources: `experiments/analysis/continuation_20261102/targeting/*.jsonl.gz`; six selected loss games versus six historical controls, all three matches, dependent observations and unmatched controls.

| Observation | Loss group | Controls |
|---|---:|---:|
| Sole living holder SAP actions | 586 | 467 |
| Of these, masked Q originally chose STAY | 558 | 310 |
| Of these, final SAP was outside original SAP mask | 222 | 63 |
| Same UID and position in next same-match observation | 580 | 452 |
| Next energy negative in that subset | 32 | 15 |
| Next energy below SAP cost in that subset | 217 | 172 |
| Arithmetic pre-energy−SAPcost+observed field <0, all holder SAP | 4 | 5 |
| Negative next energy despite nonnegative arithmetic balance | 32 | 15 |

All47 observed negative-next-energy cases started with Q-STAY and ended SAP. Only3/2 were off-mask fogSAP cases. In26/11 cases, adding the SAP cost back to the observed negative next energy would cross zero. **That arithmetic is not a counterfactual survival estimate:** changing energy/action can alter other engine phases and interactions.

Example831006/P1, observation47, UID3 at(15,4): pre-energy46, SAPcost39, observed field+8, arithmetic balance+15, next energy−11. Two armed visible enemies were within Chebyshev(sap_range+1). Other harm is consistent with the observation, but source, timing and avoided-harm effect are not identified.

For same-position observations, the residual `next_energy−(pre_energy−SAPcost+current_field)` is negative143/126, zero431/317 and positive6/9. This residual is **not enemy damage**. It mixes field timing/drift, clipping, nebula, void, collisions, enemy SAP, and potential slot identity effects. UID/position equality is not a guaranteed continuous life. Current true engine phases and complete opponent action arrays are absent from these targeting traces; `targeting_audit.md:43` explicitly documents null phase reconstruction. `mechanisms.json` is aggregated older reconstruction, not enough for per-decision causal labels.

## Narrow new energy diagnostic, if HOLD fails

Use a fixed small set of already known trajectories. At predeclared **sole-holder, Q-STAY→finalSAP** decision points, branch an identical engine state once with the existing joint native action and once with only that holder's SAP replaced by STAY. Keep both teams' other actions and RNG state identical. Record post-SAP, collision, void, field-energy, and scoring phases, own/enemy productive point counts, damage denied to enemy holders, and energy. This is a local controlled label, not a full-game win estimate.

As a diagnostic stratum, visible-target SAP with pre-energy<2×SAPcost contains185/151 recorded cases, including25/11 negative-next-energy outcomes. Do not simply implement that threshold as a policy: it reproduces the old reserve idea. A genuinely different later rule would require evidence that **a public incoming-damage estimate predicts SAP losing an otherwise surviving scoring holder, while cancelling does not preserve an opposing scorer that the shot would disable**. The labels should first determine whether that tradeoff exists often enough. Hidden state may evaluate labels, never become policy input.

## Closed experiments that must not be silently repeated

- `pt_sap_reserve=25/60`: −0.5/−4.5pp on historical development; blanket `pt_hold` −2pp (`docs/EXPERIMENT_PROTOKOLL.md:280`).
- `sap_reserve_k`, `sap_relevant`, `sap_still_all`, `holder_guard`, lethal dodge: no useful gain in V8-era work (`EXPERIMENT_PROTOKOLL.md:289`). `sap_reserve_k=.5` was again weak on V10 (`docs/ARBEITSSTAND.md:1332,1350`).
- `smart_sap`/early fog variants: historical −3 to+1.5pp, left off (`docs/ARBEITSSTAND.md`,19.10 entry table). Do not revive broad coordinated SAP target scoring as a new idea.
- Global SAP0 ablation already removed both hit bonuses and miss penalties; student/A2 studies produced no V14 replacement (`docs/AKTIONSSCHUELER_20261104.md:65`, `docs/SCHUELERNETZ_REWARD_20261104.md`).
- Holder SAP, automatic artillery, and the once-successful overkill guard are already present. New evidence must identify a remaining interaction rather than infer that all forced SAP is bad.

## Action/controller representation: demonstrated mismatch, no narrow proven optimizer bug

In all active-unit trace decisions, final actions outside the network mask occur255/69 times; all324 are **Q-STAY→nativeSAP while mask[SAP]=false**. Normal SAP masking requires a visible heuristic target (`agents/sherlock/main.py:1471–1472`). Fog SAP runs afterward with its own target and affordability checks and writes final SAP to `_prev_actions` (`:449–455`, `:651–671`). This behavior is already documented (`docs/AKTIONSSCHUELER_20261104.md:67`; prior student collections776/801 off-mask final actions).

Replay deliberately stores final canonical actions (`main.py:1555–1563`). TD loss gathers the final action's unmasked Q, while bootstrapping over next network-mask actions (`:1583–1594`); thus an off-mask current action does **not** create an infinite loss or wrong array index. Student imitation/anchor loss imitates teacher Q only on the legal mask (`scripts/student_action_distill.py:72–85`), rather than using an illegal final class as a masked cross-entropy label. No such broken-loss bug is demonstrated.

There is a learning-contract concern: outcomes of the controller's STAY→fogSAP path update Q(SAP), whereas the decision selecting that path was STAY, and future SAP may remain masked. Choosing proposed-action or executed-action semantics requires an explicit controller-aware Bellman design. Blindly relabeling every executed action as the original proposal, or unmasking SAP without exposing a valid target to the selector, can introduce a different bug. Treat this as a distinct research design, not a one-line correctness fix with promised strength.

## Narrower demonstrated reward-semantic inconsistency

`main.py:671` returns `(dx,dy,0)` for every selected fog shot. The0 propagates to `_sap_hits` at`:592–596`. `reward.py:148–150` maps0 to **−w_sap_hit**, although fog's hit outcome is unknown and the target was chosen for positive estimated expected damage (`rules.py:218–251`). With the current default weight.3 (`config.py:498`), every such training shot receives−.3 from this component irrespective of its real hit outcome. There is no special unknown category.

Independent pure-CSV check of older actual V12 fog shots in `experiments/analysis/battle/v12_fog_hits_devA.csv.gz`:21170 fired;7203 direct hits;15387 any direct/splash hit;5783 no hit, using saved post-movement truth. This is older V12 offline evidence, not V14 performance or current training exposure. It demonstrates that fog0 is not an observed miss; it does not prove neutralizing the reward improves the learner.

A narrower possible change than SAP0 is to distinguish **unknown fog outcome** from an estimated miss and make only the unknown hit-shaping contribution neutral, preserving other SAP shaping and all inference behavior. First audit current training records for actual fog exposure and the signed term; then any treatment needs an isolated paired training study. Existing scalar replay rewards cannot safely be rewritten without the corresponding contexts/provenance. This is a precise candidate semantic repair, but not a confirmed explanation of failed training or justification to restart SAP0.
