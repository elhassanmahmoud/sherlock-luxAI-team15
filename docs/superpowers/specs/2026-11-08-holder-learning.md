# Fixed HOLD learning specification — 2026-11-08

Read-only preparation from holder_rollout.py, holder_rollout_probe.py and targeting_probe.py. No diagnostic/smoke labels or results inspected, no fitting/tests/games performed. Root independently reported feasibility passed. Root adopted this design before any new training/validation labels. It is the binding specification for one fixed learning experiment, not a strength claim.

## Data and exact policy domain

Reserve 24 training maps and eight validation maps before collecting any new labels; both sides against Solution92. Reuse the existing paired-rollout collector unchanged: at most eight eligible opportunities per complete game, first eligible UID in unchanged ascending order, at least 12 global steps between opportunities, match steps 1..89, same sole-holder/current-assignment/masked-move eligibility. Maximum384 training and128 validation pairs. Keep all complete pairs, including identical-action zero labels. Never select rows based on label, final baseline action, or whether HOLD produced SAP. Old diagnostic pairs are excluded from fitting, normalization and validation.

Deployment consumes an opportunity when the first eligible UID is scored, even if HOLD is rejected. Increment the eight-opportunity budget and set last_opportunity_step immediately; the next11 steps are unmodified V14. Do not try a second UID after rejection. Reset budget only in new_game, never per match. The missing head bypasses all intervention logic; a zero coefficient/intercept head rejects every opportunity. This matches collection cadence, not its exact trajectories: repeated accepted interventions still change later states and require full-game performance testing.

Target y is the existing exact HOLD-minus-baseline twelve-step team-point-differential label; no reward shaping, Q imitation, label clipping, or selected-positive-only fit. Engine state and branch outputs are used solely for labels/audit. The feature extractor receives candidate.public, candidate.uid/proposal, candidate.q/mask only; never a branch, environment, opponent object, seed, side or label. Candidate.features (79-vector) is deliberately unused.

## Fixed sixteen public features, exact order

Let p=current canonical position, d=p+proposal direction. E=own observed energy. Enemy set consists only of public enemy_coords/energies with energy>=0. R=public sap_range; C=public sap_cost. Armed enemies have energy>=C. q contains finite values for legal entries and None for illegal entries; both proposal and STAY must be legal. span=max(q[legal])-min(q[legal]). All clip intervals below are closed.

1. clip((q[proposal]-q[STAY])/max(span,1e-6), -1,1).
2. clip(E/400,0,1).
3. move_cost/5.
4. sap_cost/50.
5. (max_match_steps-match_step+1)/max_match_steps.
6. tanh((own_points-opp_points)/20).
7. clip(energy_map[p]/20,-1,1).
8. clip(energy_map[d]/20,-1,1).
9. float(nebula[p]).
10. float(nebula[d]).
11. number of armed visible enemies within Chebyshev R of p /16.
12. number of armed visible enemies within Chebyshev R of d /16.
13. sum of nonnegative visible enemy energy at Manhattan distance exactly1 from p /6400.
14. sum of nonnegative visible enemy energy at Manhattan distance exactly1 from d /6400.
15. sum of nonnegative visible enemy energy exactly at p /6400.
16. sum of nonnegative visible enemy energy exactly at d /6400.

These fields exist in make_context and are actually captured by DiagnosticAgent. PUBLIC_FIELDS also lists optional nebula_estimate, sensor_mask and energy_observation_age, but DiagnosticAgent does not synthesize them; do not use them. energy_map is remembered public information, not guaranteed current truth. No hidden dropoff, true fog loss, target truth, global Solution state, UID number, coordinates, or future feature. The fixed simple feature set is intentionally a small combat/energy correction around the expert proposal.

## One fit, no search

Require >=96 complete training pairs across >=12 training maps and >=12 positive labels across >=6 maps. If not met, retain the data and stop this learner; do not extend maps or loosen gates. Include maps with zero pairs in collection reports, not as fabricated training rows.

Weight each represented training map equally: w_i=1/(M*n_map), where M is the number of training maps with pairs and n_map includes both sides. Fit weighted training means and population standard deviations only. If standard deviation<1e-6, use scale1; otherwise use that standard deviation. Transform z=clip((x-mean)/scale,-5,5), identically for train/validation/deployment.

Fit a single float64 weighted ridge regression with intercept:
  minimize sum_i w_i*(y_i-b-beta dot z_i)^2 + 0.1*sum_j beta_j^2.
Do not penalize b. No alternate penalties, heads, feature sets, epoch selection or validation refit. Always execute baseline unless predicted gain b+beta dot z is strictly >1.0 point. A zero head including zero intercept is exactly neutral. Export JSON with feature order/version, eligibility/cadence version, H12, mean/scale, coefficients/intercept, ridge0.1, threshold1.0, baseline tensor hashes and exact data/source hashes. Reject nonfinite or malformed supplied heads at load.

## Fixed offline validation rule

Freeze fit/head hash before opening validation labels. Evaluate the same fixed threshold at every recorded validation opportunity; all rows remain in reporting. Require >=32 validation pairs across >=4 of the eight maps, and >=8 predicted-HOLD selections across >=4 maps. No threshold tuning.

For each of all eight validation maps define G_m = one half of the sum of actual y_i for predicted-HOLD opportunities across its two sides. A map with no chosen opportunities has G_m=0. G is a counterfactual opportunity proxy in points/game on V14 trajectories, not actual repeated-policy game improvement. Require mean(G_m)>0 and the lower2.5th percentile of5000 whole-map bootstrap means, NumPy default_rng(0), strictly>0. Also report total selected gain, selected positive/zero/negative counts, selected mean gain, all eight G values, and weighted/unweighted validation MSE; MSE is not a gate. With only eight maps, this is a conservative screening heuristic, not a general significance or strength claim.

Failure ends this exact head attempt without refitting, threshold changes, additional maps, or swapping validation into training. Passing nominates this one frozen head for a separately predeclared small actual-game comparison against V14/Solution and controls. Keep this fitted head unchanged; do not refit on validation. Performance must test the exact eight-opportunity/cooldown deployment policy, and can reject distribution shift from repeated interventions.

## Minimal implementation scope and verification

Reuse collector and audited branch/scoring machinery; add one pure feature extractor, one small ridge fit/evaluate CLI, and a narrow optional inference hook with explicit per-game cadence counters. No generic training framework or V14-network optimization. Require extractor equality between recorded candidate and live hook, legal-q/None handling, both mirrored sides, reset/cooldown/rejection/budget boundaries, hidden-state-independent extraction, training-only normalization, fixed head serialization and missing/zero-head complete action identity. Existing snapshot clone machinery must preserve the new cadence fields in future experiments. No tests while model/game processes run.
