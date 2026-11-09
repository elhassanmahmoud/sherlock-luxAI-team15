# Residual composite Q: bounded source-only feasibility

Verdict: mathematically feasible with the current homogeneous dueling QNet and unchanged production inference, but not implemented by the existing training helper and not guaranteed bit-for-bit equivalent in float32. This note is future reasoning only; it changes no current run, model, montage, cohort or gate. Only source text was read: no imports, archives, model calls, tests or games.

## Composite learning objective

Let M(x)=sum_i q_i(x)/36 be the frozen original mean, R_theta the trainable residual and R_bar its target copy. The consistent masked DDQN objective is:

    Q_theta(s,a) = M(s,a) + R_theta(s,a)
    a_star = argmax_legal [M(s') + R_theta(s')]
    y = r + (1-done)*gamma*[M(s') + R_bar(s')]_a_star
    loss = Huber(Q_theta(s,a), y).

Equivalently, train R_theta(s,a) toward y-M(s,a). The original mean is frozen/no-gradient everywhere; next-state online selection and target evaluation are also no-gradient. Only the residual owns Adam/gradients, and target updates copy R_theta into R_bar. Terminal/dead/match-boundary handling and actual replay action labels must retain their existing meanings.

This matches the behavior's composite score M+R and avoids the current individual-q versus deployed-average TD discrepancy. Existing Agent_x._learn does **not** do this: it predicts self.q(s,a) and selects/evaluates next actions solely with self.q/self.target_q. Merely changing the action hook would leave the requested residual objective absent. BehaviorEnsemble also assumes a member18 warmstart and a36-member replacement mean, so it is not this residual mechanism.

Off-policy replay remains structurally compatible, but this is no convergence, calibration or strength guarantee. At R=0, M generally has a nonzero Bellman error for the current reward/transition distribution; learning may first correct value calibration rather than improve action preferences. Post-Q rule overrides can also make the executed continuation differ from the raw masked argmax used in the target. Partial observation, replay coverage and function approximation remain limitations.

## Algebraic packing into ordinary37-member inference

The stock inference path averages its primary q and every extra_q. Define37 outputs as:

    q_i_scaled = (37/36)*q_i, for all36 original members
    R_scaled = 37*R.

Then their equal mean is:

    [sum_i ((37/36)*q_i) + 37*R]/37 = M + R.

For this project's dueling QNet, q=v+a-mean(a). Both v and a end in linear layers, with no later output nonlinearity. Scaling **both weight and bias** in value.2 and adv.2 by c scales the complete real-valued output by c. The body and earlier branch layers stay unchanged. Scaling only the advantage stream, only weights, or only one original member would not implement the stated formula. The non-dueling alternative would scale head.weight/head.bias instead, but the current original architecture is dueling.

Stock checkpoint_ensemble_dims and Agent_x.load_agent have no36/38 count restriction; a primary plus36extras can represent37 members. All members must be representable by the checkpoint's shared hidden size and dueling setting; an arbitrary differently shaped residual head is not directly accepted by this loader. With the same input features, inference configuration and internal context, the composite score then feeds the existing masking, greedy choice and post-Q rules in the unchanged production agent. This preserves that inference pipeline; it does not guarantee identical training-time rule execution.

## Actual blockers and qualifications

- **Training changes are required.** A separate experiment-only composite actor/TD path would be necessary; current _learn and BehaviorEnsemble cannot be reused unchanged to claim this objective. The current fixed run is unaffected.
- **Zero initialization must be localized.** Zeroing the final weights and biases of both residual streams makes R=0 while earlier layers can retain nonzero features. Initially, hidden/body gradients are zero because the final weights are zero; final-layer gradients can be nonzero and later unlock deeper gradients. This is a normal initial delay, not permanent learning failure. Zeroing every layer instead leaves zero ReLU features and zero weight gradients; only final biases may move, producing a state-independent correction. Even with localized zeroing, a zero TD error or inactive features can yield zero gradients on particular samples.
- **Real-number equality is not float32 equality.** 37/36 is not exactly binary-representable; scaling stored tensors, linear reductions, dueling cancellation and37-member versus36-member reduction orders round differently. Even R=0 need not reproduce the unscaled original mean bit-for-bit. Near-tied legal-action margins can flip, then the rule pipeline and subsequent trajectory can differ. No bound or observed incidence can be asserted without numerical evidence, which was not collected here.
- **Train/eval differences remain.** Current training uses epsilon0.05 while eval uses0. Several source branches explicitly require not self.training even with rules_in_training/rules_in_training_all/rescue_in_training: examples include dodge verification/prediction, stage actions, unstack, end_sap, no_strand, siege and holder_guard. Which apply depends on actual configuration. Equal composite Q formulas do not remove these conditions, changing observations, or exploration.
- **Experiment helpers would reject the montage today.** match_weight_compare.mount accepts0or2 additions and validate_and_load accepts36or38 members; the current comparison also requires byte-identical original36 states. A37-member scaled artifact violates those current contracts. The production loader is capable, but new experiment-specific montage/validation contracts would be needed for any separately authorized future study. Original protected files must not be scaled in place.
- **Learning cost increases substantially.** Each update needs frozen M at current and next minibatch inputs, roughly two complete36-network batch evaluations in addition to residual forwards/backward. The current behavior method pays the36-member mean during action selection but its learning update evaluates only the single learner/target. This is a real compute difference; no runtime, memory or battery measurement was made.
- **Inference packaging is not a training checkpoint.** A scaled37-net eval artifact is not an ordinary residual learner resume state. Its optimizer/target metadata cannot be treated as a valid unscaled residual training continuation merely because Agent_x can load it. Deployment uses the online residual; target_R belongs to training only.

