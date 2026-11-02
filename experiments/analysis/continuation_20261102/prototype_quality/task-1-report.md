# Task 1 implementation report — 2026-11-02

Status: implementation and focused verification complete; independent review,
centrally scheduled full suite, default-off stream comparison and games remain
with root. Commit `3152fed` on `improvement/targeting-20261102` from `75af0c5`.
Only the four assigned source/test files are committed.

Implemented `art_move_guard=False` and `point_pair_swap=False`. The pure owner
helper copies the mapping, preserves targets and lowest live-ID productive
holders, requires compatible config/own known passable goals and origins, all
four reachable/first-step-legal routes, then selects one strict maximum BFS gain
among at most120 sorted pairs. Lexicographic ties remain stable. It skips BFS
below two eligible units. Current movement masks are computed before features
only in the enabled shared-belief/training-permitted path and reused; normal
default-off order is unchanged. Cache prevents counter duplication.

The artillery guard runs inside the existing forced-artillery branch only for
an allowed pre-artillery MOVE and active existing overkill gate. It calls the
existing pure rejection check and preserves the move for later normal safety
rules; neural SAP, STAY, live targets and disabled cases retain prior behavior.
Counters report stage-local plan changes, not executed movement or point gain.

## Red / green evidence

Python for every run:
`/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`.

1. Before production edits: `-m pytest -q tests/test_targeting_prototypes.py`.
   `red.log`: **37 failed,11 passed in3.02s**. Failures were missing helper/flags
   and the expected enabled decision-order, feature-goal and preserved-move
   behavior; baseline routing cases already passed. Log:
   `/tmp/sherlock-continue-20261102/targeting_impl/red.log`.
2. After minimal implementation, same test command:
   **48 passed in2.68s**, exit0 (`green.log`).
3. Added boundary characterization for zero-gain tie, noncanonical team0,
   explicit120-pair limit, all four movement directions and existing recovery
   aware overkill behavior. Final focused command:

```
-m pytest -q tests/test_targeting_prototypes.py tests/test_mask_and_act.py tests/test_active_targets.py tests/test_art_splash.py tests/test_nebula_fix.py tests/test_rules_2110.py::test_sap_no_overkill_second_holder_keeps_energy tests/test_rules_2110.py::test_reach_assign_skips_tile_under_asteroid tests/test_rules_2110.py::test_path_fix_leaves_dead_end tests/test_rules_2110.py::test_nebula_soft_prefers_equal_detour_but_keeps_paths_open tests/test_rules_2110.py::test_art_surplus_does_not_stop_units_heading_to_own_point_tile
```

**92 passed,4 subtests passed in2.90s**, exit0. Log:
`/tmp/sherlock-continue-20261102/targeting_impl/focused-final.log`.
Earlier narrower run:84 passed,4 subtests in2.99s (`focused.log`).
`git diff --check` and staged equivalent were clean before commit.

No fullsuite, real game, engine episode or checkpoint load was run by this
implementer. Fixtures use small randomly initialized agent networks replaced by
a deterministic synthetic policy. Initial pytest was deferred until root released
the slot after its separate Gauss fullsuite. No weights, rewards, runner,
opponents, shared documentation or other source files changed.

## Review limits

- Four legal first steps are required conservatively, including each current
  route as well as each swapped route, matching the binding brief.
- BFS improvement is local potential and does not ensure whole-route energy.
- No performance or gameplay strength claim; flags remain default off.
- Fullsuite/default-off stream equivalence are intentionally pending root's
  resource scheduling and independent review.
