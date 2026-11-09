# Independent pair48-v2 final audit — PASS

Executed the prepared, unchanged v2 checker exactly once after owner complete and an independent actual PID/PGID check. Owner21015 and original workers21033/21038 plus their groups were absent before Torch import/final archive access and again after the audit. Owner and workers completed successfully; no phase was launched or released by this reviewer.

**7,769 assertions passed; 520 hash bindings across472 input/evidence files; Exit0 and empty stderr.** Actual HEAD/source remains `207f504cf75920e4569ef3084b6cd916df76243c`. Admission, source/executable/input maps, V14/ZIP protection, receipts, Root review and actual manual release all match. Release SHA is `9eae20cf3dd4dc376f07fa3e914c1f13baed4a7763b54a63be778149ddeb105e`.

| Actual completed evidence | Control | Match |
|---|---:|---:|
| Fixed games |40prefill+400learn|40prefill+400learn|
| env_steps |193,320|193,320|
| Actual checkpoint/Adam updates |60,000|60,000|
| Finite reported learning-game means |400|400|
| Total replay insertions |1,575,665|1,580,128|
| Retained final replay rows |300,000|300,000|

Both440-row raw logs exactly equal their final receipts and the independently regenerated NumPy48opponent/seed/side sequence. Every game has303steps, points v2, correct result/point arithmetic, fixed epsilon and exact before/after environment and optimizer counters. Reward/UID/final-label live-audit counts cover every inserted transition and every303act/update boundary. All400recorded learning-game mean losses per arm are finite and nonnegative. The accepted40-row prefill prefix, proof/file/result/script/report hashes and waiting markers remain unchanged; accepted prefill NPZ arrays were not loaded again.

After process exit, actual `final.pth` files were loaded as CPU weights-only data. Both contain the expected finite Float32 twelve-parameter79→256→256Dueling networks, six actions, no ensemble, correct role/start48/member18/config and complete440-game metadata. Independently reconstructed actual Q/Target/Adam identities match each receipt. Both Qs differ from their accepted initial identity and from each other. Final Q equals Target exactly at update60000. Every actual Adam parameter has a finite scalar step exactly60000 and finite, correctly shaped first/second moments; second moments are nonnegative. Actual optimizer settings match the fixed learning rate and default Adam configuration.

Both final replay NPZs were independently loaded: exact six-field schema/dtypes, inferred full ring size300000, finite79-column current/next states and rewards, six-action labels, binary terminal flags and nonempty six-action masks. Independently reconstructed full replay hashes match the receipts. Post-learning trajectories may differ and were not required to remain paired.

Actual checkpoint hashes:

- Control: `931ae709779144d578cdf8134f8ef8bb777c653f3f390426a96e03eb141d2429`
- Match: `9e8cef664136d5b5e5f36a9a3de43cc60425dcd3ad2c33cee043d59c6022b6d0`

Actual receipt hashes:

- Control: `98d0a007ddc3698f18c385ec773adad61e0a4ad6062b6309f27de20247e78aad`
- Match: `f4bbc016623b27227641cf5a6b59eff5691dba78c1152585284301e2229d7859`

## Limits

All actual final tensors, Adam counts and final ring arrays are recovered independently. Only400game mean losses per arm were archived, not the individual60000batch losses. The successful bound game path refuses caught errors on either player; raw rows do not separately archive each player's error counter, so zero-error enforcement is a runtime assertion. Complete training contexts/UID/outcome/counterfactual streams and displaced replay rows are absent; original reward formulas and per-game nonreward digests cannot independently be reconstructed from final replay alone. Their live audit coverage and digests are bound, while the separately accepted full prefill contrast remains unchanged.

This accepts completed pair48-v2 training data only. It establishes no performance improvement, nomination, V14 replacement or authorization for pair49. No new games/tests/training, project imports, repository/source changes or release writes occurred.

## External artifacts

- Checker `/tmp/match-weight-pair48-v2-final-audit/check.py`: `c626978347d2828eca1fe7ca6a24d99a90085ac0a32d5ee382c4d3887d55ee9e`
- Results `/tmp/match-weight-pair48-v2-final-audit/results.json` and `run.log`: `f5811b8e0e6cdb9104a5c497c8b4cb797bc52e3ada5d8a77345fdcfa89137235`
- Bindings `/tmp/match-weight-pair48-v2-final-audit/bindings.json`: `2e4f008d9de713c19012ecaa60bb58e13eab7b3e08be0b17ff3aba790998709f`
- Empty stderr: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
