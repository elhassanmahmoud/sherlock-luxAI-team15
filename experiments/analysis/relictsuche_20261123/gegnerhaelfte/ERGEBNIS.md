# Der erste eigene Punkt auf der gegnerischen Kartenhälfte

**V16 punktete auf 129 von 132 normalen Sichtkarten bereits mit seinen ursprünglichen Befehlen auf der gegnerischen Hälfte. Ein trainiertes Modell konnte den späteren Ertrag eines solchen Kontakts auf getrennten Karten nicht zuverlässiger vorhersagen als der Lernmittelwert.**

In der ersten Stichprobe erreichte V16 auf allen 72 Karten die gegnerische Hälfte und punktete dort im ersten Match. Der erste solche Punkt kam auf den 48 Lernkarten im Median in Zug 62 und auf den 24 getrennten Prüfkarten in Zug 59. Nach dem ersten Reliktblick vergingen im Median 24 bzw. 18,5 Züge bis zum Kontakt. Die späte Überquerung erst in Zug 89 auf dem Anlasssitz fällt damit ans späte Ende. Karte 164300077 und die gesamte zugehörige 160er-Hauptprüfung blieben von sämtlichen nachfolgenden Berechnungen ausgeschlossen. [Vorabplan](PLAN.md) · [Messungen je Karte](entscheide.jsonl.gz)

| Erste Stichprobe, Original-V16 gegen Solution | 48 Lernkarten | 24 Prüfkarten |
|---|---:|---:|
| Erster eigener Punkt jenseits der Mittellinie | 48 | 24 |
| Davon bei oder nach der ersten öffentlichen Reliktsicht | 47 | 24 |
| Frühester bis spätester Erstkontakt | Zug 27–100 | Zug 39–84 |
| Median aller auf der anderen Hälfte gewonnenen Matchpunkte | 86,5 | 81,5 |
| Möglicher Zusatzweg zu einem logisch nachgewiesenen Feld nach allen Vorbedingungen | 0 | 0 |

Für einen Zusatzweg müsste V16 ein bereits durch eigene öffentliche Gutschriften bewiesenes und unreserviertes Ziel kennen. Ein einzelnes freies Schiff müsste es auf einer bekannten passierbaren Route erreichen können, ohne seine derzeitige oder nächste Punktaufgabe aufzugeben. Die Prüfung verlangte höchstens zwölf Wegschritte und untersuchte alle vier Züge. Ohne passende Beispiele konnte die vorgesehene Regression für einen zusätzlich angeordneten Vorstoß keine Gewichte lernen. Auf den ersten zwölf festgelegten Lernkarten gab es 118 öffentliche Zeitfenster nach Sicht. In genau einem lag bereits der strenge rechnerische Punktbeweis vor. Dort gab es einen erreichbaren Weg und genug Energie, aber das Ziel war bereits belegt oder für die übrige Flotte vorgesehen. [Prüfung der einzelnen Bedingungen](engpass.json) · [Auswahl und Kartenverteilung](modell.json)

## Was ein natürlicher Kontakt wert war

Für diese getrennte Beobachtungsfrage wurden nur die übrigen 60 Sicht-2–4-Karten desselben früheren Spielarchivs verwendet. Die ersten 36 lieferten die Lernmenge, die letzten 24 die Prüfung. Hier wird betrachtet, wie viele Punkte das tatsächlich auf sein erstes gegnerseitiges Zielfeld bewegte Schiff dort in zwölf Zügen alleine erzielte. Die Merkmale bestanden vor der Bewegung. Der Schiedsrichter ermittelte nur die spätere Gutschrift. Die Kontaktserie hat keine Karte mit der Zusatzwegserie gemeinsam. [Festgelegte zweite Stichprobe](KONTAKTPLAN.md) · [Originalbefehle und Kontaktbeobachtungen](kontakte.jsonl.gz)

Mit strengem öffentlichem Punktbeweis vor dem ersten Schritt und einem freien Schiff lieferte die Serie fünf geeignete Lernkarten und genau eine Prüfkarte. Ein kleines Regressionsmodell wurde tatsächlich gefittet. Auf dem einzelnen Prüffeld erzielte das Schiff einen Punkt, das Modell erwartete 4,79 und der Lernmittelwert 7,60. Für eine belastbare Aussage waren mindestens acht Lern- und acht Prüfkarten verlangt. [Gelernte Gewichte und getrennte Prüfung](kontaktmodell.json)

