# Task 1 independent spec and quality review

Date: 2026-11-08. Scope: Task 1 only, current working-tree changes in `agents/sherlock/config.py`, `agents/sherlock/main.py`, `agents/sherlock/reward.py`, and `tests/test_fog_unknown_reward.py`.

**Spec verdict: PASS. Quality verdict: PASS. No blocking findings.**

## Evidence inspected

- Read project rules, current handoff entry, task brief (including binding spec), implementation report, review package, current production diff, and surrounding action/reward/reset/config code.
- Traced all action/target overrides between the Fog proposal and native emission, including end-SAP, dodge, siege, still-target/overkill cancellation, holder movement and smart-SAP replacement. Inspected actual `_fog_sap`, `_end_sap`, `rules.plan_sap`, and `rules.siege_action` return construction.
- Inspected synthetic test assertions for final provenance, equal-value replacement, cancellation, reset/isolation, mirroring, legacy call compatibility, reward arithmetic and paired replay invariance.
- No tests, engine games, model loads, gradients or original-policy traces were executed in this review. Existing verification is the implementer's reported 30 focused cases and 57 regression cases with one real-game case intentionally deselected; this review does not re-label that report as independently executed test evidence.

## Contract assessment

1. The dataclass flag defaults to `False`; existing `from_dict` construction supplies that default for old checkpoint dictionaries. Reward and update use `getattr(..., False)` for missing flags.
2. Production changes add observation-only metadata along the action path. They do not change masks, rule conditions/order, selected actions, numeric SAP tuples, `_prev_actions`, or existing statistics. `_fog_sap` still constructs `(dx, dy, 0)`.
3. A fresh per-unit `fog_origin` holds the actual Fog tuple. Only the final emitted SAP can populate `_sap_unknown`, using object identity after every override. End-SAP, siege-SAP and smart-SAP construct their own tuples; even equal coordinates/values cannot inherit Fog origin. A cancellation/movement skips the final SAP branch. Retaining the original Fog tuple through rules that do not replace its target correctly preserves provenance.
4. `_sap_unknown` is reset at episode reset and the first line of `_act`, covering match-reset/empty frames; the UID is recorded before coordinate mirroring. `_decide(next_obs)` during update does not clear or replace it.
5. With the flag false/missing, `_update` retains the historical five-positional-argument `unit_rewards` call. Existing external five-argument calls also remain valid with the new keyword-only optional argument omitted.
6. The only altered reward branch is the hit-shaping term for a marked SAP when explicitly enabled. Missing provenance keeps the old term. Sparse rewards return before this branch; zero weight, death, terminal potential, energy, points, discovery, exploration and match terms retain their original calculations. Current producer guarantees an unknown estimate of zero, giving exactly `+w_sap_hit` relative to control when shaping is enabled.

## Remaining integration ownership

Root still owns full original-V14 reference traces on both sides, broader integrated verification, training-audit integration and the four-arm mechanical acceptance. This focused PASS does not establish those later checks, successful training or improved playing strength. Root should include this review in the integrated `docs/ARBEITSSTAND.md` update; no shared handoff/source files were edited here.
