# 400 neue Trainingspartien für Mahmoud

Der v4-Schüler spielte selbst. Der Kaggle-Drittplatzierte bewertete die Stellung aus derselben öffentlichen Sicht und bekam anschließend den ausgeführten Befehl des Schülers mitgeteilt. Das ergab auf 400 verschiedenen Karten **1.350.818 beschriftete Einheitsentscheidungen**. Die übliche Trainingsmaske lässt **1.317.756** davon zu. Alle **48.323** aufgezeichneten Lehrer-Schüsse waren legal, 57 zielten auf das eigene Feld. Die Daten umfassen 120.000 Kartenansichten über jeweils drei Matches.

| Gegner des Schülers | Spiele | Gewonnene Spiele | Gewonnene Einzelmatches | Lehrerentscheidungen |
|---|---:|---:|---:|---:|
| Kaggle-Dritter | 235 | 2 | 21/705 | 743.127 |
| V14 | 90 | 80 | 221/270 | 330.562 |
| Original-Solution | 75 | 70 | 197/225 | 277.129 |

Diese Siege beschreiben den reinen v4-Schüler während der Aufnahme. Gewichte wurden dabei nicht nachtrainiert. Die 400 Karten 7172000–7172399 mit jeweils einem Schülersitz sind von Mahmouds 600 für Runde 3 reservierten Karten getrennt.

## Daten übernehmen

Im lokalen Desktopprojekt liegt das vollständige Archiv unter `experiments/imitation/k3_v4_extra_7172000_400.tar.gz` (59.745.300 Bytes). Die SHA-256-Prüfsumme lautet `e1411e3e6d8c155dd2978c40f80f786e336ea881053e1ab7461d0598d4e9f7a7`. Für die Übergabe genügt dieses Archiv. Auf dem Zielrechner in einen leeren Ordner entpacken und dem Trainingsprogramm dessen Unterordner `k3_v4_extra_7172000/data/` als zusätzlichen Datensatz übergeben. Das Archiv bewahrt die Hardlinks der vollständigen Produzentenprüfung.

Alle 400 NPZs wurden nach Abschluss neu geöffnet und gegen Register, Rückmeldungen, Masken, kanonische Lehrerbefehle und Hashes geprüft. Auch aus dem fertigen Übergabearchiv ließen sich alle 400 Originaldateien mit den richtigen Einzelhashes lesen. Die Rohdaten liegen lokal. Im Repository stehen das Einzelregister und die Prüfsummen. [Index aller 400 Spiele](index-400.json) · [Übergabe und Hashes](uebergabe.json) · [Aufnahmeverfahren](README.md)
