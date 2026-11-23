# 27 der 35 Niederlagen begannen mit einem gewonnenen ersten Match

Wir haben **alle 35 Niederlagen** aus zwei festen Solution-Vergleichen mit zusammen 1.600 Startplätzen nachgespielt. Sie verteilen sich auf 27 Karten. Jede Partie endete 1:2. In 27 Fällen gewann V16 Match 1 und verlor dann beide folgenden Matches. Je viermal war Match 2 bzw. Match 3 der einzelne eigene Sieg. Alle 35 Ergebnisse einschließlich der Punkte beider Teams entsprechen ihren archivierten Originalen.

Für jeden Sitz haben wir das knappere der beiden verlorenen Matches betrachtet. Ein gewonnener Punkt in einem bestimmten Zug hilft, aber drei zusätzliche Punkte in *jedem* Match hätten bei unverändertem weiterem Spielverlauf **keinen eindeutigen zusätzlichen Sieg** ergeben. Drei Sitze hätten dadurch eine Chance über die Gleichstandsentscheidung bekommen.

| Gedachte zusätzliche Punkte pro Match | Verlorene Spiele mit einem garantierten zweiten Matchsieg | Mit günstigster Gleichstandsauflösung |
|---:|---:|---:|
| 1 | 0/35 | 0/35 |
| 3 | 0/35 | 3/35 |
| 5 | 4/35 | 5/35 |
| 10 | 7/35 | 7/35 |
| 25 | 18/35 | 18/35 |
| 50 | 25/35 | 25/35 |

Im Median fehlten **23 Punkte** zum sicheren Umschwung. Das knappere verlorene Match war 20-mal Match 2, neunmal Match 3 und sechsmal Match 1. In diesen 35 Matches war der mittlere Fall bei Zug 25 ausgeglichen, bei Zug 50 lag V16 12 Punkte zurück, bei Zug 75 bereits 54 und bei Zug 90 sogar 70. In 24/35 Fällen holte V16 in den letzten zehn Zügen wieder auf. Bei Zug 100 betrug der Median des Rückstands noch 22. Jeder Median bezieht sich auf die Verteilung am jeweiligen Zeitpunkt. Ihre Differenz ist nicht der mittlere Gewinn eines einzelnen Agenten.

Für die nächste Verbesserung lohnt sich deshalb besonders die **mittlere Phase von Match 2 nach einem gewonnenen ersten Match**. Dort eine zusätzliche dauerhaft punktende Besetzung zu etablieren, kann über viele Züge wirken. Eine feste Punktegutschrift setzt unveränderte Folgezüge voraus. Ob eine konkrete Bewegung auch fünf oder fünfzehn Züge später mehr Punkte bringt, kann nur ein Vergleich der beiden tatsächlichen Spielverläufe zeigen.

Für 25 der 35 Sitze wurden die gespeicherten ursprünglichen V16-Befehle wieder abgespielt und die öffentlichen Beobachtungen geprüft. Die weiteren zehn wurden mit dem gesicherten V16-Kurspaket neu berechnet. Alle 105 tatsächlich vergebenen Matchsiege und die nach dem letzten Zug rekonstruierten Spielpunkte wurden abgeglichen. [Einzelergebnisse](spielabstand.json) · [Methode](PLAN.md) · [Reproduktion](abstand.py)
