# Independent prototype review

**Verdict: APPROVE. No blocking findings.**

Reviewed the complete four-file change `c02c2a5..b73523f` against Task 1, its global constraints, the approved V4 strategy, and the implementation report. This is both the specification/code-quality review and the whole prototype branch review for that change range. The untracked experimental checkpoint and root-owned experiment files are outside this code review.

## Findings

- The helper implements the frozen search: baseline plus two highest finite legal movement proposals, a 15% finite legal all-action Q-span allowance, deterministic sorted nearby pairs, at most nine combinations per pair, strict global distinct known-point occupancy improvement, normalized regret then change count then action-tuple ties. Accepted pairs reserve both units, and rejected pairs do not. Earlier accepted destinations and fixed outsiders remain in subsequent occupancy calculations.
- Numeric exclusions and fallback match the agreed contract. Invalid/nonfinite visible enemy positions or energies return no changes; negative-energy enemies are ignored. Nonfinite or negative friendly energy, invalid positions, illegal/nonfinite baselines and final SAP cannot create alternatives. Movement occupancy requires known movement energy. Inputs are not mutated, and no broad exception handling obscures errors.
- The enemy guard applies to both current and alternative destination tiles, preserving immediate combat stacks unless a permitted alternative is away from every visible nonnegative-energy enemy. The objective is explicitly nominal occupancy, with no claim to predict field energy, SAP, void, collision or hidden enemies.
- Integration is after every existing action override. The final world action classes are converted back to canonical space, changed movement classes are mirrored back, and `_prev_actions` is updated for changed units. SAP rows are not rewritten. The default-off/evaluation-only gate leaves disabled and training action selection unchanged.
- Targeted inspection of the unchanged `_decide`, `make_context`, `_action_mask`, and geometry helpers confirms that `ids` contains the full observed friendly team, the position/point context uses the matching coordinate frame, masks are row-aligned, and direction mirroring is involutive. These checks resolve the concrete integration risks without expanding into a general framework audit.
- The implementation remains small and bounded: for the intended 16-unit game, at most 120 pairs and nine combinations per pair. The two episode counters do not modify evaluation CSV schemas. No model, feature, reward, training, engine or released-weight change appears in the reviewed diff.

## Verification and limits

The focused tests exercise behavior rather than merely repeating the search, including occupancy gains, fixed outsiders and earlier updates, combat guards, numeric fallbacks, top-two/mask/regret constraints, UID row order, nonmutation, pair reservation, both mirrored sides, final SAP preservation, late rule overrides, and disabled/training paths.

I used the supplied fresh evidence of **48 focused tests passed** and **457 full-suite tests plus 14 subtests passed**. I did not rerun tests, load heavy models, or start games. The implementation report's synthetic helper timing is a sanity check only; representative full-act timing, checkpoint identity/runner checks, disabled-baseline reproduction, and the frozen game comparisons remain the root's Task 2+ gates. This approval establishes code/spec readiness for those checks, not a win-rate gain or release qualification.

Only this report was written; no repository source, index, refs or weights were changed by the reviewer.
