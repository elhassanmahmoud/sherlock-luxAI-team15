# Actual candidate acceptance — 03 November 2026

**PASS. All six actual candidate files are technically accepted for the fixed performance study. This is not a strength result or release approval.**

Independent execution completed with exit0: **14,812 checks, zero failures**,1.38 seconds. Only serialized checkpoint/tensor reads and comparisons were performed, with Torch intra/inter-op and BLAS thread counts fixed to1. No agent/network construction, optimizer, forward pass, gradients, game, training, tests, source/HEAD/plan/weight edit or commit occurred.

| Role | Actual members | Verified source selection | Inference configuration | Replaced members | Nominatable |
|---|---:|---|---|---|---|
| PAIR18 | 18 | Fixed18 indices in the plan, exact order | Exact V14 | None | Yes |
| PAIR24 | 24 | Fixed24 indices in the plan, exact order | Exact V14 | None | Yes |
| FT18 | 18 | Source indices18–35, exact order | Exact V14 | None | Yes |
| Z36 | 36 | All36 source members, exact order | V14 plus only `zone_rescue=True` | None | Yes |
| C36 | 36 | All36, with the accepted control end tensor | Exact V14 | Only index18 | **No** |
| R36 | 36 | All36, with the accepted rescue end tensor | Exact V14 | Only index18 | Yes |

The expected PAIR18/PAIR24 rosters were independently written from the fixed plan, not read from builder constants. Every actual member was compared to its expected source/trained tensor by exact bytes, dtype, shape, parameter-key order and state metadata. Every state has the expected12 Dueling-DQN parameter tensors,79 inputs/6 actions,152,967 parameters,Float32 CPU storage and only finite values; members within each candidate are unique. `target_q` is an exact copy of the candidate's first `q`, including FT18 where the first member is source18. The manifest's ordered tensor hashes, file hashes, source-index lists, member counts, equal weighting and nomination flags agree with actual contents.

C36/R36 provenance matches the independently accepted training results in `/tmp/sherlock-final-20261103/training_final_review.md` and its hashed JSON evidence. Both receipts bind source V14 component18,120 prefill/1,200 learning/96 known validation games,180,000 updates and459,960 environment steps. The actual accepted final checkpoint hashes are:

- Control: `686dd59c54668b270ed47a12479e1c7c0119617819f07a72219f916c87d08abb`; tensor `361463b9fbff1e2e839ba8e2027e3e3df2eea95ad6536668793ca568f630c2e7`.
- Rescue: `fe57f67fb263b206a8147d7d0ed6cab9bd27c6987e3e53789f14e8f08f4082b7`; tensor `2c8adc63c9b0e1e1e13715a68c7471f34047a97e481dcdc0107e106331fbcd88`.

Only serialized member18 differs from the original36-member V14 in C36/R36; the other35 members remain exact. The two trained replacement tensors are distinct. Their training-time configs are not leaked into inference: C36/R36 configs equal raw V14, with `rescue_in_training` effectivelyFalse and both old P flagsFalse. All candidate checkpoints contain exactly the inference fields; there is no stale optimizer, replay or ensemble-source history. The saved counters are the explicitly normalized inference values `env_steps=60000`, `learn_steps=0`, not claimed training totals.

The source remains SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. **251 protected files** were rehashed before and after, including all238 recorded source/engine/protocol files, interpreter executable, prepared inputs, active V14 weights in both checkouts, baseline and existing primary ZIP. Candidate manifest/files, accepted receipts/checkpoints and review evidence were also stable. HEAD remained `7c906e16943ff7217afe1eae392834439cc76634`.

Actual candidate manifest: `/Users/moayedshawesh/Desktop/KI/sherlock-november-followup/experiments/ensembles/final_battle_20261103/manifest.json`, SHA-256 `20d6b784a4ad94199642a386ee67793d5a008e413616ea66f87df28de9fa44b7`.

Machine-readable result: `/tmp/sherlock-final-20261103/candidates_actual_review.json`. Reproducible read-only audit: `/tmp/sherlock-final-20261103/candidates_actual_audit.py` (outside the frozen repository). Performance may proceed only after root's normal fresh source/resource/power/quota/time admission and shared performance freeze. No performance quote or automatic promotion follows from this technical acceptance.
