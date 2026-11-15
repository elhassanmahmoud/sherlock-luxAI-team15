# Bewegungsberatung nach dem ersten Match

## Beobachtung vor dem Versuch

Auf 60 früheren Karten gewann der Zwei-Ansichten-R3 gegen Solution 118/120, V14 109/120. Zehn neue Siege standen einem neuen Verlust gegenüber. Gegen Kaggle gewann V14 4/120, verteilt auf nur zwei Karten mit je zwei Siegen. Der Zwei-Ansichten-R3 gewann 0/120. Die veröffentlichten Zeilen enthalten die Summe der Matchsiege, Punkte und Eingriffe über 303 Züge. Die Reihenfolge der einzelnen Matches und die frühen öffentlichen Punktstände fehlen.

Drei früher gespielte Archivblöcke erlauben getrennt die Auswertung der öffentlich beobachteten Punktedifferenz bei Zug 25 und der ersten Matchentscheidung. Die Tabelle zeigt, in wie vielen externen Spielen das betreffende Ereignis tatsächlich eintrat.

| Gespielter Agent | Kaggle, bei Zug 25 hinten | Solution, bei Zug 25 hinten | Kaggle, erstes Match verloren | Solution, erstes Match verloren |
|---|---:|---:|---:|---:|
| V14 | 2/28 | 2/26 | 26/28 | 0/26 |
| Erster Bewegungsschüler R1 | 4/96 | 16/96 | 88/96 | 3/96 |
| Original-R3, eine Ansicht | 12/48 | 15/48 | 44/48 | 0/48 |

Keiner dieser Agenten gewann eine der aufgeführten Partien gegen Kaggle. Auf 16 separaten Karten der früheren FT18-Studie verlor V14 alle 32 Auftaktmatches gegen Kaggle. Die beiden gewonnenen ganzen Spiele stammen von einer Karte (7279007). In beiden lag V14 im ersten Match mit 108 zu 152 zurück und gewann die folgenden beiden Matches. Gegen Solution verlor V14 auf diesem Block nur eines der 32 ersten Matches. Ein frühes Punktedefizit bei Zug 25 kennzeichnet die gesuchten Partien in den Archiven unzureichend. Der öffentliche Matchverlust trennt die Verläufe stärker. Er allein belegt keinen Vorteil einer späteren Umschaltung.

Eine bei Spielstart verfügbare Alternative wurde anhand der vier öffentlichen Kursparameter und der jeweils beiden bereits im FT18-Versuch verwendeten Bereichshälften geprüft. Auf 400 älteren Karten wurde die Hälfte gewählt, in der V14 gegen Kaggle den größten Unterschied in der tatsächlich beobachteten Siegquote gegenüber der komplementären Hälfte hatte. Die Entscheidung wurde vor Berechnung der Parameter auf den 60 Diagonalkarten gespeichert. SAP-Reichweite bis einschließlich fünf ergab 12/460 gegenüber 0/340, mit zwölf Siegen auf sechs Karten. Ein fester Wechsel für das ganze Spiel ist aus den Endergebnissen direkt nachrechenbar. Auf den 60 Diagonalkarten wählte diese Regel auf 36 Karten V14 und deckte beide Kaggle-Siegkarten ab. Sie gewann 4/120 gegen Kaggle und 112/120 gegen Solution. Das ergibt insgesamt 116/240 gegenüber 118/240 mit dem Zwei-Ansichten-R3. Gepaarte 95-%-Kartengrenzen für die Differenz −4,58 bis +2,92 Prozentpunkte. Dieser Ansatz ist verworfen.

Sieben der zehn neu gewonnenen Solution-Sitze des Zwei-Ansichten-R3 endeten 3:0. Auf diesen sieben ist ein Wechsel nach verlorenem erstem Match ausgeschlossen. Die drei übrigen endeten 2:1. Von den vier früheren V14-Kaggle-Siegen endeten zwei beim Zwei-Ansichten-R3 mit 0:3 und zwei mit 1:2. Für diese letzten beiden ist die Reihenfolge offen. Direkt gegen V14 endeten 64 der 100 Siege des Zwei-Ansichten-R3 mit 3:0.

## Eingriff

Bis zur ersten öffentlichen Matchentscheidung spielt der unveränderte Zwei-Ansichten-R3. Meldet die Beobachtung beim ersten Matchwechsel eine Niederlage, gibt der Agent für alle verbleibenden Aktionen die soeben berechnete Weltaktionsmatrix seines eigenen V14-Basisteils zurück. Nach einem Auftaktsieg spielt er den Zwei-Ansichten-R3 weiter. Alle Beobachtungen, Erinnerungen und Buchungen entstehen auf der tatsächlich gespielten Partie. Der Parameterschätzer erhält die tatsächlich zurückgegebene Aktionsmatrix. Im ersten Match, nach einem Auftaktsieg und auf der Gegenseite werden dieselben Agenten und Quellen verwendet wie in der ursprünglichen Diagnose. Die Schaltentscheidung liest nur den öffentlichen Matchstand und die eigene Seite.

FT18 startete früher mit V14 und wechselte nach einem Sieg zu einer anderen Netzauswahl. Die Restart-Versuche ersetzten einzelne Wege bis zum ersten eigenen Punkt. Die R3-Kontextstudie wählte einzelne Befehle nach Zielrichtung, bestätigtem Feld und Gegnerreichweite. Hier bleibt ein einzelner Agent auf seiner eigenen Spielhistorie, und genau einmal entscheidet der erste Matchausgang über den Rest der Partie.

## Festgelegte Diagnose

