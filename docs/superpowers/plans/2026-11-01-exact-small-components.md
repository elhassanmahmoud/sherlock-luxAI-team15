# Bounded exact inference: implementation plan

> Use subagent-driven-development. Current A/B/C evaluation remains frozen elsewhere.

Goal: technical fallback only, no immediate new benchmark or release.
Spec: docs/superpowers/specs/2026-11-01-exact-small-components-design.md.
Architecture: exact Fraction RREF on a small complete component of valid belief records,
opt-in gauss_infer=False. No new dependencies, no hidden state, no policy/network changes.

Constraints: work only in sherlock-november-followup; no model jobs while two evaluations
run in the other worktree. No new seeds, no strength claims, no deployment without a
separate fresh comparison plan. First study's outcome/nomination must remain independent.

- [ ] Write RED tests for five-variable point/null example and failure of existing
  subset+overlap to solve it; exhaustive independent binary soundness cases.
- [ ] Implement helper in agents/sherlock/exact_infer.py; wiring only belief/config/main.
  At most400 records, raw record16 physical tiles, whole component24 canonical variables,
  40 distinct rows; skip oversize components completely. Symmetric tiles contribute
  multiplicity2, not set-deduplicated coefficients.
- [ ] Hard deterministic4096 cell updates and256-bit numerator/denominator limits on input/stored matrix values;
  abort atomically with no facts. No wallclock-dependent production decisions.
- [ ] At most8 attempts per match and at least8 observed steps between attempts.
  Match reset/new game resets attempt limits. Reopening dead knowledge clears solver
  caches but MUST NOT replenish the per-match attempt budget. No recursive solver closure.
- [ ] Ignore gauss entirely when either window-inference option is on; retain current
  stable/epoch guards. Contradictions, rank deficiency/free variables, symmetry conflicts
  and nonbinary fixed pivots give no unsafe facts; no rounding or arbitrary free values.
- [ ] GREEN tests: order invariance, coefficient2, empty/disconnected/large components,
  all work limits, immutable inputs, real belief wiring, temporal resets/contradictions.
  Pure numpy/Fraction tests only now, no Torch models/Lux games or full suite.
- [ ] Independent code review and CPU microbenchmark before any optional shadow trace.
  If additional facts or bounded cost cannot be established, discard the prototype.

A later strength study requires explicit fresh predeclaration, separate records and time
admission. This implementation plan does not authorize a new game run or a promotion.
