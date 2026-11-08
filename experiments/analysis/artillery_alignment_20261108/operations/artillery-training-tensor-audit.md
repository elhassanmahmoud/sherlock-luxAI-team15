# Independent artillery tensor/replay audit

PASS_TENSORS_AND_REPLAY

Checks: 1686. Historical training source `02ce1b2ce9a5b0780da1ee6462a2368b2226d495`.

| Arm | Q changed tensors | Target changed tensors | Adam updates | Replay rows |
| --- | ---: | ---: | ---: | ---: |
| control43 | 12 | 12 | 60000 | 300000 |
| aligned43 | 12 | 12 | 60000 | 300000 |
| control44 | 12 | 12 | 60000 | 300000 |
| aligned44 | 12 | 12 | 60000 | 300000 |

Limits:

- No network was instantiated or evaluated. Independent CPU weights_only deserialization and exact tensor/schema inspection are performed; the original production-loader check remains separately required.
- Initial checkpoint has no optimizer payload. Fresh/unchanged prefill Adam is represented by source-bound initial/prefill proof hashes; final Adam tensors and all 60000 step counters are inspected directly.
- Replay is checked for shape, dtype, finite values, action classes, binary terminals and legal STAY successor masks. Raw transition-by-transition environment reconstruction is not performed.
- Recorded successor masks are not current-action legality masks. No claim is made that the stored action must be permitted by its successor mask.
- The caller must coordinate this one process after all four training workers and separately from original-validator checks. Process labels cannot detect arbitrary unlabelled numeric work.
- Technical training completion does not establish stronger gameplay or candidate promotion.

No project imports, model forward passes, training updates, games, commits or pushes. All bound input/protected files were unchanged.
