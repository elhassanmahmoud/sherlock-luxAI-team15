# Fester Ensemblebau nach den drei Explorationspaaren

Vorbereiteter Helper: `/tmp/exploration_ensemble_builder.py`; zugehörige reine Standardbibliothekstests: `/tmp/test_exploration_ensemble_builder.py`.

Erst nach den unabhängigen vollständigen Audits aller drei 3.000er-Paare ausführen, wenn keine Trainings, Evaluationen oder sonstigen schweren Jobs laufen. Root prüft die Quellenfreigabe. Das Flag bestätigt diese bereits erledigten Audits; der Helper liest das bekannte Pair-Runner-Stateformat und benötigt keine neue externe Audit-API.

Aus dem Repository:

```sh
.venv/bin/python -B /tmp/exploration_ensemble_builder.py --run --confirm-pair-audits
```

Portabel kann die Datei später unter `experiments/analysis/autonomous_20261020/tools/exploration_ensemble_builder.py` archiviert werden; dort wird die Repositorywurzel über `__file__.parents[4]` bestimmt.

Der Helper erstellt exklusiv das zuvor nicht vorhandene Verzeichnis:

`experiments/candidates/exploration_s47_49_fixed_ensembles/`

Darin genau vier Checkpoints und ein Manifest:

| Datei | Zusammensetzung in fester Reihenfolge |
|---|---|
| `control3.pth` | Control 47, 48, 49 |
| `slow3.pth` | Slowexplore 47, 48, 49 |
| `v3_control3.pth` | alle 18 V3-Netze, dann Control 47, 48, 49 |
| `v3_slow3.pth` | alle 18 V3-Netze, dann Slowexplore 47, 48, 49 |

Die V3-Datei ist fest an SHA-256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935` gebunden. Der Helper verlangt insgesamt 24 verschiedene Q-State-Hashes; keine automatische Entfernung von Duplikaten oder Auswahl anderer Inputs. Die Netzliste wird wie in `scripts/build_ensemble.py` flach angehängt. `Agent_x` mittelt alle Netze gleichgewichtet; die V3+3-Kandidaten haben jeweils 21 Netze, keine neue Gruppengewichtung.

Die beiden installierten Abgabedateien müssen identische Dateihashes besitzen. Ihre effektive `AgentConfig` wird einmal aus dem Checkpoint und den unveränderten Defaults ermittelt, im Manifest gespeichert und für alle vier Ausgaben verwendet. Die Trainingsconfigs bleiben in ihren Quellen und Identitätsnachweisen unverändert. Wie beim bestehenden Builder bleiben Q, Target und Optimizer des jeweils ersten Checkpoints erhalten; keine Quell-Optimizer oder Quelldateien werden geschrieben. Die Ergebnisse sind Inferenzartefakte, keine freigegebenen Trainings-Resumes.

Prüfungen vor/bei dem Bau:

- Drei abgeschlossene Pair-States, exakt Seeds 47–49/3.000 Spiele, richtige Varianten und feste Pfade; Preflight, tatsächlicher Initialzustand, Manifest, finale Identitäten und zugehörige CSV-/Checkpoint-Dateihashes.
- Innerhalb jedes Paars gleiche Q-/Target-Initialisierung und RNG, Configdiff ausschließlich Epsilon-Decay 60.000/454.500, Terminal-/Aktivziel-/Sap-Geometrieflags aus.
- Identische Pythonquellen einschließlich Dateimenge und Interpreter über die Paare. Abweichende historische HEADs werden separat protokolliert; die zulässigen Daten-/Dokumentationsübergänge müssen Root und die vorgelagerten Pairaudits bestätigt haben.
- `PLAY_KEYS` entspricht dem bestehenden Builder. `feature_dim`, `n_actions`, Eingabesemantik, Tensorstruktur und Dtypes müssen passen. Alle Tensoren der geladenen Checkpoints, einschließlich Targets und Optimizerstates, müssen endlich sein; keine unberücksichtigte CNN-Zusatzpolicy.
- Torch wird erst nach den State-/Hash- und Prozessprüfungen geladen. CPU und Bibliotheksthreads sind auf einen Thread begrenzt. Die Erkennung bekannter schwerer Pythonjobs ersetzt keine globale Exklusivsperre; Root hält die ausdrücklich geforderte Ruhephase ein.
- Vier exklusiv geschriebene Ausgaben werden erneut geladen und auf exakte Config und geordnete Q-State-Hashes geprüft. Quellenhashes werden vor und nach dem Bau verglichen. Manifest enthält alle Eingabe-/Ausgabehashes, Netzprovenienz und Fertigstatus.

Bei Fehler oder Unterbrechung nach Verzeichniserstellung bleiben Teilergebnisse erhalten. Ein erneuter Start überschreibt weder das Verzeichnis noch einzelne Dateien. Es gibt keinen Resume, keine automatische Promotion, keinen Abgabeschreibpfad und keine Spielausführung.

## Bisherige Prüfung

```sh
python3 -B /tmp/test_exploration_ensemble_builder.py
```

Acht Tests mit abstrakten Netzzuständen, synthetischem Pair-JSON und gemockten Prozesslisten bestehen. Sie prüfen feste Gruppierung, Duplikate/Überlappung, Config-/Dimensionskompatibilität, Nichtmutation der Quellen, Prozesszulassung, vollständige sechs Inputs, erlaubte historische HEAD-Änderung und Ablehnung partieller/falscher/veränderter Inputs. Kernverhalten war zuvor mit 16 Assertions rot; die HEAD-Korrektur hatte einen separaten roten Regressionstest. Logs: `/tmp/exploration_ensemble_builder_red.log`, `/tmp/exploration_ensemble_builder_head_red.log`, `/tmp/exploration_ensemble_builder_green.log`.

Es wurden bei der Vorbereitung keine echten Modellcheckpoints geöffnet oder gehasht, kein Torch/NumPy/JAX importiert und keine Torch-Serialisierung ausgeführt. Die echte Checkpointkompatibilität und Ausgabe-Readback-Prüfung erfolgen erst beim später ausdrücklich gestarteten Bau. Unabhängiger statischer Review durch strategy_review fand nach der HEAD-Korrektur keine weiteren konkreten Fehler in Gruppierung, Configübernahme, Tensorprovenienz und Ausgabeschutz.
