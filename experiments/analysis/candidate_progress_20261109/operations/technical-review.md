# Independent candidate-progress technical review — PASS

Actual completed artifacts checked under source `c023b28bd4369ffc1c32b5347fb8574bdd42c472`. Owner11116 and worker11139/group were independently absent before any tensor archive load and again after the audit. State is complete, active empty, worker Exit0; exactly four fixed JSONs match the final receipt. **1,468 assertions passed,449hash bindings across444input/evidence files; corrected checker Exit0, stderr empty.** No new games, agents, tests, project imports, repository/Git writes or source changes.

| Role/key | Early steps / unit-steps | Match wins | Points | Native action digest |
|---|---:|---:|---:|---|
|OFF9946007/player_0|0/0|1:2|739:507|b896825b5af59984e23ecabe521c41a8793b2c0b17f2fdf287b7e613640e1fd0|
|ON9946007/player_0|3/48|3:0|936:352|d6ccf885373e8293f20c0807010021f1d74afe27ba6183a91948b223458bcd68|
|OFF831006/player_1|0/0|1:2|1088:1205|90b2269ed7f97e97aba7e5953a2020f1bafb7e99822165b39cc0ce904fc4386f|
|ON831006/player_1|0/0|1:2|1088:1205|90b2269ed7f97e97aba7e5953a2020f1bafb7e99822165b39cc0ce904fc4386f|

Both OFF rows independently equal every archived baseline field, including native action hash, all three match point/win records, overall result and zero errors. Every game has303steps,3resets,300decisions and points v2. Matchpoint sums/winners are consistent with the player's side;831006/player_1 stores its per-match arrays in global team order. ON has recorded real early-hook exposure and native divergence on9946007/player_0; the other key remains equal. These known technical outcomes are not a strength test.

The actual OFF/ON model archives and original V14 were loaded as CPU/weights-only data after process closure. All36members in original order, every parameter tensor and target, and every non-configuration checkpoint field are identical to original V14. All member tensors are finite. Independently reconstructed tensor identity matches both receipts: `6c9f2bc37e72f78c12269ebb48c06b16f091b1d338c0d9c7ba1a6566deaa5afd`. Configs match independently reconstructed current defaults overlaid with all original explicit settings, with only `frozen=False` and the OFF/ON flag specified. OFF and ON differ solely in `cand_stall_rescue`.

A first external checker stopped because it incorrectly compared the historical72-field raw configuration against170normalized fields. Investigation confirmed all72explicit original values unchanged and every missing field equal to the literal current default. Only the external checker was corrected, using AST-read defaults without project imports. Its first script/error log are preserved; one corrected data-check execution then passed. This did not repeat a game or modify project code.

The separate Root prelaunch path correction has SHA `e05a680ce13ac85573a5a49394d5062872b6277c8085944daef4f0c643df0d64`. Its error log hash `a796726e430f7b00c225bda749bf4210ce4fddce1304e2b56a90f6ad231179e3` matches actual bytes and fails at usage-path validation before owner output creation/worker spawn. It is not a repeated model attempt.

## Limits

The runner did not archive raw action arrays, full trajectories or per-step early target snapshots. Action-digest reproduction and48deduplicated early UID-step queries are archived live assertions, independently compared and file-bound; reviewed source enforces the current candidate-target gate. Actual saved model tensor/config equality is independently recovered. Post-game live tensor equality remains the runner's recorded assertion. No general performance claim, nomination or V14 replacement follows from these four consumed keys.

## Artifacts

Machine-readable findings: `/tmp/candidate-progress-technical-audit/results.json`, SHA `3d82a388da2a2a97c5c4c68eb4503bc7961fc6319cd919ae085d7dc2921e6d9f`.

Hash bindings: `/tmp/candidate-progress-technical-audit/bindings.json`, SHA `24c8d3dc3f89d8cd2ac60ba13c4a7ca85d050d967a55a61b900b9d39f31f6f9a`.

Corrected script: `/tmp/candidate-progress-technical-audit/audit.py`, SHA `ca320632ca584353c572a909cf006633d121bf3054774fef03d31be1ac0b2b45`.

Actual technical receipt SHA `a8ce83fb94e36cace006976aecfad1b1036a7c96f4e71b338181ae57faec08d1`; admission SHA `ce1e7605c52e8fe8c65e5a4ca76f6349c1e18c73320fd63dfcd66b5e91951ab0`.
