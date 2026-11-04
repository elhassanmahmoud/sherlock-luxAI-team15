# Minimal student reward experiment — design only, 4 November 2026

Recommendation: a single training-only ablation, **w_sap_hit = 0**, against the same distilled student's unchanged reward configuration (expected baseline 0.3; verify the actual checkpoint). Do not alter AgentConfig defaults, inference rules, or V14/ZIP. Existing potential shaping already exists; adding another distance reward would confound this experiment.

## Hypothesis and alternatives

The SAP term rewards a pre-action hit estimate saved by `_act`, not measured post-action damage (`main.py:591–598`, `reward.py:150–153`). It awards `w_sap_hit * hits` when the estimate is positive, even though the opponent can move and the attack can be strategically unhelpful. Hypothesis: this proxy contributes misleading positive rewards; removing it can preserve point holding/energy without sacrificing useful attacks. This is a code-based hypothesis, not an established cause of previous failures.

A smaller weight such as 0.15 is less disruptive but gives a weaker diagnostic. Increasing opponent-point penalties is less attractive today: that component already exists, is shared across units, and an earlier `opp6` result was unconvincing. Do not add a new damage estimator in this time window.

## Minimal implementation boundary

Use a new experiment wrapper around existing `finetune`/`Learners` APIs. Register two temporary in-memory variants carrying the **entire verified student configuration**, differing only in `w_sap_hit`. Write distinct init directories containing identical Q/target tensors and fresh Adam state; keep canonical player sharing, LR, epsilon, rules, gamma, learning schedule, and frozen=False identical. Assert the live configuration and saved manifest really contain the assigned values after loading. Follow final_rescue_train's isolated validation and final-action/replay audit pattern, but do not reuse its hard-coded 1,200-game receipt or claim that receipt applies.

Historical buffers are suitable as feature sources for distillation, not automatically for reward treatment. They store scalar rewards. **Do not copy their `.buffer.npz` into either RL init**: without raw contexts the SAP component cannot reliably be relabeled. Both arms start empty and use identical fresh prefill. Prefill learning stays disabled; its actual actions/states must match between arms because reward alone has changed, while stored rewards should differ exactly where expected.

## Fixed comparison

Freeze one distilled end checkpoint before RL. Compare C (original reward) with R (SAP weight zero), plus the unchanged distilled baseline in evaluation if budget permits. Use one identical training seed, recorded map/side/opponent sequence, same opponent files, and fixed game/update budget; alternate both sides. Retain the existing 0.6 solution92 / 0.2 sol92_sq / 0.1 default / 0.1 rush mix. Use independently reserved maps after auditing seed inventory; do not silently reuse held-out cards from earlier studies. No snapshots, checkpoint picking, or extra treatment weights. Stop both at a common predeclared completed checkpoint if the deadline prevents the full budget.

## One measurable reward diagnostic

In a training-only wrapper around the `main.unit_rewards` binding, compute rewards twice from the same untouched contexts/actions: actual config and a copy with w_sap_hit=0. Log by game: total actual reward, sum of absolute removed SAP contribution, SAP transition count, and count of SAP transitions where original reward > 0 but zero-SAP reward <= 0. Also record SAP attempts and owned-point occupancy. The counterfactual differences must equal the existing signed hit formula exactly. These diagnostics measure exposure to the intervention; neither estimated hits nor lower TD loss demonstrate better gameplay.

## Contraindications and interpretation

Rule-enforced SAP actions may limit what the student can change; removing the term also removes its miss penalty and can reduce useful offense. Keep all rule flags identical and measure actual final actions. One paired training seed and a tiny evaluation establish feasibility, not superiority. All seven original promotion gates still apply; no promotion today without full completion.

`QNet(hidden=512)` means one 512-wide network with **two** hidden body layers plus dueling heads, not a one-hidden-layer architecture. Distillation fidelity on historical features is not evidence of closed-loop strength.

Audit performed by static reads only. No code/model changes, model loads, games, or tests executed.
