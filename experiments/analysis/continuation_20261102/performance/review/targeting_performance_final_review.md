# Final independent P/PT performance review

**Specification: PASS. Code quality: PASS. No open Important or Critical findings
in the final reviewed driver/statistics scope.** This supersedes driver-version
references in the earlier review; prior resolved findings and their red/green
records remain preserved.

## Exact reviewed hashes

| Artifact (under /tmp/sherlock-continue-20261102/) | SHA256 |
|---|---|
| evaluation_runner/targeting_eval_driver.py |69ef238fd17d180b432f5fd4f58a1b0b6a33a4fd67a8166ae0768c01d7a5e3d7|
| evaluation_runner/test_targeting_eval_driver.py |a657f15371f931bc4344fc52e3d463aa1aace7fa8b88f22cc149be7274403b0c|
| targeting_stats.py |d3ce385961852fb3fdaf4b482df0d26636def6c60b9b0edc0f50230b084d2d6a|
| test_targeting_stats.py |9abcf60a22f70c2992237064bd0445f16304e936c5f54a053c99a2ebbc652d13|
| build_targeting_candidates.py (unchanged) |7f5dcefdc704acce9c6a2cb614da35e07aaca7c5ea06bf889f8261a376e61f8c|
| test_build_targeting_candidates.py |157c01cd1901b5e67052dee00caee2232a916d5eafac3ea7380d42cd5d034dbd|
| targeting-performance-protocol.md |bb1a8056bc02f1bfffd9e34dad192ecdb73890453edcc51ffdb72fa414cfe2d8|

## Final change verification

- Execution uses only existing par_eval, exactly two workers per sequential job.
  Default adapter and worker CLI are gone. Selection has five jobs/4600 games;
  confirmation three/9000. Opponents, maps, sides, role weights and two inference
  overrides remain fixed and bound by build_jobs/check_plan. Combined jobs retain
  default as the seventh opponent; no statistical panel expansion occurs.
- Two wall-time classes use fixed floors2.22/3.0. effective_rates retains all
  complete-job observations, takes the largest observed/initial relative slowdown
  across classes and applies it to both floors. project_seconds weights exact
  remaining class counts, adds20%, and never divides by two.
- Selection reserves all future confirmation games:8400 combined+600 direct.
  Confirmation derives prior observations from the pinned complete selection
  receipt's per-job wall_seconds/actual_games and timing_class. check_complete_state
  verifies those classes/counts against fixed jobs; check_plan recomputes the prior
  lists and checks receipt/summary hashes. run_phase copies those lists and appends
  current observations. There is no Selection→Confirmation rate reset.
- Hard deadline remains04:30Z with3600seconds reserved: model jobs must finish
  before03:30Z/04:30Berlin, leaving closure until05:30Berlin. Initial latest starts
  remain18:10:34 selection /21:41:02 confirmation; observed slowdown tightens them.
- Existing input paths now resolve canonically before rebuilding job paths, fixing
  logical/tmp versus/private/tmp mismatches. New outputs still reject user-created
  symlink paths and existing files. Read the alias regression.
- Signal-protected spawn/ownership registration and cleanup, child signal-mask
  restoration, shared resource lock, atomic owned state reservation, conditional
  error-receipt writes and final plan/freeze recheck remain intact. Battery start
  >=35%, stop<=25%, AC exception and owned process-group handling remain intact.
- Statistics revalidates the fixed plan/current shared freeze and requires before
  and after source identities equal that freeze. Combined CSVs are split into
  PANEL6 and default subsets after exact-key validation. The panel bootstrap still
  clusters the same map's six opponents and two sides, excluding default. Gates,
  1e-9 P-before-PT tie rule and confirmation nominee binding are unchanged.
- Direct output now includes pure wins/draws/losses alongside score/interval;
  previous minor reporting gap is resolved. No new nomination or runner-up path.

## Evidence and limits

Re-read final changed code, targeted tests, fixed protocol and integration with
existing evaluation/analysis helpers; independently computed file hashes. Root
and implementer report19 driver tests plus21 statistics/builder tests passing
without skips, including complete synthetic4600/9000 file pipelines. Those suites
were not redundantly rerun by this reviewer. Earlier independent narrow red/green
counterexamples are documented in the preceding review files.

No repository edits, Torch/model/tensor loading, policy execution, fresh games,
training or actual evaluation phase were performed by this review. Candidate
builder is unchanged from its earlier PASS. The real four-arm audit, candidate
construction/loaded-model verification, reviewed source integration, final shared
runtime freeze, seed provenance and resource admission still precede any fresh
841+ outcomes. At the stated33% battery, no new long phase is admitted without AC
or an explicit superseding user instruction. Code approval is not execution or
promotion approval for incomplete training.
