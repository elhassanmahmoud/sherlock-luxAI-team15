# Ein zusätzlicher Sieg gegen Solution im ersten Vergleich

Wir gaben den zwei ursprünglichen V16-Netzen zusätzliche Felder als Eingabe, wenn Sherlock ihre Punktwirkung aus den **öffentlich sichtbaren** eigenen Positionen und dem gemeinsamen Punktestand beweisen konnte. Alle Fahr- und Schussbefehle bestimmt weiterhin der normale V16-Agent. Der neue Beweis wirkt bei geringer Sicht in allen drei Matches. Er ergänzt den früheren Versuch, ein freies Schiff möglichst rasch zum ersten Relikt zu schicken.

| 64 neue Karten mit Sichtweite eins, beide Startseiten | Punktewissen | Original-V16 |
|---|---:|---:|
| Ganze Spiele gegen Solution | **123/128** | 122/128 |
| Gewonnene Einzelmatches gegen Solution, erstes / zweites / drittes | 113 / 116 / 117 | 113 / 114 / 119 |
| Ganze Spiele direkt gegeneinander | **66/128** | 62/128 |
| Zu Vergleichszwecken aus den ursprünglichen V16-Selbstspielen | | 64/128 auf den gleichen Sitzen |

Der externe Unterschied beträgt +0,78 Prozentpunkte. Das 95-%-Intervall nach Karte reicht von 0,00 bis +2,34. Im Direktduell liegt das Intervall der Siegquote bei 47,66–55,47 %. Ein neuer ganzer Sieg gegen Solution und kein verlorener bisheriger Sieg ergeben den Unterschied. Bei der tatsächlichen Befehlsfolge änderten sich 23 Solution-Sitze und 18 direkte Sitze auf insgesamt 21 verschiedenen Karten. Der vorab festgelegte kleine Test qualifiziert die Variante für die unabhängige Prüfung. [448 vollständige Spiele](partien.jsonl.gz) · [Auswertung](ergebnis.json) · [Prüfbedingungen](PLAN.md)

## Wo kamen Punkte hinzu?

Auf den zuerst neu gemeldeten physischen Zielfeldern einschließlich ihrer Spiegel ergaben sich gegen Solution während der ersten zwölf Züge nach dem Beweis 113 zusätzliche eigene und 16 weniger gegnerische Gutschriften gegenüber den jeweiligen V16-Spielverläufen. Das ergibt über alle 128 Sitze im Mittel +1,01 Nettopunkte (95-%-Intervall +0,44 bis +1,68). Über die restliche Partie lagen diese Felder im Mittel bei +5,50 netto (+1,06 bis +10,59). Im direkten Duell war der kurzfristige Effekt ebenfalls positiv, über die ganze restliche Partie jedoch unsicher (+0,41, Intervall −3,18 bis +3,84). Die Werte beziehen sich auf die zuerst mitgeteilten Felder und deren Spiegel. Welchen Ausweichbewegungen an anderen Orten die gesamten Spielsiegdifferenzen zuzuschreiben sind, lässt sich daraus nicht ableiten. [Feldwerte je Zeitfenster](feldwirkung.json) · [Einzelspuren](feldwirkung_karten.jsonl.gz)

Der Monitor prüfte jeden neu gemeldeten Punkt und sein Spiegelfeld unmittelbar gegen den verborgenen Schiedsrichterzustand. Alle neuen Meldungen waren richtig. Auf genau einem Solution-Sitz (162640027, Player 1) enthielt das ursprüngliche Kartenwissen in 37 Zügen einen falschen positiven Eintrag. Auf diesem Sitz gab es **keinen** neuen Beweis und die komplette Befehlsfolge entsprach dem Original. Die Vorhersage eines allgemein stärkeren Agenten wird auf 160 getrennten Karten aller Sichtweiten geprüft. Bis zu deren Auswertung bleibt V16 die Abgabe. [Ungefilterter Vergleich](ALLGEMEIN.md)
