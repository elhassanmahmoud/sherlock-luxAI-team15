# Die einzige verbleibende Niederlage gegen Solution bei Sichtweite zwei

**Karte 164300077, Spieler 0.** V16 verlor Match 1 mit 184–205 und Match 2 mit 559–574. Der Sieg in Match 3 mit 644–523 kam zu spät. Auf der anderen Startseite gewann V16 alle drei Matches. Auf dieser Karte wurde nur das erste Reliktpaar aktiv. Sämtliche Punkte beider Mannschaften in allen zwölf unten gezeigten Matches stammen aus dieser ersten Generation. Die zweite und dritte Generation blieben durchgehend inaktiv. [Messdaten pro Match, Generation und Sitz](bilanz.json)

## Wann der Rückstand entstand

Im ersten Match wurde das Reliktpaar nach dem Befehl in Zug 46 aktiv. Sherlock P0 punktete bereits bei diesem Übergang, Solution erstmals nach Zug 48. Beide sahen erstmals in der öffentlichen Beobachtung von Zug 47 einen Reliktknoten. Nach Zug 60 führte Sherlock 15–12. Ab Zug 63 lag es mit 18–21 dauerhaft zurück. Der Rückstand erreichte 74 Punkte in Zug 87. Sherlock holte bis zum Ende auf 21 Punkte auf. [Archivtreue Wiederholung P0](v16_p0.json.gz)

Im zweiten Match sahen beide Seiten bereits in der Startbeobachtung einen bekannten Knoten. Ab Zug 11 lag Sherlock dauerhaft zurück. Der Rückstand wuchs bis Zug 73 auf 90 Punkte und schrumpfte bis zum Ende auf 15. Auf beiden Startplätzen lag V16 nach Zug 70 genau 84 Punkte zurück. P1 drehte das Match in Zug 99 und gewann schließlich 546–537. [Archivtreue Wiederholung P1](v16_p1.json.gz)

| Sherlock-Sitz und Match | Punkte Sherlock / Solution, Generation 1 | Erster eigener / gegnerischer Punkt | Erster eigener / gegnerischer Reliktblick |
|---|---:|---:|---:|
| P0, Match 1 | 184 / 205 | 46 / 48 | 47 / 47 |
| P0, Match 2 | 559 / 574 | 4 / 3 | 0 / 0 |
| P0, Match 3 | 644 / 523 | 3 / 3 | 0 / 0 |
| P1, Match 1 | 145 / 79 | 46 / 63 | 47 / 64 |
| P1, Match 2 | 546 / 537 | 4 / 3 | 0 / 0 |
| P1, Match 3 | 631 / 513 | 3 / 3 | 0 / 0 |

Züge zählen ab null innerhalb jedes Matches. Ein Punkt bezieht sich auf den ausgeführten Befehl, ein Blick auf die Beobachtung vor dem Befehl. Die Null in Match 2 und 3 bedeutet, dass die öffentliche Startbeobachtung schon einen sichtbaren Knoten enthielt. [Nachspielverfahren](nachspielen.py)

## Welche Gebiete die fehlenden Punkte einbrachten

In den beiden verlorenen Matches erhielt Solution **alle 779 Punkte innerhalb von Reliktgebieten, die Sherlock bereits kannte**. Ob auch das genaue Feld in Sherlocks eigener Punktkarte bereits positiv markiert war, unterschied sich. In Match 1 stammten 41 der 205 gegnerischen Punkte von positiv markierten Feldern und 164 von übrigen Feldern im bekannten Gebiet. In Match 2 waren es 357 von 574 und 217 übrige. Die V16-Markierung wurde unmittelbar vor dem jeweiligen Befehl aus dessen öffentlichem Wissensstand gelesen. Den tatsächlichen Punkt ordnete der Schiedsrichter anschließend einmal je belegtem Feld und Team zu. [Feldweise Auswertung](auswerten.py)

| P0, Match | Team | Positiv markiertes Feld | Übriges Feld im bekannten Gebiet | Außerhalb bekannter Gebiete |
|---|---|---:|---:|---:|
| 1 | Sherlock | 122 | 61 | 1 |
| 1 | Solution | 41 | 164 | 0 |
| 2 | Sherlock | 494 | 65 | 0 |
| 2 | Solution | 357 | 217 | 0 |

Solution punktete in beiden verlorenen Matches ausschließlich auf der eigenen Kartenseite. Im ersten Match waren (18, 23) mit 38 Punkten und (21, 22) mit 34 die am häufigsten von Solution besetzten Punktefelder. Im zweiten waren es (21, 22) mit 98 und (19, 23) mit 77. V16 erzielte auf der anderen Kartenhälfte in Match 1 erstmals in Zug 89 Punkte und holte dort insgesamt 22. In Match 2 kamen alle 559 eigenen Punkte von seiner eigenen Hälfte. Die Hälften sind durch die Kartendiagonale zwischen den beiden Startgebieten getrennt. Auf dieser Diagonale fiel kein Punkt. [Vollständige Feldbilanz](bilanz.json)

## Was unverändertes R3 auf derselben Karte erreichte

| Startplatz | R3 gegen dieselbe Solution, Matches 1 / 2 / 3 | Ganzes Spiel |
|---|---|---|
| P0 | 263–92 / 616–623 / 621–588 | Sieg in Match 1 und 3 |
| P1 | 367–21 / 598–585 / 604–610 | Sieg in Match 1 und 2 |

Auf dem Verlustsitz P0 fand R3 das erste Relikt ebenfalls in Zug 47 und punktete erstmals nach Zug 46. Es erreichte bereits in Zug 66 ein zahlendes Feld auf der gegnerischen Kartenhälfte, **23 Züge früher als V16**, und verdiente dort 60 statt 22 Punkte. Auf seiner eigenen Hälfte erzielte R3 zusätzlich 203 statt 162 Punkte. Solution erhielt im ersten Match gegen R3 nur 92 statt 205 Punkte. So drehte die regulär gespielte R3-Politik den ersten Matchausgang auf dieser bekannten Karte. Das zweite Match verlor auch R3. Die frühe Belegung der gegnerischen Hälfte und der Rückgang gegnerischer Punkte sind beobachtete Unterschiede zwischen zwei vollständigen Spielweisen. Der isolierte Beitrag eines einzelnen Befehls ist damit offen. [R3 P0](r3_p0.json.gz) · [R3 P1](r3_p1.json.gz)

Die beiden V16-Wiederholungen prüften in allen 303 Zügen auch die tatsächlich erzeugten Befehle beider Spieler vor der Übergabe der Archivbefehle an die Umgebung. Die vollständigen Befehlsprüfsummen und alle sechs V16-Matchergebnisse stimmten mit dem ursprünglichen 960er-Test überein. R3 spielte in einem getrennten Prozess über den regulären ZIP-Lader dieselbe Karte auf beiden Sitzen. Die vier Spiele sind eine nach dem bekannten Ausgang ausgewählte Ursachenprüfung. Die Siegstatistik und die Abgabeempfehlung stammen weiterhin aus der abgeschlossenen Hauptprüfung. [Primärer Vergleich](../abschlusspruefung/ergebnis.json)
