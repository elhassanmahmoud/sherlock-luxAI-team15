# Quellen und Bearbeitung des neuen Foliensatzes

Stand 14.10.2026. Fachliche Basis: Git-Commit `12e0c4d9c31a81c54ba453b4f3fbb350b0589faa` vor dieser reinen Präsentations-/Dokumentationsarbeit.

## Nachweise je Thema

| Folien | Inhalt | Repository-Quelle |
|---|---|---|
| 1–3 | Team, Spiel, Agentenablauf | README.md; lux/specs.md; agents/sherlock/main.py; belief.py |
| 4 | 79 Merkmale und Inferenz | agents/sherlock/features.py; belief.py |
| 5–6 | Dueling und Double DQN | agents/sherlock/model.py; main.py; reward.py; replay_buffer.py |
| 7, 12 | Training und Konfiguration | Sechs Manifeste unter experiments/runs/20261010_full_s0 bis s2 und 20261011_full_sym_s0 bis s2; gespeicherte cfg des aktuellen agent_p0.pth |
| 8, 11 | 60/60 und 28/60 Siege | experiments/compare/TEST_old3_sym3_points_v2.csv und zugehörige JSON |
| 9 | Spielbeispiel | docs/presentation/replays/sherlock_sieg_vs_default.json, Frames 23 und 90 |
| 10–11 | Grenzen und Ausblick | docs/EXPERIMENT_PROTOKOLL.md; docs/ARBEITSSTAND.md; docs/STATISTIK_20261014.md |
| 13 | Gelernt / programmiert | Agentenmodule wie oben; scripts/scoring.py nur für externe Messung |

`slides.json` enthält Sprecher, Zeitbudget, vollständige Sprechernotizen und die Quellen jeder Folie. Die PowerPoint ist die bearbeitbare Folienquelle; JSON ist eine zusätzliche Übergabehilfe, kein automatisch synchronisierter Export. Nach Änderungen PowerPoint, PDF und Vortragsplan gemeinsam abgleichen.

Das native Diagramm auf Folie 8 nutzt gerundete Siegquoten 1,000 und 0,467 (100,0 % und 46,7 %). Die exakten Zähler stehen daneben: 60/60 und 28/60. Die zugehörige eingebettete Datentabelle dient der Bearbeitung des Diagramms, nicht als neuer Rohdatensatz. Keine historischen Konfidenzintervalle übernommen.

## Echte Spielbilder

