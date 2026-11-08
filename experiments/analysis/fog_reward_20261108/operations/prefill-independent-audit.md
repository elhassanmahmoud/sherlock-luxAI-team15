# Independent Fog prefill data audit

PASS at 2026-11-08T12:35:27.176766+00:00

Independent stdlib artifact audit; trajectory/replay hashes are recorded receipts, not independently replayed raw simulator states or replay arrays. No model imports, games, gradients or tests.

- Seed 41: PASS; control41: 40 prefill games, 615 unknown SAP transitions, mass 184.500000, 60000 post-admission updates observed; neutral41: 40 prefill games, 615 unknown SAP transitions, mass 184.500000, 60000 post-admission updates observed
- Seed 42: PASS; control42: 40 prefill games, 411 unknown SAP transitions, mass 123.300000, 1650 post-admission updates observed; neutral42: 40 prefill games, 411 unknown SAP transitions, mass 123.300000, 1650 post-admission updates observed

Checks: fixed component/config/schedules; zero prefill gradients; unchanged Q/target/optimizer identities; full per-game replay counts; unknown exposure and reward mass; actual formula hashes; frozen bundle/proof hashes and raw-row correspondence; independently recomputed aggregate hashes; paired trajectory/replay/counterfactual equality. Complete model/optimizer tensor audit is deferred until every worker has ended.
