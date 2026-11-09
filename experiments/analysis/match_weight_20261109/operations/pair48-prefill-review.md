# Independent pair-48 prefill review — PASS

Checked the actual completed forty-game prefills under source `a96ddebacc57d44945fe925f259ec72ddd58a02b` and admission `317e315d7008d58df45d5eb807f9e7a09561f106952338faa07f4d583f510f75`. One external JSON/NumPy check: **994 assertions passed, 452 file-hash bindings, Exit 0, empty stderr**. No Torch/project imports, model deserialization, tests, games, repository edits or release writes.

Before and after arithmetic, owner 15711 and original workers 15728/15733 were independently alive with the correct process groups/parent. Owner remained running with both roles active, each worker had no returncode, and both current waiting markers matched the actual prefill hashes. No release existed during either check.

- Exactly forty raw rows per arm match the independently regenerated NumPy-48 opponent/card/side schedule on 9960300–9960319. Every game has 303 steps and points v2; env_steps progress from 60000 to 72120, learn_steps remain 0, losses are null, epsilon remains approximately 0.05. Both arms have the same recorded 30 wins/10 losses; these are prefill outcomes, not a strength comparison.
- Each actual preserved replay contains **142,110 transitions**, below capacity and sufficient for learning. Shapes/dtypes, finite values, six-action labels, binary done and nonempty next masks pass. Every original prefill transition is preserved; no ring rows were displaced.
- Across arms, actual `s`, `a`, `ns`, `done` and `mask` arrays are **bit-for-bit identical**. Actual ordered UID, outcome and both Float64 original-formula arrays are also bit-for-bit identical. Reconstructed full/nonreward/stream identities match the proofs. All eighty per-game ordered nonreward and formula digests were independently regenerated from the actual persisted data.
- For each arm, actual stored Float32 `r` is **bit-for-bit equal** to Float32 conversion of that arm's archived original-formula stream. Stored rewards differ as intended on outcome exposure and are bit-identical between arms without outcome. Each arm contains **1,757 nonzero match-term rows: 1,320 positive and 437 negative**.
- Every Float64 formula contrast satisfies the prespecified `18 × outcome` check (abs_tol 1e−10, rel_tol 1e−12). Maximum actual formula error: **3.552713678800501e−15**. Actual stored Float32 subtraction has concrete quantization contrast up to **9.536743190707853e−7**; after accounting for each individually measured quantization error, unexplained residual is at most **3.3306690738754696e−15**. Tolerances were unchanged.
- Both roles' initial/current Q, Target and Adam identities match their initial files and each other, with Q equal to Target and zero recorded learning. These are recorded live identities; this reviewer did not deserialize checkpoint tensors. Root's separate original validator supplies the tensor inspection.

Actual prefill hashes:

- Control: `64c5cb6eadad09c7392d4e780b53c4c77eb21f2b92f8e7a519760924dcd66a8c`
- Match: `399e8ff4edce8d57f3619b5648d8b8ec6376c7a5e720cbcd9ea021c0ef677a66`

## Limits

The full actual prefill replay and both original-formula/outcome streams are independently recovered, including actual stored r; original formula provenance cannot be re-executed without complete contexts. Native/public/final-action digests are paired and bound, but raw action/trajectory streams are absent. Initial tensor equality and zero-gradient counters remain recorded assertions in this data-only check. No inference about training completion, general strength or promotion is made. No learning release was issued by this reviewer.

## Artifacts

- `/tmp/match-weight-pair48-prefill-audit/check.py`: `0a5d58f5115fee6b08af61fb63fa807e5ae4a8fc21a9ab46a0f1b6606b3825a9`
- `/tmp/match-weight-pair48-prefill-audit/results.json` and `run.log`: `cf1b51e2cb9be3cf3572c535b2e5508e3f42fa26818e4af1ba94b8a1298d51f4`
- `/tmp/match-weight-pair48-prefill-audit/bindings.json`: `29ce2b35faff360b0f00a2dc2bad9f7365a26bdecdeada10424006a3c3bb66ba`
- Empty `run.stderr`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
