# Read-only ensemble-scale review — 08 November 2026

## Finding and decision

**Raw-Q averaging can give greater decision influence to members with larger action-dependent Q gaps, but there is no evidence here that mis-scaled members explain V14's remaining losses or recent ensemble failures.** A scalar offset common to all six actions cannot dominate the argmax. Reward heterogeneity exists in the documented lineage, but it is chiefly a different training objective, not an established multiplicative scale mismatch. Q gaps are estimated return differences, not calibrated confidence or correctness probabilities.

This question is **not a new hypothesis**: legal-Q scale diagnostics were executed in October, including 30 October; a more relevant member/remainder comparison was proposed explicitly on 3 November. Blind normalization, voting, or learned weighting is not justified by the available evidence. I do not recommend starting another ensemble experiment from this review, and do not propose changing the active Fog study.

The only artifact written for this task is this report. No repository/source/HEAD/weight writes, models, Torch imports, repository imports, games, tests, training, or subagents. Read commands and Python standard-library JSON/gzip arithmetic only. Observed HEAD: `a3111c3`; existing/active operational files were left untouched. Project handoff and experiment protocol were read; their closed-study constraints remain applicable.

## 1. What current inference actually does

- `agents/sherlock/main.py:338–349`: compute the principal net and all extras, then **one unweighted arithmetic mean per net** at line 343; mask illegal actions afterward, then argmax. There is no member normalization, voting, per-member temperature, uncertainty correction, or learned member weight in this path. Training omits the extras (`not self.training`).
- `agents/sherlock/model.py:66–72`: dueling output is `V + A - mean(A)`. The same state's value-head output is an action-common offset and cancels in every action comparison. Likewise any independent per-member common offset cancels when ensemble action scores are compared. Merely seeing one member with Q around 100 and another around 10 establishes nothing about dominance.
- For two legal actions a,b, the decision margin is `mean_i[Q_i(a)-Q_i(b)]`. A positive multiplicative change to one member preserves that member's rankings but scales its contribution to this margin. That is the precise mathematical route for scale dominance. It is a possibility, not a measured failure.
- Masking and later rules still matter: `main.py:347–349` separates raw/masked choices; subsequent rule processing can override them. A hypothetical alternative ensemble argmax is not automatically a different final action or improved game outcome.
- `scripts/build_ensemble.py:27–28,59–73`: compatibility checks concern architecture/input/play semantics; reward weights are not required to match. The builder preserves one outer config (optionally replaced by `--cfg-from`) and stores source checkpoint paths, not an independently attached training config for each member. `main.py:1668–1687` loads extras from state dictionaries and dimensions. Therefore the current outer checkpoint config does not describe every member's original reward history.

## 2. Member lineage and reward provenance are substantially known

Existing independent presentation provenance, `docs/presentation/source/ENSEMBLE_BATTLE_0611_20261104.json`, records the V14 checkpoint hash, 36 distinct member hashes, identical architecture and 152,967 parameters per member (lines 1–88), ordered sources (89–112), original training metadata (113–569), and 18 matched fine-tuning chains (571–1237). It records first18 equal V10 and matching original/descendant source sets at 1239–1240 and 1265. These are existing model-audit results; I did not reload weights or independently recalculate tensor identities today.

Zero-based member order in that record:

| Members | Recorded source / history | Original reward distinction |
|---|---|---|
| 0–5 | `20261019_full_rules_s0..s5` | Standard shaping; `w_opp_points=0` |
| 6–11 | `full_rules_s10_sol70`, `s11_sol70`, `s6_sol70` … `s9_sol70`, in that order | Same reward; different Solution-heavy training distribution |
| 12–17 | `20261019_full_rules_opp_s12_pool..s17_pool` | Additional opponent-points penalty, `w_opp_points=1` |
| 18–35 | Ordered descendants of members 0–17, fine-tune seeds10–27 | Each +1500,+2000,+2000 games =5500; all fine-tune stages use `w_opp_points=0` |

