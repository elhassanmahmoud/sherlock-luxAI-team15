# Independent implementation review — network breadth, 4 November

**Status: one P2 correction required before source freeze.** Reviewed the actual four new files and chosen120/280/160map protocol; no source edits, models, games or training. Existing tests were inspected but not rerun; the worker's reported30passes/4.07s is not claimed as my execution. One tiny20-element NumPy arithmetic reproduction was run to establish the finding below.

## P2: raw float ranking can violate the preregistered exact tie-break

`scripts/network_breadth_study.py:177–181` sorts raw floating-point panel delta before Solution delta/network count. `panel_delta` reports a mean of per-map fractional differences, so mathematically equal panel totals can differ by rounding depending on map placement.

Concrete valid screen construction: baseline loses every panel game; both candidates win exactly5of240panelgames, all outsideSolution; Solution totals therefore tie. Both passdefault/direct and allselectiongates. SOLO28 spreads the5wins across5maps, whereasFO42 places the5wins onone map. Actual NumPy arithmetic in the current environment:

- SOLO28: `mean([1/12]*5 + [0]*15) = 0.020833333333333332`.
- FO42: `mean([5/12] + [0]*19) = 0.020833333333333336`.

The current function picksFO42 before reaching the required fewer-networks tie-break, which must pickSOLO28. This can change the single candidate allowed into confirmation.

Fix nomination ordering using exact integer half-win deltas (`2*wins + draws`, candidate minus baseline) over the six panel opponents, then the exactSolution half-win delta, then actualnetworkcount/name. Allscreen denominators are equal and fully validated, so this is equivalent to the intended mathematical ranking. Keep floating estimates/intervals for reporting. Add a targeted regression with the differing map placements above; no broad suite request is implied.

## Other reviewed boundaries

No other substantive defect found in the inspected implementation:

- Builder constructs ordered1/42unique finitefloat32states, exactV14rawconfiguration, q/target_q equality, properempty singleton ensemble and normalized inference counters, with source/output protection and actualreload checks.
- Fixed920/4800game schedules, distinct blocks, owncutoff/STOP/quotapolicy, two-worker commands and one-thread childenvironment agree with protocol. No accidental reuse of olddriver's bounddeadline/freeze functions.
- Summary stores frames byrole ANDblock, concatenatesSolution once, enforces20or400Solutionmaps,120panel/default and160directmaps inconfirmation, and keeps the extraSolutionblock outofpanelweighting.
- CompleteCSVkey/schema/303step/v2checks precede statistics; nomination is recomputed from bound complete screen evidence; oneglobalstudyreservation plus phase reservations prevents anotherfreshfreeze/outputpath restart.
- Source/interpreter/engine/protocol/manifest/pilotreceipt+CSV/model hashes are bound; actualpilotrate evidence is recomputed and onlyraises conservative projections. Outputroot confinement, exclusiveprocesslock, ownprocessgroupcleanup and capital-P MacPython recognition were inspected.
- Exact seven gates and fixed ranking intent are preserved; the float tie issue above is the remaining implementation mismatch.

Actual source/model/pilot/seed acceptance remains mandatory and outside this code review. In particular, the model-free freeze checks metadata/hashes; the coordinator's promised independent actualcandidate/pilot inspection supplies the substantive artifact/provenance check. No actualmodels/games had been run at this review handoff.

## Reviewed file identities

- `scripts/network_breadth_candidates.py`: `28ed012c8b9051763bdcf79e3660cff78acabe4bd2bd5ca9e9d0aabc5e2808d5`
- `scripts/network_breadth_study.py`: `30842eefd54e6043f44b7dce0ee40eb38ddf5e0a53806162069e403a35d529c5`
- `tests/test_network_breadth_candidates.py`: `dab5eb3f399d4e8a7b08eb8fd5a1eb938150e1b6339723ba23fe05f48590d5d9`
- `tests/test_network_breadth_study.py`: `9420a79f2f432dc74c56d9a7e164bfeb949d0eafe0e543f23f7f258fdbe339b2`

Available for narrow review of the ranking fix and its regression result.
