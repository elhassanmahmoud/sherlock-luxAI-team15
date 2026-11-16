# Welche Lehrer-Schüsse erkennt der reine v4-Schüler?

Auf den ersten fünf vollständigen Karten je Gegner empfiehlt der Kaggle-Lehrer **1.542 zulässige Schüsse**. Mit den gespeicherten Eingaben wählt der v4-Schüler in **652 Fällen einen Schuss (42,3 %)** und in **468 Fällen auch das Lehrerziel (30,4 %)**. Auf den 890 übrigen Lehrer-Schüssen hätte der Zielkopf allein bereits **614-mal (69,0 %) das richtige Feld** gewählt. Die Entscheidung zwischen Schuss und Bewegung/Halten ist in dieser Stichprobe die häufigere Fehlerquelle.

| Gegner im Schüler-Spiel | Zeilen gesamt | Zulässige Lehrerbefehle | Vollständig richtig | Lehrer-SAP | v4 schießt | Davon exaktes Feld | v4 bewegt sich | v4 hält | Zielkopf richtig auf allen Lehrer-SAP | v4 schießt bei Lehrer-Nicht-SAP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Kaggle-Dritter | 15.155 | 14.692 | 10.960 | 705 | 288 | 187 | 383 | 34 | 449 | 457 |
| V14 | 18.382 | 18.001 | 14.275 | 397 | 168 | 116 | 178 | 51 | 285 | 272 |
| Solution | 18.504 | 17.865 | 14.051 | 440 | 196 | 165 | 181 | 63 | 348 | 252 |
| **Summe** | **52.041** | **50.558** | **39.286** | **1.542** | **652** | **468** | **742** | **148** | **1.082** | **981** |

„Exaktes Feld“ verlangt die identische kanonische Zielkoordinate für dieselbe Einheit im selben Zug. Die Spalte „v4 schießt“ enthält sowohl richtige als auch andere Ziele. Die eigenständige Zielkopfprüfung verwendet die Zielkarte aus demselben Netzdurchlauf und dieselbe Reichweitenmaske, auch wenn der Aktionskopf eine Bewegung wählt. Gegen Kaggle sind 187/288 gemeinsam gewählte Schüsse zielgleich (64,9 %), gegen V14 116/168 (69,0 %), gegen Solution 165/196 (84,2 %).

**Precision und Recall für die Entscheidung zu schießen.** Von den 1.633 vorhergesagten Schüssen entsprachen 652 einer zulässigen Schussempfehlung des Lehrers. Die SAP-Precision beträgt damit **652/(652+981) = 39,9 %**. Von den 1.542 zulässigen Lehrer-Schüssen erkannte v4 652, also **42,3 % Recall**. Wenn beide einen Schuss wählten, stimmte das genaue Ziel in **468/652 = 71,8 %** überein. Über alle zulässigen Lehrer-Schüsse waren das **468/1.542 = 30,4 %** vollständig richtige Schussbefehle.

**Erlaubte Lehrerbefehle nach Aktion.** Bewegungsrichtungen sind kanonisch. Die 6×6-Verwechslungsmatrix jedes Sitzes steht in der JSON-Datei in derselben Reihenfolge.

| Gegner | Halten | Hoch | Rechts | Runter | Links | SAP |
|---|---:|---:|---:|---:|---:|---:|
| Kaggle-Dritter | 4.131 | 804 | 5.010 | 3.220 | 822 | 705 |
| V14 | 7.681 | 909 | 3.694 | 4.326 | 994 | 397 |
| Solution | 8.867 | 897 | 2.982 | 3.689 | 990 | 440 |

**Nach Match.** Jede Zelle nennt zulässige Lehrer-Schüsse / v4 schießt / v4 schießt exakt aufs Lehrerfeld. Die tatsächliche Matchuhr der Sammlung ordnet die Zeilen zu.

| Gegner | Match 1 | Match 2 | Match 3 |
|---|---:|---:|---:|
| Kaggle-Dritter | 240 / 92 / 58 | 275 / 125 / 85 | 190 / 71 / 44 |
| V14 | 157 / 63 / 42 | 154 / 64 / 45 | 86 / 41 / 29 |
| Solution | 92 / 27 / 23 | 184 / 97 / 78 | 164 / 72 / 64 |

**Ein messbarer nächster Lernvergleich.** Für einen späteren Fit die Treffer des Aktionskopfs für Lehrer-SAP und die zusätzlichen Schüsse auf Lehrer-Nicht-SAP gemeinsam ausweisen. Hier stehen 890 ausgelassenen Schüssen bereits 981 zusätzliche auf anderen Zeilen gegenüber. Eine pauschal höhere Schussneigung würde beide Gruppen betreffen. Aus der Übereinstimmung mit Lehrerbefehlen folgt keine Aussage über Treffer, Schaden oder Spielsieg.

## Archivbasis und Grenzen

