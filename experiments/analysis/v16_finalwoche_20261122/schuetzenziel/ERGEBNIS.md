# Müssen zwei Schützen dasselbe mögliche Ziel verschieden bewerten?

**Diese konkrete Grenze der gemeinsamen V16-Zielkarte trat im Lernmaterial selten auf.** In 3.983 simultanen Schützenpaaren lagen beide vom Lehrer gewählten Ziele in der Reichweite beider Schiffe. Nur zehn Paare verlangten trotzdem zwei verschiedene Ziele (**0,25 %**). Es waren 16 verschiedene Einheitsentscheidungen in sechs Zugbildern auf sechs der 160 Karten. Die drei vorab festgelegten Mindestbedingungen (150 Paare, zwölf Karten, 2 %) wurden sämtlich verfehlt. Die Studie endet nach der Strukturprüfung. [Vorabplan](PLAN.md) · [Primärzählung je Karte](struktur.json) · [unabhängige Rekonstruktion der zehn Fälle](gegenprobe.json)

| Material | Legale Lehrerschüsse | Beide Ziele für beide legal | Verschiedene Ziele trotz beidseitiger Legalität |
| --- | ---: | ---: | ---: |
| 120 ältere DAgger-Lernpartien | 14.556 | 2.817 Paare | 3 Paare |
| 40 V16-DAgger-Lernpartien | 5.240 | 1.166 Paare | 7 Paare |
| Gesamt | **19.796** | **3.983 Paare** | **10 Paare** |

Es gab insgesamt 9.850 ungeordnete Paare, die im gleichen Zug schossen; bei 8.968 dieser Paare überschnitten sich die Reichweitenfenster. Zwei verschiedene Lehrerziele allein wären kein Widerspruch. Liegt etwa das beste Feld nur in der Reichweite von Schiff A, kann Schiff B mit derselben Zielkarte ein anderes Feld wählen. Der eindeutige Widerspruch entsteht erst, wenn auch das abweichende Ziel des anderen für beide Schiffe erreichbar ist.

Bei der unabhängigen Gegenrechnung wurden Energie und Reichweite neu aus den Archivmerkmalen rekonstruiert und für jedes Paar die Schnittgrenzen der beiden Quadrate direkt berechnet. Alle Zähler und die Zahl betroffener Karten stimmen mit dem ursprünglichen Vergleich überein. Beide Spielerpositionen sind unter den zehn Fällen vertreten. Lehrerziele sind in kanonischen Koordinaten des jeweiligen Schiffs abgelegt. Match- und Zeitgrenzen werden durch ein gemeinsames Bild desselben Spiels eingehalten.

**Einordnung.** Die Häufigkeit beschreibt diese bestimmte, über Paarvergleiche nachweisbare Einschränkung. Sie sagt nichts darüber, wie oft V16 ein falsches Ziel wählt, obwohl eine gemeinsame Rangfolge das richtige Ziel grundsätzlich darstellen könnte. Auch längere indirekte Prioritätszyklen wurden nicht geprüft. Die Archivsuche ergab frühere Ziel- und Kampftaktiken; eine bereits veröffentlichte V16-Studie genau zu dieser Paarbedingung war nicht auffindbar. Die zurückgehaltenen Schusszielkarten blieben bei dieser Messung geschlossen. Null Gradientenupdates, null neue Ausführungen, keine veränderten Gewichte.

Aus dem Repo-Stamm mit der Projektumgebung und den vorhandenen Lernarchiven:

```sh
haupt="$HOME/Desktop/KI/sherlock-luxAI-team15"
python="$haupt/.venv/bin/python"
pilot=experiments/analysis/v16_finalwoche_20261122/schuetzenziel
basis="$haupt/experiments/imitation/finalwoche_20261122/netzwahl"
ausgabe=$(mktemp -d)
"$python" "$pilot/daten.py" structure "$basis" "$ausgabe"
cmp "$pilot/struktur.json" "$ausgabe/struktur.json"
"$python" "$pilot/gegenprobe.py" "$basis" | cmp - "$pilot/gegenprobe.json"
```
