# Einzelnetz und 42 Netze: abschließender Vergleich

**Abgeschlossen am 04.11.2026, 11:13 Uhr Europe/Berlin. Datenprüfung bestanden; FO42 erfüllt drei der sieben Übernahmebedingungen nicht. V14 bleibt unverändert.**

Alle fünf Teilaufträge und 3.840 Spiele wurden vollständig ausgewertet. Die Spielstände, Rohdateien und Protokolle in diesem Ordner sind bytegleiche Kopien aus dem eingefrorenen Experiment-Checkout `bed06df3335caa4d7a79c928132143a9c7e0a8fc`. Keine nachträgliche Kandidatenwahl oder zweite Bestätigung.

| Messgröße | FO42 | V14 | Unterschied / 95-%-Intervall |
|---|---:|---:|---|
| Mittel über sechs Gegner, je 960 Spiele | 773 Siege (80,52 %) | 772 Siege (80,42 %) | +0,104 Prozentpunkte [−3,646; +3,750] |
| Solution_92, je 800 Spiele | 771 Siege (96,375 %) | 762 Siege (95,250 %) | +1,125 Prozentpunkte [−0,375; +2,750] |
| default, je 160 Spiele | 160 Siege | 160 Siege | 0 Prozentpunkte |
| Direkt gegen V14, 320 Spiele insgesamt | 180 Siege | 140 Siege | FO42 56,25 % [48,75; 63,75] |

Es gab in diesen Zeilen keine Unentschieden. Die bessere Solution-Punktschätzung ist kein gesicherter Stärkegewinn: Ihr Intervall enthält null. Gegen Solution wurden keine 100 % erreicht.

## Karten und Vergleichsregeln

- Panel und default: 80 Karten `862000–862079`, beide Seiten. Die sechs Panelgegner sind Solution_92, `sol92_sq`, V3, V7, V10 und V13; alle zählen gleich viel.
- Zusätzliche Solution-Spiele: 320 andere Karten `862080–862399`, beide Seiten. Zusammen mit den ersten 80 Karten sind das 400 Karten und 800 Spiele pro Modell gegen Solution. Die Zusatzspiele verändern das Panelgewicht nicht.
- Direktvergleich: 160 separate Karten `863000–863159`, beide Seiten, insgesamt 320 Spiele.
- Intervalle: 5.000 Bootstrap-Stichproben ganzer Karten, PCG64-Startwert 0, lineare 2,5-/97,5-%-Quantile. Beide Seiten und die Panelgegner einer Karte bleiben zusammen.

Die Auswahlrunde verwendete zuvor 20 andere Karten `861000–861019`. Auswahl- und Bestätigungsergebnisse werden nicht zusammengelegt. FO42 war der einzige zugelassene Kandidat. SOLO28 scheiterte bereits in der Auswahl; es wurde hier nicht erneut getestet.

## Entscheidung

Nicht erfüllt: Panelgewinn mindestens +1 Prozentpunkt, untere Panel-Intervallgrenze über null und untere Direktduell-Intervallgrenze über 50 %. Erfüllt: Solution-Differenz mindestens null, deren untere Grenze über −1 Prozentpunkt, default mindestens 99 % und default-Differenz mindestens −1 Prozentpunkt.

Der [vorab festgelegte Plan](../../../../docs/superpowers/plans/2026-11-04-network-breadth.md) bleibt maßgeblich. Die [unabhängige Prüfung](../confirmation_review/confirmation_independent_review.md) und ihr [vollständiger Beleg](../confirmation_review/confirmation_independent_review.json) bestätigen die Rohdaten, alle Intervalle und die Entscheidung. Das [Archivmanifest](../confirmation_review/archive_manifest.json) enthält Dateigrößen und SHA-256-Prüfsummen. Der [Abschlussbericht](../../../../docs/ABSCHLUSSBERICHT_20261104_NETZE.md) erläutert den Gesamtversuch und die nächsten Schritte.

Die bestehenden V14-Gewichte und `Gruppe15.zip` blieben bytegleich. Heute erfolgte nur eine erneute Hash- und Inhaltskontrolle der bereits früher unter Python 3.13 und 3.10 geprüften V14-Abgabe; kein neuer FO42-Paketbau oder Laufzeittest.
