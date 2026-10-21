# Read-only review: artillery sap and related incoming changes

Reviewed `f540da4^..baef7a8` through Git objects in `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15`, 21 October 2026. The checkout was not advanced or edited. No model imports, checkpoint loads, tests, games or integration were performed. Shared AGENTS/CLAUDE guidance and incoming work log were read. Only this report is written; proposed reproductions below are not executed results.

## Decision

**An isolated, fixed `art_sap=True, art_min_hits=3, art_safe=True, art_reserve=0` candidate merits one independent fresh comparison after the current CNN phase, conditional on a short correctness/reproduction check and an explicit freeze of its exact behavior.** Keep `siege=False`, `threat_feats=False` and all V3 tensors/other configuration unchanged. Do not include mixed ensembles or siege in that candidate.

This is more grounded than another target-swap implementation: there are actual interventions and a complete positive development comparison. Raw incoming CSVs contain 108/120 Solution_92 wins versus the established V3 reference 102/120, and 120/120 default wins. Both opponents have complete unique keys on 500720–500779, both sides, with no draws. Art2 gives 105/120, art4 101/120, unsafe art3 and reserve20 art3 each 103/120. Seven variants were explored including siege; the selected +5pp and its development confidence interval are selection-biased, not confirmation. Neighbor sensitivity lowers confidence but does not by itself invalidate a pre-frozen independent test.

Two concrete correctness findings need disposition before treating the incoming branch as generally reviewed. The first affects the interpretation of art3; the second is an unrelated default-path ensemble regression. A fix changes the tested candidate: never silently carry the old 108/120 result over to patched behavior. Prefer a focused fix/recheck and complete development requalification if the art3 admission criterion is intended to mean three live enemies. Alternatively, an unchanged historical candidate can be tested explicitly as a heuristic using the old estimated-hit count; it remains action-legal, but the limitation must be recorded.

Fresh evaluation must use separately reserved cards, leave Mahmoud's 503220–503819 study reservations alone, and keep the existing V4 acceptance thresholds. It cannot be used to tune hit count/reserve/safety again. No promotion from development evidence alone.

## Findings

### P2 — Artillery can satisfy the hit threshold with enemies already marked for removal

At `agents/sherlock/main.py:437`, `_artillery_ok` trusts `sap[2]`. `_best_sap_target` at lines 543–555 computes that count from every visible enemy coordinate, without filtering negative energy. `make_context` retains visible masked negative-energy units. The installed engine explicitly clears their unit masks at the beginning of the next step, before movement and sap (`luxai_s3/env.py`, remove-units block around 230–234).

Therefore a supposed three-enemy artillery shot can have just one surviving target even before any opponent moves. This is a new admission decision built on a pre-existing approximate target count, not a claim that all of the old sap selector was introduced by this patch.

Minimal proposed reproduction using the existing stay-agent fixture: own unit `(5,5,100)`, sap cost40/range4; enemies `(8,8,80)`, `(9,8,-1)`, `(8,9,-1)`; `art_sap=True, art_min_hits=3`, other rules off and own tile not a point. The selected center is `(8,8)`, count3, energetic armed target at Manhattan6, so the new rule emits SAP. Both -1 enemies disappear before the shot; only one target remains. Repeat with energy0 to confirm zero-energy enemies must remain counted. Test the count used for the chosen shot, not merely total visible enemies.

Suggested narrow correction, if chosen: compute the artillery admission hit count at the already selected center from visible enemies with energy>=0, without modifying the shared V3 sap-target selector. That keeps the change local, but still creates a revised candidate requiring its own development result. No measured frequency or game impact is available from the provided aggregate probes.

### P2 — Rebuilding a homogeneous saved ensemble can silently omit appended networks on load

`scripts/build_ensemble.py:38–54` builds the new `dims` list, but writes `ensemble_dims` only if a member dimension differs from the main dimension. New `Agent_x.save_agent` always writes `ensemble_dims`. If the base is a saved homogeneous ensemble with a nonempty dimensions list, appending another same-size network leaves that old, shorter list in the output. `Agent_x.load_agent:701–702` then uses `zip(ensemble, dims)`, silently discarding the excess networks.

Minimal proposed reproduction: save a 79-feature agent with one 79-feature extra network (`ensemble_dims=[79]`); build it together with a separate 79-feature checkpoint. Builder reports three total networks, saves two extras but still `[79]`; reload yields only one extra. Test tensor identity/count after both construction and resave/rebuild. Also reject a malformed dimensions-list length instead of truncating it silently.

This is a genuine regression in the default homogeneous builder path, unrelated to `art_sap`. The isolated candidate should not need this builder: modify only a copied V3 config and verify all 18 original network states remain present and unchanged. Old V3 files without `ensemble_dims` use the fallback and are not affected by this particular defect.

### P3 / documented limitation — “Safe” means outside visible direct Manhattan targeting, not damage-safe

