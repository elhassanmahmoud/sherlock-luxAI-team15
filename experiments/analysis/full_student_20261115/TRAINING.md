# Zwei vollständige Einzelschüler nach fünf Epochen

Beide CNN sind auf demselben Mac mit gleicher Architektur, Initialisierung und Lernrate trainiert. Die Kontrolle sah die 152 bisherigen Lernkarten, der neue Schüler zusätzlich 216 Karten mit vollständigen Partien des Kaggle-Lehrers. Das erhöhte auch die Zahl der Lernschritte. Die folgenden Treffer zählen den vollständigen Lehrerzug einschließlich des genauen Ziels bei einem erlaubten Lehrerschuss.

| Zurückgehaltene Stellungen | Kontrolle | Mit vollständigen Lehrerpartien | Zusätzliche Treffer |
|---|---:|---:|---:|
| V14, 8 Karten | 35.886/51.048 | 36.226/51.048 | +340 |
| Früherer Schüler, 24 Karten | 108.438/156.243 | 109.003/156.243 | +565 |
| Nativer Lehrer, 24 Karten | 81.091/114.893 | 90.360/114.893 | **+9.269** |

Auf den selbst erreichten Lehrerstellungen steigt die Übereinstimmung von 70,58 % auf 78,65 %. Auf Stellungen des früheren Schülers sind es 69,40 % gegenüber 69,77 %. Beide vorab festgelegten Vergleiche sind erfüllt. Der neue Schüler wird im selben Punkte-Hybrid wie die Kontrolle gegen externe Gegner und direkt gegen V14 geprüft. Das ist ein separater lokaler Kandidat neben Mahmouds v4.

Die Prüfsummen beider trainierter Netze stimmen mit dem Auswertungsbeleg überein. Mahmoud kann sie aus dem Repository laden. Für das Spielwerkzeug zeigt `--models` auf den Ordner mit beiden Dateien. [Trainierte Gewichte](../../candidates/whole_students_20261115/) · [Zähler und Prüfsummen](evaluation/offline.json) · [Lernverlauf Kontrolle](historical_fit.log) · [Lernverlauf mit zusätzlichen Beispielen](plus_teacher_fit.log) · [Datensammlung](SAMMLUNG.md) · [Versuchsplan](PLAN.md).