Mit den normalen öffentlichen **V16-Positivmarkierungen** anstelle des zusätzlich verlangten strengen Gutschriftbeweises waren 26 natürliche Erstkontakte im Training und 15 in der getrennten Prüfung auswertbar. Das Schiff hielt das Zielfeld im Mittel für 6,08 bzw. 4,00 eigene Punkte innerhalb von zwölf Aktionen. Das Modell mit 13 öffentlichen Merkmalen unterschritt den absoluten Fehler des Lernmittelwerts, verfehlte jedoch das vorher festgelegte Hauptkriterium des quadratischen Fehlers. Die Lern- und Prüfkarten blieben in beiden Definitionen identisch. [Vorab definierter Abgleich der Feldmarkierungen](V16_MARKIERUNG.md) · [Fit und Kartenprüfung](markierungsmodell.json)

| Vorhersage auf 15 zuvor getrennten Kontakten | Mittlerer quadratischer Fehler | Mittlerer absoluter Fehler |
|---|---:|---:|
| Lernmittelwert | 21,91 | 4,56 |
| Nur Zeitpunkt und Sichtweite | 27,75 | 5,03 |
| 13 öffentliche Merkmale | 24,45 | 3,96 |

Die geschätzte MSE-Verbesserung gegenüber dem Lernmittelwert beträgt −2,53 Punkte². Ihr 95-%-Kartenintervall reicht von −20,65 bis +12,34. Zug, Energie, Punktestand, sichtbare Gegner und Zielumgebung reichen in dieser Stichprobe nicht aus, um den späteren Ertrag zuverlässiger als den Lernmittelwert vorherzusagen. Die Daten stammen von vorhandenen V16-Befehlen. [Geprüfte natürliche Kontakte](markierungen.jsonl.gz)

Mit den regulären V16-Markierungen hätte sich vor dem echten Kontakt auf drei der 36 Lernkarten und fünf der 24 Prüfkarten ein möglicher Zusatzweg ergeben. Alle **17 vorgeschlagenen Zielfelder waren tatsächlich aktiv und zahlend**. Im unveränderten Originalverlauf erreichte genau eine vorgeschlagene Einheit ihr Ziel als erstes gegnerseitiges Punktefeld innerhalb des festgelegten Zwölf-Zug-Fensters. Das war auf der Prüfkarte 162860133 der Vorschlag in Zug 48 für Schiff 9 zum Feld (13, 13), das in Zug 59 einen Punkt brachte. Auf den Lernkarten kam kein solches positives Beispiel vor. Ob ein eigener Befehl andere Schiffe am Punktesammeln gehindert oder einen zusätzlichen Punkt gebracht hätte, bleibt offen. [Eindeutig zugeordnete Ziele und Originalbelegungen](wege_gegengeprueft.json)

## Wie häufig der Kontakt insgesamt vorkam

Die beiden Stichproben erfassen zusammen alle 132 Karten mit normaler Sicht des älteren 160-Karten-Archivs. Jede Karte ist mit genau einem Sitz vertreten, 66-mal Spieler 0 und 66-mal Spieler 1. V16 punktete auf **129/132 Karten** im ersten Match mindestens einmal auf der anderen Hälfte. Auf 127 Karten geschah das bei oder nach seinem ersten öffentlichen Reliktblick. Die Tabelle zählt tatsächliche Karten, einschließlich der drei ohne Kontakt. [Ursprüngliches Spielarchiv](../punktwissen/allgemein_partien.jsonl.gz)

| Sichtweite | Karten | Erster V16-Punkt auf der anderen Hälfte | Davon bei oder nach Reliktsicht | Median des Kontaktzugs unter den Karten mit Kontakt |
|---|---:|---:|---:|---:|
| 2 | 46 | 44 | 43 | 62 |
| 3 | 43 | 42 | 41 | 61 |
| 4 | 43 | 43 | 43 | 62 |

Der Anlassfall zeigt eine legale Frühankunft durch R3. Das unabhängige ältere Archiv zeigt, dass V16 die andere Hälfte selbst häufig erreicht. Für die zusätzliche Umlenkung eines freien Schiffs fehlte ein positiver Lernbestand, und für den natürlich gespielten Kontakt verfehlte das gelernte Modell seine Schwelle. Damit entfiel der gezielte Gegenversuch. Sämtliche Originalbefehle der betrachteten V16-Seite, die offiziellen Punkte jedes ausgewerteten Zuges und die Archiv-Matchendstände wurden bei der Wiedergabe geprüft. Die wiederholten Abläufe zählen jeweils als dieselbe ursprüngliche Karte.
