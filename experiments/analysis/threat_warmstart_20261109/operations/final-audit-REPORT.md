# Independent final training audit — PASS

The unchanged prepared script was executed once after explicit Root authorization. Exit0; stderr empty. Before importing torch or loading end files, it independently required owner `complete`, both worker returncodes0, empty active list, and actual absence of owner92788 and worker92800/92805 PIDs and process groups. The same process checks passed after the audit. No model agents/environments, games, tests, stop/release writes, project imports, Git actions or repository writes occurred. The accepted prefill audit was hash-pinned and reused; its NPZ arrays were not loaded again.

**32,333 assertions passed; 481 file-hash bindings across448 distinct input/evidence files. No mismatch or failed assertion.** Both actual end receipts, every bound artifact, recorded source/input/protected maps, executable bytes, actual Root review/release and prefill audit pins agree under recorded source `af8b2711d37a9fd4509415972345c5849c21db62`.

| Actual final evidence | Control | Threat |
|---|---:|---:|
| Completed fixed games |40prefill+400train|40prefill+400train|
| Environment steps |193,320|193,320|
| Checkpoint/Adam updates |60,000|60,000|
| Reported finite training game mean losses |400|400|
| Total replay insertions |1,586,176|1,588,556|
| Final retained replay rows |300,000|300,000|
| Nonzero current feature-tail rows |0|129,339|
| Nonzero next feature-tail rows |0|130,096|
| Retained whole games independently rehashed |83|83|
| Retained compact examples matched |332|332|

The raw440-row game logs exactly match each receipt and the independently regenerated NumPy47 fixed plan. Every game has303steps and point-counting v2. Environment/optimizer counters follow the exact cadence throughout, summing to120,000 actual optimizer updates across both arms. All400 recorded training game mean losses per arm are finite and nonnegative; prefill losses are null.

Both actual `final.pth` files were loaded with CPU/weights-only loading after process gates. All twelve expected Dueling parameter tensors have the exact101→256→256 architecture, float32 type and finite values. Actual Q/Target/Adam typed identities match their receipts. Every Adam parameter state has step60,000 and correctly shaped finite first/second moments; variances are nonnegative. Q equals Target exactly at the final500-step synchronization. Both Q identities differ from their recorded initial identity, and final Q identities differ between arms.

Control Q/Target input suffixes are exactly zero, as are corresponding Adam moments. Threat Q/Target suffixes are nonzero. Persisted batch audit records60,000 sampled batches per arm; control has zero exposed samples/extra-column gradients. Threat records5,935,791 current and5,976,672 next exposed samples and60,000 steps with nonzero extra-column gradients. These gradient/batch counts are live assertions, consistent with actual final tensor and replay contrast.

Actual final NPZs each contain300,000 finite valid transitions with101-column current/next states, six-column nonempty next masks, legal action labels and binary terminal flags. Independent full and original79 array identities match the receipts. Reconstructed chronological ring-buffer bounds agree with all recorded insertions. Every wholly retained game (166total) has independently recomputed full and original79 transition digests matching its recorded row;664 compact examples match actual same-game replay slices. All retained control tails are zero; threat current/next tails exhibit the exposure counts above. Post-learning trajectories differ as permitted; equality of final original79/action/reward arrays is not an acceptance condition.

## Evidence limits

Individual60,000 batch losses per arm were not archived: only400game means per arm can be independently checked finite. Complete observations/native-action trajectories, initial tensor archives and sampled batch/gradient histories were not retained. Their recorded identities/digests and public-feature/gradient assertions cannot be independently regenerated in full. Only whole games still retained in each final ring buffer were rehashed; displaced training transitions are unavailable. Earlier prefill recovery and equality rely on the separately pinned4555-assertion audit, not a repeated scan. No evaluation or playing-strength conclusion follows from this technical acceptance.

## Artifact hashes

- `audit_final.py`: `b3a8875de3a8ae2c23e2bf6ae987bcd78841f7c94080d68c457f6587b7df967b`
- `results.json` and `run.log`: `e3bf5e62ab3292494100050c3c38bbf022aeb798c0d3474ffcc875b59d8752e4`
- `bindings.json`: `0313c2fb8b8f3096d69ae33aabd1284f7be82a10396311db8c2c5d449db68a48`
- Empty `run.stderr`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
