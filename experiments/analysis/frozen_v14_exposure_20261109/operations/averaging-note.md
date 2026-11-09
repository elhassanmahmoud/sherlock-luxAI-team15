# Exact averaging: current behavior training versus fixed 38-member inference

Read-only derivation from current source, at one identical feature vector x and action a. No checkpoint/archive loads, forward passes, tests or games. No change to the current training, montage or fixed200-game gates.

Let q_i be original member i, j=18, M=(sum_i q_i)/36, and q_s=q_18+delta_s be the current learned network for start s. The deltas are pointwise output differences, not parameter deltas and not measured quality improvements.

**Training behavior** (ensemble_behavior_study.py, BehaviorEnsemble._hook):

    B_s = (sum_{i != 18} q_i + q_s)/36
        = M + delta_s/36.

The original member18 is displaced, not retained beside the learned network. Exactly35 frozen members and the current learner contribute. The hook exists only during this learner's non-gradient _act_est call.

**Fixed EXPOSURE38 inference** (original mount appends two q states; normal Agent_x averages primary plus extras):

    E = (36M + q_e48 + q_e49)/38
      = M + [2(q_18 - M) + delta_e48 + delta_e49]/38.

This differs from either training mixture in two ways: the other learned network joins, and the original member18 is restored while two descendants of it are appended. Even if both learned deltas were zero, E would equal M + 2(q_18-M)/38, generally not M. In that zero-delta identity, the member18 lineage carries3/38 of the mean versus1/36 originally; this is a weight decomposition, not evidence that trained descendants remain similar.

Each individual learned delta has coefficient1/38 rather than1/36: ratio36/38=18/19, about5.26% lower. This does **not** mean the combined learned signal is always weaker. If both deltas are identical and point the same way, their joint coefficient is2/38 rather than the single training delta's1/36, about1.895 times as large. Opposite deltas can cancel. More generally:

    E = (36B_e48 + q_18 + q_e49)/38
    E - B_e48 = (q_18-M)/19 + delta_e49/38 - delta_e48/684.

The added source/partner values therefore matter more than describing only a denominator change. Division by a positive common denominator alone cannot change a greedy argmax. Action effects depend on the combined legal-action margins, tie behavior and subsequent rules, not on coefficient percentages interpreted as action or win percentages. The equal arithmetic mean is applied to raw Q values; there is no per-member scale calibration in these paths. Action-independent output offsets do not change that member's action margins, while different action-dependent magnitudes can affect its practical influence.

**Prior BEHAVIOR38** uses the identical append-and-average construction with its accepted on48/on49 networks:

    H = M + [2(q_18-M) + delta_on48 + delta_on49]/38
    E - H = [delta_e48 + delta_e49 - delta_on48 - delta_on49]/38.

Thus the source-member reweighting is structurally shared and cancels in the pointwise E-versus-H score contrast. The current comparison tests two different learned pairs under the same final38-member rule. Neither pair was trained with its final38-member action mixture: each arm saw its own36-member replacement mixture. Once actions differ, visited observations and later input vectors can also differ, so the pointwise identity is not an identity between complete trajectories or win outcomes.

**DDQN versus behavior discrepancy.** Agent_x._learn uses only the learner q and its own target_q: legal argmax from q_s(next_state), evaluation of that action by target_s, and y=r+(1-done)*gamma*target_s. It does not backpropagate through the frozen35 or optimize the deployment38-member mean; its gradient is not scaled by1/36 or1/38. Replay records the actually executed final action after the behavior path. Using actions from a different behavior policy is compatible with this off-policy DDQN update structure and is not, by itself, an implementation error. It also does not prove adequate replay coverage, value calibration, convergence, or improved decisions under the final ensemble. The learned individual q is not explicitly trained as a residual correction to M, even though delta_s is useful for this algebra.

The score-mixture discrepancy is additionally distinct from training epsilon0.05 versus eval epsilon0, training/eval rule branches, and the changed opponent distribution. No magnitude, sign, action-quality or strength conclusion follows without actual data; the formulas alone do not diagnose prior losses. They leave the already fixed training and200-game selection unchanged.

Source locations read: scripts/ensemble_behavior_study.py BehaviorEnsemble.__init__/_act/_hook; scripts/frozen_v14_exposure.py BehaviorEnsemble alias and worker use; scripts/match_weight_study.py make_learner; scripts/match_weight_compare.py mount/inference_config; scripts/ensemble_behavior_compare.py run_technical; agents/sherlock/main.py _act (raw ensemble mean, masking, epsilon and rule overrides) and _learn (individual DDQN target/gradient).
