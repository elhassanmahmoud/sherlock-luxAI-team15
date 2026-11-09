# Independent match-weight technical-v2 review — PASS

Reused the accepted external checker with only v2 output/admission paths and current source binding changed; no new numerical or pairing method. One execution exited 0 with empty stderr: **531 assertions passed, 452 hash bindings across 446 input/evidence files**. Actual source `207f504cf75920e4569ef3084b6cd916df76243c`; admission `aa2961c96284366d2b15174a2b3cebd7e8fd7adb3c94a94a6b9a2b5e89a9a25f`. Owner 20578 and worker 20605/group were independently absent before and after arithmetic, with complete state, active empty and Exit 0.

Exactly four actual JSONL rows match the receipt and fixed role/key order. Every game has 303 steps, points v2, zero recorded learning, null loss, unchanged recorded initial/current/final Q/Target/Adam identities and correct counters/epsilon. Role configs differ only w_match 2/20. Native/public/nonreward/final-label digests, outcomes and counts match pairwise.

| Key, each role | Transitions | Exposed outcome rows | Positive/negative | Recorded outcome |
|---|---:|---:|---:|---|
|9946007/player_0|3489|45|45/0|3:0, 785:304 points|
|831006/player_1|3421|38|15/23|1:2, 1252:1037 points|

All four actual NPZ arrays have the expected finite typed UID/outcome/two-original-formula schema. Pairwise arrays are elementwise identical; independently reconstructed array and ordered counterfactual hashes agree. Each arm has 6,910 transitions and 83 exposed match-term rows. Every formula contrast satisfies the unchanged abs 1e−10 / rel 1e−12 bound against 18×outcome. Maximum formula error is 3.552713678800501e−15; concrete Float32 quantization contrast reaches 9.536743190707853e−7, leaving at most 2.6645352591003757e−15 unexplained residual. No tolerance changed.

## V1 preservation and reproduction

Every v1 technical receipt artifact retains its original hash. The interruption closure, stopped pair48-v1 owner state and incomplete checkpoint bytes agree with their accepted hashes; both v1 prefill proofs and all their preserved files agree with the accepted proof/file hashes. Twenty previously hash-bound v1 evidence files were checked unchanged. There is no complete prior byte-hash baseline here for every unbound v1 raw log, so no broader historical claim is made.

All four new native-action digests, recorded outcomes/counts and compressed original-formula NPZ file bytes equal the corresponding v1 values. This is an additional reproducibility result on known technical keys, not new performance evidence. The v2 code writes only separate v2 outputs; this audit wrote only external artifacts and issued no release or next-phase admission.

## Limits

No models, agents, games, tests, project imports or repository/source changes. Initial/final tensor identities and zero-update counters remain archived live assertions in this data-only audit. The technical runner archives both original-formula/outcome streams, not a separate actual stored-r channel/full replay or complete contexts. Actual push/Float32 slot equality was checked live by reviewed code; offline formula contrast/quantization is independently recovered. Raw trajectory/action/UID-label reconstruction is unavailable. Four consumed technical keys provide mechanism consistency and exposure, not a strength conclusion.

## Artifact hashes

- `/tmp/match-weight-technical-v2-audit/check.py`: `e94080b6c9d038be881af01b445775f8786f1de26ddaa2b4a1567eddefa5967b`
- `/tmp/match-weight-technical-v2-audit/results.json`: `c3efba613727a0834b8654f83e7aee4676dc3d9ecda6de4e2cddf54f69b77255`
- `/tmp/match-weight-technical-v2-audit/bindings.json`: `a687d07614a82b3aa23fdba84e765719296c6ea455f218150f2e96b99ddf52a9`
- `/tmp/match-weight-technical-v2-audit/v1-preservation.json`: `a71ef1e72ebd64d2186ae65feb26713405da16398996dc60f720c4b3459975b3`
- Actual v2 technical receipt: `3e4de943b8dd74d1a674d6effeb18931bdcb87ebed57d08d523312f0b2ff285b`
