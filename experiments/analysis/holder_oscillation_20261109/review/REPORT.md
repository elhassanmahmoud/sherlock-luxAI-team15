# Independent current-loss review — PASS

Reviewed the completed fixed-key probe and the final analyst report SHA `42f5898b48e896404dc09e6f22018418ff76ea30c24ac2a102bfc9819f2bee54`. No blocking factual or interpretation findings remain. The five bounded evidence groups agree with the original trace;232event assertions passed, plus the initial evidence/baseline checks and a narrow final report-text check.

Scope:9946007/player_0 against Solution, exactly the existing two executions. No new games/models/tests, project imports, repository/Git changes or additional cards.

## Actual evidence and result

Manifest SHA `d23ed6aa47bcbf8412a7b35fff162187713c13f8c5c03682fa17f96abb866083`; compressed trace SHA `2c577ce5898f7463971cefa15b5996c2331e7f5c94b0d6d68493025c86e42db2`. Both match. All24 manifest sources, weights, fixed key list and baseline file hashes match. Recorded source is `db2d41ae61b8a867aa086b1c8c5079b151df00dd`.

Exactly303rows cover obs_step0–302 without gaps, match_idx0/1/2 and match_step0–100;300decision frames and3resets. Every recorded passivity field is true and independently equal between observed/unobserved summaries. The baseline CSV row independently agrees:739:507points,1:2match wins,result0,v2,303steps. Match results85:117,200:263,454:127 imply those totals and winners.

Original-trace match-boundary cross-check uses pre-action points plus productive post-step unique tiles:80:116+5:1=85:117;196:258+4:5=200:263;446:127+8:0=454:127. Productive tiles require actual mask, energy≥0 and a true point tile; stacked units count once. This is retrospective private truth, not agent knowledge or a complete causal scoring reconstruction.

## Five concrete event groups

| Evidence | Independent review |
|---|---|
|E1, steps40/41/44/45|First permanent post-action deficit follows40:0:0→0:1. First public relic/candidate information appears44 with39candidates. UID4 is assigned(18,6),BFS1, but Q/legal and final action DOWN take it from(19,6) to(19,7); this destination is a previous candidate removed by45. Assignment is not arrival.|
|E2, steps76/81/82/88/89/90|No nonnegative unit enters a prior-public-candidate tile on actions45–75; the next such entry is76. First own point follows81, with UID4 arriving at(18,4). Pre-observation82 already has own_points1 and three candidate occupants; action82 then raises own_points to3. Known point count remains0 through88, then6at89 and8at90. This documents timing, not the reason internal inference changed.|
|E3, steps135/138–142|All quoted Q/mask/final-action/energy fields match. At138 UID0/UID1 legal Q-STAY contrasts with final SAP; subsequent energy50→8/53→23. Subsequent departures and negative energies−37/−18for UID0/1at141 and−29for UID2at142 agree. Negative-energy occupants are excluded from productive counts. Final-action mismatch establishes post-network modification; exact unique rule ownership and causal decomposition of energy loss are unresolved.|
|E4, steps141–154|First permanent deficit follows142:49:48→50:52. Actions143–152 add0own versus46opponent points;153 adds the next own point. Public known productive pre-step counts4/2/1/0at135/139/141/142 match. These observations support a production gap, not a counterfactual attribution of the final63-point deficit.|
|E5, steps136–140|UID2 physically follows(18,3)→(18,2)→(18,3)→(18,2)→(18,3). At137 its target is(18,4); at138 tileA is shared, living_stack_size2and sole_holderfalse. Independent scan confirms exactly five qualifying departures:(136,UID2),(139,UID0),(140,UID1),(141,UID2),(143,UID5). None completes the specified immediate A–B–A with nonnegative continuous observations and unchanged target; later exclusions include failure to return or negative energy. Physical pendling exists; the narrower stable-assignment sole-holder mechanism is not established.|

The report distinguishes pre/post action, assigned versus reached target, Q versus final action, public belief versus private truth, and sequence versus causation. Its conclusion is proportionate: this single selected loss supplies no general frequency/strength inference or demonstrated benefit of a new holding rule. It does not justify repeating a closed study or selecting further cards. The phrase about the long information-to-productive-arrival interval must retain that unproductive candidate entry already happened44; this is explicit in the report.

## Limits and artifacts

The combined two-player native-action digest cannot independently be regenerated: the trace contains own native actions only. Passivity is supported by independently matching recorded summaries and trace binding. Full energy phases, private engine-action causality, internal belief reasoning and durable unit-identity guarantees are not reconstructed. No counterfactual was run.

External artifacts: `initial-results.json`, `event-results.json`, `report-text-results.json`, `check_initial.py`, `review_events.py` and their logs. These are read-only data checks, not repository tests. Event evidence SHA `0117e620332b763b7b58fbedcc1d2b088b952439bcf0c309d2a9ddd5e5761d7e`; analyst analysis SHA `30faea99143bb5496608402353d59b538f4b5f72f3ecb52e90025e66def7fa28`.