I parsed all18 original manifests and all54 named fine-tune-stage manifests without loading checkpoints. Original gamma is0.99, reward_fix true, hidden256 for all18; opponent penalty is0 for12 and1 for6. All54 fine-tune stages have the same checked signature: gamma0.99, reward_fix true; point1, shape0.5, explore0.3, energy0.1, stack0.3, death0.5, match2, discovery0.5, sap_hit0.3, opponent_points0. Example direct evidence: original member12 `experiments/runs/20261019_full_rules_opp_s12_pool/manifest.json:18–69`; its final descendant `experiments/runs/20261029_ft3_v10_s22/manifest.json:179–195`. Full source/chain mapping is in the provenance JSON, not inferred from filenames alone.

**Interpretation:** original12–17 and their descendants have experienced different reward objectives over their histories. Opponent-points subtraction changes state/action preference, not just units of reward; a division by an empirical span would not make those objectives identical. Even all-equal reward coefficients do not guarantee equal learned action margins because visited states, training ages, opponents and approximation error differ. The 18 descendants share ancestry with the originals; these are not36 independent restarts.

Limits: known lineage is based on manifests and earlier hash audits, not independently re-proved initial/final checkpoints today. The earlier V3 audit itself states that completed run budgets need not equal a selected historical checkpoint's training age: `experiments/analysis/autonomous_20261020/training_followup_20261021/v3_training_lineage_audit.json:3`. No claim of fully recovered optimizer/replay history per current member.

## 3. Already tried / already proposed

| Evidence | What actually happened | Meaning / boundary |
|---|---|---|
| `experiments/analysis/autonomous_20261020/exploration_qmargin_diagnostic.json:1–6,1031`, metrics from1282 onward | Existing1024 eligible replay-next-state diagnostic: per-net legal spans, top-two gaps, centered RMS, raw legal argmax agreement; old18-net basis plus control/slow new members. Explicitly descriptive, no normalization or selection. | Generic legal-gap diagnosis is already done. One control replay distribution, excludes terminal/one-action states; not V14/current new-member proof. |
| `docs/ARBEITSSTAND.md:1154` | Existing20,000 replay-state mixture check: mean legal spans V10=1.18, ft2=1.06, ft3=1.01, ftrl=1.08; mixed choice agrees92.8% with V10 and91.6% with ft2 alone. Historical conclusion: no half dominated; normalization not worth pursuing. | Directly relevant counterevidence to a large group-wide scale mismatch in the construction era. Raw per-member arrays for this20k check were not found in searched analysis paths. Similar means cannot exclude rare/local member dominance. The original conclusion is broader than these summary numbers alone prove. |
| `scripts/decision_trace.py:121–153`; `docs/ARBEITSSTAND.md:1039,1324` | Existing vote-vs-Q-average observation. V11:36,209 unit decisions, average differs from a maximal-vote action in about5.87%; V12 about5.75%. | **Voting was measured as an alternative preference, not deployed or tested as a stronger policy.** The summary counts a tie for highest votes as agreement (`agree==top_vote`, line76), so “majority” is really plurality/tied plurality here. |
| `docs/RESCUE_NACHTRAINING_DIAGNOSE_20261103.md:57,67` | Explicitly documented unknown Q-scale explanation and proposed fixed-state comparison of member18/C/R against unchanged35-member remainder, centered legal margins/ranks and final-action changes. | This exact broad next-step suggestion already exists. It was a proposal, not a completed experiment; do not relabel it novel or measured. |
| `docs/ABSCHLUSSBERICHT_20261104_NETZE.md:10–25` | FO42: equal-weight current36+six old FO nets. Confirmation panel+0.104pp, Solution+1.125pp with intervals including0; three of seven release conditions failed. | Closed composition/size study; no proof normalization would have rescued it. |
| `docs/ENSEMBLE_ABSCHLUSS_20261108.md:7–33,46–48` | Six real newly trained members; A39/B39/ALL42 fail compact nomination; ALL42 Solution40/40 but direct18/40. Fresh REPLACE36: panel−2.67pp [−6.25,+0.92], direct51.5% [44.5,58.5]; six of ten gates failed. | Closed study; no reopening, new threshold, post-hoc weight fitting or substitution from these results. Its closing question about altered action preferences is already on record. |
| `docs/AKTIONSSCHUELER_20261104.md:100–108`; `docs/superpowers/specs/2026-11-04-action-student-design.md:15–16` | Action-student objectives used a single teacher-derived training RMS and value-only calibration before RL. | Actual calibration, but of a distilled student's loss/value head, **not** member-wise inference normalization. It cannot be cited as a V14 normalized-ensemble trial. |

