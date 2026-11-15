# Richtungsberater im Kursformat

Der Kandidat verwendet das ursprüngliche R3-Bewegungsnetz mit einer Kartenansicht und denselben V14 wie die Forschungsfassung. Bei einer legalen Empfehlung ab 50 und unter 70 Prozent darf R3 zusätzlich zwischen zwei unterschiedlichen Bewegungsrichtungen wechseln. Für Stillstand und Schüsse gilt dieses Zusatzfenster nicht. Die ursprüngliche Auswahl ab 70 Prozent, die Aktionsprüfung und die Rückmeldung der ausgeführten Befehle stammen aus derselben Forschungsfassung.

Der Kurseinstieg für beide Spieler ist `agents.sherlock.main.Agent_x`. Beide laden `agents/sherlock/weights/agent.pth`. Der separate Kandidat heißt `r3-richtungsberater-kandidat.zip`. Zwei Paketbauten ergaben dieselben Bytes. Von 27 Einträgen im geprüften ursprünglichen R3-Paket blieben 26 bytegleich. Der Einstieg importiert den Richtungsberater und übergibt die Gewichte als temporäre Datei. Das einzige zusätzliche Modul enthält dieselbe Logik wie die Forschungsdatei, mit lokalen Paketimporten. Die Originalpakete für Zwei-Ansichten-R3 und den Rückwechsel nach einer Auftaktniederlage lassen sich ebenfalls bytegleich mit ihren bisherigen Prüfsummen bauen.

| Artefakt | SHA-256 |
| --- | --- |
| Ursprüngliche R3-Kurs-ZIP | `8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d` |
| ZIP mit Richtungsberater | `e433a81dafc8c22c9ec16a22e6fbc9acf2e1960e343044b5ff72c0548da11d8e` |
| Gemeinsames Gewichtsbündel | `d20814949d4460c523ac718acf74e282ef5cdf4e3b743b4713d6aac95795d554` |
| V14 im Bündel | `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` |
| R3 im Bündel | `99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9` |
| Originale Forschungsdatei mit Richtungsregel | `1c300c6ad4cf2f92107c804c29e20414d86c5a2d3faa66ae5feb8100450e6e7b` |

## Zwei bekannte Kursverläufe

Die technischen Referenzen sind die ersten geeigneten Solution-Partien je Sitz auf zwei verschiedenen Karten in der [veröffentlichten Vorauswahl](../games/screen/external/games.jsonl). Beide Partien enthalten viele tatsächlich ausgeführte zusätzliche Richtungswechsel.

| Karte und Sitz | Matches | Punkte Sherlock / Solution | Geänderte Einheitsbefehle | Davon Zusatzfenster |
| --- | --- | --- | ---: | ---: |
| 7170230, Spieler 0 | 3 zu 0 | 1688 / 1277 | 711 | 194 |
| 7170231, Spieler 1 | 3 zu 0 | 1968 / 1701 | 717 | 160 |

Das frühere Spielarchiv enthält Endzahlen und Eingriffszähler. Die einzelnen Aktionsmatrizen werden bei der technischen Wiederholung aufgezeichnet. In einem separaten Prozess lädt der Kurs-Runner den Kandidaten aus der ZIP. Auf denselben Beobachtungen vergleicht der Prüfer pro Zug sämtliche 16 vollständigen Weltbefehle beider Agentenversionen, einschließlich der Schusskoordinaten. Für jeden Sitz müssen 303 Matrizen, alle laufenden Eingriffszähler, die Punkte, drei Matchausgänge als Gesamtsumme und 303 Kurs-Updates übereinstimmen. Die Prüfung mit Python 3.13.13 ist bestanden. Alle 606 Aktionsmatrizen und Updates sowie die beiden Endstände stimmen überein. Die Kursfassung fing keinen internen Fehler ab. [Prüfprotokoll und Aktionshashes](kursparitaet.json). Diese beiden Wiederholungen dienen der technischen Prüfung. Die Spielstärke wird im [getrennten Vergleich](../BESTAETIGUNGSPLAN.md) bestimmt.

## Nachbauen und vergleichen

Vom Projektstamm mit der Spielumgebung der archivierten Vorauswahl (Python 3.13.13, arm64). Ein aktueller Checkout und der alte Forschungsstand haben unterschiedliche Fassungen der übergeordneten Beraterklasse. Deshalb wird die Basis aus dem jeweiligen Git-Objekt rekonstruiert und nur die einzelne Richtungsregel ergänzt. Die ursprüngliche Kurs-ZIP steht lokal im Hauptprojekt. Falls sie fehlt, erzeugt der [ursprüngliche Paketbau](../../movement_soft_20261115/candidate_package/README.md) denselben Eingang.

```sh
RUN=$(mktemp -d)
mkdir "$RUN/research"
git archive 0105658188b2ec5eaf5c3a4b0ef477be9a1412f8 agents scripts lux | tar -x -C "$RUN/research"
git show b04ae698dfbf79694010430c6e34ecc5d4f1d103:scripts/r3_turn_advice.py > "$RUN/research/scripts/r3_turn_advice.py"
git show bd202fb26c5b6e919007760c62eb5830a1439191:experiments/candidates/movement_dagger_20261115/r3_soft.pth > "$RUN/r3.pth"
BASE=experiments/analysis/movement_soft_20261115/candidate_package/r3-final-candidate.zip
ZIP="$RUN/r3-richtungsberater-kandidat.zip"
.venv/bin/python -B scripts/build_r3_diagonal_course_candidate.py --turn-advice --base "$BASE" --out "$ZIP"
.venv/bin/python -I -B scripts/check_r3_course_parity.py --turn --zip "$ZIP" \
  --research "$RUN/research" --v14 "$RUN/research/agents/sherlock/weights/agent_p0.pth" --r3 "$RUN/r3.pth" \
  --screen experiments/analysis/r3_turn_advice_20261115/games/screen/external --out "$RUN/kursparitaet.json"
```
