# Independent artillery data audit

PASS

All 1192 helper events independently reconstructed from the two original compressed traces; 39590 checks passed.

| Trace | Events | Eval F / Train F | Eval F / Train T | Eval T / Train F | Eval T / Train T |
| --- | ---: | ---: | ---: | ---: | ---: |
| 831006/player_1 | 404 | 380 | 0 | 24 | 0 |
| 831043/player_0 | 788 | 771 | 0 | 0 | 17 |

The training result uses an independent scalar conjunction: not the first holder on a point, not reserved for an own point when surplus protection is active, sufficient hit count, sufficient energy reserve, and no armed visible enemy in the configured safety distance. Training omits the splash-estimator branch. No production helper or analysis module was imported or executed.

Every output key/order, archived evaluation answer, SAP argument, event-time unit context, normalized full configuration, all five before/after state hashes, native-action digest, report field and artifact hash was compared with the original evidence. Both 303-row traces (300 decisions each) are complete; no missing, duplicate or surplus helper events were found.

Historical run source: `76d01cf08177f85bf0b1fff7c2b007734ca21d3a`. Original trace source: `0c0dda642e9876141a705c2b8ed807a4f26ed870`. Audit HEAD: `dd15d994d777aba1df0db14a509c83a98738c425`. The 346 run-source bindings and 23 original trace-source bindings were checked against their historical Git blobs or external runtime bytes, not by equating the closed run with the later HEAD.

All 357 monitored local files stayed byte-identical during this audit, including both V14 weights and Gruppe15.zip. No games, models, forward passes, learning updates, pytest, commits or pushes were executed.

Limits:

- The original evaluation boolean is independently recovered from its original event, not recomputed; the step-local estimator posterior was not archived.
- All five stored before/after hashes were independently reconstructed from original inputs; no claim that hashing can prove historical execution beyond the archived evidence.
- The post-act point/assignment stability premise is supported by the existing separate source review; event-time unit position, energy and target are rechecked for every event here.
- Original manifest passivity fields agree, but the historical joint two-policy action digest cannot be regenerated from the archived own-actions stream alone.
- Selected correlated states do not measure final action changes, action quality, training effects, prevalence or strength; no training-rule change, new run or promotion follows from this audit.

Reproduce (from repository root, with the existing NumPy environment):

```text
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B experiments/analysis/artillery_training_exposure_20261108/operations/independent_data_audit.py
```

The adjacent JSON records every event's independently derived gates and the complete before/after hash inventory.
