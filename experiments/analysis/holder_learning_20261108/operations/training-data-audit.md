# Independent training-data audit — PASS

Completed neutral_v1 and train_v1 audited under 759c8fa1908184de04421ee9fb3547e55bf7663a. 209739 checks passed using standard-library reads, arithmetic and hashes. No tests, model imports, games, source edits or validation data reads.

- Neutral proof: four complete games, exact reference/collector frame equality, zero coefficient/intercept head, eight recorded scoring opportunities per collector game. No branch pairs or extra steps.
- Training: 96 complete games, 29088 live steps; exact24 maps6500000–6500023 and both sides. 162 pairs, 3888 primary steps and 912 reverse/repeat steps.
- Every raw reference frame equals its collector frame. Every pair baseline equals its twelve subsequent live frames. Frame/action/branch/trajectory hashes, artifact checksums, state/observation chains, point increments, match/game totals and labels independently checked.
- Public eligibility, sole holder, legal proposal/STAY, spacing, boundary, effectiveness, identical-action continuation, pair/event/manifest consistency and recorded reverse/repeat success checked. All negative/zero labels retained; games with zero pairs included in counts.
- All 330 pinned source files, executable, plan/inputs and three released submission files match. Exact counters and final resource receipt timing checked.
- Labels: 162 effective, 92 positive, 50 negative, 20 zero. Fixed training adequacy: {'pairs': 162, 'represented_maps': 20, 'positive': 92, 'positive_maps': 18, 'passed': True}. No fit or policy-strength conclusion.

Limits: raw state tensors and duplicate reverse/repeat trajectories are not separately archived; their digest equality and runtime assertions are audited. Neutral hook calls are runtime counts. Full per-game counts and every independently recomputed label are preserved in training-data-audit.json.
