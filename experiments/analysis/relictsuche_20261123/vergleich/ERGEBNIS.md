# 560 ganze Spiele mit drei Suchwegen

Der Zielschätzer brachte gegen Solution den ersten eigenen Punkt im Mittel **4,30 Züge früher** als Sherlock V16. Das gepaarte 95-%-Kartenintervall reicht von +1,75 bis +7,10 Zügen. Der mittlere erste Reliktfund rückte um 2,73 Züge vor, sein Intervall schließt null ein. Der Zielschätzer gewann 72 von 80 ganzen Spielen gegen Solution, V16 gewann 75. Im direkten Duell gegen V16 gewann der Zielschätzer 28 von 80. Keiner der drei Kandidaten erfüllte alle Auswahlbedingungen. Die getrennten Bestätigungs- und Generalkarten bleiben unbenutzt.

## Eröffnung und Spielausgang

Die ersten 40 frischen Karten mit Sensorreichweite eins wurden auf beiden Startseiten gespielt. Sicht und Gutschrift geben die mittlere Vorverlegung gegenüber V16 im selben Sitz gegen Solution an. Die Punktedifferenz ist die Veränderung des Vorsprungs nach Zug 70. Klammern zeigen das 95-%-Kartenintervall aus 20.000 Ziehungen ganzer Karten. Der Direktvergleich nennt tatsächlich ausgespielte Siege gegen die Abgabe.

| Agent | Sicht früher, Züge | Gutschrift früher, Züge | Veränderung der Punktedifferenz nach Zug 70 | Match 1 gegen Solution | Ganze Spiele gegen Solution | Direkt gegen V16 |
|---|---:|---:|---:|---:|---:|---:|
| Original V16 | Ø Zug 43,24 | Ø Zug 43,26 | Ø +7,00 Vorsprung | 76/80 | 75/80 | – |
| Routenlernen | −3,24 [−8,24; +1,64] | +0,63 [−2,86; +3,98] | −8,14 [−22,11; +4,48] | 71/80 | 76/80 | 32/80 |
| Routenwert | +0,31 [−0,41; +1,21] | +0,13 [−0,74; +1,06] | −0,20 [−6,24; +5,48] | 77/80 | 75/80 | 36/80 |
| Zielschätzer | +2,73 [−0,35; +6,08] | +4,30 [+1,75; +7,10] | +4,21 [−7,09; +14,75] | 77/80 | 72/80 | 28/80 |

Der Zielschätzer punktete auf 37 Sitzen früher, auf 26 gleichzeitig und auf 17 später. Er verlor auf vier zuvor gegen Solution gewonnenen Sitzen und gewann einen zuvor verlorenen Sitz. Die mittlere Veränderung der ganzen externen Siegquote betrug −3,75 Prozentpunkte [−11,25; +2,50]. Beim Routenlernen kippten auf einer Karte zwei Niederlagen zu Siegen, auf einer anderen Karte ging ein Sieg verloren. Die externe Veränderung betrug +1,25 Prozentpunkte [−3,75; +7,50]. Der Routenwert lieferte auf allen 80 Sitzen denselben ganzen Sieger wie V16. Bei null gegensätzlichen Sitzen ergibt der beobachtete Kartenbootstrap ein Intervall von [0; 0]. Auf neuen Karten können Unterschiede auftreten.

## Beide Startseiten und tatsächliche Eingriffe

| Agent | Match 1 gegen Solution, P0 / P1 | Ganze Spiele gegen Solution, P0 / P1 | Direkt gegen V16, P0 / P1 | Geänderte Karten gegen Solution / V16 | Geänderte Befehle gegen Solution / V16 |
|---|---:|---:|---:|---:|---:|
| V16 | 37 / 39 | 38 / 37 | – | – | – |
| Routenlernen | 37 / 34 | 38 / 38 | 16 / 16 | 38 / 38 | 1.084 / 1.086 |
| Routenwert | 38 / 39 | 38 / 37 | 18 / 18 | 14 / 12 | 134 / 96 |
| Zielschätzer | 39 / 38 | 37 / 35 | 14 / 14 | 38 / 38 | 818 / 790 |

Jede Sitzspalte umfasst 40 Spiele. Die direkten Siegquoten mit Kartenintervall betragen 40,0 % [25,0; 55,0] für Routenlernen, 45,0 % [36,25; 53,75] für Routenwert und 35,0 % [21,25; 50,0] für den Zielschätzer. Auf allen externen Sitzen traten Sicht und erste Gutschrift bis Zug 100 ein. Der vorab definierte Ersatzwert 101 wurde dort nie benötigt.

Alle 560 Partien absolvierten jeweils 303 Aktionen pro Seite. Jede Abweichung wurde gegen den tatsächlichen ursprünglichen V16-Befehl kopiert und verglichen. Eine veränderte Einheit behielt über alle Eingriffe derselben Partie ihre ID. Auf den 60 inaktiven externen Kandidatensitzen stimmten beide vollständigen Befehlsfolgen und alle Ergebnismaße exakt mit der tatsächlichen V16-Referenz überein. Alle technischen Fehlerprüfungen für beide Spieler bestanden. Vier vorher gespielte historische Technikpartien reproduzierten 20 unabhängige Eröffnungswerte. Sechs Komponententests prüften unter anderem Sitzpaarung, Aktivierungsrichtung, unvollständige Panels und beide Freigaberouten. Die eigenständige Gegenrechnung aus dem Roharchiv reproduzierte 33 Merkmalsreihen samt Kartenintervallen sowie alle drei Auswahlentscheidungen.

[Vorab festgelegte Karten und Gates](PLAN.md) · [Alle Rohpartien](discovery/partien.jsonl.gz) · [Kennzahlen nach Gegner und Sitz](discovery/ergebnis.json) · [Herkunft und Hashes](discovery/herkunft.json) · [Separates Kontrollprogramm](gegenrechnung.py) · [Historische Technikprüfung](technik/pruefung.json)