`_artillery_ok:441–446` correctly implements its narrow source docstring: no visible enemy with energy>=sap_cost is within Manhattan range. That exploits Solution_92's inspected `harvest` targeting rule. It is not the engine's Chebyshev sap safety region and does not exclude splash, hidden enemies, collisions, void damage or subsequent negative field energy.

Concrete splash example: artillery unit `(5,5)`, allied buddy `(6,5)`, armed Solution harvester `(9,6)`, range4. Shooter-to-artillery Manhattan distance5 passes the safety check; shooter-to-buddy distance4 permits a direct shot at the buddy, whose 3x3 splash also hits `(5,5)`. A separate three-enemy reachable cluster can satisfy art3's offensive condition. This does not make the artillery action illegal; it disproves a stronger “cannot be hit back” description. Include this case as a limitation test rather than automatically broadening the filter and creating another parameter trial.

### Separate siege issue, excluded from art3

`rules.SiegePlan:266` treats `belief.last_seen == belief.match_step` as actual current visibility. Belief updates `last_seen` for both direct and symmetrically mirrored sensor tiles, while terrain updates use direct sensors. Consequently, a mirrored unseen enemy-half point can be classified as visible and removed from the fog occupancy pool. This is incorrect visibility semantics, not hidden-input leakage. Minimal fixture: direct sensor only at the mirrored coordinate, target point itself outside sensor, positive opponent point gain; inspect fog membership. Siege is already development-negative and should remain excluded; no need to repair it as part of art3 confirmation.

## Legality and energy/action behavior

- Art3 consumes `ctx` values derived from the player's observation and belief: visible enemies/energy, own unit energy, public action parameters and inferred known points. No engine state, seed, `full_params`, future action or opponent internal state enters `_artillery_ok` or its action hook.
- The new mechanism observer separately reads true engine state/full parameters for attribution. Its inspected call sequence supplies only `info['params']` and each player's legal observation to agents. This is external diagnosis, not a deployment input. Its causal damage attribution has not been independently validated here and should not be treated as stronger evidence than the raw game results.
- Artillery is gated by `sap is not None` and the ordinary SAP action mask. `_best_sap_target` chooses an observed in-bounds center within the Chebyshev range. Player1 deltas use the existing canonical mirror conversion. Negative reserve does not bypass the mask's energy>=cost check, though only reserve0 is the proposed candidate.
- At energy exactly equal to sap cost, a shot is legal and can leave zero energy; zero is not immediate removal. Later field/splash/void effects can still kill the ship. `art_reserve=0` is not a survival guarantee. Do not revive the previously disproved argument that sap cost itself changes the engine's collision-energy comparison.
- The hook can replace movement as well as STAY and records the emitted action in `_prev_actions`. It leaves an already chosen SAP unchanged. A first owner on a known point tile is excluded; secondary stacked ships can fire. There is no team overkill coordination in this isolated rule.
- `siege` and `smart_sap` can override the shot afterward in other configurations. Both are off in V3/art3; do not infer those combinations satisfy the original art3 hit/reserve criteria.
- With art/siege/threat disabled and an unchanged legacy 79-feature checkpoint, no new artillery branch runs; feature shape and all ordinary Q inputs remain unchanged. The old-ensemble inference now slices `t[:, :79]`, which should preserve values. Static inspection is not a substitute for default-off replay equivalence on the actual candidate artifact.

## Meaningful missing checks before a fresh run

The incoming tests exercise two-hit STAY→SAP, a Manhattan threat veto, reserve rejection, holder exclusion and player1 mirroring. They do not directly test the selected three-hit configuration or replacement of a learned movement action.

Minimal additions/reproductions after the active CNN job ends:

1. Exact art3 threshold: two versus three nonnegative enemies around the chosen center; negative-energy counterexample and zero-energy boundary above.
2. A deterministic movement-preferring network: art3 emits SAP only in the eligible case, `_prev_actions` records SAP, an existing SAP remains unchanged. Include energy `cost-1`, `cost`, and reserve boundary `cost+reserve-1`/`cost+reserve`.
3. One player1 art3 case near the board/range boundary; final absolute center stays in bounds and deltas stay legal. Existing mirror test covers only the two-hit fixture.
4. Default-off actual-V3 replay equality across both sides, then reproduction of the fixed art3 development CSV under the exact source/weight/config/engine intended for confirmation. A changed rule must not be described as reproducing the old run merely because aggregate wins happen to match.
5. Check saved candidate config, identical 18 network tensors and network count after reload; do not involve threat/mixed/CNN artifacts.
6. The homogeneous ensemble append regression above, separately, before general integration of the builder changes. Full-suite claims remain pending where process-guarded tests were intentionally deferred.

No wide sweep, retraining, new safety heuristic, siege repair or observer rebuild is needed for this decision. The result to seek next is a clean independent acceptance or rejection of one frozen artillery candidate, not another favorable development maximum.
