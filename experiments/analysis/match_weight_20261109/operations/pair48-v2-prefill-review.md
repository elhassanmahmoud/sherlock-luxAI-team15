# Independent pair-48 v2 prefill review — PASS

Checked the actual completed forty-game prefills under source `207f504cf75920e4569ef3084b6cd916df76243c` and admission `f49d770fb7f4f7688434b7a371151aa5b72bd75c752bf756fde4c7f69f23dcac`. One external JSON/NumPy check: **997 assertions passed, 455 file-hash bindings, Exit 0, empty stderr**. No Torch/project imports, model deserialization, tests, games, repository edits or release writes.

Before and after arithmetic, owner 21015 and original workers 21033/21038 were independently alive with the correct process groups/parent. Owner remained running with both roles active, each worker had no returncode, and both current waiting markers matched the actual prefill hashes. No release existed during either check.

- Exactly forty raw rows per arm match the independently regenerated NumPy-48 opponent/card/side schedule on 9960300–9960319. Every game has 303 steps and points v2; env_steps progress from 60000 to 72120, learn_steps remain 0, losses are null, epsilon remains approximately 0.05. Both arms have the same recorded 30 wins/10 losses; these are prefill outcomes, not a strength comparison.
- Each actual preserved replay contains **142,110 transitions**, below capacity and sufficient for learning. Shapes/dtypes, finite values, six-action labels, binary done and nonempty next masks pass. Every original prefill transition is preserved; no ring rows were displaced.
- Across arms, actual `s`, `a`, `ns`, `done` and `mask` arrays are **bit-for-bit identical**. Actual ordered UID, outcome and both Float64 original-formula arrays are also bit-for-bit identical. Reconstructed full/nonreward/stream identities match the proofs. All eighty per-game ordered nonreward and formula digests were independently regenerated from the actual persisted data.
- For each arm, actual stored Float32 `r` is **bit-for-bit equal** to Float32 conversion of that arm's archived original-formula stream. Stored rewards differ as intended on outcome exposure and are bit-identical between arms without outcome. Each arm contains **1,757 nonzero match-term rows: 1,320 positive and 437 negative**.
- Every Float64 formula contrast satisfies the prespecified `18 × outcome` check (abs_tol 1e−10, rel_tol 1e−12). Maximum actual formula error: **3.552713678800501e−15**. Actual stored Float32 subtraction has concrete quantization contrast up to **9.536743190707853e−7**; after accounting for each individually measured quantization error, unexplained residual is at most **3.3306690738754696e−15**. Tolerances were unchanged.
- Both roles' initial/current Q, Target and Adam identities match their initial files and each other, with Q equal to Target and zero recorded learning. These are recorded live identities; this reviewer did not deserialize checkpoint tensors. Root's separate original validator supplies the tensor inspection.

Actual prefill hashes:

- Control: `ca972ec02071bb01ef2cf7f482487a53388bf7d6dfa5f9086234ba723df29ad5`
- Match: `2b8821c7c79b394f3a2a57210ab0886e3a33da3dac08e6d864e5a27ee2363068`

## Limits

The full actual prefill replay and both original-formula/outcome streams are independently recovered, including actual stored r; original formula provenance cannot be re-executed without complete contexts. Native/public/final-action digests are paired and bound, but raw action/trajectory streams are absent. Initial tensor equality and zero-gradient counters remain recorded assertions in this data-only check. No inference about training completion, general strength or promotion is made. No learning release was issued by this reviewer.

## Artifacts

- `/tmp/match-weight-pair48-v2-prefill-audit/check.py`: `86cc63b6fb06623af6a9876472522389cd6dddcb79058d95e2ee5e057bfd734d`
- `/tmp/match-weight-pair48-v2-prefill-audit/results.json` and `run.log`: `62cf2c59dde2d62f2081aa3acec8648466e3cd05ca72466d75738fea040980b6`
- `/tmp/match-weight-pair48-v2-prefill-audit/bindings.json`: `e1d0936e77e7b82615c1e188fe0d136eada953b4d950f5aeaa2ab464c110f868`
- Empty `run.stderr`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

The accepted checker was rebound only to v2 paths, admission and current source. Numerical/pairing logic was unchanged. V1 files were not written; the actual full/nonreward/formula hashes also reproduce the earlier v1 prefill identities. This does not reinstate the abandoned v1 learner or combine partial training.
