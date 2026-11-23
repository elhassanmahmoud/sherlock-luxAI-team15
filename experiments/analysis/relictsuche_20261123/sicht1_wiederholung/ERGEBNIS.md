# Unabhängige Wiederholung auf 96 Sicht-1-Karten

**V16 bleibt die Abgabe.** Der eingefrorene Kundschafter gewann gegen Solution_92 auf beiden Sitzen zusammen 178 von 192 Spielen, V16 gewann 177. Der Unterschied von einem Sieg erfüllt die vorab festgelegte Schwelle für eine Übernahme nicht. Im Direktvergleich gewann der Kundschafter 102 von 192 Spielen. Die untere Grenze seines 95-%-Intervalls liegt bei 43,75 %, gefordert waren mindestens 45 %.

## Ganze Spiele und erste Suchsignale

Alle Intervalle beruhen auf 20.000 Ziehungen ganzer Karten mit jeweils beiden Sitzen. Positive Unterschiede bei den Zeiten geben an, wie viele Züge der Kundschafter früher war. Ein bis zum Ende von Match 1 ausgebliebenes Signal zählt als Zug 101.

| Messgröße | V16 | Kundschafter | Unterschied | 95-%-Kartenintervall des Unterschieds |
|---|---:|---:|---:|---:|
| Ganze Siege gegen Solution | 177/192 | 178/192 | +0,52 Prozentpunkte | −2,60 bis +3,65 Prozentpunkte |
| Siege in Match 1 | 166/192 | 169/192 | +1,56 Prozentpunkte | −3,13 bis +6,25 Prozentpunkte |
| Siege in Match 2 | 176/192 | 175/192 | −0,52 Prozentpunkte | −3,13 bis +2,08 Prozentpunkte |
| Siege in Match 3 | 174/192 | 175/192 | +0,52 Prozentpunkte | −2,08 bis +3,13 Prozentpunkte |
| Erster eigener Reliktblick gegen Solution, mittlerer Zug | 46,71 | 45,81 | 0,91 Züge früher | −0,92 bis +2,89 Züge |
| Erste eigene Gutschrift gegen Solution, mittlerer Zug | 44,83 | 44,09 | 0,73 Züge früher | −0,45 bis +1,99 Züge |

Bei der ersten Sicht war der Kundschafter auf 57 Sitzen früher, auf 37 später und auf 98 gleichauf. Drei seiner Sitze und vier V16-Sitze erreichten bis zum Ende von Match 1 keinen Fund. Die erste Gutschrift kam auf 56 Sitzen früher, auf 36 später und auf 100 beim gleichen Zug. Beide Spieler blieben auf jeweils acht Sitzen ohne Gutschrift.

## Die sieben geänderten Gesamtsieger gegen Solution

Die Pfeile führen von V16 zum Kundschafter. „S“ steht für gewonnenes, „N“ für verlorenes Match, von links nach rechts M1 bis M3. Die erste Abweichung ist der erste tatsächliche Unterschied in den an die Umgebung übergebenen Befehlen. Zugnummern beginnen bei null.

| Karte | Sitz | Ganze Partie | Matches V16 → Kundschafter | Erste Abweichung | Erstsicht | Erste Gutschrift |
|---|---:|---|---|---:|---|---|
| 165300052 | 0 | gewonnen | SNN → SSN | 19 | 37 → 47 | 36 → 45 |
| 165300075 | 0 | gewonnen | NNS → SNS | 16 | 43 → 43 | 40 → 40 |
| 165300075 | 1 | gewonnen | NNS → SNS | 16 | 43 → 43 | 40 → 40 |
| 165300152 | 1 | verloren | SSS → NNS | 21 | 78 → 101 | 78 → 101 |
| 165300159 | 1 | gewonnen | NSN → NSS | 25 | 83 → 79 | 52 → 54 |
| 165300166 | 1 | verloren | SSN → NNS | 19 | 74 → 78 | 42 → 42 |
| 165300214 | 0 | verloren | SSS → NNS | 17 | 80 → 93 | 31 → 31 |

Auf 165300075 änderten sich beide Gesamtsieger bei gleichen Zeiten für Erstsicht und erste Gutschrift. Auf 165300052 entschied das zweite Match trotz späterer Gutschrift und Sicht, auf 165300159 das dritte Match mit 147 zu 144 Punkten. Bei allen drei verlorenen Sitzen kippten die ersten beiden Matches gemeinsam. Die vollständigen Punktstände aller sieben Spielpaare stehen in [unabhaengig.json](unabhaengig.json).

## Nachrechnung aller Vergleichsarme

| Spieler und Gegner | Ganze Siege P0 | Ganze Siege P1 | Zusammen |
|---|---:|---:|---:|
| V16 gegen Solution_92 | 89/96 | 88/96 | 177/192 |
| Kundschafter gegen Solution_92 | 90/96 | 88/96 | 178/192 |
| Kundschafter gegen V16 | 53/96 | 49/96 | 102/192 |

Im externen Vergleich blieben 90 Karten in der Summe beider Sitze unverändert. Zwei Karten gewannen einen Sitz hinzu, eine gewann beide, drei verloren je einen. Bei unabhängiger Vorzeichenumkehr dieser sechs Karten tragen 32 von 64 möglichen Kombinationen mindestens den beobachteten Gewinn von einem Sitz. Das ergibt einseitig **p = 0,500** gegenüber der geforderten Höchstgrenze 0,0125. Auch die geforderte positive untere Intervallgrenze gegen Solution wurde verfehlt.

Die direkte Siegquote beträgt **53,13 %** mit 95-%-Kartenintervall **43,75 bis 61,98 %**. Auf 43 Karten gewann der Kundschafter beide direkten Sitze, auf 37 verlor er beide. Auf den übrigen 16 Karten waren sämtliche Kommandos bei getauschten Spielern identisch, mit je einem Sieg für jeden. Nur die geforderte beobachtete Direktquote von mindestens 50 % ist erreicht.

Die Nachrechnung bestätigt die ersten 96 Sicht-1-Karten ab 165300000 anhand der Spielparameter sowie die versiegelten Quellen. Sie öffnete die Rohdaten erst nach Veröffentlichung aller **576 Partien, 1.728 Matches und 174.528 Züge**. Sämtliche gespeicherten Kommandos beider Spieler ergeben ihre verzeichnete Prüfsumme. Gegen Solution waren 31 von 192 gepaarten Aktionsreihen vollständig gleich, einschließlich Matchständen und Suchzeiten. Auf den anderen 161 Sitzen wich am ersten unterschiedlichen Zug genau eine eigene Einheit mit einer erlaubten Bewegung ab, während sämtliche Gegnerbefehle noch übereinstimmten.

Jeder Gesamtsieger wurde aus seinen drei Matchsiegern neu bestimmt. In 1.675 Matches lässt sich der Matchsieger zusätzlich allein aus den Punkten bestätigen. In den 53 Punktgleichständen wurde der archivierte Siegerentscheid der Spielumgebung verwendet. Das Archiv enthält keine Endenergien für eine unabhängige Wiederberechnung dieser Gleichstände. Der Prüfer führte keine Spielsimulation aus.

Der Vergleich bezieht sich ausschließlich auf diesen neuen Kartensatz. [Vorabplan](PLAN.md) · [Kartenliste](karten.json) · [Prüfcode](unabhaengig.py) · [Prüfergebnis](unabhaengig.json) · [Spielarchiv](partien.jsonl.gz)
