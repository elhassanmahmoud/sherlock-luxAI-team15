# Independent offline Fog influence code/method review

Date: 2026-11-08. **Specification PASS; code/integration PASS; descriptive-methods PASS. No remaining blocking findings.** No environment/game extension, weight selection, optimization or strength claim is approved by this review.

Exact files reviewed:

- `scripts/fog_influence.py`: SHA-256 `be6da3adccc23c5d4fd7a0f20e62a1a9c62b602e67c1629be8e3ea4ed7fa80e0`.
- `tests/test_fog_influence.py`: SHA-256 `c6bfb049f6890c53aa63eb25716f458e052e73e2eca19c1eee852691787d8cff`.

Read the fixed spec/plan, prior method review, final implementation report, both files, actual replay save/push/update and inference/masking/CNN-loading paths, and the reused admission/guard interfaces. This reviewer ran no tests, model imports/loads, forwards or games. Implementer reports 11 focused synthetic tests passed in 2.41 seconds; root reports its own 11 passed in 2.42 seconds and clean diff-check. Their assertions were inspected, not independently executed here.

## Resolved finding

The initial fixed output path was the already existing `experiments/analysis/fog_influence_20261108` directory containing method-review metadata, so its nonexistence check would reject every run. Final code uses the exclusive `.../run_v1` child. Existing method-review evidence remains intact; an actual run cannot overwrite or adopt an earlier run.

## Sampling and evidence

`sample_buffer` reads only `ns`, the matching stored `mask`, and `done`; source confirms those are next-state features/masks written together by `ReplayBuffer.push`. It excludes terminal rows and all-illegal masks, requires finite float32 79-column features and six boolean mask columns, and checks each accepted buffer hash before and after reading. The recorded prior action and current `s` are not treated as next-state ground truth.

One PCG64 seed-0 generator samples sequentially in the fixed control41, neutral41, control42, neutral42 order, without replacement within each buffer, up to 2500 eligible indices per arm. All models receive the exact same pooled bank. Original buffer row indices and arm indices are persisted with features/masks before any forward, together with buffer hashes, bank byte/content hashes, ordered member hashes and method metadata. Bank artifacts then join guarded inputs. Exact byte-unique `(ns,mask)` count is reported while retained duplicates and row dependence are explicit.

Replay binding is anchored to the exact independent final-training audit SHA, not merely a filename. Accepted models/final arms reuse the historical training trust anchor and candidate admission. The actual candidate tensors/config/order are revalidated. These checks preserve the original 36 followed by the exact corresponding final41/42 pair and their common component-18 parent.

## Numerical and descriptive contracts

All actual checkpoints must lack a CNN policy and contain finite float32 member tensors with the original hidden/dueling structure, 79 inputs and six actions. Strict QNet loading is used; no Agent or environment is constructed. Forwards are CPU float32, eval/no_grad, in fixed 512-row batches. Forty member arrays are retained. Both independently reloaded 38-member checkpoints are separately forwarded on the bank, compared to assembled means with the declared atol/rtol 1e-6, and their independent means are also saved for later audit.

**Masking precision:** the actual Agent currently uses `-np.inf` for illegal actions (`main.py:349`); the diagnosis's predeclared sentinel is `-1e9`. It requires finite Q values and rejects any resulting illegal winner. Therefore every accepted diagnosis winner equals the legal Agent argmax, including first-index tie handling; pathological Q values that would let a masked entry win fail closed. The original spec wording claiming the Agent itself uses `-1e9` is inaccurate; root corrected that description before any real forward output, without changing arithmetic, implementation or gates.

The summaries distinguish `P−B` from the full-ensemble contribution `(2/38)*(P−B)`, including values at both V14 and candidate winners. Fixed V14-best versus V14-runner-up margin change is computed for every row with at least two legal actions, including rows whose winner never changes. Changed candidate-versus-V14 original, full and contribution margins are separate. Float32 decomposition error is reported rather than hidden. Per-member raw Q/legal-gap distributions, proposal changes and SAP-to/from counts are descriptive. Each of the four learned members is also compared against original component18 on that same bank. No inferential intervals, action-quality labels, reconstructed Fog provenance, final-rule effects or causal reward conclusions are manufactured.

## Operation and completion

The process lock and newer foreign model/probe/test guard allow one diagnostic process. AC, fresh allowed usage strictly below 100%, STOP/signals, source/HEAD/interpreter/plans and all accepted input/protected hashes are checked before model inspection and during sampling/forwards, with full checks at most ten seconds apart. Signals/STOP are checked each batch. No children, games, learning steps, saved weights or ensemble weights are introduced. Partial failures preserve incomplete evidence and do not silently restart.

Outputs store per-member and candidate Q arrays, indices, labels and member hashes; output hashes are added to guarded inputs and the summary. Actual acceptance still requires root's source commit/freeze, real guarded offline execution and independent artifact/arithmetic audit. This small trained-on replay diagnosis can quantify neural-proposal influence only; it cannot reopen the failed comparison or justify promotion.
