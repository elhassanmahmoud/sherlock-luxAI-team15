# Welche Entscheidungen halfen Sherlock?

Auf zwölf bekannten Trainingskarten (7271000–7271011) wurden alle drei Varianten auf beiden Seiten bis zum Spielende ausgeführt. Jede Karte hatte genau einen Gegner. Die 24 Kontrollspiele reproduzierten ihre ursprünglichen Matchstände und alle 75.967 verglichenen Einheitsentscheidungen. Die Spiele der beiden Eingriffe entwickelten sich nach der ersten Änderung frei weiter. Die folgenden Zahlen zählen gewonnene Spiele; die Zahl in Klammern zählt die gewonnenen Einzelmatches von jeweils 24.

| Wer entscheidet? | Kaggle-Platz 3, 8 Spiele | Solution_92, 8 Spiele | V14, 8 Spiele |
|---|---:|---:|---:|
| V14 allein | 0 (2) | 8 (24) | 4 (12) |
| Lehrer bei Schussentscheidungen | 2 (4) | 8 (23) | 8 (22) |
| Lehrer bei Bewegungen | 2 (6) | 8 (24) | 8 (22) |

Beide Eingriffe drehten sechs Niederlagen in Siege und kosteten auf diesen Karten keinen bisherigen Spielsieg. In der Kampfvariante änderten sich 4.981 Befehle (2.476 Schussverzichte, 2.263 zusätzliche Schüsse, 242 andere Ziele). In der Bewegungsvariante änderten sich 33.910 Befehle. Sie gewann insgesamt 52 Einzelmatches, die Kampfvariante 49, die Kontrolle 38. Nach dem [vorher veröffentlichten Auswahlkriterium](GEGENPROBE.md) wird der eigene Bewegungsschüler geprüft. Der Experte durfte nur eingreifen, wenn beide Entscheidungen eine Bewegung oder Stehenbleiben vorsahen.

Hier hat der echte Lehrer mitgespielt. Ob ein kleines eigenes Netz das hilfreiche Verhalten auf neuen Karten reproduzieren kann, entscheidet erst der [getrennte Spielvergleich](SELEKTIVER_SCHUELER.md). Die acht Siege gegen Solution liefern in dieser kleinen Auswahl keinen Hinweis auf eine höhere Siegquote als V14.

Pro Spiel und Arm sind Endstand, Herkunft, Reproduktion und Zahl der Eingriffe archiviert. [Kontrolle](teacher_replay/control.jsonl) · [Kampf](teacher_replay/combat.jsonl) · [Bewegung](teacher_replay/movement.jsonl) · [Karten und Quellen](teacher_replay/study.json)
