# Next evidence triage — 08 Nov 2026

## Scope and boundary

Read-only review at frozen repository HEAD `c096e4f0d1720900ee04d5acaa7faaef465fcded`. Read `CLAUDE.md`, the newest entries in `docs/ARBEITSSTAND.md`, the ensemble-scale review, the closed HOLD and ensemble reports, and the fixed Fog comparison specification. No repository edits, model/Torch imports, games, tests, or training. I did not inspect the active comparison's live performance outputs. The source/task boundary leaves no evidence for declaring any candidate stronger.

## Triage

### 1. A genuinely trained member may have too little decision influence in the full ensemble

**Why this is plausible:** CONTROL38 and NEUTRAL38 each append just two trained members to the same 36-member V14 ensemble, with equal weight per member (`docs/superpowers/specs/2026-11-08-fog-comparison.md`, “Zulassung und feste Modelle”). In a 38-member arithmetic mean, those two updates account for only 2/38 = 5.3% of the aggregate before considering whether their action margins actually disagree with V14. The update can therefore learn a real local preference yet rarely change the ensemble argmax; subsequent action rules can further prevent a changed network proposal from changing the final action. Existing historical decision traces report network-versus-rule action changes in 8.3% (V12) and 7.5% (V11), in `docs/ARBEITSSTAND.md` around the entries cited by `/tmp/sherlock-ensemble-scale-review.md` (lines 1039/1324 in that review's source references). This is a mechanism for limited policy influence, not evidence that the current Fog members are weak or that rules are a bottleneck on Fog-relevant states.

**Smallest falsifier:** After the already-fixed Fog comparison is complete and audited, use a predeclared fixed bank of existing traces to replay only the trained members and the V14 ensemble. Report (a) signed contribution of the two new members to the legal-action margin, (b) whether the aggregate argmax changes, and (c) whether downstream rules retain or erase that change. Use separate fog/ordinary contexts and do not fit weights or thresholds. Existing mean-only traces cannot support this; the ensemble-scale review found per-member Q only in five duplicated historical examples. A sufficient trace bank must retain per-member outputs or be replayed through the already-bound models. This is descriptive diagnosis, not a game-strength test. No need to launch it while the fixed comparison is running.

**Decision:** plausible, practically relevant, and not presently established. The current 38-member candidate comparison is the smallest already-authorized test of whether the learned pair changes overall outcomes; wait for its fixed result rather than add games.

### 2. Fog reward-target uncertainty is the concrete new learning assumption, but its causal effect remains unresolved

**Evidence:** The documented pipeline maps an unknown final fog-SAP outcome to the same stored zero as a nonpositive estimated hit, then applies the negative hit-shaping term (`docs/superpowers/specs/2026-11-08-fog-reward.md`, “Auftrag und Hypothese”). The completed training report documents 615 / 411 explicit final unknown SAPs over the two 40-game paired warmups and neutral reward mass 184.5 / 123.3 (`experiments/analysis/fog_reward_20261108/TRAININGSERGEBNIS.md`). This establishes that the reward distinction was exercised, not that the old target was harmful: the sign of an unknown outcome is genuinely unknown, and a conservative penalty may be useful. The one frozen comparison already includes CONTROL38 and NEUTRAL38, so its within-pair result is the appropriate small causal check for this target change; merely comparing NEUTRAL38 to V14 would confound reward treatment with additional training.

**Smallest falsifier:** Use the already planned, fixed CONTROL38-vs-NEUTRAL38 paired comparison and its predeclared mechanism analysis in `docs/superpowers/specs/2026-11-08-fog-comparison.md`. A neutral arm with no useful margin/action changes, or no consistent improvement over its same-start control, falsifies the practical case for this specific target adjustment at this training budget. Do not extend the sample or refit. The comparison is in progress; do not inspect interim results.

**Decision:** this is the strongest concrete target hypothesis already under test, but there is no admissible result yet. Do not open a second reward experiment before the frozen decision.

## Evidence limits / recommendation

The ensemble-scale review (`/tmp/sherlock-ensemble-scale-review.md`) already shows that generic Q-scale normalization, voting, and learned member weighting are not novel or supported: prior margin diagnostics and a 20,000-state summary exist, and V14 member-level traces are missing. It also documents that member reward histories differ in objective (members 12–17 had opponent-points penalty in original training; their descendants later used the common fine-tuning reward). This does not justify blind normalization or infer which members are right.

The recent negative studies do not identify a general learning bottleneck: the HOLD head's separated validation failed two fixed gates (`experiments/analysis/holder_learning_20261108/ERGEBNIS.md`), and REPLACE36 failed its fresh confirmation (`docs/ENSEMBLE_ABSCHLUSS_20261108.md`). These results close those specific prototypes; they do not show that all target changes fail. Present evidence is insufficient to name a second untested bottleneck with confidence. The only defensible follow-up is to finish the already frozen Fog comparison, then—only if useful—run the no-games, fixed-trace influence diagnostic above. No implementation, new models, or new performance games are recommended from this triage.
