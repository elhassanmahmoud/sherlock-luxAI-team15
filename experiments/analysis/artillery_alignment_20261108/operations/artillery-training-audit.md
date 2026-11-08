# Artillery training data audit

PASS_DATA_ONLY

Checks: 1388715.

| Arm | State | Prefill | Training | Recounted prefill events | Additional executed SAPs |
| --- | --- | ---: | ---: | ---: | ---: |
| control43 | FINAL_DATA_VERIFIED | 40 | 400 | 16336 | 0 |
| aligned43 | FINAL_DATA_VERIFIED | 40 | 400 | 16402 | 171 |
| control44 | FINAL_DATA_VERIFIED | 40 | 400 | 18152 | 0 |
| aligned44 | FINAL_DATA_VERIFIED | 40 | 400 | 17457 | 231 |

Frozen source `02ce1b2ce9a5b0780da1ee6462a2368b2226d495`. All source/initial/protected inputs are read-only. No model/runtime imports or game executions. Missing future evidence remains pending.

Limits:

- No model was loaded. Tensor contents/finiteness, actual optimizer moments and actual reload are not independently verified by this stdlib audit; source-bound proof declarations and file hashes are checked only.
- Only prefill helper events are stored individually. Training exposure is checked for exact schedules, conserved aggregates and recorded digest format, not rehashed from unavailable per-event training logs.
- Event context itself is not archived here; before/restored digest equality is checked, not independently reconstructed helper inputs or boolean formulas.
- Opponent order is checked against the supervisor-bound pre-gradient prepared schedule and its acquisition pin; NumPy PCG64 is not reimplemented.
- Running-file snapshots are complete row prefixes, not an atomic snapshot of all live files; future and unflushed entries are excluded and missing future completion is pending.
- No strength, reward causality, candidate promotion or training-rule quality claim follows from this technical data audit.

Pending:


Synthetic self-check: {'status': 'NOT_RUN', 'prior_evidence': '/tmp/artillery-training-audit.v1.json', 'note': 'Synthetic checks run only when --selfcheck-only is explicitly requested.'}.

Re-run: `python3 -B /tmp/artillery-training-audit.py`
