# Kombination auf 80 neuen Karten

Die Kombination aus signalgesteuertem Kundschafter und Mitte2-Berater gewann **157/160 gegen Solution**. Original-V16 gewann **157/160**. Die Siegquotendifferenz (Kombination minus V16) beträgt 0,00 Prozentpunkte. Das 95-%-Intervall über ganze Karten reicht von **0,00 bis 0,00 Prozentpunkten**. Gegen den Kaggle-Dritten steht es 6 zu 4 Siegen aus je 160 Spielen. Im direkten Vergleich gewann die Kombination 38/80. **Die feste Leistungsschwelle ist verfehlt. V16 bleibt die freigegebene Abgabe.**

| Gegner / Startseite | Original-V16 | Kombination | Zusätzliche / verlorene Siege | Matchsiege V16 → Kombination | Veränderte Sitze |
|---|---:|---:|---:|---:|---:|
| Solution · beide | 157/160 | 157/160 | 0 / 0 | 455 → 457 | 127 |
| Solution · P0 | 79/80 | 79/80 | 0 / 0 | 230 → 230 | 65 |
| Solution · P1 | 78/80 | 78/80 | 0 / 0 | 225 → 227 | 62 |
| Kaggle-Dritter · beide | 4/160 | 6/160 | 2 / 0 | 46 → 48 | 12 |
| Kaggle-Dritter · P0 | 2/80 | 3/80 | 1 / 0 | 23 → 24 | 6 |
| Kaggle-Dritter · P1 | 2/80 | 3/80 | 1 / 0 | 23 → 24 | 6 |

## Tatsächlich gespielte Befehle

Die folgenden Kategorien zählen ganze Sitze nach den tatsächlich geänderten Befehlen. Treffen beide Module im selben Spiel eine abweichende Entscheidung, beziehen sie sich auf verschiedene Züge.

| Gegner | kein Eingriff | nur Mitte2 | nur Kundschafter | beide | geänderte Befehle gesamt |
|---|---:|---:|---:|---:|---:|
| Solution | 33 | 118 | 1 | 8 | 171 |
| Kaggle-Dritter | 148 | 12 | 0 | 0 | 12 |

Im Direktduell änderte die Kombination auf 17 von 80 Sitzen mindestens einen Befehl. Sie gewann 12 dieser veränderten Sitze und 26 der übrigen 63. P0 gewann 19/40, P1 19/40. Auf 23 der 40 Karten blieben beide Sitze unverändert, auf 0 griff die Kombination auf beiden Sitzen ein. Bei 17 weiteren Karten gibt der unveränderte Gegensitz eine direkte Referenz für die Wirkung auf den anderen Sitz.

## Wo die noch offenen Niederlagen liegen

Die 3 Solution-Niederlagen der Kombination lagen auf 2 Karten (160386062, 160386070). In 3 dieser Sitze war Match 1 verloren, in 3 änderte keines der beiden Module einen Befehl. Mitte2 setzt voraus, dass Sherlock das erste Match gewonnen hat. Die [Zugdiagnose aller drei verlorenen Auftaktmatches](auftakt/ERGEBNIS.md) findet im ersten Match bis Zug 70 auf keinem dieser Sitze auch nur ein bekanntes Punktefeld.

Gegen Kaggle änderte sich der Spielsieger auf 2 Startseiten. Beide Startseiten liegen auf derselben Karte (160386074). Das gepaarte Intervall für den Kaggle-Unterschied beträgt 0,00 bis 3,75 Prozentpunkte. In den direkten Spielen mit einem unveränderten Gegensitz kippten 2 ganze Ergebnisse. Auf 160386003/P0 ging die Matchbilanz von 2:1 auf 1:2 zurück. Auf 160386020/P0 ging die Matchbilanz von 2:1 auf 1:2 zurück.

## Entscheidung und Herkunft

Für die positive Entscheidung waren alle drei Bedingungen gemeinsam festgelegt. Die untere Grenze für zusätzliche Solution-Siege ist nicht strikt positiv. Die Bedingung für mindestens so viele ganze Kaggle-Siege wie V16 ist erfüllt, die Grenze von 40/80 Direktspielen ist verfehlt.

Die elf vorher ausgewählten älteren Siegwechselsitze, ihre 44 Wiederholungen und vier technische Kontrollen zählen getrennt. Das neue Panel umfasst 80 zuvor reservierte, ungefilterte Kartenseeds, beide Startseiten, komplette Spiele und Originalgegner. Das Intervall zieht jeweils beide Sitze einer Karte zusammen (20.000 Wiederholungen, fester Seed 231786). Alle drei Matches, beide Punktesummen und der vollständige Entscheidungszähler wurden je Spiel geprüft. Bei identischen externen Befehlen waren die Endresultate beider Programme identisch.

[Vorfestlegung](PLAN.md) · [Welche bekannten Rettungen kombinierbar waren](ARCHIV.md) · [Zahlen, Seiten und einzelne Siegwechsel](frisch/ergebnis.json) · [Rohdaten Teil A](frisch/worker_0.jsonl) · [Rohdaten Teil B](frisch/worker_1.jsonl)

Aus dem Repo mit der Kurs-Python-Umgebung:

```sh
d=experiments/analysis/v16_finalwoche_20261122/signalstudie/kombi
python "$d/auswerten.py" frisch
python "$d/berichten.py"
```
