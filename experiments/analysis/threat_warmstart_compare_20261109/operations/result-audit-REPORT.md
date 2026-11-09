# Independent fixed-screen results audit — PASS

Executed the unchanged prepared script exactly once after explicit Root authorization; Exit0, empty stderr. Before result arithmetic and again after it, owner5348 plus all five registered job PIDs/groups were independently absent; owner state was complete, active empty and all five returncodes0. Recorded2/2/1wave barriers and exact one-worker commands match. Source remains bound to `ffc8b451fd0bd69a5b7e364776d8575e43ee01d2`; admission SHA `a44281800ab23b57b8f25c5b88b3f2833d32c6c3dfd8bd0fcfe417420e994592`.

**10,464 assertions passed; 433 hash bindings across430 distinct input/evidence files.** No mismatches. Independently parsed all five actual40-row CSVs: exact declared header,200 unique planned opponent/seed/side keys, both sides on each of20cards per block,303steps per game, point-counting v2, finite/integer metrics and consistent result/game-win/point-win arithmetic. Original summary counts, four gates, nomination, all intervals and file/source/admission fields match the independent calculation.

| Block | Wins | Draws | Losses |
|---|---:|---:|---:|
| V14 vs Solution |35|0|5|
| Control vs Solution |36|0|4|
| Threat vs Solution |36|0|4|
| Threat directly vs V14 |16|0|24|
| Threat directly vs Control |14|0|26|

Threat meets both Solution actual-win gates (36≥35and36≥36). Both direct gates fail (16<24and14<24). **No nomination.** This audit authorizes no extra games or promotion.

Independently recomputed descriptive95%intervals using5000 resamples of whole-card two-side means and a fresh NumPy `default_rng(0)` for each comparison:

- Threat minus V14 against Solution: +2.5percentage points, interval[−5;+10]pp.
- Threat minus Control against Solution:0pp, interval[−7.5;+7.5]pp.
- Direct Threat vs V14 score:40%, interval[20;60]%.
- Direct Threat vs Control score:35%, interval[15;55]%.

The intervals use half-score draws; gates count actual wins. This run has no draws. No cards were excluded. The paired Solution comparison uses identical map and side keys; direct blocks use their separate fixed cohorts.

Technical phase is separate: four fixed stock/null-adapter row records and their action/trajectory/point/result equality agree in the bound technical receipt; its1/8/16batch assertions, recorded36-member layout, exact member18 replacement order and model-copy hashes are consistent. These are archived live assertions. No raw traces or model outputs were independently recovered.

## Limits

CSV values are independently recounted, not regenerated from engine traces. Current model files are byte-hashed only; no models loaded, project imports, tests, games, training audits, repository/Git mutations or stop/release writes occurred. Historical actual descendant-process counts cannot be fully reconstructed from command/wave records. One training initialization and repeated project selection limit inference; intervals are descriptive with no multiplicity correction. Failure of this one-member substitution does not invalidate every possible threat-feature method. No stronger candidate or general strength gain is established.

## Artifact hashes

- `audit_results.py`: `e2e530b5c93d8bcb2d7d2a39fbc3527f68d521aa7da96945e86bca7c26e5a6b2`
- `results.json` and `run.log`: `99bfc87fc68809d5a3a42bdcd0021ce034288aaf3ac62e93d3bc9263a7a0a62c`
- `bindings.json`: `830205a675abc7c50595f61387172674e5ca035391c0f43fa88dd31df77a4ea5`
- Empty `run.stderr`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Original summary: `67469e648f260404d6661625979ea73e107cbb457a2a9c0e881d0e4d15c23ee1`
