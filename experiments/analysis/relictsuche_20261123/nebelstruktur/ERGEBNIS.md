# Die Nebelumgebung verbessert die Sichtschätzung, ändert aber keinen Weg

Auf 160 separat zurückgelegten Karten verbesserte das räumliche Modell die Vorhersage, ob ein einzelner zusätzlicher Sensorpunkt ein bisher unsichtbares Nachbarfeld aufdeckt. Trotzdem wählte die nominierte Suche in allen **681 angebotenen Situationen denselben Weg**. Die Sicht auf das erste aktive Relikt blieb innerhalb des achtzügigen Fensters auf jeder Karte gleich. Damit endet der Versuch nach der Offlineprüfung. [Vorab festgelegte Kriterien](PLAN.md) · [Ergebnisse auf den 160 Karten](valid.json)

## Welche Sichtwirkung das Modell lernt

Wenn die übrigen Schiffe eine Zelle noch nicht sehen, reicht auf einem Nachbarfeld genau ein zusätzlicher Sensorpunkt, sofern die Restleistung dort null beträgt. Bei negativer Leistung muss das Schiff näher herankommen oder mehr Unterstützung erhalten. Das frühere Flottennetz schätzt dagegen, was die übrigen Schiffe aus eigener Kraft sehen. Die ältere Nebelstudie spielte 107 einzelne Richtungsänderungen nach, bei denen zwei oder mehr Sensoren gemeinsam den ersten Fund hätten ermöglichen können. [Flottennetz](../flottenblick/VORHERSAGE.md) · [Frühere Einzelzugprüfung](../nebelsicht/ERGEBNIS.md)

Aus 480 Original-V16-Trainingskarten lieferten 362 insgesamt 1.788 Situationen. Ein punktweises Netz lernte zunächst aus dem letzten Gelände- und Sichturteil am betreffenden Feld, den aktuellen Flottenmerkmalen und dem Vorhersagehorizont. Anschließend blieben diese Gewichte fest. Zwei räumliche Faltungen lernten aus umliegenden sichtbaren Klar-, Hindernis- und Nebelfeldern, wie sich die Schätzung ändert. Bei dieser Korrektur hat das Zielfeld selbst keinen Eingang. Die Modellgewichte enthalten keine Karte, kein Reliktziel und keine Schiedsrichterbeobachtung als Laufzeiteingabe. [Modell](modell.py) · [Training und Herkunft](fit.json) · [Eingefrorene Gewichte](gewichte.npz)

## Sichtwirkung auf getrennten Karten

131 der 160 Prüfkarten enthielten einen angebotenen Suchweg. Die Tabelle betrifft tatsächlich erreichbare Nachbarfelder, die von der aufgezeichneten Restflotte im jeweiligen Zug unbesichtigt blieben. Es gab 192.867 solche Feld-Zeitpunkt-Beobachtungen mit unbekanntem oder mindestens vier Züge altem Gelände. In 21.507 davon schluckte die Dämpfung den einen zusätzlichen Sensorpunkt. Mehrfachbeobachtungen derselben Karte werden bei den Intervallen gemeinsam gezogen. Kleinere Brier-Werte bedeuten bessere Wahrscheinlichkeitsvorhersagen.

| Vorhersage | Unbekannt oder mindestens vier Züge alt | Nur noch nie gesehene Zellen |
|---|---:|---:|
| Bisheriges festes Randgewicht der Suche | 0,08593 | 0,09908 |
| Einfache Vergleichstabelle aus Sensorpaare | 0,07920 | 0,09082 |
| Neu trainiertes punktweises Netz | 0,07926 | 0,09077 |
| Dasselbe Netz mit örtlicher Nebelumgebung | **0,07823** | **0,08940** |
| Für die Routenwahl tatsächlich verwendetes Randgewicht | 0,08597 | 0,09907 |

Gegenüber dem eigenen punktweisen Vergleich sank der Brier-Fehler um 0,00103 (95-%-Kartenintervall 0,00049 bis 0,00152). Bei 135.748 Beobachtungen noch nie gesehener Zellen betrug die Verbesserung 0,00138 (0,00071 bis 0,00198). Die resultierende absolute Wahrscheinlichkeit und das tatsächlich eingesetzte Randgewicht sind unterschiedlich: Der feste Plan addierte ausschließlich den räumlichen Korrekturbetrag zum bereits bestehenden Routengewicht. Unter dieser Einschränkung verbesserte sich der Brier-Wert des angewandten Randgewichts über alle ausgewerteten Zellen nicht. [Getrennte Berechnung und Intervalle](valid.json) · [Messungen je Situation](valid_karten.jsonl.gz) · [Einfache Vergleichstabelle](../sensorpaare/modell.py)

## Warum die Wahl gleich blieb

Nach Altersfilter und Begrenzung auf Sichtgewichte zwischen null und eins änderte sich je Situation im Mittel nur 0,32 % des gesamten Kartenfelds über acht Zukunftszüge. In 294 von 681 Situationen bewegte sich mindestens ein Routenwert um mehr als 0,00001. Die maximale Wertänderung über alle angebotenen Wege und Situationen lag bei 0,480. Der typische Abstand der besten zur zweitbesten Bewegungsroute betrug 0,990 (Median). In keiner Situation wechselte die beste Bewegungsroute oder die Entscheidung zwischen Fahren und Warten. Die Sichtdifferenz zur nominierten Suche beträgt damit exakt null.

Eine zweite Rechnung überprüfte alle 160 tatsächlichen Reliktpaare und ihre Aktivierung direkt aus dem Kurs-Spielzustand. Sie ergänzte die Restleistung für sämtliche angebotenen Routen mit null, eins oder zwölf Sensorpunkten nach der tatsächlichen Entfernung und reproduzierte alle 681 Sichtzeitpunktvergleiche. Eine von Torch unabhängige Faltungsrechnung auf 24 über die Kartenfolge verteilten Situationen stimmte bei allen acht vollständigen Sichtkarten bis auf einen maximalen Unterschied von 0,00000012 überein. [Unabhängige Gegenprüfung](nachrechnung.json) · [Prüfmethode](nachrechnung.py)
