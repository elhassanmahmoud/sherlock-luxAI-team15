# Wie V14 auf Karte 4242 entscheidet

**Match 1, Schritt 45, Spieler 0.** Einheit 6 steht bei (12, 4). Die 36 Netze bewerten die Bewegung nach unten am höchsten. Auf dem Zielfeld (12, 5) liegt ein Asteroid. Die Maske sperrt diese Richtung. Unter den fünf verfügbaren Aktionen liegt Rechts vorn. Sherlock sendet den Befehl [2, 0, 0] und bewegt die Einheit nach rechts.

| Aktion | Stehen | Hoch | Rechts | Runter | Links | Schießen |
|---|---:|---:|---:|---:|---:|---:|
| Mittlerer Q-Wert | 10,07 | 9,37 | **11,08** | 11,46 | 9,51 | 8,21 |
| Verfügbar | ja | ja | ja | **nein** | ja | ja |

Die Aufnahme liest die sechs Werte aus der tatsächlichen Netzausgabe vor dem Anwenden der Maske. In diesem Beispiel stimmt die gesendete Aktion mit der besten erlaubten Netzempfehlung überein. Alle 303 Befehlsmatrizen von Spieler 0 stimmen mit der [ursprünglichen Kursaufnahme](../continuation_20261102/existing_v14_preflight/README.md) überein. [Exakte Q-Werte und Maske](folienbeispiel.json)

## Vergleich der beiden Quellstände

Der direkte Vergleich des ursprünglichen R3 gegen V14 spielte mit den Quellen aus Git-Stand 0105658. In der heutigen Arbeitskopie unterstützen vier dieser Agentendateien zusätzliche Funktionen. Der Prüfer lädt den ursprünglichen und den aktuellen V14 (Quellen c13681d) in getrennten Prozessen über denselben Konstruktor wie der damalige Evaluator. Er prüft die geladenen Gewichte, die 36 tatsächlichen Netzaufrufe je Auswertung und die Fehlerzähler. Jeder Stand erzeugte alle 606 aufgezeichneten Befehlsmatrizen beider Sitze auf der Kurskarte 4242 exakt, einschließlich der Matchwechsel bei 101 und 202. Die Gewichtsdateien und die bereits eingereichte V14-ZIP wurden nur gelesen.

Dieser Vergleich belegt die Aktionsgleichheit auf der aufgezeichneten Partie mit der heutigen Referenz. Der historische Direktvergleich bleibt bei 120 gespielten Partien. Beim Nachspielen gab es keine weiteren Spiele gegen R3. [Prüfprotokoll beider Quellen](versionsvergleich.json)

Die folgenden Aufrufe verwenden die Python-Umgebung des Projekts. Das Ausgabeziel muss jeweils neu sein.

```sh
STUDIE=experiments/analysis/v14_course_trace_20261116
.venv/bin/python -I -B "$STUDIE/check.py" run --repo . --out /tmp/v14-quellenvergleich.json
.venv/bin/python -B "$STUDIE/capture.py" --project . --out /tmp/v14-netzwerte.json
```
