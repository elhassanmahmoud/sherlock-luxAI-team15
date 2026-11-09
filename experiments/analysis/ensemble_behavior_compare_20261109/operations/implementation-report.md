# Ensemble-Behavior-Vergleich: tatsächliche Integration

Basis `07f3b4739cca520bdf5c5e4baa4976bf5e09afd6`. Nur die drei neuen zugewiesenen Projektdateien integriert; bestehende Quellen, Gewichte und historische Daten unverändert. Keine Commits, echten Archive dekodiert, Simulatoren, Spiele, Aufnahme oder Phase gestartet. Gegenüber den zuvor statisch geprüften Entwürfen ausschließlich irreführende Draft-Docstrings entfernt; keine fachliche Korrektur erforderlich.

## Tatsächliches Red/Green

Alle drei Läufe verwendeten:

```text
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider
```

1. Nur neue Testdatei integriert, dann `tests/test_ensemble_behavior_compare.py`: erwarteter Importfehler des noch fehlenden `scripts.ensemble_behavior_compare`, Exit 2, 2,53 s. Originalbeleg `red-missing-module.log`, SHA `740ce0c494464ece3a5ad74e8383a41efcc1078f8cc8274f86e817b289367704`. Das ist der fehlende Modulvertrag, kein behaupteter einzelner Assertion-Fehlschlag.
2. Beide Werkzeuge integriert, dieselbe neue Testdatei: **60 PASS, 3,36 s, Exit 0**. `integrated-tests.log`, SHA `2667b34d7a1ce0623e5e329d9b4154f31fdb64dbff4f8d08ab13ff218f59cc79`.
3. `tests/test_ensemble_behavior_compare.py tests/test_match_weight_compare.py`: **109 PASS, 4,36 s, Exit 0**. Die 49 vorhandenen Vergleichstests schließen deren Owner-Verträge ein. `final-tests.log`, SHA `81afbf50c8f205f0169e41cc4d4621c7d88e149d6700730471538de0e3afbac4`.

Produktionsarchive, echte Simulator-/Spielaufrufe und echte Prozessstarts sind in der neuen Suite gesperrt; ausdrücklich synthetische In-Memory-Checkpoints prüfen den originalen Loader. Keine Gesamtsuite und kein pytest-Cache.

## Stabile Projektdateien

| Datei | Zeilen | SHA256 |
|---|---:|---|
| scripts/ensemble_behavior_compare.py | 421 | `7715fc4e671a44d4c1cfa2dd5761d972bceb42c95fb068ffb6cf7801a34e56cb` |
| scripts/ensemble_behavior_compare_owner.py | 101 | `003836187e40ca02bc87fe80cd1e9cfb5086eec657e4b4d5395158d938b854e5` |
| tests/test_ensemble_behavior_compare.py | 514 | `b92bef1950e12cfa83b82276f50054f021e994cb2a7af51867381315233884f5` |

Root/Watcher-Review: `/private/tmp/ensemble-behavior-compare-final-review.md`; kein offener konkreter Blocker. Modelle/Runtime und echte Phase bleiben separat aufzunehmen und tatsächlich zu prüfen.

## Aufnahmehelfer und Vertrag

`/private/tmp/ensemble-behavior-compare-build-admission.py`, SHA `4d71e5a19b0d201f0c568397fc41daf78b2c475f06a2fe9fcc3c6ead6352f498`.

Pflicht: `--stage technical|performance --expected-head FULL_40_HEX_COMMIT --stop-file ABS`. Standard prüft nur; ausschließlich `--write` veröffentlicht exklusiv `experiments/analysis/ensemble_behavior_compare_20261109/STAGE-v1-admission.json`. Performance benötigt zusätzlich `--technical-acceptance ABS`. Kein Start und kein automatischer Phasenwechsel.

Tatsächlich rein auf JSON-/Hashmetadaten geprüft mit:

```text
TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B /private/tmp/ensemble-behavior-compare-build-admission.py --stage technical --expected-head 07f3b4739cca520bdf5c5e4baa4976bf5e09afd6 --stop-file /private/tmp/ensemble-behavior-compare-technical/STOP
```

Exit 0, PASS: 110 gebundene Inputs, 422 Sourcefiles, `admission_written=false`, `started=false`. Originalbeleg `builder-check-only.log`, SHA `4318b6707df0dff325e9cf7f37d319304b00e5410ba6bf887934b80a534541f1`. Für die tatsächliche Aufnahme nach Quellenpublikation muss der dann aktuelle **neue** Vergleichscommit explizit angegeben werden; der obige historische Prüf-HEAD wird nicht automatisch weiterverwendet.

Der Helfer bindet die echte Trainingsclosure fest auf `fca3a077e57f079605db362f9dc68facadf787b0a3e819d1aca85050a84b23ce`, sämtliche `closure.files`, ursprüngliche Trainings- und Referenzadmission-Inputs, beide Final-/Receiptketten, alte Root-Montageannahme/Owner/Receipt, beide bytegleichen Referenzkopien, Schutzdateien, die drei neuen Dateien sowie alte und neue Planbindungen als Vereinigung. Die bestehende Seedannahme und ihre Dateien werden wiederverwendet. Keine Archivdekodierung oder erneute historische admission()-Ausführung.

Gemeinsame Admission: `schema_version/profile/stage/start_authorized`, `root/python/plans/source/inputs/protected/allow_battery/stop_file/out`, `v14_source`, `training_completion/training_completion_sha256`, `reference_admission/reference_state/reference_receipt/reference_acceptance`, `cohorts/seed_acceptance`. Performance ergänzt `technical_admission/technical_state/technical_receipt/technical_acceptance` und `models={v14,control,behavior}`. Root-Montageannahme bindet `profile/status=PASS/source/admission_sha256/technical_receipt_sha256/owner_state_sha256/actual_assembly_and_stock_loader_pass=true/original_processes_ended=true`.

Owner-CLI nach tatsächlicher getrennter Aufnahme: `python -B -m scripts.ensemble_behavior_compare_owner technical|performance --admission ABS --admission-sha SHA --usage-file ABS`. Nullspielige Montage und 200er-Performance bleiben getrennte Aufnahmen. Der reine Buildercheck ersetzt weder den produktiven Admissionvalidator noch die reale Montage-/Loaderprüfung.
