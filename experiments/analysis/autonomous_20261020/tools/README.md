# Portable observation-only target and Sap diagnosis

Prepared from the exact temporary diagnostic and reviewed Sap observer used by
the parent. The only executable changes are path resolution: the diagnostic
finds its repository among `__file__` ancestors, the observer is a sibling, and
the unchanged Sap helper is a sibling source file. The `cand_boost` argument,
cache-step assertion, `smart_sap` forwarding and alternate-planner rejection are
preserved. No agent algorithm or policy is installed by copying these tools.

Intended destination after parent review:

    experiments/analysis/autonomous_20261020/tools/

Copy this directory's contents there. The repository must contain the code
version identified by the source hashes in `manifest.json`. An arbitrary older
checkout may lack required configuration fields such as `cand_boost` or
`contest_sap`. This archive does not contain models, an environment or the full
agent implementation. `source_snapshots/proposed_rules.py` preserves provenance
for the exact helper; it is never imported by the diagnostic.

## Lightweight checks

From the repository root:

```sh
.venv/bin/python -B experiments/analysis/autonomous_20261020/tools/sherlock-target-diagnosis-20261020.py --self-test
.venv/bin/python -B experiments/analysis/autonomous_20261020/tools/test_observer_edge_cases.py
```

The target self-test exercises the repository's real NumPy feature functions.
It explicitly checks that Torch and JAX were not loaded. The four observer
checks cover negative opponents, empty-point bonus exclusion, cluster scoring
and unsupported `smart_sap` overrides. They start no games.

## Reproduce the fixed observation run

Only after the parent permits a new game process and the code is frozen, use a
new output filename (existing outputs are rejected):

```sh
.venv/bin/python -B experiments/analysis/autonomous_20261020/tools/sherlock-target-diagnosis-20261020.py \
  --run-games --weights experiments/candidates/all18_v3.pth \
  --out experiments/analysis/autonomous_20261020/target_diagnosis_v3_rerun_720_739.json \
  --first 720 --n 20
```

This runs 20 already-known development maps, both sides, against Solution_92:
40 games, three match summaries per game. It loads the chosen checkpoint and
uses the normal environment; it does not train or modify weights. `--first` and
`--n` are restricted to the existing development block 500720–500779. The
baseline must have `contest_sap=False` and `smart_sap=False`. Compare all
non-time game metrics with the matching reference before interpreting counts.

## What the counters establish

Target diagnosis first reproduces the original assignment exactly on affected
steps, then computes an active-unit-only assignment on a private belief copy.
Live-unit target changes, reassigned known own point fields, and nearby units
with movement energy are separate opportunity measures. Negative first owners
and blocked `pt_sap` opportunities are reported separately; the proposed target
filter does not repair occupancy or first-owner features.

For Sap, use the sum of `strictly_better_proxy_centers` divided by the sum of
`eligible_executed_saps`. Also report eligibility relative to `executed_saps`.
The mutually exclusive classifications are unsupported override, no original
target, changed actual target, negative-enemy context and eligible action, in
that order. Their counts sum to issued Sap actions; the negative-context count
is an exclusion count after the earlier checks, not every negative observation.
Sum numerators and denominators across rows instead of averaging row rates.

These are repeated unit/step opportunities, not independent events, lost
points, guaranteed legal paths, confirmed Sap hits or causal playing-strength
improvements. Sap scores use visible energy and the existing assumed dropoff
0.5. Opponents can move before damage; actual dropoff may differ. No hidden
engine information is used for decisions or shadow scoring. Real policy
changes require separate, isolated paired evaluation.

## Integrity and verification

`manifest.json` records original temporary-source hashes, repository dependency
hashes, archive hashes and checks actually performed. `portability-review.diff`
shows the path-only changes with historical workstation paths redacted; it is a
review document, not an apply-ready patch. The extracted helper's function AST
is identical to its source. No running source, repository file, weights, or Git
state were changed to prepare this archive. No games were started by archival
verification; full inference/environment integration was not rerun here.

## Zweite Inferenzrunde

`inference_development2.py --run` führt genau drei sequenzielle Vergleiche aus: V3, nur `active_targets`, nur `sap_geometry`. Maximal zwei Evaluationsworker, keine parallelen Trainings; 60 bekannte Karten × beide Seiten × zwei Gegner je Arm. Der Referenzarm muss alle 240 nichtzeitlichen Ergebnisse des früheren V3-Laufs exakt reproduzieren. Quellen/HEAD/Gewichte bleiben während des gesamten Laufs eingefroren. Exklusive Ausgabepfade unter `inference_development2/`, keine Überschreibung oder Übernahme von Gewichten. Vorab festgelegte Auswahl im autonomen Plan. Prozessprüfung mit elf stdlib-/AST-Fixtures einschließlich Replikationstrainern und SIGHUP geprüft; unabhängig statisch geprüft.

## Explorationsvergleich in dieser Nacht

`exploration_replication.py --run --run-seed 47 --games 3000` produziert genau ein frisches Paar (`control`/`slow`), nach manueller Ressourcen-/Restzeitprüfung. Weitere erlaubte Starts 48/49, immer 3000 Spiele. Nur `eps_decay_steps` unterscheidet sich. Explizite Zeitgrenzen sind auf diese Nacht festgelegt; keine automatische Promotion oder Folgejobs. `--self-test` prüft das Gerüst ohne Modellimporte. Der gebundene Plan und `exploration_pretraining_checks.json` dokumentieren Zulassung, Tests und Grenzen.
