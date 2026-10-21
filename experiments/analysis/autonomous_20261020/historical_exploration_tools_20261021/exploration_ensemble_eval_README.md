# Kontrollierte Ensemble-Entwicklungsauswertung

Vorbereitet: `/tmp/exploration_ensemble_eval.py`. Kein tatsächlicher Lauf wurde gestartet.

Nach allen drei Pairaudits und erfolgreichem festem Ensemblebau, aus dem Repository:

```sh
.venv/bin/python -B /tmp/exploration_ensemble_eval.py --run
```

Reine Tests ohne NumPy/Torch/JAX:

```sh
python3 -B /tmp/exploration_ensemble_eval.py --self-test
```

Bei Archivierung unter `experiments/analysis/autonomous_20261020/tools/exploration_ensemble_eval.py` wird die Wurzel portabel über `__file__.parents[4]` bestimmt.

## Fester Ablauf

Der Runner verlangt ein vollständiges Buildermanifest aus `experiments/candidates/exploration_s47_49_fixed_ensembles/`. Er prüft die vier festgelegten Gruppen, 18+3+3 verschiedene Netz-Hashes, sämtliche vorhandenen Eingabe- und Ausgabe-Dateihashes und die unveränderte installierte Vergleichsabgabe. Die Checkpointconfigs wurden durch den Builder auf dieselbe einmal erfasste effektive Inferenzconfig gesetzt; der Runner überprüft die unveränderten Checkpointdateien, ohne selbst Torch zu laden.

Exklusives neues Ausgabeverzeichnis:

`experiments/compare/autonomous_20261020/exploration_ensemble_development/`

Zunächst wird die installierte Abgabe byte-identisch nach `installed_reference.pth` kopiert und gehasht. Dann laufen genau diese fünf Arme nacheinander:

1. `reference`
2. `control3`
3. `slow3`
4. `v3_control3`
5. `v3_slow3`

Jeder Aufruf nutzt `scripts.par_eval`, 500720–500779, beide Seiten, `default,solution92`, zwei Worker und eine neue CSV. Insgesamt 1.200 Spiele. Keine Trainings oder schweren Paralleltests. Vor Start und regelmäßig während der Jobs werden HEAD, Pythonbinary, Pythonquellen, Modelle, Referenz und Buildernachweise geprüft. Das Manifest hält die gemeinsame Inferenzconfig fest; es gibt keine zusätzlichen `--set`-Overrides.

Vorhandene oder teilweise Ausgaben werden nicht wiederverwendet. Eigene Prozessgruppen werden bei SIGINT/TERM/HUP, Fehlern oder Deadline beendet; fremde Prozesse werden nicht angefasst. Keine neuen Evaluationsjobs nach 21.10.2026 03:00 UTC (05:00 Berlin), Abbruchreserve ab 03:59:50 UTC. Die bekannte-Prozess-Erkennung ersetzt keine globale Sperre; Root hält die freigegebene Ruhephase ein.

## Auswertung

Erst nachdem alle fünf Jobs erfolgreich beendet und alle fünf CSVs auf exakt 240 einzigartige vollständige Keys, 303 Schritte, Point-counting 2 und gültige Resultate geprüft wurden, wird NumPy geladen. Es werden ganze Karten mit beiden Seiten gemeinsam resampelt: 5.000 Bootstrap-Ziehungen, Seed 0. Referenzvergleiche werden für alle vier Ensembles berichtet; zusätzlich Slow3 minus Control3 als Diagnose.

Nur `v3_control3` und `v3_slow3` sind auswählbar. Die Gates sind vorab fest:

- Solution92-Differenz positiv und untere 95%-Kartengrenze strikt größer 0.
- Default-Differenz mindestens −2 Prozentpunkte; Grenze über ganzzahlige Halbresultate geprüft.
- Bei zwei zulässigen Kandidaten größere Solution92-Differenz; exakter Gleichstand wählt Control.
- Sind beide unzulässig, kein Kandidat. Dreierensembles können niemals ausgewählt werden.

