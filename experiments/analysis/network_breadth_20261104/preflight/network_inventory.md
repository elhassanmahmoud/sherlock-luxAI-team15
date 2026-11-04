# Bounded checkpoint inventory — 04 Nov 2026

Read-only inspection by inventory subagent. No games, training, tests, source edits or checkpoint writes. Python used: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`; checkpoint reads used CPU and one Torch/BLAS thread. Read `AGENTS.md`, project rules in `CLAUDE.md`, newest `docs/ARBEITSSTAND.md`, targeted historical logs/manifests/CSV. Repository root R below means `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15`. Indices are **zero-based in [checkpoint['q']] + checkpoint['ensemble']**, not directly in `ensemble`.

## Main finding

Current V14 really contains 36 distinct network tensors. File `R/agents/sherlock/weights/agent_p0.pth` SHA256 is `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. Members 0–17 are the original V10/V3 networks; 18–35 are their FT3 descendants. **Adding FT3 to V14 would merely repeat 18 existing networks.** Existing configs/release files are not independent network families.

A filename inventory covering all seven `/Users/moayedshawesh/Desktop/KI/sherlock-*` checkouts found **no separate FT3, FT5, FTRL, league, ftv8 or ftold checkpoint path**. Main checkout has 68 actual `.pth` model files (the 69th glob result is Python's `distutils-precedence.pth`), many duplicates/release copies. External storage and remote machines are outside this bounded inventory. Current frozen-study panel explicitly says historical `league_nets6`/`threat6` are missing and uses V3/V7/V10/V13 instead (`experiments/analysis/final_battle_20261103/performance_confirmation/provenance/final_battle_plan.md:42`).

## Families, actual availability and provenance

| Family | Actual local network access | Historical provenance / limits |
|---|---|---|
| Original V3/V10 | V14 indices 0–17; also historical release files | Three groups of six: original rules, sol70, opponent-pool. Config variants V3/V7/V10 are not new networks. |
| FT3 | **V14 indices 18–35**, 18 distinct descendants | `R/experiments/runs/20261029_ft3_v10_s10`–`s27`: 18 manifests status done, final 2,000-game stage; chained 1,500 + 2,000 + 2,000 = 5,500 finetuning games each. Pipeline builds seed order 10..27, so seed s maps to V14 index s+8. `battle_ft3_18.pth` and individual source weights absent; recover inference tensors from V14. |
| FTRL | **Absent locally**, 18 completed manifest/CSV records only | `R/experiments/runs/20261029_ftrl_v10_s10`–`s27`, 1,500 games each, 50% pool (V10/old3/mix36/V3/V7), 20% Solution,20% square,5% weak,5% default. Related but different training branch from original V3 networks; not a new initialization family. |
| FT4 | Absent locally | 18 completed descendants of FT3, +2,000 games each. Prior 36/54 mixtures failed admission, details below. |
| FT5 | **No completed FT5 family ever existed** in recorded history | Only s10–s15 started, stopped at 1,425–1,450/2,000 games; validation through1,000. Six manifests have no done status; s16–s27 never started. `battle_ft5_18`, `mix36e_as`, `mix54e_as` never built. Partial checkpoint paths are absent here. ARBEITSSTAND lines675–687. |
| League | **Absent locally**, six completed records only | `R/experiments/runs/20261026_full_rules_v10_s73_league`–`s78_league`, 4,000 games each, independent starts73–78, league opponent curriculum. `experiments/ensembles/league_nets6.pth` and `league_mix24.pth` recorded as gitignored on Mahmoud's machine, absent here. |
| FO6 | **Available** as `R/experiments/candidates/all24fo.pth` indices18–23 | Six additional distinct 79-feature/256-hidden DQNs, source runs `20261020_full_rules_fo_s30_sol70`–`s35_sol70`, each4,000 games with70% Solution and `far_opp=10` during training. Original18 in this bundle are not identically ordered to V14; extract only18–23. |
| Exploration control3 / slow3 | Available in `R/experiments/candidates/exploration_s47_49_fixed_ensembles/control3.pth` / `slow3.pth`, indices0–2 | Three fresh starts47–49, 3,000 games each. Control and slow-decay paired; all six distinct from V14. Both families already had negative/no-benefit historical evidence. |
| Historical old3_sym3 | Available `R/experiments/releases/20261020_old3_sym3/agent_p0.pth`, indices0–5 | Six distinct 79-feature nets, none identical to V14. Original/symmetry era; much weaker old rule set, unknown value after V14 config. Not recommended just to inflate count. |
| Recent single finetunes | Main has `R/experiments/runs/20261101_nov_info_{control,discovery}_s9/weights/agent.pth`; `R/experiments/analysis/continuation_20261102/training/first_wave/{adapt18,control18}/end.pth`; newer final-study files in followup checkout | Related descendants, not independent families. Existing frozen nominees/studies remain closed; do not recycle rejected CONTROL/FT18/P/PAIR/Z/R candidates into another confirmation. |
| CNN/PPO | Available `R/experiments/candidates/cnn2_ppo0040.pth`, `cnn3_bc.pth`, `cnn3_ppo0050.pth`, `cnn3_ppo0060.pth` | Genuine different architecture but historical73%-level vs Solution (older setting). Not compatible with simply appending DQN state dicts; needs separate model/inference path. Not a promising same-day larger-DQN option. |

## Small single-network development shortlist

Use **one tensor only and V14 inference config** to isolate network count. These are new singleton constructions, not a retest of the rejected FT18 ensemble. Historic per-member validation is only16 games on the same eight old cards500000–500007 and V10 rules, so it may nominate candidates but cannot certify excellence or generalization.

| Candidate | Exact tensor source | Historical FT3 final Solution / default |
|---|---|---|
| S28 (first choice to investigate) | `R/agents/sherlock/weights/agent_p0.pth`, index28 = FT3 seed20 | 16/16 Solution,16/16 default |
| S19 | same, index19 = FT3 seed11 | 15/16,16/16 |
| S26 | same, index26 = FT3 seed18 | 15/16,16/16 |
| S34 | same, index34 = FT3 seed26 | 15/16,16/16 |

To keep search bounded choose S28 plus at most two of the three ties **before fresh outcomes** (all three are equivalent at this coarse evidence level; no reason to imply one beats another). Seed10/index18 is a useful predefined representative if avoiding selection by old validation:14/16 Solution,16/16 default. Do not mistake `target_q` or the optimizer for extra inference networks. Keep old sources untouched and construct experiment artifacts separately.

Per-network fingerprints measured by sorted state-dict key + shape + dtype + raw CPU tensor bytes (this is an inventory fingerprint, not the project's possibly different tensor-hash convention):
- index28: `f29e2c56f46f34c8c9db5b5e290f4a71fbc91a2fdeb4886f34f87ee10619c88f`
- index19: `dd9b31d7b388bc5934818fa45b9ae8d62238d6f60f2c129ce59ba8a80f48e189`
- index26: `00fb006630f71711208e41ba9ce1b567eeb29e328f68cfaef5eb1bd63cbb6d5e`
- index34: `ab75ee9c4edfde57901bfacd6cb8454e52cc8de006bf449e355fd91bad992fd3`

## Genuinely larger candidates feasible from these bytes

1. **FO42:** V14 indices0–35 + `all24fo.pth` indices18–23, equal mean, V14 config. Verified **42 unique networks**, no duplicates. Best available local larger-family candidate, but only modest historical rationale: the old all24fo vs all18_fo10 comparison was +2.75pp [−1,+6.5] on400 Solution games, not established advantage. FO6 is independently trained and gives a genuinely different family.
2. **CTRL39** (secondary/low-priority): V14 + control3 indices0–2, verified39 unique. Much weaker rationale: old V3+control3 was85% vs V3 85%, Δ0[−7.5,+7.5]. Current V14 config could change the result, but the prior should be modest.
3. **FO45** (optional if more than one larger candidate needed): V14+FO6+control3. Distinct source families; verify combined uniqueness in builder before use. Lower priority than FO42; avoid exploding combinations.

Do not recommend V14+FT3 (=54 slots but only36 unique), any whole `all24fo` concatenation (=duplicates original18), a config-only release variant, or old3/slow3 solely to satisfy a network count. A future **V14+FTRL18** would be54 genuinely changed tensors if obtained and identity-checked, but FTRL shares initial ancestry with original18 and historical larger mixture already failed fresh selection. League6 would add six independent starts if retrieved, but neither family is present now. Do not wait on nonexistent FT5_18.

## Already failed related paths (historical; not new tests)

- Latest FT18 singleton-family ensemble: failed four/seven confirmation gates04Nov; overall panel−0.9167pp, Solution755/800 vs761/800. Closed; does not determine any individual member's strength.
- `mix48_as` (V10 + ft2_18 + ftv8_12) and `mixrl54_as` (V10 + ft18 + FTRL18):30Oct selection panel R gains+1.31/+1.38 below+1.5 admission gate. Neither confirmed; do not describe larger-is-better.
- `mix36d_as` (original18+FT4): mean6 +0.81[−1.14,+2.81], direct48.3%; `mix54d_as` (original18+FT3+FT4):−0.61[−2.64,+1.47], direct57.7%; both failed development admission against V11.
- League L24: +0.81[−1.44,+3.12], gate+1.5 missed; L6:−2.25[−5.44,+0.75], direct40%[33.5,47]. Study ended without nominee.
- Slow exploration: across3 starts−13.06pp vs control; all3 negative. V3+slow3 was81.67 vs85%, no candidate. Exclude this family from a strength-motivated shortlist.
- CNN/PPO and earlier added-net families historically did not beat contemporary reference reliably.

## Feasibility and limits

All recommended DQN tensor families inspected have79 features and hidden256, so extracting singleton or concatenating compatible networks is mechanically feasible without training. Inference singleton ≠ rule-free agent; it retains V14 rules. A larger model needs timing/package size checks before any release, but no such checks were run for this inventory. Fewer networks should reduce network inference work, but speed and playing strength have not been measured here. Do not claim an excellent singleton from16 old validation games. Completion by16:00 and30% quota reserve favor a small predetermined screen, then at most one fresh confirmation under a separately fixed new protocol, not broad training or repeated failed confirmations.

Source paths used for historical evidence: `R/docs/ARBEITSSTAND.md` lines7–13,687,731–738,790–816,887,1022–1029,1515–1517,1711–1713; `R/scripts/pipeline_battle_ft3.sh`, `pipeline_battle_ft5.sh`, `pipeline_battle_ftrl.sh`; family manifests/val.csv; `R/experiments/candidates/README.md` (historical, its current-abgabe labels are stale). Exact artifact paths and member identity are fresh read-only findings above; historical performance numbers are not rerun results.
