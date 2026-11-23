# Lässt sich der Nutzen eines anderen Korridors vorhersagen?

Das Modell lernte aus 320 Eröffnungen auf verschiedenen Sicht-1-Karten. Auf 306 Karten kam ein freies Schiff zur Auswahl. Wir wiederholten diese Ausgangslagen mit drei Suchrichtungen gegen Solution. Zusammen mit den Kontrollen ergaben sich **1.238 echte erste Matches** und 918 Richtungsbeispiele. Das Modell bewertet jede Richtung anhand der öffentlichen Lage. Bei weniger als einem geschätzten Nutzenpunkt übernimmt das Schiff den ursprünglichen Befehl.

Auf 80 getrennten Karten spielten wir 302 weitere erste Matches. Der eingefrorene Lerner veränderte auf 32 Karten tatsächlich einen Befehl. Auf sieben sah das Team sein erstes Relikt früher, auf fünf später. Die mittlere Verbesserung von **0,61 Zügen** hat ein 95-%-Intervall von −0,81 bis +2,11 Zügen. Die erste Gutschrift kam im Mittel 0,96 Züge früher (−0,40 bis +2,73), die Punktedifferenz nach Zug 70 sank um 3,31 Punkte (−8,54 bis +1,41). Sowohl der Lerner als auch V16 gewannen **68 der 80 ersten Matches**.

Auf 32 Karten hätte mindestens eine der Suchrichtungen das Relikt früher sichtbar gemacht. Dem Lerner fehlten Informationen, um diese Möglichkeiten zuverlässig zu erkennen. Auf den neuen Karten korrelierten seine Bewertungen mit dem später gemessenen Nutzen mit −0,04. Eine nachträgliche Auswahl mit Kenntnis sämtlicher Spielverläufe hätte 77 erste Matches gewonnen. Diese Zahl beschreibt den Spielraum der Richtungen und steht keinem spielenden Agenten zur Verfügung.

[Plan](PLAN.md) · [Gewichte](modell.json) · [Auswertung](offline.json) · [Unabhängige Nachrechnung](gegenpruefung.json) · [Lernpartien](training.jsonl.gz) · [Prüfpartien](pruefung.jsonl.gz) · [Vollständige Spiele gegen beide Gegner](../vergleich/PLAN.md)
