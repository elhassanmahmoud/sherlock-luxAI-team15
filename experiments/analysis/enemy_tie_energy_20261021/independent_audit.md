# Independent enemy-tie development audit — 21 October 2026

**Ready within reviewed scope. Development gate fails; stop this variant.**

Frozen source: `8281c1c392b92c2660b07f24bc27ac0ce8b703bd`. Both evaluation jobs completed successfully, ran sequentially with two workers, and finished within the original six-hour deadline.

| Opponent | V3 W/D/L | Candidate W/D/L | Candidate − V3 | Paired 95% interval |
|---|---:|---:|---:|---:|
| default | 120/0/0 | 120/0/0 | +0 pp | [+0, +0] pp |
| solution92 | 102/0/18 | 105/0/15 | +2.5 pp | [-2.5, +8.33333] pp |

Each row covers 120 games (60 cards × both sides). Result rate assigns draws 0.5. The bootstrap resamples whole paired cards 5,000 times with seed 0 and 2.5/97.5 percentiles. Exact half-result units, before rounding, determine the gates.

Solution delta: 6/240; positive delta gate True; strictly positive lower interval gate False. Default delta: 0/240; ≥−0.02 gate True.

Strict headers, exact 240 unique seed/side/opponent keys in each file, finite numbers, 303 steps, point-counting version 2, match-win/result and point-result consistency all pass. V3 reproduces every historical non-time field: 5040 numeric comparisons, maximum absolute difference 0.0 (strict tolerance <1e-9); side/opponent strings match exactly.

All 111 frozen source/interpreter/engine hashes and 10 protected checkpoint hashes match the initial snapshot plus the recorded launcher addendum. Candidate bytes and identity metadata are unchanged. Metadata records only enemy_tie_energy=True as the effective config difference, 18 distinct finite networks, and all other checkpoint fields identical. This data-only review did not reload tensors; its identity assurance binds the existing metadata to unchanged bytes.

Freeze provenance: the launcher was added to the source manifest after the reviewer’s initial snapshot; its file modification time precedes the first development launch. The addition was separately preserved and hashed; no original manifest entry changed.

No tests, games, model/backend imports, project analysis helper imports, source edits or repository changes were performed. This report and its supporting script/snapshot are under `/tmp`. Known-card screening does not establish universal improvement or a causal mechanism.

Development gate fails: stop this single variant. No fresh or direct continuation and no promotion is supported.

Full hashes, job evidence, per-card integer differences and exact gate values: `/tmp/sherlock-enemy-tie-development-audit-20261021.json`.
