# Independent final Fog training audit

**PASS — technical training acceptance under frozen source a3111c3d0aa0aa974298daabe300bba7be157da1.**

All four workers ended before any model import. No games, gradients or tests were executed by this audit.

Each arm has 40 prefill + 400 learning + 32 diagnostic executions, 60000 optimizer updates and 193320 environment steps. Total: 1888 study executions, 240000 updates.

| Arm | Q tensor SHA-256 | Target tensor SHA-256 | Adam SHA-256 |
|---|---|---|---|
| control41 | 02932ab0c275097d7e28ab764acfa3bbe347ef3d8484889f0208a69b5676ec88 | 02932ab0c275097d7e28ab764acfa3bbe347ef3d8484889f0208a69b5676ec88 | 8217dc6364467341dd6ca6cbee1c5a6a3e15c72579e498b8b6d1d63d0328005d |
| neutral41 | 34259aaa7e172a969e127d52bab5676a1869a497af8cfa88a8e5326c29be0077 | 34259aaa7e172a969e127d52bab5676a1869a497af8cfa88a8e5326c29be0077 | 0aec5586bfeba394c577fb408950dd45de362042d0411c9a70aceffe989357d4 |
| control42 | 6e606eb8acf89d327e7a869b18e313d8bbff02e2189c4c04f605632bb740df3c | 6e606eb8acf89d327e7a869b18e313d8bbff02e2189c4c04f605632bb740df3c | 4de518ddc34ebade699ea2c0f7c32aad8f00369a14ab73f9ae351aa87f0bdbda |
| neutral42 | 84c0daef896814b18e9ece56c6d5bc829dd2e6035f7a1b36624cdda671eae348 | 84c0daef896814b18e9ece56c6d5bc829dd2e6035f7a1b36624cdda671eae348 | 137d2a4d30da970342ee83fe1e7c09922069a72961a18ae14f8f398b1c257681 |

Independently loaded saved Q/target/Adam are finite and changed from their exact component-18 starts; every Adam state records 60000 steps. Saved hashes equal final live-state audit hashes. Fixed schedules, all raw rows and CSV chronology, actual reward-formula selection/mass, replay coverage, isolated diagnostics and both prefill admissions pass. Source inventory/content, HEAD, interpreter, preparation and protected V14/ZIP hashes were verified before and after the audit. Full artifact bindings and per-arm counters are in the companion JSON.

This historical acceptance was produced before changing HEAD/source. Future work should consume these hash bindings; it must not pretend that the current HEAD still equals the training HEAD.

Limits: Technical training acceptance only; no strength or promotion decision. Trajectory/replay content identity is audited from frozen recorded hashes and raw summary rows; simulator states/replay insertions were not independently replayed. Saved tensors loaded independently with Torch; runtime actual Agent reload proof is bound from worker evidence, not rerun by this auditor.
