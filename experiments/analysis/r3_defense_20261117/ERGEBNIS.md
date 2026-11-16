# V15s Feldbeschuss als Ergänzung für R3

**Ein allgemeiner Siegquotenvorteil gegenüber R3 ist im zweiten Kartensatz nicht bestätigt. R3 bleibt die Abgabe.**

## Was V15 auf den vier Startplätzen erreicht

Gegen das vollständige V15 erzielte Solution auf vier von vier Starts weniger Punkte als gegen R3, zusammen 606 weniger. V15 selbst erzielte 78 Punkte mehr. Seine eigenen Punktefelder hielten auf einem der vier Starts im Durchschnitt länger als bei R3, bei Solution war die mittlere Wertungsserie auf allen vier Starts kürzer. Diese Starts stammen von drei Karten und wurden anhand früherer Niederlagen der Einzelübergabe ausgewählt.

Auf 7158030/P1 brachte ein gegnerisches Feld gegen R3 im Mittel 36,6 Züge hintereinander Punkte, gegen V15 22,0. Auf 7158020/P0 schossen in Match eins, Zug 55, zwei Einheiten auf bestätigte Punktefelder. Auf beiden war vor dem Schuss kein Gegner zu sehen. Beide hatten im vorigen Zug für Solution gepunktet und brachten im Schusszug keinen Punkt mehr. Der isolierte Einfluss eines Befehls ist messbar, wenn beide Alternativen aus exakt derselben Stellung mit demselben Gegnerbefehl gespielt werden. [Alle vier Fallanalysen mit Matchzahlen](diagnose/ERGEBNIS.md) · [Verifizierte Rohaufnahmen](replays/README.md).

## Wie viele Punkte verhinderte V15 tatsächlich?

Auf V15s vier Originalspielbahnen wurden die ausgewählten 61 V15-Befehle in 49 Spielzügen für eine einzelne Neuberechnung durch die jeweilige R3-Empfehlung ersetzt. Zufall, Gegnerbefehle und alle übrigen V15-Befehle blieben identisch. Solution erhielt in diesen Zügen 163 Punkte mit den tatsächlichen Befehlen und 205 mit den Ersatzbefehlen. V15 verhinderte netto 42 gegnerische Punkte unmittelbar, davon 38 auf Feldern, die im vorherigen Zustand schon für Solution gewertet hatten. Sherlocks eigene Gutschrift war in jedem Vergleich identisch. Beispielsweise bekam Solution auf 7158020/P1 in Match eins, Zug 42 mit V15s Schuss vier statt sechs Punkte. [Alle Ein-Zug-Vergleiche auf V15s Verläufen](replays/v15_gegenprobe/ERGEBNIS.md).

Auf den vier Spielbahnen des neuen R3-Kandidaten verhinderten die übernommenen Befehle in 79 geprüften Zügen **34 gegnerische Punkte** unmittelbar. 29 der 34 kamen von einem einzigen Start (7158030/P1). Die eigenen gewerteten Felder waren in jeder Gegenprobe identisch. Diese Summe vergleicht punktuelle Alternativen entlang des gespielten Verlaufs. Sie lässt sich weder als Punktevorsprung am Matchende lesen noch direkt zu den 606 Punkten aus dem Vergleich ganzer V15- und R3-Spiele addieren. [Gegenprobe auf dem Kandidaten](gegenprobe/README.md).

## Die getestete Regel

Pro Einheit darf ein V15-Schuss den R3-Befehl ersetzen, wenn sein Ziel laut öffentlicher Beobachtung ein bestätigtes, scheinbar freies Punktefeld ist. Reichweite, Energie und die geplante eigene Felddeckung müssen den Schuss zulassen. Sichtbare Daten für die Entscheidung und nachträglich aus der Spielengine ermittelte Wertungen sind unabhängig erfasst. Die exakte Auswahl fand 159 mögliche Schussänderungen auf den vier R3-Verläufen, 180 auf denen der früheren Einzelübergabe und 61 auf den V15-Verläufen. [Festgelegte Regel](REGEL.md) · [Nachrechnung an gespeicherten Zügen](replayregel.json).

## Unabhängig gespielte Vergleiche

Auf 40 weiteren Karten spielten alle drei Versionen beide Startseiten gegen die originale Solution_92. Pro Spiel entscheiden drei Matches, unabhängig von der Gesamtpunktzahl. Die Punkte sind hier über alle 80 Spiele aufsummiert.

| Agent | Gewonnene Spiele | Gewonnene Matches | Eigene Punkte | Solution-Punkte |
|---|---:|---:|---:|---:|
| Original-R3 | 78/80 | 232/240 | 103442 | 45638 |
| R3 mit Feldbeschuss | 80/80 | 235/240 | 102433 | 44783 |
| Original-V15 | 77/80 | 224/240 | 91703 | 47921 |

Die Differenz zum Original-R3 beträgt 2,50 Prozentpunkte. Das 95-%-Kartenintervall reicht von 0,00 bis 7,50 Prozentpunkten. Der Bootstrap zieht 10.000-mal ganze Karten, sodass beide Startseiten zusammenbleiben. Die beiden zusätzlichen Siege kamen auf den zwei Startseiten derselben Karte zustande. Hinzugewonnene Sitze: 7165740/P0, 7165740/P1. Abgegebene Sitze: keine.

