# Wo V16 und der volle Kundschafter gemeinsam verloren

**In jedem verlorenen zweiten oder dritten Match erzielte Solution auf den später aktivierten Reliktgruppen mehr Punkte.** Das galt für 18 von 18 solchen Matchniederlagen von V16 und für 19 von 19 des Kundschafters. In jeweils 14 dieser Matches hielt Sherlock bei der ersten Gruppe mindestens mit. Beide Versionen gewannen drei der elf Auftaktmatches, und zwar dieselben drei Sitze. [Einzelne Matches mit offiziellen Endständen und Punkten je Gruppe](matches.csv)

| Auf elf gemeinsamen Verlustsitzen gegen Solution | V16 | Voller Kundschafter |
|---|---:|---:|
| Verlorene Matches insgesamt | 26/33 | 27/33 |
| Davon Match 1 / Match 2 / Match 3 | 8 / 11 / 7 | 8 / 10 / 9 |
| Rückstand ausschließlich auf der ersten Gruppe | 8 | 8 |
| Rückstand ausschließlich auf späteren Gruppen | 14 | 14 |
| Rückstand auf erster **und** späteren Gruppen | 4 | 5 |

Als Rückstand zählt, dass Solution auf den zugehörigen Feldern mehr Punkte erhielt als Sherlock. „Spätere Gruppen“ fasst die zweite und dritte Generation zusammen. Die drei Kategorien schließen einander aus. Betrachtet man bei Rückständen in beiden Kategorien nur den größeren, entfielen **10 von 26** verlorenen V16-Matches auf die erste und **16 auf die späteren Gruppen**. Beim Kundschafter waren es **10 von 27** und **17**. Die Zuordnung zerlegt den tatsächlichen Punktestand. Eine gezielte andere Bewegung wurde in diesen Partien nicht getestet. [Rechenbilanz](bilanz.json)

## Welche Generationen Punkte lieferten

Auf allen elf Sitzen wurde in Match 1 nur die erste Reliktgruppe aktiv. Diese acht jeweiligen Auftaktniederlagen stellen sämtliche Fälle mit Rückstand ausschließlich auf Gruppe 1. In den späteren Matches sammelten beide Teams zusammen auf **jeder** der sieben Karten auch Punkte an späteren Gruppen. Vier der elf Sitze lagen auf Karten mit zwei tatsächlich aktiven Gruppen, sieben auf Karten mit drei. Der Ein-Gruppen-Verlauf des früher untersuchten Sicht-2-Verlusts trat auf keiner dieser sieben Sicht-1-Karten auf. [Vollständige Rekonstruktionen](rekonstruktionen.jsonl.gz)

| Summe über die verlorenen Matches des jeweiligen Spielers | Gruppe 1, Sherlock / Solution | Gruppe 2, Sherlock / Solution | Gruppe 3, Sherlock / Solution |
|---|---:|---:|---:|
| V16, 26 Matches | 5.467 / 5.085 | 1.133 / 3.831 | 284 / 171 |
| Kundschafter, 27 Matches | 6.099 / 5.552 | 1.635 / 4.690 | 306 / 280 |

Der größte aufsummierte Nachteil lag bei **Gruppe 2**. Solution erhielt hier 2.698 Punkte mehr als V16 und 3.055 mehr als der Kundschafter. Diese Summen gewichten punktreiche Matches stärker. Die getrennten Matchanzahlen in der ersten Tabelle gewichten jedes verlorene Match gleich. Beide Spieler gewannen auf 165300225 P1 und 165300336 P0/P1 jeweils das erste Match und verloren anschließend Match 2 und 3.

Die Auswahl umfasst sämtliche elf gemeinsamen Niederlagen auf sieben Karten der abgeschlossenen 96-Karten-Wiederholung. Auf sechs Sitzen waren beide vollständigen Befehlsbänder bytegleich, fünf unterschieden sich. Für 22 Spielzuordnungen waren damit 16 unterschiedliche Schiedsrichterwiedergaben erforderlich. Die bestehende Auswertung prüfte bei jedem regulären Zug den Punktezuwachs beider Teams und zählte auch den Schlusszug jedes Matches. Unabhängig davon wurden die 303 Zugzuwächse je Spiel für beide Seiten erneut aufsummiert und gegen die drei Generationssummen und die offiziellen Matchendstände abgeglichen. Diese nach dem Ergebnis ausgewählten Sitze liefern eine Erklärung der verlorenen Punkte und gehen unverändert genau einmal je Spieler in den ursprünglichen Vergleich ein. [Verwendete Zuordnung](../punkte_nach_gebiet/zerlegen.py) · [Ursprünglicher Vergleich](../sicht1_wiederholung/ERGEBNIS.md)
