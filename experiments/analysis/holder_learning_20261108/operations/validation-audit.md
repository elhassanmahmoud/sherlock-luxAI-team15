# Independent validation audit — PASS

Audited completed validation_v1 and root validation report under unchanged759c8fa1908184de04421ee9fb3547e55bf7663a; frozen head0f61a4070020dab415ce02ae76f4c752533d4f97e58af7ece2bcffc09d4a8dc4. 63539 checks. No project/Torch imports, tests, games, fitting, changed thresholds or extra maps.

- Exact8 maps6501000–6501007, both sides,32 complete executions/9696 live steps; 28 pairs, 672 primary and 264 repeat/reverse steps.
- Every reference/collector raw frame and every twelve-step baseline/live sequence matches. Frame/action/branch/trajectory and artifact hashes, point arithmetic, public eligibility, spacing, same-action continuation, pair summaries/events, counters and all pinned source/input/protected files verified.
- Independently regenerated all16 public features, frozen training normalization and clipped transforms, predictions and strict>1.0 decisions. Every label retained: 14 positive,12 negative,2 zero.
- Selected14 across5 maps: 10 positive,0 zero,4 negative; total selected gain18.0, selected mean1.2857142857142858.
- Eight map gains (including zero-event maps): [-4.5, 6.0, 2.0, 0.0, 1.5, 0.0, 4.0, 0.0]. Mean1.125; independent5000 PCG64(0) whole-map bootstrap lower2.5%=-0.8765624999999995. Weighted MSE108.00862921971618, unweighted MSE207.425767029735.
- Fixed gates:{'minimum_pairs': False, 'minimum_maps': True, 'minimum_selected': True, 'minimum_selected_maps': True, 'positive_mean_map_gain': True, 'positive_bootstrap_lower': False}. Overall screening passed:False. All published root statistics/provenance match (float tolerance1e-12).

PASS concerns data and arithmetic integrity. Opportunity labels on baseline trajectories do not establish repeated-policy gameplay improvement. Raw state tensors and duplicate reverse/repeat branches are not archived; exact digest equality and runtime flags are checked. Full independent features, predictions, labels, selections and map counts are preserved in validation-audit.json.
