# Opt-in neutral shaping for unknown fog hits

08 November 2026. Static review plus existing JSONL aggregation only. No tests, model loading, games, repository edits or commits. Historical source/records remain unchanged.

## Minimal safe design

Add `AgentConfig.fog_unknown_reward_neutral: bool = False` beside SAP shaping configuration. Retain `w_sap_hit`, `_fog_sap`'s existing `(dx,dy,0)` tuple, every mask, rule, target and native action unchanged. The new flag affects only reward computation during learning; inference never branches on it.

**Do not return `None` as the third tuple member.** Consumers assume a number: `_artillery_ok` does `int(sap[2])` (`main.py:750`), final accounting does `hits>0` (`:598`), `reward.py:149–150` compares/multiplies it, and the old reward-audit wrapper compares `hits>0`, `hits<=0` and uses `max(1,hits)` (`scripts/student_reward_train.py:246–269`). A negative sentinel also unnecessarily overloads the hit-count contract and can change optional artillery thresholds if put into the tuple.

Use explicit **final-shot provenance**, not merely "fog helper called":

1. Reset `_sap_unknown` (set of canonical UIDs) with `_sap_hits` at initialization and each `_act`, including match resets (`main.py:180,317–318`).
2. For each unit initialize local `fog_origin = None`. In the existing fog branch, call the helper once as today; when a genuine fog tuple replaces the ordinary SAP target, retain that exact tuple object as `fog_origin`. Do not change selection or duplicate calls/RNG work.
3. Only at final emitted SAP (`main.py:591–598`) add UID to `_sap_unknown` if `sap is fog_origin`. Keep `_sap_hits[uid]=hits` exactly as before. If later rules cancel SAP, move, or replace the tuple, no unknown final event is recorded.
4. Give `unit_rewards` a backwards-compatible optional keyword such as `unknown_sap=None`. With the opt-in flag true, final action SAP and UID in that set, omit **only** the SAP hit-shaping term. Known positive estimates retain bonuses; explicit known0 retains the old miss penalty; all point/death/energy/potential/terminal terms remain identical. Old five-argument callers default to existing behavior.
5. `_update` passes the new keyword for the new opt-in path. Preserve the old five-argument call when flag false to keep historical audit wrappers compatible. The new study needs its own provenance-aware reward audit; do not invoke old SAP0 accounting against a changed contract.

The tuple identity must be checked at emission: fog can be followed by `end_sap` replacement (`:496–501`), dodge/movement (`:535–545`), overkill cancellation (`:571–575`), holder guard (`:577–582`), and smart-SAP retarget/cancellation (`:583–587`). An early boolean alone would incorrectly neutralize later known shots. Even equal-coordinate retargeting is a new origin if its hit estimate was recomputed.

## Consumers and compatibility

- `_fog_sap` (`main.py:651–671`) produces0; `_act` emits native SAP and populates `_sap_hits` (`:591–598`); `_update` consumes both (`:1547–1548`).
- `unit_rewards` is the actual semantic consumer (`reward.py:107,148–150`).
- PPO recorder calls `unit_rewards(...agent._sap_hits)` (`ppo_agent.py:62`); PPO's own action loop stores visible-target numeric counts (`:145–201`) and has no fog override. Optional keyword preserves that path.
- `student_reward_train.reward_audit` consumes numeric estimates and wraps `main.unit_rewards`; it must remain unchanged for historical flag-false studies. A new audit must support the optional provenance input and verify `treatment−control = +w_sap_hit` exactly for final unknown SAP when shaping is enabled, zero otherwise.
- Generic `scripts/metrics.py:77–86` independently recomputes visible SAP opportunities from emitted actions; it does not consume `_sap_hits` and must not be relabeled as unknown provenance. `effect_counters.sap_hits_est` is `hits>0`, also unchanged.
- Distillation/anchor loss and replay action classes are unchanged. Do not combine this experiment with proposed-action relabeling, mask changes, or controller-aware TD targets.

## Proposed focused tests (not run)

1. Default/absent flag and known positive/zero hit dictionaries produce exact old rewards; unknown keyword absent is backward compatible.
2. True flag + final unknown SAP changes only the hit term by+w; zero SAP weight, shaping disabled, non-SAP, deaths and terminal transitions retain all other terms.
3. Fog survives to emission → unknown; fog later replaced by known `end_sap`/`smart_sap` → known; cancelled/moved/no final SAP → no unknown. Test equal-coordinate replacement as well as different coordinates.
4. Next unit/frame/reset cannot inherit stale provenance. Test both canonical sides.
5. Synthetic action-path fixtures compare native action arrays, `_prev_actions`, masks, numeric `_sap_hits`, and legacy counters flag false/true. No full games needed for these tests.
6. New paired-prefill audit proves identical actual actions/state streams and identical q/target/optimizer, with only unknown-shot reward/replay-r differences. Final action-to-replay audit remains active.