Die Auswahl wurde vor Inferenz aus dem hashgebundenen Register aller 400 vollständigen, frischen DAgger-Spiele festgelegt. Je Gegner wurden die fünf kleinsten Seeds verwendet, mit dem ursprünglich ausgelosten Sitz. Alle 15 sitzen auf verschiedenen Karten; jeder Gegner liefert fünf Spiele. Die 50.558 zulässigen Entscheidungen sind wiederholte Einheitenbeobachtungen innerhalb dieser Spiele. Die Rohsummen gewichten jede zulässige Einheitsentscheidung gleich. Die Labels stammen in allen Gruppen vom selben Kaggle-Schattenlehrer auf den vom reinen v4-Schüler erreichten Stellungen. Der Lehrer erhielt nach jedem gespielten Schritt Rückmeldung über den tatsächlich ausgeführten v4-Teambefehl.

Die Originalprüfung der NPZs verifiziert jeden 303-Schritte-Sitz, die UID-Abdeckung, die Folgemeldungen, die kanonisierten Lehrerbefehle und deren SHA-256. Für Bewegungen gilt die aufgezeichnete Aktionsmaske des Sherlock-Decoders. Die ursprüngliche Funktion `prepare_labels` stellt SAP-Bezahlbarkeit aus auf ganze Energie/Kosten gerundeten Features wieder her und prüft beide Koordinaten sowie die Chebyshev-Reichweite. Alle 1.542 Lehrer-SAP waren zulässig. Die 1.483 ausgeschlossenen Zeilen betreffen andere Lehrerbefehle. Die Welt- und kanonischen Richtungen sowie SAP-Deltas folgen dem Originalcode für den jeweiligen Sitz.

**Dies sind Netzvorhersagen auf Archivstellungen.** Der echte `ImitationAgent.act` erhält die gespeicherten und zurückskalierten Ebenen (int8/127), Merkmale (float16→float32), Unit-IDs, Masken und Feldhalter. Er nutzt die Originalgewichte, die ursprüngliche SAP-Zielmaske einschließlich Eigenfeld sowie STAY-Abzug 1,5 und Unstack. Die übrigen nachgelagerten Aktionsschalter waren aus. Auf 31 Einheitszeilen zeigen Belegungs-/Haltermerkmale ausdrücklich eine gefilterte Einheit am selben Feld. Die Archivierung lässt Einheiten negativer Energie weg, und die ursprünglichen Netzeingaben vor Rundung sind nicht gespeichert. Die 15 kanonischen Lehrerströme stimmten bytegenau mit ihrer Aufnahme überein. **0/15** rekonstruierten Schülerströmen entsprach der vollständige ursprüngliche Welthash. Die genaue Zahl geänderter Livebefehle lässt sich aus diesem Gesamthash nicht bestimmen. Die kleine vorab ausgewählte Stichprobe beschreibt das reine Offline-Netz. Sie belegt weder eine Wirkung auf Spielsiege noch die tatsächlich ausgeführten einzelnen Livebefehle. Es wurden keine neuen Spiele oder Trainingsupdates ausgeführt.

## Reproduktion

[sample.json](sample.json) enthält die 15 vorab festgelegten Sitzschlüssel und NPZ-Prüfsummen. [ergebnisse.json](ergebnisse.json) enthält Einzelmatrizen, Matchsummen, alle Aktionsstromvergleiche sowie die geprüften Quell- und Modellhashes. [diagnose.py](diagnose.py) enthält die vollständige Auswertung, [run.log](run.log) das Laufprotokoll. Im Projekt weist `experiments/analysis/umbau_20261115/dagger_zusatz/README.md` den Wiederaufbau der eingefrorenen Sammlerquelle und den Datensatz nach.

Die Variablen `QUELLE`, `DATEN` und `DIAGNOSE` bezeichnen den eingefrorenen Sammler mit dessen Checkpoint, das entpackte `k3_v4_extra_7172000` und diesen Diagnoseordner. `PY` ist der Interpreter der Kursumgebung. Verwendet wurden Python 3.13.13, Torch 2.14.1 und NumPy 2.5.4 auf CPU mit je einem Torch-/BLAS-Thread. Gemessener Spitzen-RSS des einen Prozesses 498,8 MiB.

```sh
"$PY" -B -u "$DIAGNOSE/diagnose.py" --source "$QUELLE" --data "$DATEN" --out "$DIAGNOSE/wiederholung.json"
```

Feste Prüfsummen (SHA-256):

- Sammlerquellenregister `adeb0c096fc025f8ced1abbbff55b2f2d651147b48d4161f8708de07b6055521`
- Datensatzprotokoll `bdbc249aeb9831b8f83eaf2144da3f361ac983e20d6cd16f46b955ec2bd34290`
- 400er-Index `fd46ae863eb6a99a2876480f13eb0ec61fcdcb52da78711f82b93f2d2648e94e`
- Originaler v4-Schüler `0e8b280cb2173c4efd0d0c94e38119bf2f570dd5af06f52e1b5a7c9743ad7b7f`
- Vorauswahl `cb7fee3485c1276b24563b5503f92cf54f2e32cb63d34736ee660d3d955030a9`
- Ergebnis dieses Laufs einschließlich des maschinenabhängigen Spitzen-RSS `a67f3dd09db64a82dff0d5ca388d020a94a1da620837a9f7dedbb4c136021156`