### Zweiter, getrennter Solution-Satz

Nach 80/80 gegenüber 78/80 im ersten Vergleich wurde vor den weiteren Spielen ein neuer Satz mit 60 Karten und beiden Startseiten festgelegt. Auf diesem Satz gewann der Kandidat **116/120**, R3 **118/120**. Der gepaarte Unterschied beträgt -1,67 Prozentpunkte (95-%-Kartenintervall -4,17 bis 0,00). Hinzugewonnene Sitze: 7165876/P0. Abgegebene Sitze: 7165876/P1, 7165882/P1, 7165892/P1. Ein allgemeiner Siegquotenvorteil gegenüber R3 ist im zweiten Kartensatz nicht bestätigt. Die beschreibende Summe über beide Kartensätze beträgt 196/200 gegenüber 196/200. Der zweite Satz wurde wegen des Ausgangs des ersten angesetzt. [Vorab-Festlegung](BESTAETIGUNGSPLAN.md) · [Versiegelte Einzelspiele](bestaetigung/games.jsonl) · [Gepaarte Auswertung](bestaetigung.json).

Ein ergänzender zweiseitiger, exakter Vorzeichen-Permutationstest vertauscht beide Agenten gemeinsam für beide Startseiten je Karte. Die p-Werte sind 1,000 im ersten und 0,500 im zweiten Satz. Im zweiten Satz unterscheidet sich die Anzahl gewonnener Startseiten auf zwei Karten. Auf einer weiteren Karte tauschten die Seiten ihren Gewinner. [Prüfwerte](vorzeichentest.json).

Trotz der geringeren Siegzahl ließ der Kandidat im Prüfsatz in Summe 1.088 Gegnerpunkte weniger zu als R3 (81.847 gegenüber 82.935). Sein eigenes Team erzielte zugleich 2.473 Punkte weniger (164.076 gegenüber 166.549). Die Zahlen vergleichen die gesamten Spielverläufe.

### Direktduelle

| Direktvergleich auf denselben 16 Duellkarten | Siege des zuerst genannten Agenten | 95-%-Kartenintervall |
|---|---:|---:|
| Kandidat gegen R3 | 20/32 | 40,62 bis 81,25 % |
| Kandidat gegen V15 | 6/32 | 0,00 bis 37,50 % |
| Original-R3 gegen V15 | 4/32 | – |

## Die vier bekannten Fälle mit der neuen Regel

| Karte / Sitz | Original-R3 | Frühere Einzelübergabe | Original-V15 | R3 mit Feldbeschuss |
|---|---:|---:|---:|---:|
| 7158016/P0 | 2:1 | 1:2 | 3:0 | 2:1 |
| 7158020/P0 | 1:2 | 1:2 | 2:1 | 1:2 |
| 7158020/P1 | 1:2 | 1:2 | 2:1 | 1:2 |
| 7158030/P1 | 0:3 | 1:2 | 3:0 | 3:0 |

Die Zellen enthalten die Matchsiege im jeweiligen Spiel. Die vier Fälle zählen getrennt von der neuen Kartenstichprobe.

## Wie oft änderte sich der Befehl?

| Stichprobe | Spiele mit Änderung | Abweichende Schussbefehle | Davon ohne sichtbaren Gegner im 3×3-Zielgebiet | Davon von eigenem bestätigtem Punktefeld |
|---|---:|---:|---:|---:|
| Vier Diagnosefälle | 4/4 | 108 | 102 | 0 |
| Weitere Solution-Karten | 77/80 | 1619 | 1040 | 571 |
| Direkt gegen R3 | 32/32 | 944 | 613 | 390 |
| Direkt gegen V15 | 32/32 | 642 | 376 | 214 |

## Reproduktion

Das [Messprotokoll](PLAN.md) legt die 340 Spielausführungen und Startseiten fest. Zwei vollständige Dateien enthalten die [Kontrollen](controls/games.jsonl) und den [Kandidaten](candidate/games.jsonl). Mit dem Projekt-Python liefert `python -B auswerten.py` aus diesem Ordner die [validierten Ergebnisse](auswertung.json) einschließlich der gepaarten Unterschiede. Die Originalquellen für R3, V15, Gegner und Engine sind im [Laufzeitregister](../r3_v15_blend_20261116/laufzeit.json) festgehalten. `spielreihe.py controls` und `spielreihe.py candidate` verwenden jeweils `--runtime LAUFZEIT --out NEUER_ORDNER`. Die Befehlsfolgen, Matchendstände und alle Feldwertungen der zwölf Diagnoseverläufe lassen sich mit `replays/pruefen.py` erneut prüfen. Das geprüfte Abgabe-ZIP hat SHA-256 `8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d`.

Der zweite Kartensatz umfasst 240 zusätzliche neue Spielausführungen. Seine Ergebnisse lassen sich mit `python -B bestaetigen.py --out bestaetigung` und der ergänzende Permutationstest mit `python -B kartenpaare.py` prüfen.
