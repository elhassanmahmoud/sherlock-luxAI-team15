# Independent narrow review: nearest-enemy energy tie selection

Date: 21 October 2026

Decision: **Approved for the scoped implementation. No important correctness bug found.** This is source-review approval, not permission to skip the preregistered integration or game gates and not evidence of improved playing strength.

Reviewed `d93d4d5..1b3f6a7` in `/Users/moayedshawesh/Desktop/KI/sherlock-enemy-tie`, limited to `agents/sherlock/config.py`, `agents/sherlock/features.py`, and `tests/test_enemy_tie_features.py`. Read the diff once, the implementation handoff, the actual plan in the main checkout, and the named unchanged integration points for config loading, context construction, and feature callers. Repository instructions and the newest handoff confirm the other training checkout is frozen.

## Correctness and default parity

- `AgentConfig.enemy_tie_energy` defaults to False. The existing `from_dict` filters to dataclass fields and constructs with keyword arguments, so old checkpoint dictionaries receive False; `to_dict` includes the option. Actual agent checkpoint loading uses this same `from_dict` path.
- `make_context` reads the option with `getattr(..., False)`. Both the ordinary belief and alternate feature-belief path call this context builder before `build_features`, so the option reaches the actual feature caller.
- A missing or false context flag takes the unchanged original `argmin` selection and feature arithmetic. When true, `flatnonzero(d == d[k])` restricts selection to the minimum Manhattan distance. Its original index order and NumPy's first-maximum selection preserve the original enemy order for equal energy.
- The enemy arrays are constructed with identical visible-ID filters, so energy indexing remains aligned with coordinates. Negative-energy opponents remain in those arrays and can still be selected. No filters, arrays, assignment logic, counters, masks, or feature dimensions are changed.
- The selected minimum distance stays constant. Only enemy displacement and relative energy (indices 69, 70, 72) can differ from the tie switch; count calculations remain based on the full existing enemy array. Downstream learned actions may consequently differ when enabled, as intended by this experiment.

## Tests and isolation

The new test file contains 34 parametrized cases by inspection: config compatibility (1), complete legacy vectors on both canonical sides (12), enabled selection cases on both sides (12), empty-enemy sentinels (6), actual config/context/feature wiring (2), and import delta (1). The hand-derived complete-vector expectations avoid using the function under test to manufacture the expected result. The retained RED log shows 9 intended failures and 25 passes before implementation, including passing legacy vectors.

Coverage includes a stronger nearest tie, equal-energy order, all-negative ties, nearer negative energy versus farther high energy, noncontiguous nearest candidates, one enemy, no enemies, missing context flag, false flag, full 79-value vectors, and unchanged shared context. The config-object-missing-attribute fallback is evident from the source but not directly exercised by a dedicated fixture; this does not block this small change.

Tests load the real empty Sherlock package under a private name and then its actual config, belief, geometry, and feature modules. This avoids the top-level `agents` package's eager discovery, without substituting production functions. Those source dependencies are NumPy/stdlib; the engine import in `conftest.py` is inside an unused fixture. The module's import-delta check detects new backend imports during this private module load, but alone does not prove a whole pytest process never loaded a backend earlier or later. The handoff explicitly reports a separate process-wide audit after `pytest.main` with plugin autoload disabled and no Torch/JAX/luxai_s3 modules. The reported final result is 34 passed; I did not rerun tests or independently repeat that runtime audit under the active-training restriction.

## Required later checks

Full integration remains pending until the frozen training finishes: actual checkpoint/model loading, relevant wider tests and ordinary package imports, reference-game reproduction with the option off, legal-action/runtime/package checks, and the planned model/config/source/engine identity audits. Candidate strength must then follow the single preregistered comparison and gates in the actual plan; no game, weight, or performance conclusion follows from this review.

This review ran read-only source/text inspection only. No Python/model imports, tests, games, training, repository/HEAD changes, weight accesses, venv modifications, or changes to the frozen `sherlock-counterplay` checkout were made. The only written file is this requested review report. Root owns integration and shared documentation updates.
