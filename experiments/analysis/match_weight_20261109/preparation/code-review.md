# Independent match-weight code/method review — PASS

Read the final study runner, owner, both focused test files and supplied final logs against the fixed plan, `/tmp/match-weight-runner-design.md` and actual unchanged Core._update/unit_rewards/action_audit behavior. No blocking findings. No tests, model loads, agents or games were executed by this reviewer; no repository edits. Real technical and pair-result acceptance remain separate Root work.

## Actual reward intervention

The runner constructs two config copies differing only `w_match=2/20`; all other fixed79-feature/member18/rule/reward settings are common. It uses the unchanged original unit_rewards function and cumulative match-win delta, not total points, raw engine reward or generic done. No finetune globals, reward monkeypatch, new target, validation or best-checkpoint path is introduced.

An instance-local wrapper observes every actual ReplayBuffer.push. It binds the original `_prev_feats` UID order to the final canonical action, original s, actual cached next feature/mask, alive/dead handling and original match/death terminal. The independent existing action_audit simultaneously binds returned native actions, including mirror transformation, to actual replay labels/counts. Legitimate final rule actions outside the earlier network mask are counted rather than rejected.

At each update the observer recalculates both original formula streams on the same live contexts and checks the actual push reward exactly against its role's original value. After original_push it checks the actual buffer slot: exact Float32 reward conversion, label, current/next arrays, terminal and mask. This is a real storage check, not a logging-only contrast. Dying units retain the cumulative match-outcome term.

Formula difference is checked against18×outcome with the prespecified abs_tol1e−10/rel_tol1e−12. Offline evidence verifies the actual stored Float32 value against the role formula and accounts for each measured original-to-Float32 quantization error; only the fixed Float64 arithmetic residual remains. No tolerance derives from real results.

Four technical compressed arrays now preserve ordered UID/outcome/both original rewards and bind their hashes in each row/receipt. Offline technical checks verify the formula contrast and exposed outcomes. These arrays do not contain an independent raw actual-r field: exact actual storage is checked live; unlike prefill, technical replay itself is not archived. That limit must accompany later independent data claims. Full actual prefill replay plus both raw reward streams are preserved and independently recoverable.

## Pairing and Root barriers

The exact original V14 member18 is loaded through the existing strict source validator. Q=Target, fresh Adam, empty replay, env_steps60000, learn_steps0, seed48/49 and epsilon≈0.05 are checked. Normalized configs are verified against the actual source. Separate fixed440plans contain40prefill+400train games per role; cards/sides/opponents match the plan, no extra validation games or restart path.

Native actions, public trajectory, results, final action-label audit, all actual nonreward transition fields and both counterfactual formula streams are paired before gradients. Prefill proofs bind actual ordered replay/metadata, both counterfactual streams and saved unchanged Q/Target/Adam. Only actual r is omitted from paired nonreward identity. Real nonzero match-outcome exposure and sufficient replay are required.

Each original worker writes prefill plus waiting evidence and waits. Root approval loads actual saved prefills, checks both roles/start/source/admission/config/paired fields and waiting markers, and requires a separate PASS Root review bound to both actual prefill hashes. The exclusive atomic release cannot overwrite an old release. Workers alone cannot create it; learning is enabled only after validation. Pair49 separately requires a source-bound accepted pair48 closure; owner never chains phases or releases learning automatically.

Owner/worker argv, PID/PGID/parent, source, admission, protected files and usage/STOP/signal checks use the existing guards. One Lux environment is reused and closed per worker. Maximal two original model workers. STOP/failure preserves an explicitly ineligible incomplete checkpoint with no continuation. Opponent and own caught-error counters now invalidate each game through require_no_agent_errors.

After exactly400learning games, complete metadata requires193320env_steps and60000updates. End checkpoints and replay are hashed; saved actual Q/Target/Adam step counts, changed finite Q, chronology and finite reported game losses are validated after both workers exit. No training-start winner selection exists. All four end models still require separate actual acceptance; no strength or performance result follows from code review.

## Supplied verification read

- Study22synthetic tests PASS in2.93s: actual push/storage, shuffled UID order, dying unit, ±1/0outcomes, Float32 quantization, native mirror-label composition, actual synthetic saved prefill/release contract, incomplete/env cleanup, four persisted technical arrays and opponent error refusal.
- Owner19tests PASS in2.52s: technical/pair48/pair49 API, exactly one phase/no retry, manual waiting release, receipt identity failures, quota/STOP/source-change cleanup and final validator ordering.
- Root integration41tests PASS in2.96s. These are supplied actual logs, not tests rerun here. Suites forbid released archive loads and real engine games.

## Reviewed bytes

| File | SHA-256 |
|---|---|
|scripts/match_weight_study.py|51ae12833922c5167f6318fa9b14f99528b1d207a5e0a21b19e2ad04aac32b41|
|scripts/match_weight_owner.py|d6e277bab1ccdb7941670261407fb0a8fc1fe90be6addace9c776cc5451c8762|
|tests/test_match_weight_study.py|1d21b95c32848669855a7f957887b5d8442d24d69df0cc7f72ac9be23b82c78b|
|tests/test_match_weight_owner.py|8dfbf8c9e2588e0c6e477e96a33cccbb96f96005e0b01b213f4716e8b78017af|
|/tmp/match-weight-impl/green-3.log|43ec7624b61719a9c05ed795aa312424b85e6c94da4973cb719172f85afc3186|
|/tmp/match-weight-owner-implementation/final-tests.log|268b38fc5ecfd318aad1f31a974afe302b33cbac374387f059935b21da026a61|
|/private/tmp/match-weight-integrated-tests.log|28b58686c1c02969628f4a4fcb0a53ab85fa6bebe49ccfcb656b234e561e3692|

## Evidence limits for later reports

Technical/prefill numerical streams permit independently checking the analytical contrast and Float32 quantization; technical actual storage/contexts remain runtime assertions, while prefill actual r is archived. After learning begins, contexts and all counterfactual rows are not retained, so original formula/UID checks are live assertions plus per-game digests; final replay alone cannot reconstruct all original reward contexts or displaced rows. Individual batch losses are not archived; finite game means do not independently establish every batch loss. Manual Root admission and actual result audits must preserve these distinctions.
