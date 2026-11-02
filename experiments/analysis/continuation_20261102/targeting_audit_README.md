# Independent targeting data audit, prepared before results

The script `audit_targeting.py` uses only the Python standard library. It never
imports the probe, Torch, NumPy or a model. It has not been run against actual
24-game outputs; those must remain unopened until Root's completion signal.
Preparation verification: syntax parsed and seven hand-calculated helper
assertions passed (BFS, matching, action mirroring); no games or models involved.

After Root signals complete, run once with:

```sh
python3 /tmp/sherlock-continue-20261102/audit_targeting.py \
  --repo /Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics \
  --run /Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics/experiments/analysis/continuation_20261102/targeting \
  --keys /Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics/experiments/analysis/continuation_20261102/diagnostic_keys.json \
  --receipt /tmp/sherlock-continue-20261102/targeting_execution.json \
  --out /tmp/sherlock-continue-20261102/targeting_independent_audit
```

The JSON separates technical failures from descriptive counts. Source snapshots,
protected weights and interpreter are independently hashed using the guard's
explicit `identity` schema. The exact twelve keys, both replicas per key,
303/3/300 steps, v2 points and original CSV outcomes are checked. All 3636 raw
frames are streamed. Unit/free-field/BFS/argmax/canonical-action invariants and
all two-owner counterfactual pairs are recomputed without probe helper calls.
The observed caller action is required for artillery→overkill→final-STAY chains.

Each descriptive measure gives its count and supporting distinct games, maps,
and phases. Field phases are consecutive observations of a known own point with
no own unit; a condition may occur during only part of a phase. Unit metrics may
reference such a target phase; low-energy holder episodes are separately defined
pre-action observations, with unit identity continuity unverified.

Important limits are explicit in JSON: no retained opponent action arrays for
rebuilding both-team native action SHA, no retained per-network outputs for
re-averaging, no energy-phase reconstruction, no safe-route energy guarantee.
Stored hashes are compared across passive/unobserved replicas and bound to the
execution receipt; they are not described as rebuilt from missing arrays.
Controls are exactly the first six known baseline wins, not representative or
matched controls. Lower counterfactual BFS sum is not strength evidence.

Root's current schema/code review may introduce a final provenance correction
before execution. Check the completed tool diff before the real audit, adapt only
if its declared trace format changed, and record any resulting audit limitation.
