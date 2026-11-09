# Independent match-weight technical data review — PASS

Checked actual completed four-game artifacts under source `a96ddebacc57d44945fe925f259ec72ddd58a02b`. Owner15472 and worker15489/group were independently absent before and after data arithmetic; owner complete, active empty, worker Exit0. No models, games, tests, project imports or repository changes.

One external CSV/JSON/NumPy data check exited0 with empty stderr: **528assertions passed;449hash bindings across443input/evidence files.** Actual admission, source/executable/input/protected maps, owner receipt and every receipt artifact match. Exactly four raw JSONL rows equal the receipt, with prescribed role/key order,303steps/v2, epsilon≈0.05, null losses, correct env progression60000→60303→60606per role, learn_steps0 and identical recorded initial/current/final Q/Target/Adam identities. Arm configs differ solely w_match2/20; no release exists for this technical stage.

| Fixed key, both roles | Transitions per role | Nonzero match-term rows | Win/loss outcome rows | Recorded outcome |
|---|---:|---:|---:|---|
|9946007/player_0|3489|45|45/0|3:0,785:304points|
|831006/player_1|3421|38|15/23|1:2,1252:1037points|

For each key, both roles have equal native/public trajectory, actual nonreward transition and final-action-audit digests, same counts and outcomes. Both initial identities match; Q equals Target. Recorded final-action checks cover all6910transitions per role and303act/updatecalls per game. These are paired archived live assertions, not full action/replay reconstruction.

All four actual compressed NPZs were loaded with pickle disabled. Schema, finite Float64 original reward/outcome streams, ordered int64UIDs0–15, lengths, array hashes and ordered counterfactual digests independently match. **Both roles' actual UID/outcome/control-formula/match-formula arrays are elementwise identical**, and their file hashes match pairwise. Each role has83nonzero match-term rows, including23negative and60positive outcomes.

Independently checked every formula row against18×outcome using the fixed abs1e−10/rel1e−12bound. Largest actual formula error:3.552713678800501e−15. Actual Float32 conversion of both formula streams produces quantization contrast up to9.536743190707853e−7; after subtracting those individually computed quantization errors, unexplained residual is at most2.6645352591003757e−15. This is precisely why bit-exact18subtraction of separately quantized values would be invalid. No tolerance was changed.

## Limits

No model tensors were loaded or recovered; unchanged Q/Target/Adam and zero-update identities remain recorded assertions. The technical runner archives both original-formula streams/outcomes but not a separate actual stored-r channel/full replay or raw contexts. Actual original push and Float32 buffer-slot equality were checked live by reviewed code; this audit independently establishes archived formula contrast/quantization, not recovery of those absent slots or a re-execution of unit_rewards. Native/action/nonreward digests are paired and file-bound; complete trajectories and original UID/action mapping cannot be regenerated from these compact artifacts. These four known games establish mechanism consistency and exposure, not strength or performance.

## Artifact hashes

- Checker `/tmp/match-weight-technical-audit/check.py`: `aff8cceb69228747aae3ffec108981637972da7f68d805990d58b67b12933d46`
- Results `/tmp/match-weight-technical-audit/results.json` and stdout `run.log`: `57bb0d95af4906d8ab87281fc11607f57e740a046caa11fedf964f63317e1cbf`
- Bindings `/tmp/match-weight-technical-audit/bindings.json`: `dce6fabf2b932ba990a74e8dcf782f557c473c6fd40f9b3a5f7575da945f3f58`
- Empty stderr: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Actual receipt: `fadbcc9c16b229f356b4c09e7eec02aa841898f88615b79aa8acf269179fdf9d`
- Admission: `552484350cc80c9fabcd58478c136ed14fd6a94d7b9ec8d1198430df9e4aa326`
