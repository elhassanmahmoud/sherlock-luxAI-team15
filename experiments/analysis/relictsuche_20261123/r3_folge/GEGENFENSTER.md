# Eine echte R3-Bewegung verbessert den Nettostand nach zwölf Zügen

Auf 64 neuen Sicht-1-Karten spielte der ursprüngliche V16-Auftakt je einmal gegen Solution und gegen V16. Der Sitz wechselte von Karte zu Karte und war für beide Gegner gleich. In 80 der 128 Partien auf 56 verschiedenen Karten fand sich eine zulässige R3-Empfehlung. In 66 der 80 paarigen Fortsetzungen erhielt das eigene Team früher eine Gutschrift auf dem ausgewählten Feld. Elfmal blieb der Zeitpunkt gleich, dreimal kam sie später. In 49 verschiedenen Karten gab es mindestens eine frühere Gutschrift. Alle 80 öffentlich ausgewählten Ziele waren laut Wertungsmaske tatsächlich aktive Punktefelder. [Einzelne Fortsetzungen](gegenpruefung/fortsetzungen.jsonl.gz)

| Messwert | Solution | Original-V16 | Zusammen |
|---|---:|---:|---:|
| Geplante Gegnerpartien | 64 | 64 | 128 |
| Erster Matchsieg von V16 | 59 | 37 | 96 |
| Zulässige, tatsächlich gespielte Änderung | 51 | 29 | 80 |
| Frühere / spätere Gutschrift auf dem Ziel | 45 / 2 | 21 / 1 | 66 / 3 |
| Eigene Punkte mehr nach zwölf Zügen, summiert | +91 | +29 | +120 |
| Nettopunkte mehr nach zwölf Zügen, summiert | +96 | +59 | +155 |
| Mittlerer Nettogewinn je geplanter Gegnerpartie | +1,50 | +0,92 | +1,21 |

Nettopunkte sind eigene Punkte abzüglich gegnerischer Punkte. Nach sechs Zügen lag der gesamte Nettogewinn bei +116, nach zwölf bei +155. Das vorab festgelegte 95-%-Kartenintervall für den mittleren Nettogewinn nach zwölf Zügen reicht von **+0,44 bis +2,09**. Die Rechnung berücksichtigt auch die 48 unveränderten Verläufe mit einem Effekt von null. Der Nettostand verbesserte sich auf 44 der 128 Gegnerpartien und verschlechterte sich auf 26. Für die Zeit bis zur ersten Gutschrift gilt der Endwert 13, wenn das Feld in den zwölf beobachteten Zügen keine eigene Gutschrift lieferte. [Gepaarte Differenzen](gegenpruefung/differenzen.jsonl.gz) · [Auswertung](gegenpruefung/ergebnis.json)

Die Eingriffe begannen zwischen Zug 9 und 53 des zweiten Matches, im Median an Zug 25. Insgesamt änderten sie 83 Einzelbefehle. In 51 Fällen war das gewählte Feld einen Schritt entfernt und wurde immer früher gewertet. Bei den 29 Entscheidungen mit Entfernung zwei bis vier gelang das 15-mal. Ihr summierter Nettogewinn nach zwölf Zügen betrug +60. Die Entfernung war keine nachträgliche Zulassungsbedingung.

Auf Karte `163410049`, Sitz P1 gegen Solution, stand Schiff 1 bei M2-Zug 26 zwei Schritte vom bereits bekannten Weltfeld `(6,21)` entfernt. Es fuhr auf R3s Empfehlung nach rechts. V16 hatte eine Bewegung nach unten vorgesehen. Schon der nächste Befehl stammte wieder von V16. Die erste eigene Gutschrift an diesem Ziel kam nach zwei Aktionen, während V16 in den zwölf Originalaktionen keine erhielt. Nach zwölf Aktionen stand P1 mit dem Eingriff bei 5:39 Punkten, im Original bei 2:50. [Rohfenster mit Befehlen, Positionen und Wertungen](gegenpruefung/fortsetzungen.jsonl.gz)

Alle 80 Gegenentscheidungen begannen mit identischen öffentlichen Historien, nativen Befehlen beider Seiten, R3-Vorschlägen, Schiedsrichterzuständen und Zufallsschlüsseln. Die Nachrechnung überprüfte 1.920 anschließende Zustände und reproduzierte das Kartenintervall. Damit sind alle sechs Voraussetzungen für den getrennten Ganzspielpiloten erfüllt. Eine Partie wurde hier nur über das festgelegte Zwölf-Züge-Fenster bewertet. [Unabhängige Nachrechnung](gegenpruefung/nachrechnung.json) · [Festgelegte Kriterien](GEGENPLAN.md)
