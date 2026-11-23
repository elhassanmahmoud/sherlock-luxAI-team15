# Ein Schritt verändert sieben alte Niederlagen

**Der Berater hat das festgelegte 15-Zug-Ziel verfehlt.** Er bot bei 37 der 54 untersuchten Solution-Partien eine geeignete Bewegung an, verteilt über 34 Karten. Der erste geänderte Befehl gewann sofort im Mittel 0,84 Nettopunkte. Über fünf Wertungen betrug der Gewinn 1,57, über 15 Wertungen ergab sich ein Verlust von 1,41 Nettopunkten pro Eingriff. Gleichzeitig wurden sieben vergangene Niederlagen zu ganzen Siegen. Alle 27 untersuchten Originalsiege blieben Siege. Für das frische 400-Spiele-Panel waren **alle** Kriterien gefordert. Die reservierten frischen Karten wurden in dieser Studie nicht gespielt. V16 bleibt die Abgabe. [Versuchsplan](PLAN.md) · [Alle Ergebnisse](archiv_ergebnis.json).

Es wurden gezielt 27 frühere Niederlagen nach einem gewonnenen ersten Match und 27 frühere Siege gegen Solution ausgewählt. Die Siegkontrollen betrafen 27 andere Karten und beide Startseiten. In den zugrunde liegenden Benchmarks verlor V16 nur 35 von 1.600 Sitzen. Hier sind es absichtlich 27 von 54. Der Anstieg von 27 auf 34 ganzen Siegen in dieser zusammengesetzten Gruppe erlaubt deshalb keine Hochrechnung auf die allgemeine Siegquote. Weder Kaggle noch direkte V16-Duelle waren Teil dieser historischen Wirkungsprüfung. [54 vorab bestimmte Sitze](stichprobe.json) · [Herkunft der früheren Niederlagen](../spielabstand/ERGEBNIS.md).

## Was über mehrere Züge passiert

Der Kandidat durfte nach gewonnenem Match 1 ausschließlich bei Rückstand in Match 2, Zug 26–75, genau einen Befehl ändern. Die Eingriffsschwelle, Bewegungsoptionen und Netzgewichte stammen aus dem bereits geprüften [Wertberater](../zugnutzen/ERGEBNIS_LERNEN.md). Nach diesem Einzelbefehl spielten beide Seiten mit ihren tatsächlichen neuen Beobachtungen normal weiter. Die folgenden Angaben zählen den geänderten Zug als erste Wertung. Eigen- und Gegnerpunkte sind Summen der Veränderungen über die 37 gepaarten Fortsetzungen.

| Zeithorizont | Eigene Punkte | Gegnerpunkte | Mittlere Veränderung der Punktedifferenz | Positiv / neutral / negativ |
|---|---:|---:|---:|---:|
| Erste Wertung | +31 | 0 | +0,84 | 31 / 6 / 0 |
| Fünf Wertungen | +79 | +21 | +1,57 | 26 / 9 / 2 |
| 15 Wertungen | +79 | +131 | −1,41 | 20 / 5 / 12 |
| Ende von Match 2 | +287 | +111 | +4,76 | 19 / 3 / 15 |

Die mittlere Veränderung nach 15 *weiteren* Zügen, also einschließlich Eingriff nach insgesamt 16 Wertungen, beträgt ebenfalls −2,00. Die Beträge einzelner Nachteile waren groß genug, die Mehrheit positiver Einzelverläufe zu überwiegen. Im Mittel der ursprünglichen Verlustsitze mit Eingriff erreichte der Saldo nach 15 Wertungen −0,13, zum Matchende +40,56. Bei den Siegkontrollen mit Eingriff waren es −2,38 und zum Matchende −22,52. Die gegensätzlichen Matchendeffekte zeigen, wie sehr die Zusammensetzung der historischen Stichprobe den Gesamtwert beeinflusst.

| Gruppe | Originalsitze | Match 1 gewonnen | Mindestens einmal im Zeitfenster zurück | Mindestens ein möglicher Alternativschritt | Tat­sächlicher Eingriff | Siege in Match 2, alt → neu | Ganze Siege, alt → neu |
|---|---:|---:|---:|---:|---:|---:|---:|
| Frühere Niederlagen | 27 | 27 | 25 | 22 | 16 auf 13 Karten | 0 → 6 | 0 → 7 |
| Frühere Siege | 27 | 26 | 23 | 23 | 21 auf 21 Karten | 27 → 26 | 27 → 27 |

Ein Beispiel für die unterschiedlichen Zeithorizonte ist Karte 7267291, P0. Die einzelne Bewegung in Zug 45 brachte sofort einen Nettopunkt. Nach fünf Wertungen lag ihr Verlauf 16 Nettopunkte hinter dem Original, nach 15 Wertungen sogar 51. Am Ende von Match 2 überwog wieder ein Vorteil von 50 Nettopunkten. Match 2 blieb verloren, Match 3 und damit das ganze Spiel gewannen ausschließlich im abgeänderten Verlauf. Aus diesem Beispiel lässt sich keine allgemeine Begründung für einen früheren oder späteren Eingriff ableiten.

## Technische Kontrolle

Der Optionenrechner wird strukturell gegen den ursprünglichen Python-Code verglichen; ausschließlich die alte Zeitfensterprüfung fehlt, die tatsächlichen Zugmerkmale bleiben dieselben. Auf zwei historischen Partien (P0/P1) waren alle 606 passiv erfassten Teambefehle mit V16 identisch. Im regulären Zeitfenster des Originalberaters stimmten alle 32 erzeugten Alternativen inklusive Merkmalen und alle drei tatsächlich vorgeschlagenen Änderungen einschließlich der realen Aktionsrichtungen überein. [Prüfung P0](technik_0.json) · [Prüfung P1](technik_1.json).

Alle 54 Originalpartien reproduzierten beide Punktesummen und beide Matchwertungen aus dem Archiv. Bei den 37 tatsächlichen Verzweigungen stimmten der vollständige Ausgangszustand, die bisherige Kommandofolge beider Seiten einschließlich Wertungen, der nächste Zufallsschlüssel und die simultanen Originalbefehle überein. Anschließend wurde genau ein Weltbefehl ersetzt und für Sherlock als tatsächlich gewählt festgehalten. Für die übrigen 17 Sitze war die Regel bis zum Ende inaktiv. Es gab somit **91 vollständig gespielte historische Verläufe**, zusätzlich zu den zwei Technikpartien. Das gespeicherte Archiv enthält die Punkte beider Spieler je Wertung, Gewinner aller Matches und Identitätsnachweise. SHA-256 `5bc24ce8c5d1f2bbbd543b0df46259eaea79b1c782c62965324cf40678b80c28`. [54 Vergleichsdatensätze](archiv_partien.jsonl.gz) · [Auswerteskript](auswerten.py).
