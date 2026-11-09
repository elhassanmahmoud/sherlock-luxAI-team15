# Independent pair49-v2 final audit — PASS

Executed the prepared, unchanged v2 checker exactly once after owner complete and an independent actual PID/PGID check. Owner31599 and original workers31622/31627 plus their groups were absent before Torch import/final archive access and again after the audit. Owner and workers completed successfully; no phase was launched or released by this reviewer.

**7,775 assertions passed; 526 hash bindings across475 input/evidence files; Exit0 and empty stderr.** Actual HEAD/source remains `207f504cf75920e4569ef3084b6cd916df76243c`. Admission, source/executable/input maps, V14/ZIP protection, receipts, Root review and actual manual release all match. Release SHA is `153425cd9b6fd716fa8b23e60aa2d4e0f4921629f152d6827dbcaeeb026c14b0`.

| Actual completed evidence | Control | Match |
|---|---:|---:|
| Fixed games |40prefill+400learn|40prefill+400learn|
| env_steps |193,320|193,320|
| Actual checkpoint/Adam updates |60,000|60,000|
| Finite reported learning-game means |400|400|
| Total replay insertions |1,579,058|1,583,947|
| Retained final replay rows |300,000|300,000|

Both440-row raw logs exactly equal their final receipts and the independently regenerated NumPy49opponent/seed/side sequence. Every game has303steps, points v2, correct result/point arithmetic, fixed epsilon and exact before/after environment and optimizer counters. Reward/UID/final-label live-audit counts cover every inserted transition and every303act/update boundary. All400recorded learning-game mean losses per arm are finite and nonnegative. The accepted40-row prefill prefix, proof/file/result/script/report hashes and waiting markers remain unchanged; accepted prefill NPZ arrays were not loaded again.

After process exit, actual `final.pth` files were loaded as CPU weights-only data. Both contain the expected finite Float32 twelve-parameter79→256→256Dueling networks, six actions, no ensemble, correct role/start49/member18/config and complete440-game metadata. Independently reconstructed actual Q/Target/Adam identities match each receipt. Both Qs differ from their accepted initial identity and from each other. Final Q equals Target exactly at update60000. Every actual Adam parameter has a finite scalar step exactly60000 and finite, correctly shaped first/second moments; second moments are nonnegative. Actual optimizer settings match the fixed learning rate and default Adam configuration.

Both final replay NPZs were independently loaded: exact six-field schema/dtypes, inferred full ring size300000, finite79-column current/next states and rewards, six-action labels, binary terminal flags and nonempty six-action masks. Independently reconstructed full replay hashes match the receipts. Post-learning trajectories may differ and were not required to remain paired.

Actual checkpoint hashes:

- Control: `499ff53fd318e507e31036b73920e5792b5c47443a24d91d880e7aa2a111ee01`
- Match: `5e861a989c163f730db14d083ddf8413376036ac18a8ea9603e3b764dfe1708f`

Actual receipt hashes:

- Control: `9d41acd361d7a08505aa546c922e409f96dc838764aa273696ff4c196b32298a`
- Match: `93d0a96d861f5a3b14cd19456d06498d89c0fae69d0868f5df10f8315461b0ae`

## Limits

All actual final tensors, Adam counts and final ring arrays are recovered independently. Only400game mean losses per arm were archived, not the individual60000batch losses. The successful bound game path refuses caught errors on either player; raw rows do not separately archive each player's error counter, so zero-error enforcement is a runtime assertion. Complete training contexts/UID/outcome/counterfactual streams and displaced replay rows are absent; original reward formulas and per-game nonreward digests cannot independently be reconstructed from final replay alone. Their live audit coverage and digests are bound, while the separately accepted full prefill contrast remains unchanged.

This accepts completed pair49-v2 training data only. It establishes no performance improvement, nomination, V14 replacement or authorization for comparison/performance. No new games/tests/training, project imports, repository/source changes or release writes occurred.

## External artifacts

- Checker `/tmp/match-weight-pair49-v2-final-audit/check.py`: `44271ccae6089dda9698a387e42c97ecfed4f74a588ea575f9837a80401988cd`
- Results `/tmp/match-weight-pair49-v2-final-audit/results.json` and `run.log`: `dfc503233806b7d2e7315236242519999f9bc5efceefc16517beb154b317bc11`
- Bindings `/tmp/match-weight-pair49-v2-final-audit/bindings.json`: `d4ad21f361899f3cdb5d30c19c328140193e9c0ca510cb8cd85aed923f4183b9`
- Empty stderr: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
