# Independent prototype technical acceptance audit

**ACCEPTED** for the predeclared technical block. 151 checks, 0 failures. No model loads, tests or games were started by this audit.

All 24 rows and log completions match the exact declared order: 12 default-off keys, then four fixed spent keys in each of art/swap/combined modes. Only seeds 831000–831043 occur, with the prescribed sides; no fresh 841/842/843 seeds were used. Every row reports 303 transitions and point-counting v2, internally consistent wins/results, the exact reference configuration plus only its intended two flags, and unchanged tensors. All 12 default-off stored native stream hashes and seven step/result/point fields exactly match the old unobserved records. Stored parity flags were recalculated rather than trusted.

Rehashed all 207 pinned files, interpreter and all five protected weight files; no mismatch or source-inventory change. HEAD remains `755fa26451c8a28f12ac6a9518281001e8e1458c`. The three runtime files equal reviewed commit3152fed. Plans, keys, old reference manifest and executed driver are pinned; the driver path resolves from /tmp to /private/tmp. Current V14 P0/P1 and baseline all retain SHA98a07350…d3d8; protected older backups retain their recorded hashes.

The recorded run took 120.521781s, below the 20min cap and before the deadline. A sequential single-process driver plus exactly24 load/completion log pairs supports the one-worker/24-game count. Standalone counters independently sum to art9 and swap28; combined art8/swap32 is complete. These are local plan-change counts, with no strength claim.

Evidence boundary: the pinned driver asserts 36 loaded tensor-equal networks before/after every game,79features/6actions,epsilon0,no caught errors and unchanged learn_steps; this audit checked that code and its complete execution record, and did not deserialize models. `common.play_game(train=False)` omits updates, uses public observations and invokes each policy once per transition; the wrapper hashes both teams' native arrays then calls the original env.step once. Raw arrays are absent, so this is independent comparison of recorded digests, not independent digest recomputation. Per-transition reset/endpoints and numerical battery/process snapshots are not archived here; the driver checks25% before games, and completion is120.52s. Fullsuite792+14 is coordinator-provided prior evidence, not rerun or newly certified here.

Machine-readable checks: `/tmp/sherlock-continue-20261102/prototype_technical_audit.json`.