Die PNGs wurden am 14.10.2026 im [Lux Eye S3 Viewer](https://s3vis.lux-ai.org/) aus dem vorhandenen öffentlichen Team-Replay aufgenommen. Keine generierten oder nachgestellten Spielszenen. Es sind Ausschnitte der Karte; sichtbare Punkte und Frames wurden in der Viewer-Oberfläche und in der Replay-Datei abgeglichen.

- `replay_023.png`: Frame 23, Punkte [0, 0], erstes Match; Folie 9 links.
- `replay_061.png`: Frame 61, Punkte [26, 11], erstes Match; Folie 2.
- `replay_090.png`: Frame 90, Punkte [374, 11], erstes Match; Folie 9 rechts.

Sherlock ist player_0/blau, default player_1/rot; Seed 900011. Die Bilder zeigen die vollständige Zuschaueransicht und nicht die eingeschränkte Beobachtung des Agenten. Gelbe Markierungen zeigen Relics/Punktefelder. Die Punktzahlen sind Zwischenstände im ersten Match, keine Gesamtpunktzahlen des Spiels.

[Replay direkt im Viewer öffnen](https://s3vis.lux-ai.org/#/visualizer?input=https%3A%2F%2Fraw.githubusercontent.com%2Felhassanmahmoud%2Fsherlock-luxAI-team15%2Fmain%2Fdocs%2Fpresentation%2Freplays%2Fsherlock_sieg_vs_default.json&proxy=). Zum Vortrag genügen die eingebetteten Bilder; kein Live-Aufruf nötig.

## Grenzen und unveränderter Modellstand

- 18.000 bezeichnet die Summe der sechs abgeschlossenen Basisläufe, nicht den gesamten Projektaufwand und nicht zwingend die Trainingsdauer der ausgewählten früheren Checkpoints.
- Benchmarkkarten wurden mehrfach verwendet; keine Behauptung eines unberührten Testsatzes oder einer allgemeinen 100-%-Siegchance.
- Die Diagnosen der genauen Erkundungszeitpunkte sind noch nicht zeitlich sauber ausgerichtet. Daher keine konkreten zeitlichen Vorsprünge/Rückstände auf den Folien.
- m1_early ist ein späterer Kandidat, kein Teil der aktuellen Abgabe.
- Beide Abgabe-Gewichte bleiben SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## Bildprüfsummen

- `replay_023.png`: `871157e7ff99a4c169e40b892c12621310172f44d9041ae76a32954933583670`
- `replay_061.png`: `872008904674bd28351f58dc36de1596ec91a975a5f4e2c7b9690d6a8431b31f`
- `replay_090.png`: `5c66179058e2579a036ce066af9ebbabc3703590bd0c1a18cc7b3bd6e1f57eb0`

## Randloser PDF-Hintergrund

Am 14.10. wurde ausschließlich der PDF-Export auf den dunklen Seiten 1 und 11 korrigiert: Hintergrundfläche und Beschnitt reichen dort einen Punkt über die Seitenkante hinaus. Dadurch entfällt die weiße Haarlinie durch Export-/Rasterrundung. Seitenformat, Texte und Positionen bleiben gleich; die PowerPoint ist bereits randlos und unverändert. Nach einem neuen PDF-Export die Außenkanten dieser Seiten prüfen. Aktuelle Prüfsummen stehen in `PRUEFUNG.json`.

## Kurztitel und Aufzählungen

Die Titel wurden am 14.10. auf kurze Themenbezeichnungen umgestellt. Folien 2, 8, 9 und 11 verwenden auf Wunsch von Moayed native Aufzählungen mit kurzem Strich (–) statt Punkt. Zeichen und Text verwenden Helvetica Neue; der hängende Einzug lässt Abstand zwischen Strich und erstem Wort und richtet Folgezeilen am Text aus. Die Benchmark-Anmerkung auf Folie 8 bleibt ohne Listenzeichen. Titel im Vortragsplan und in `slides.json` entsprechen der aktuellen PowerPoint/PDF. Folie 11 bündelt jetzt den Ansatz (Gedächtnis plus sechs Netze), die Benchmark-Siegezahlen und den nächsten Schritt (frühe Erkundung, neue Testkarten). Die zugehörige Sprechernotiz ist in PowerPoint, JSON und Vortragsplan synchronisiert. Fachliche Nachweise, Diagramm-Datentabelle, Zeitbudget und Sprecheraufteilung bleiben erhalten.

## Pseudocode und sichtbare Trainingsparameter

Folie 3 orientiert sich gestalterisch an Folie 4 der vom Team bereitgestellten `team20-presentation3.pdf`: heller Codekasten, Courier New, eingerückte Schleifen und kurzer Kommentar. Farben, Titel und übrige Typografie bleiben im Sherlock-Design. Es wurden keine fachlichen Trading-Inhalte übernommen; die Referenzdatei wurde nicht ins Repo kopiert.

Der Pseudocode beschreibt den vereinfachten Hauptablauf des festen Ensembles in `agents/sherlock/main.py` (`act`, `_decide`): Beobachtung ins Belief übernehmen, Merkmale erzeugen, sechs Netzbewertungen mitteln, erlaubte Aktion wählen und Aktionen zurückgeben. Match-Reset, heuristisches Sap-Ziel, Aktionsformat/Spiegelung und die tatsächliche Stapelverarbeitung sind zur Lesbarkeit ausgelassen. Es ist kein Trainingspseudocode und kein ausführbares Programm.

Auf Folie 7 stehen Lernrate 0,0003, γ 0,99, Batch 256, Buffer 300.000 Einheitenübergänge, ε von 1,0 auf 0,05 über 60.000 Umgebungsschritte und Target-Kopie alle 500 Lernupdates. Die Werte wurden erneut mit allen sechs abgeschlossenen Basislauf-Manifesten abgeglichen. Details zu Lernbeginn und Trainingsintervall bleiben auf Folie 12. Elf Vortragsfolien und zwei Reservefolien sowie das geplante Zeitbudget von 640 Sekunden bleiben erhalten.
