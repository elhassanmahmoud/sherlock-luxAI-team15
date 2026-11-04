# Single-network distillation: bounded feasibility note

**Recommendation: defer a release-seeking distillation experiment.** After approximately 11:00 Berlin, a defensible complete training, independent fresh comparison and package acceptance do not fit the existing 14:30 game cutoff and 16:00 finish. This is a proposal for later preregistration, not implementation or authorization to launch. Current sources remain frozen; the two evaluation workers retain priority. No current confirmation outcomes were read.

## Reusable inputs and proposed method

The two existing files are `experiments/runs/20261103_rescue_control18/weights/agent.buffer.npz` and `experiments/runs/20261103_rescue_adapt18/weights/agent.buffer.npz`. Archive headers previously inspected show 300,000 × 79 float32 `s` and `ns` arrays in each, plus actions, rewards, done and six-action **next-state** masks. There are no saved teacher Q-targets or map/episode identifiers. These are historical training-policy states, not a representative sample established for the final teacher.

Pin one independently accepted teacher before generating labels: V14, or FO42 only after complete qualification and technical acceptance. Freeze its tensors, configuration, source and the two buffer hashes. On the stored `s` rows, calculate the exact unmasked arithmetic mean of all teacher inference networks in float32/evaluation mode. Preserve the teacher's existing feature semantics; do not substitute its rule-adjusted final action as a Q-target.

A suitable student is one existing `QNet`/DuelingDQN with 79 inputs, six actions and hidden width 512. Preserve the teacher's gameplay configuration except the required `hidden=512` architecture setting. The final inference checkpoint contains `q`, identical `target_q`, empty `ensemble`, explicit dimensions and normalized inference counters, without optimizer/replay history.

One fixed objective can preserve both absolute mean-Q scale and action differences. For teacher vector T and student vector S, let bars denote action means:

`L = (mean(S) - mean(T))² + mean_a(((S_a - mean(S)) - (T_a - mean(T)))²`.

This equals ordinary six-action Q-value MSE. It avoids per-row target normalization that would discard absolute scale. It reproduces the teacher's preferences only insofar as the student fits them; compression does not imply improvement. Existing CNN behaviour-cloning code targets actions and map planes, so it is not a ready DQN mean-Q fitting path.

For a future preregistration, a concrete proposal is one initialization seed, Adam at 1e-4, batch 1024, three complete epochs, and the **final** checkpoint only. Fix the row partition before fitting; use the first 80% of each chronologically saved buffer for training and the last 20% for diagnostics. Audit duplicate rows and cross-buffer overlap. No early stopping, checkpoint ranking, retuning or replacement candidate after seeing diagnostics. A predeclared resource/time cap aborts an unfinished run rather than admitting a partial checkpoint. These settings have no measured runtime or quality guarantee yet.

## Evidence needed before release

Report held-out-row Q-MSE, mean-Q error, centered-action error, and unmasked action agreement/margins, separately for both buffers. The buffers lack current-state masks, so do not call these “legal-action agreement” measurements. Row partitions can contain states from the same maps and related trajectories: all such diagnostics are **row-level compression checks, not fresh-map strength evidence**.

Preregister one separate paired fresh-map comparison, its complete seed inventory and strict output checks before any new games. Retain all seven gates: panel Δ≥1 pp; panel lower bound>0; Solution Δ≥0; Solution lower bound>−1 pp; default≥99%; default Δ≥−1 pp; direct lower bound>50%. Preserve whole-map bootstrap, 5,000 samples, seed 0, and one final candidate. Existing study results cannot substitute for that fresh comparison. Independent data review and actual Python 3.13/3.10 payload/runner/replay acceptance remain necessary.

## Deadline arithmetic

Using the already declared comparison size—80 panel/default maps, 400 Solution maps, 160 direct maps—requires **3,840 games: 3,520 panel-class plus 320 direct**. Between 11:00 and 14:30 there are 12,600 seconds.

- Existing conservative floors, 20% time margin and 20 minutes of transitions: **13,526.4 seconds = 3h45m26s**, before any training or implementation/review.
- The completed technical pilot's observed conservative rates: **17,071.3 seconds = 4h44m31s**, also before training.

A faster student could change throughput, but no measured admission evidence supports banking that saving. Teacher-label generation, fitting, technical review and fresh evaluation cannot responsibly be promised within this window. Do not shrink the comparison to obtain admission or weaken gates. Preserve at least 30% quota, require fresh quota evidence below 65% before a phase, and retain the 90-minute post-game acceptance/closure reserve. Complete the current study and document this deferred experiment; make no stronger-single-network claim today without the missing evidence.