Zuerst müssen die Originalquellen und die Ergebnisse zweier neutraler Referenzsitze inklusive beider Punktzahlen exakt reproduziert werden. Anschließend spielt der Kandidat elfmal.

| Zweck | Gegner | Karte/Sitz |
|---|---|---|
| Zwei Referenzen, danach unveränderte 3:0-Kontrollen des Kandidaten | Solution | 7286100/p0, 7286101/p1 |
| Vier frühere Kaggle-Siege von V14 | Kaggle | 7286135 und 7286141, jeweils beide Sitze |
| Alle durch R3diagonal hinzugewonnenen 2:1-Sitze | Solution | 7286124/p0, 7286124/p1, 7286142/p1 |
| Beide 0:3-Niederlagen des Zwei-Ansichten-R3 | Solution | 7286137/p0, 7286137/p1 |

Auf jeder Partie werden die echten Weltbefehle beider Spieler nach erfolgreichem Spielschritt zusammen gehasht. Das Protokoll enthält einen Hash für Match 1 und für die vollständigen 303 Schritte sowie alle drei vor dem Punkte-Reset rekonstruierten Stände und die tatsächlichen Matchgewinner. Die beiden neutralen Referenzen und Kandidaten müssen paarweise dieselben Befehle über das gesamte Spiel, Matchverläufe und Endergebnisse aufweisen. Frühere Befehlsfolgen auf den anderen Sitzen sind im Originalarchiv nicht vorhanden. Der Lauf weist nach, auf welchen Sitzen der erste Match verloren wurde und der Agent 202 Folgeaufrufe ohne Beratung spielte. Bei deaktivierter Beratung wird das Netz nicht für einen hypothetischen Vergleich aufgerufen.

Die allgemeine Nominierung erfordert mindestens einen wiedergewonnenen Kaggle-Sitz, alle drei bewahrten 2:1-Solution-Vorteile und identische neutrale Kontrollen. Ein zweiter, vor der ersten Ausführung festgelegter Endpunkt erfordert mindestens einen gewonnenen der beiden 0:3-Sitze auf 7286137, ebenfalls alle drei bewahrten Vorteile und beide identischen Kontrollen. Jeder Endpunkt wird für sich ausgewiesen. Die Karte 7286137 bleibt eine einzige Diagnosekarte.

## Getrennte nächste Prüfungen

* Allgemeine Nominierung. 16 neue Karten 7170800–7170815, beide Sitze, drei Agenten gegen Solution und Kaggle sowie Kandidat direkt gegen V14, insgesamt 224 Spiele. Vorrang haben die Solution-Siege mindestens auf Niveau von V14 und Zwei-Ansichten-R3. Außerdem extern strikt mehr Siege als Zwei-Ansichten-R3 und mindestens zwei mehr als V14, direkt eine Mehrheit. Bei positiver Auswahl 60 weitere externe Karten 7170820–7170879 (V14 und Kandidat, 480 Spiele) sowie 60 eigene direkte Karten 7170900–7170959 (120 Spiele). Die gepaarte externe Untergrenze gegenüber V14 muss über null, die direkte Untergrenze über 50 Prozent liegen und Solution mindestens V14 erreichen. Bootstrap auf ganzen Karten mit beiden Sitzen, 10.000 Ziehungen und PCG64-Startwert 2711.
* Eigenständige Solution-Frage. Bei bestandenem zweitem Endpunkt 7170960–7170975, beide Sitze, ausschließlich Solution, V14/Zwei-Ansichten-R3/Kandidat, insgesamt 96 Spiele. Die kleine Folgeprüfung verlangt mehr Siege als Zwei-Ansichten-R3 und mindestens so viele wie V14. Die Ergebnisse berechtigen lediglich zur Beurteilung dieses Zielgegners. Keine weitere Phase startet automatisch.

Der Prüfer gleicht die originalen Laufmanifeste und 600 historischen Rohzeilen mit festen SHA-256 ab. Ausgangspunkt ist die eingefrorene Spielkopie von `scripts.r3_diagonal_games`; der neue Adapter und sein Runner werden zusätzlich versiegelt. Für eine freie Worker-Spur im Verzeichnis dieser Spielkopie:

```sh
"$PROJECT/.venv/bin/python" -B -u -m scripts.r3_diag_after_loss_games run diagnose --repo "$PROJECT" --out "$OUT"
"$PROJECT/.venv/bin/python" -B -u -m scripts.r3_diag_after_loss_games run screen --repo "$PROJECT" --out "$OUT"
"$PROJECT/.venv/bin/python" -B -u -m scripts.r3_diag_after_loss_games run confirm --repo "$PROJECT" --out "$OUT"
"$PROJECT/.venv/bin/python" -B -u -m scripts.r3_diag_after_loss_games run solution --repo "$PROJECT" --out "$OUT"
```

Der nächste Befehl prüft den jeweils benötigten abgeschlossenen Vorbefund neu. Jede Phase legt die Vollspiele als JSONL, ihre Prüfsummen und eine gesonderte Auswertung ab. [Ursprüngliche Diagonalstudie](../movement_reflection_20261115/PLAN.md) · [Frühere öffentliche Parameterwahl](../late_ft18_20261115/public_selector/ERGEBNIS.md) · [FT18 nach gewonnenem ersten Match](../late_ft18_20261115/after_win/fresh/ERGEBNIS.md) · [Frühere Restart-Route](../movement_soft_20261115/restart_route/FRISCHE_KARTEN.md) · [R3-Kontextstudie](../r3_context_selector_20261115/ERGEBNIS.md)