Search of agent/scripts/docs and analysis Markdown/JSON found no completed strength trial of member-normalized V14 Q averaging, voting-based V14 play, learned per-member weighting, or epistemic-uncertainty weighting. This is a bounded repository finding, not proof no external or undocumented trial occurred. CNN mixing/temperatures and normalized coordination regret are different mechanisms, not these interventions.

## 4. Can existing traces answer the question without loading models?

**Only an illustrative calculation, not a representative dominance diagnosis.**

1. `scripts/decision_trace.py:138–153,170–171` retains all-decision summary statistics but serializes per-net Q only for the first matching example in each of five categories. It rounds Q and features to three decimals. Saved36-member files are `experiments/analysis/decision_trace_20261030_v11.json` and `decision_trace_20261031_v12.json`; five `q_per_net` arrays each. I compared the arrays: all five are exactly duplicated between these two files, so this is **five distinct selected states, not ten independent states**. They are historical V11/V12 situations, not a population of current V14 losses or new A/B/Fog-member outputs.
2. Rich later traces capture member forwards transiently but discard member outputs: `scripts/student_failure_trace.py:169–176,191–199` writes only ensemble `raw_q`; `scripts/targeting_probe.py:401–408` likewise averages before writing `q_values` at212. A standard-library read of the first nonempty V14 row in `experiments/analysis/a2_anchor_20261104/traces/04_V14_866000_player_0/observed.jsonl.gz` confirmed only mean `raw_q`, features, mask and network/final actions, not per-member Q.
3. Means cannot be inverted into36 member outputs. Features/observations would allow a later model-forward replay, but that explicitly violates this task's no-model-load restriction. Old replay buffers also need models to compute current per-member Q. Historic statistical summaries cannot supply missing joint state-wise member contributions.

### Small completed descriptive arithmetic

To make the feasibility statement concrete, I decomposed the winner-vs-runner legal-Q margin on the five saved V11 examples using only recorded numbers. For the existing `uneinig` example (seed690000, side0, step114, uid2; `decision_trace_20261030_v11.json:1435` onwards), right wins over down by about0.041861. Votes: right12, down15, stay9. Contributions to that **ensemble** margin:

- Original0–11: +0.085639
- Opponent-penalty originals12–17: −0.054222
- All descendants18–35: +0.010444

Removing member1 alone changes the recorded mean preference from right to down: remaining35 mean Q(right)27.075857, Q(down)27.081571. Member1's right-minus-down gap is1.707. The original mixed result and this leave-one-member result are robust to the three-decimal rounding at these margins (pairwise mean rounding bound approximately0.001).

This is **local cancellation**, not proof that member1 is globally mis-scaled or wrong. Its common Q offset is irrelevant; member1 is not one of the six original opponent-penalty members. In the other four selected examples, no single-member removal reverses the winner/runner ordering. These curated examples supply neither action counterfactual labels nor game outcomes for removals. They cannot establish frequency, causal usefulness, superiority of votes, or a valid weight choice. Later rules also override two of the five example actions.

## 5. Recommendation

**No new diagnostic experiment recommended now.** The relevant generic scale diagnostic is already documented/executed, the more specific fixed-state member/remainder comparison was already proposed, and existing representative traces lack the per-member outputs required for a novel informative no-model version. The small historical arithmetic above exhausts what is defensibly available under the current restrictions; do not turn it into a candidate or fit weights to it.

Continue the currently frozen, bounded Fog study unchanged; prioritize its planned compact comparison once models qualify. One possible **post-freeze** follow-up, already proposed in substance on3November rather than novel: choose one fixed existing V14 trace bank before inspecting outputs, replay recorded feature rows through baseline member18, the completed CONTROL/NEUTRAL members and unchanged35-member remainder; report legal centered margins, signed member contributions, and ensemble-argmax changes separately for recorded Fog/ordinary contexts. No new games are needed for that descriptive calculation, but it requires model loads, is impossible from current mean-only traces, and cannot determine final-rule/game-outcome benefit. Do not optimize weights or reinterpret old performance cards from it. This report does not initiate that follow-up, calibration, normalization or any new strength trial.