## Actual prior training exposure: recorded counts, not inference extrapolation

Aggregated original `experiments/runs/20261104_action_student/rl_seed{27,28}/runs/control/rollouts.jsonl`, phase=`train`:

| Source | Games | SAP transitions | Recorded estimated_misses |
|---|---:|---:|---:|
| A2 control27 | 160 | 11859 | 1061 |
| A2 control28 | 160 | 12711 | 1295 |
| A2-anchor control25 | 160 | 12284 | 1472 |
| A2-anchor control26 | 160 | 12718 | 1884 |

Anchor paths: `experiments/runs/20261104_a2_anchor/seed{25,26}/engine/control/runs/control/rollouts.jsonl`. These are actual recorded reward-audit training events, excluding prefill/validation. The matched A2 prefill40 games record451/435 estimated misses for seeds27/28; anchor-prefill records393/369 for25/26. Therefore exposure is demonstrably nonzero in historical training. **These counters are named estimated_misses, not explicit fog-origin events.** In the reviewed action implementation fog is the zero-hit producer while ordinary visible SAP estimates are positive; identifying every historical0 as fog relies on source/config lineage, not a stored origin label. New runs should record explicit final origin rather than treating these as gold labels.

Later ensemble training also records actual nonpositive-estimate shots: `20261107_diversity_r1_{A0,A1,A2,B0,B1,B2}/rollouts.jsonl`, training-only `effect_counters.sap_attempts−sap_hits_est` =31611,32961,30466,22705,22138,23963 respectively. This is not a measured count of physical misses. None of these counts comes from inference diagnostic cases.

## Small matched study, two seeds

**Recommended parent for a reward-mechanism pilot: the already saved A2 final distilled single network**, with q/target identical and no inherited Adam or replay. It is the strongest known student baseline, has demonstrated exposure, and fits the existing512-wide source contract (`student_reward_train.py:98–126`). Do not start from prior CONTROL/SAP0/ANCHOR end weights. Alternative for production-member relevance: fix V14 component18 before outcomes, same component for both seeds; reuse the component extraction/checkpoint preparation pattern in `ensemble_diversity_train.py:137–159`. Its256 width requires a new generic validator, not bypassing the existing student512 guard. Do not compare multiple parents in this pilot.

Use a **new study wrapper over `scripts.finetune`**, not restart or mutate closed `student_reward_train` or `student_anchor_train` jobs. Reuse their final-action, paired-prefill, isolation, output protection and completion patterns. Two predeclared RNG seeds × control/treatment =4 arms; same parent, fresh identical Adam, fresh replay, paired opponent/map/side schedule. Only intervention is the new flag; w_sap_hit remains.3. No teacher anchor, no SAP0, no architecture or inference-rule change.

Small fixed budget:40 prefill +80 learning games per arm, final checkpoint only (half the earlier160-game learning budget;480 total prefill/learning executions). Preserve A2 training LR1e−4, epsilon.05, train_every2 and existing mix60%Solution/20%square/10%default/10%rush. Do not add rescue-training changes. This is a mechanism pilot, not sufficient strength confirmation. If using component18 instead, predeclare LR5e−5 consistently in both arms, as in the existing ensemble training pattern.

Reserve genuinely new training/prefill/validation card blocks before run; `finetune` uses base+seed×10000, prefill+5000 and separate validation (`finetune.py:51,111–113,208,222`). Use the scoped base override/restoration pattern already in `ensemble_diversity_train.py:281,397,436`; do not reuse old closed-study seeds just because RNG seed numbers match. Initial and final diagnostics on four fixed validation maps against default/Solution, both sides, cost32 executions per arm (=128), giving **608 total executions** before any separate fresh strength comparison. Known validation is diagnostic, not checkpoint selection. Two processes maximum, no tests concurrently.

Before gradients, require explicit unknown-shot count>0 in each paired prefill and exact reward-delta/accounting/passivity checks; otherwise terminate that pilot as exposure failure rather than training or changing conditions. After fixed budget report each seed's treatment−control, actual unknown shaping mass, occupation/energy and finite learning audit. Any fresh V14 promotion assessment needs its own prospective modest budget; no automatic broad ensemble search or reopening failed SAP0 studies.