`state.json` enthält Befehle, Zeiten, Quellen-/Modelle-/CSV-Hashes, Config, Rohvergleichswerte, Gates und Fertigstatus. Die Auswahl ist ausschließlich eine Entwicklungsentscheidung, kein Methodenstärke- oder Promotionsnachweis.

## Getrennte Folgeschritte

Der Runner startet keine frischen Spiele und keinen Direktvergleich. Nur bei ausgewähltem Kandidaten enthält `prepared_followup` vorbereitete Befehle und explizite Voraussetzungen:

- Frisch: Referenz und genau der eine Kandidat auf **510200–510399**, je 800 Spiele. Das CLI-Argument ist `--first 10200 --n 200`, da `par_eval` 500000 addiert. Vor Start müssen Quell-/Modell-/Configidentität und Zeitbudget erneut geprüft werden. Nie einen zweiten Kandidaten auf diesem Block ausprobieren.
- Frisches Gate: beide CSVs vollständig, 200 ganze Karten samt beiden Seiten, Bootstrap 5000/Seed0; Solution92-Differenz >0 mit Untergrenze >0; Default-Verlust höchstens 2 Prozentpunkte.
- **Erst nach bestandenem frischem Gate:** Direktvergleich des unveränderten Kandidaten gegen die eingefrorene Referenz auf 60 bekannten Karten/beiden Seiten, 120 Spiele. Untere 95%-Kartengrenze des mittleren Ergebnisses muss >0,5 sein.
- Technische Kursprüfung, Reproduktion, Sicherung, Hashprüfung und ausdrückliche Promotion bleiben separate Arbeitsschritte. Keine Abgabe wird von diesem Runner geschrieben.

Diese Folgebefehle sind keine vollständigen separaten Phasen-Runner und besitzen allein keine eigene Timeout-/Hashüberwachung. Root muss sie mit den benannten Guards kontrolliert ausführen oder vorher einen getrennten Phasen-Wrapper bereitstellen. Sie werden weder automatisch noch als gemeinsame unbedingte Befehlsfolge gestartet.

## Vorbereitungsevidenz und Grenzen

Die drei Kernfixtures waren zunächst erwartungsgemäß rot; anschließend bestanden acht Tests mit synthetischen CSVs und Builderdaten sowie gemockten Prozesslisten. Sie decken Auswahlgrenzen, Tie-Regel, ausgeschlossene Diagnosearme, exakte Seeds, Datenfehler, Builderprovenienz und getrennte Folgekommandos ab. Logs: `/tmp/exploration_ensemble_eval_red.log` und `/tmp/exploration_ensemble_eval_green.log`.

Keine echten Modelle, CSV-Ergebnisse oder Prozesse wurden durch die Tests geöffnet/ausgewertet/gesteuert. Die tatsächliche NumPy-Bootstrapberechnung und Game-/Prozessintegration wurden in dieser Vorbereitung nicht ausgeführt. Die Statistik verwendet bekannte Entwicklungskarten und zwei Kandidaten; das getrennte frische Gate bleibt erforderlich.

Zusätzlich werden `slow3_minus_control3_diagnostic` und `v3_slow3_minus_v3_control3_diagnostic` mit denselben gepaarten Karten ausgewiesen. Das sind Leistungsvergleiche gegen gemeinsame Gegner, keine direkten Selbstspiele und keine weiteren Auswahlregeln. Fertige CSVs werden bis zum Abschluss erneut gegen ihre gespeicherten SHA-256 geprüft; negative Punktzahlen werden abgewiesen.

Finale Runneridentität: SHA-256 `27faea85202b6149aced00bd4c1cd85fd654101d7cbbcf7567fb713becd8099e`. Gegenüber dem statisch geprüften Zwischenstand `82f3c60...` wurde ausschließlich der exakte Scriptname `exploration_confirmation.py` zur Fremdjob-Erkennung ergänzt. Der separate vorbereitete Bestätigungsrunner ist in `exploration_confirmation_README.md` beschrieben. Beide Tools vor Beginn der Quellfreeze archivieren.