## Frozen-mean replay cache: possible without changing features

Because M is a fixed feed-forward function of the existing79-float arrays, its six raw outputs for s and ns can in principle be stored beside each collected transition. Later minibatches can combine those constants with current R_theta and R_bar; this preserves the mathematical composite TD expression and changes no agent input feature. It avoids reevaluating36 frozen networks at both s and ns for every repeated batch256 update. With capacity300000, two float32 six-value arrays require14.4MB (about13.7MiB) plus any validation metadata. Collection still pays for baseline evaluation; no speedup factor or practical runtime has been measured.

The actual ReplayBuffer is a ring: push writes to the old pos, then increments pos; sample draws indices once with rng.integers and returns arrays but **does not expose the indices**. A cache must be aligned to the exact same slots/overwrite generations and sampled indices. Independently sampling again would advance RNG and mismatch rows. Exposing or retaining the one real draw inside a separately authorized experiment is an interface issue to solve; the current sampler cannot simply zip an unrelated cache batch onto its output. Saved replay is reordered oldest-first when full, so cache serialization/restoration must undergo the identical permutation or be recomputed from the actual saved arrays. Missing, stale or wrong-model cache data cannot silently substitute zeros.

Other required distinctions, drawn from current _update and reward_audit:

- Cache the actual stored float32 s/ns arrays, not a reconstructed observation or UID alone. Units die/respawn and _update stores zero ns plus done=True and a stay-only mask for dead units; a future unit reusing the ID is not that transition. Final stored action can differ from initial greedy choice, so current-state M must support the actual stored action.
- Keep all six **unmasked, finite** baseline values. Apply that transition's stored next-action mask to M(ns)+R_theta(ns) at target selection. Do not cache a fixed argmax, because R changes with every update. Do not retain -inf-masked numpy aliases: _act modifies q in place after the network mean. A captured baseline must be a pre-mask copy.
- The current BehaviorEnsemble output is a replacement mixture containing the learner, **not** the frozen original M. It cannot serve as this immutable cache. A baseline already computed during a hypothetical residual action call is reusable only when it is the genuine original mean on the exact stored feature bytes, with matching ordered model hashes, architecture, dtype and numerical convention. Likewise adjacent ns/s outputs can only be reused after actual feature equality, not chronological assumptions.
- Mathematically equivalent cache/direct paths need not be byte-identical in float32. Live small batches and later minibatches of256 can choose different linear-algebra reductions; device/library changes also matter. Caching preserves the recorded numerical baseline values, not a portable promise that every later direct forward would return the same bits. Numerical tolerances, legal-action margins and rule thresholds would require actual checks in any future authorized implementation. None were performed here.
- Frozen original weight/order identity must remain fixed for the cache lifetime. If the baseline or input construction changes, the cache is invalid; no dynamic-baseline refresh assumption belongs to this residual formulation. Cache creation must not consume learner sampling/exploration RNG or change existing reward, terminal flags or row order.

This makes a cache a plausible way to control the dominant repeated-baseline cost. It is not existing functionality, an approved design, or a new run request; the current training and its fixed evaluation are unchanged.

Source evidence: agents/sherlock/model.py QNet.forward and checkpoint_ensemble_dims; agents/sherlock/main.py _act/_update/_learn/load_agent and training-dependent rule branches; agents/sherlock/replay_buffer.py push/sample/save/load; scripts/match_weight_study.py reward_audit; scripts/ensemble_behavior_study.py BehaviorEnsemble; scripts/match_weight_compare.py mount/validate_and_load. No proposed extra trial, new spec or current-study change follows from this feasibility note.
