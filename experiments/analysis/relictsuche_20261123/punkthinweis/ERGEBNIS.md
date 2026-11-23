# Ein eigener Punkt verrät häufig die Gegend des ersten Relikts

Auf 80 neuen Sicht-1-Karten spielte Original-V16 beide Startseiten gegen Solution bis zum Ende des ersten Matches. **Auf 44 von 160 Starts** war die erste eigene Gutschrift schon öffentlich bekannt, während V16 noch kein Relikt gesehen hatte. Auf 34 dieser Starts gab es ein zweites, bewegungsfähiges Schiff, für das sämtliche bisherigen eigenen Punkte anhand der öffentlichen Belegungen ausgeschlossen werden konnten. Der genaue Zusammenhang von Belegung und Gutschrift lokalisierte das Relikt deutlich besser. Er sagte seltener voraus, welches einzelne Feld tatsächlich Punkte einbringt. [Vorabplan](PLAN.md) · [Kennzahlen](ergebnis.json)

| Reihenfolge im unveränderten Originalverlauf | Starts |
|---|---:|
| Erster eigener Punkt bereits öffentlich bekannt, Relikt noch unsichtbar | 44 |
| Eigener Punkt und Relikt erstmals in derselben Beobachtung | 39 |
| Relikt zuerst sichtbar | 77 |

Die 44 früheren Hinweise verteilen sich auf 26 Karten und die Startseiten 21 zu 23. Bis zur späteren Sicht vergingen im Median sieben Züge, auf 26 Startplätzen mindestens fünf. Auf allen 44 Starts blieben ab dem Hinweis mindestens 20 Aktionen. Auf 34 Starts (21 Karten, 16-mal P0 und 18-mal P1) gab es eine kurze andere Route für ein freies zweites Schiff. In der unveränderten Partie gewann V16 40 der 44 ersten Matches. In den zehn Aktionen nach dem Hinweis erzielte es durchschnittlich 5,86 Punkte, in den darauffolgenden zehn bereits 16,45 Punkte. [160 tatsächliche Startplätze, Seeds und Quellenhashes](quellen.json.gz)

## Was verrät die Belegung?

Der Schätzer prüft, welche der 300 spiegelgleichen Reliktlagen für die bisherige Sicht und die exakte eigene Punktesumme möglich bleiben. Schiffe auf demselben Feld zählen für die Mannschaftswertung einmal. Bei spiegelbildlichen Punkten hängt das Ergebnis von demselben Bit im geheimen Muster ab. Überlappende Paarumgebungen können zwei verschiedene Bits auf dasselbe physische Feld abbilden. Das Modell behandelt diese Fälle ausdrücklich und summiert die möglichen Aktivierungszeiten und Punktmuster. Es nutzt den auf 49.152 getrennten Karten gelernten Erstpaarprior. Das Vergleichsmodell erhält dieselben vorherigen Nullpunkte, Sichtzeiten und die Information, dass das erste Paar spätestens bei der Gutschrift aktiv war. [Öffentliche Inferenz](belegung.py) · [Training des Ortspriors](../zielschaetzer/ort.json)

| Zeitpunkt | Modell | Mittlerer Rang des tatsächlichen ersten Paars (von 300) | Mittlerer Logverlust |
|---|---|---:|---:|
| Erster positiver Hinweis, 44 Starts | Ohne genaue positive Summe | 59,4 | 4,817 |
| | Mit positiver Summe und belegten Feldern | **8,7** | **2,973** |
| Erstes verfügbares anderes Schiff und andere Route, 34 Starts | Ohne genaue positive Summe | 52,2 | 4,643 |
| | Mit positiver Summe und belegten Feldern | **5,9** | **2,493** |

Bei der ersten Gelegenheit senkte die exakte Belegung den Logverlust im Mittel um 2,150. Das auf ganzen Karten resampelte 95-%-Intervall liegt bei −2,555 bis −1,731. Der Ansatz lässt die Schiffe in Ruhe, die auch nur möglicherweise zu einer der bisherigen positiven Beobachtungen beigetragen haben. Im unabhängigen Abgleich enthielt diese Schutzmenge in sämtlichen betrachteten Stellungen die wirklich beteiligten Schiffe (677 kumulierte Schiffsbeiträge über 425 Positionen). [Gegenrechnung mit erschöpfender Prüfung auf 200 kleinen Beispielen](gegenrechnung.json)

Bei den 425 ausgewerteten Beobachtungen brauchte die genaue Ortsrechnung auf dem Versuchsrechner im Median 11,2 Millisekunden Prozesszeit und im 95. Perzentil 84,5 Millisekunden. Die Auswahl von Vergleichs- und Modellroute zusammen lag im Median bei 1,7 Millisekunden. Spielengine und V16-Befehl sind darin nicht enthalten. [Gemessene Rechenzeit](laufzeit.json)

## Ein neues Punktefeld direkt anzufahren bleibt unsicher

Am ersten verfügbaren Startpunkt suchte jedes Modell ein noch unbestätigtes, bis zu sechs Schritte entferntes Feld mit anderer erster Bewegung als V16. Die jetzigen und geplanten Besetzungen, legalen Befehle, bekannte Hindernisse und Schussaufgaben waren für beide Modelle dieselben. Das vollständige Modell traf **4/34** echte Punktefelder, das Vergleichsmodell **1/34**. Der Unterschied von +8,8 Prozentpunkten liegt im 95-%-Kartenintervall von 0,0 bis +22,9. Die geschätzte Punktwahrscheinlichkeit der ausgewählten Felder betrug im Mittel 8,1 % bzw. 4,1 %. Bei Gleichgewichtung aller tatsächlich erreichbaren anderen Zielfelder waren im Mittel 1,6 % echte Punktefelder. [Routenprüfung](gelegenheit.py) · [Alle Einzelpositionen und ausgewählten Wege](diagnose.json.gz)

Nähme das gewählte Schiff das Feld tatsächlich ein und hielte es fünf Züge lang, gab es auf den unveränderten Gegner- und Teamverläufen zusammen 19 echte, von anderen eigenen Schiffen unbesetzte Punktgelegenheiten. Dieselben Schiffe holten auf ihrer Originalbahn in diesen Zeitfenstern bereits neun Punkte als einzige eigene Einheit am jeweiligen Feld. In den zehn folgenden Zügen gab es 37 potenziell freie Punktzüge am Ziel und 14 tatsächliche exklusive Punkte auf der ursprünglichen Bahn. Die Rechnung setzt ein erfolgreiches Ankommen und Halten voraus, berücksichtigt weder Gegnerreaktionen noch abweichende Teambewegungen und liefert keinen kausalen Mehrertrag. 19 der 34 Routen waren aus dem öffentlichen Kartengedächtnis ganz einsehbar. [Vollständige Ergebnisse](ergebnis.json)

Aus dieser Diagnose folgt ein engerer Versuch. Der Zweitscout kann die genauer bekannte Gegend kurz direkt **beobachten** und nach dem Fund an V16 zurückgeben. Alle 160 Ausführungen hier waren unveränderte V16-Eröffnungen mit exakt 101 Aktionen und verifizierten Schlussgutschriften. Die separat protokollierte Untersuchung dieses Beobachtungsschritts hat eigene Karten. [Versuchsplan für die echte Sichtung](../punktsicht/PLAN.md)
