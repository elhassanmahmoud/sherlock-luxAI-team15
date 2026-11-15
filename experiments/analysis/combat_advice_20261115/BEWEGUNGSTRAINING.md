# Erster eigener Bewegungsberater

Der Kandidat verwendet den bisherigen V14-Agenten und ein zusätzliches eigenes CNN mit 155.049 Parametern. Das CNN sieht die 16 Kartenebenen und die 79 Zahlen je Schiff. Aus sechs möglichen Aktionen schätzt es den Lehrerzug. Im gewählten Bewegungsmodus darf es nur eingreifen, wenn V14 und das CNN jeweils eine Bewegung oder Stehenbleiben vorgeschlagen haben, der gewählte Zug legal ist und der höchste Aktionswert nach Softmax mindestens 0,70 erreicht. Andernfalls führt Sherlock den V14-Zug aus. Der Kaggle-Agent wird beim Spielen dieses Kandidaten nur dann geladen, wenn er als Gegner antritt.

| Nach fünf Epochen | Messung |
|---|---:|
| Lernkarten / Validierungskarten (je beide Seiten) | 32 / 8 |
| Ausführbare Lehrerbefehle im Training | 193.764 von 201.432 |
| Ausführbare Lehrerbefehle in der Validierung | 49.338 von 51.048 |
| Richtige Aktionsklasse unter allen 51.048 Lehrerbefehlen | 62,4 % |
| Richtiger vollständiger Befehl einschließlich möglicher Schussrichtung | 61,2 % |
| Ziel exakt getroffen, wenn der Lehrer schießen wollte | 60 % |

Die Richtung spielt eine Rolle: Auf den Validierungskarten wurden 81 % der Stillstände, 30 % der Aufwärts-, 70 % der Rechts-, 55 % der Abwärts- und 23 % der Linksbewegungen korrekt erkannt. Diese Werte messen Übereinstimmung mit dem Lehrer. Der Nutzen wird in ganzen Spielen gegen die drei Gegner geprüft.

Auf den gespeicherten Validierungsstellungen würde die 0,70-Schwelle 3.432 von 51.048 Aktionsklassen ändern (6,7 %). In 2.434 Fällen gewinnt der neue Zug die Übereinstimmung mit dem Lehrer, in 605 Fällen geht sie verloren, in 393 weichen beide Vorschläge ab. Die Zahl der Übereinstimmungen steigt von 28.096 auf 29.925 (+3,58 Prozentpunkte). Diese Rechnung verwendet quantisierte Archivstellungen vor der letzten Legalitätsprüfung. In einem Spiel verändern frühere Züge alle folgenden Stellungen. [Einzeldaten je Karte und Sitz](bewegung_validierung.json)

[Eigene Gewichte](../../candidates/selective_advice_20261115/movement.pth) · [Trainingsverlauf](selective_training.log) · [Vergleichsbedingungen](SELEKTIVER_SCHUELER.md)

SHA-256 der eigenen Beratungsgewichte: `5327d0ff4e2cc4b09bdcb43ae51fbd7dcc9f6d8487f79f4a7cfd1ad176813575`. Architektur, Parameter und die 80 einzelnen Dateiidentitäten stehen auch im Checkpoint. Als Quelle für diesen Lauf wurde der Projektstand `ece525b` separat ausgepackt.
