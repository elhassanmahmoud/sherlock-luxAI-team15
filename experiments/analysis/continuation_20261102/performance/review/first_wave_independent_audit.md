# Independent first-wave acceptance

**ACCEPTED_FIRST_WAVE_ONLY** — 1762 checks, 0 failures. **PT remains inadmissible without the completed index19 pair.**

Both arms have720 exact raw rollouts (120prefill+600train),96 known P-validation games and600 ordered training CSV rows. Source plans/configs/HEAD/protected hashes match; paired actual opponent/card/side sequences agree and only the two role flags differ. Initial component18 and fresh learning state agree with pinned actual-loader evidence. Prefill changes neither q/target/Adam nor learn_steps. All600 learning episodes have150 actual updates, yielding90000; env_steps=60000+720×303=278160. Every Adam slot has step90000 and finite moments; final q/target are finite, changed from source, and exactly synchronized. Serialized q/target/optimizer hashes equal the recorded live/reloaded end proof. Validation restores learning and own/global RNG identity.

RNG comparison boundary: actual finetune initialization correctly uses global seed4228, while convenience preflight used28; both Python state hashes were independently reproduced, and actual paired initial global/own RNG states agree. Between separate training games, scheduled DefaultAgent construction resets global NumPy state; before-game300 therefore need not equal the previous post-game global hash. Milestone checks preserve the complete learning and own-agent RNG identity; exact global before/after equality remains required within each validation.

The original supervisor remains incomplete with its exact known KeyError. Its pinned source and receipt remain preserved; this is acceptance of two actual complete arms, not all-four orchestration completion. No repository files, source, HEAD or weights were changed. No Agent construction/forward/gradient/game occurred.

Known validation W/D/L (16 games per opponent/time) is descriptive only:

| Arm | After training games | Default W/D/L | Solution W/D/L |
|---|---:|---|---|
| control18 | 0 | 16/0/0 | 15/0/1 |
| control18 | 300 | 16/0/0 | 14/0/2 |
| control18 | 600 | 16/0/0 | 14/0/2 |
| adapt18 | 0 | 16/0/0 | 15/0/1 |
| adapt18 | 300 | 16/0/0 | 16/0/0 |
| adapt18 | 600 | 16/0/0 | 15/0/1 |

These reused known maps neither nominate a policy nor establish strength. Exact per-match/point totals and checks are in first_wave_independent_audit.json.

Root patch note for the deferred four-arm auditor (not applied):

- Its `actual_initial_matches_preflight` currently compares complete proof dictionaries. Compare all learning state, q/target, complete config, optimizer/replay, counters and own-agent RNG exactly, excluding only `global_rng_sha256` and `initial_identity.rng_sha256` from convenience-preflight equality. Preflight uses global runseed28/29; actual finetune uses the fixed runseed+4200=4228/4229. Independently check the actual Python seeded-state hash and require both actual partners' global and own RNG identities to agree. This partial audit verified both28 and4228 Python hashes exactly.
- Its `before_train_milestones` compares an earlier post-rollout global hash to a snapshot taken after the next opponent constructor. Remove only global_rng_sha256 from that cross-episode equality; keep all learning/own-agent RNG fields strict, while normalizing learn_enabled only at the prefill-to-training boundary and accounting for intentionally consumed recent_losses. Scheduled game300 has opponent default; the existing constructor sets NumPy seed0 before the next common.play_game reseeds global RNG from its game seed.
- Do not alter validation checks: each actual validation before/after identity, including global_rng_sha256, remains exactly equal. Both arms pass all three strict validation isolation records. No observed validation drift was excused.

The existing four-arm script has not been edited by this partial-wave task. Final checkpoint reads used one short audit process at a time, with no trainers active; no third model worker was launched.
