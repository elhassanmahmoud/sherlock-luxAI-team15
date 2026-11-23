# Nachrechnung des einzelnen Suchschritts

**Das Entwicklungsziel ist verfehlt.** Der Kundschafter mit höchstens einem abweichenden Befehl gewann alle 64 Spiele gegen Solution_92. Das gelang auf diesen Karten auch V16. Gegenüber dem vollständigen Kundschafter kam der erste eigene Reliktblick im Mittel **2,41 Züge später**. Das 95-%-Kartenintervall reicht von 0,09 bis 5,11 Zügen später. Der Plan verlangte einen früheren Erstfund.

| Spieler | Gegner | Ganze Siege P0 | Ganze Siege P1 | Zusammen |
|---|---|---:|---:|---:|
| V16 | Solution_92 | 32 | 32 | 64/64 |
| Ein Suchschritt | Solution_92 | 32 | 32 | 64/64 |
| Vollständiger Kundschafter | Solution_92 | 31 | 32 | 63/64 |
| Ein Suchschritt | V16 | 16 | 18 | 34/64 |
| Vollständiger Kundschafter | V16 | 16 | 18 | 34/64 |

Auf dem Sitz 0 der Karte 166200025 erhielt die Begrenzung den Sieg gegen Solution, den der vollständige Sucher abgegeben hatte. Bei der direkten Siegquote von 53,13 % liegt das Kartenintervall für den einzelnen Schritt bei 37,50 bis 68,75 %. Gegenüber dem vollständigen Sucher gingen im Vergleich mit demselben V16-Gegner 14 zuvor verlorene Sitze an die kürzere Variante und 14 zuvor gewonnene Sitze an die längere. Die Schwelle von mindestens 32 direkten Siegen und die verlangte externe Siegzahl sind erreicht.

| Öffnung gegen Solution | V16 | Ein Schritt | Vollständiger Sucher |
|---|---:|---:|---:|
| Erster öffentlicher Reliktblick, mittlerer Zug | 44,52 | 45,83 | 43,42 |
| Erste eigene Gutschrift, mittlerer Zug | 42,84 | 42,56 | 41,25 |

Der unabhängige Prüfer reproduzierte die ersten 32 Sicht-1-Karten ab 166200000, prüfte sämtliche 320 vollständigen Spiele, die drei Matchentscheidungen pro Spiel und die 20.000 Ziehungen ganzer Karten. In 25 Matches waren die Punkte ausgeglichen. Dort stammt der Matchsieger aus der gespeicherten Wertung der Umgebung. Bei beiden Gegnern griff der einzelne Suchschritt auf jeweils 56 von 64 Sitzen ein, stets mit derselben Einheit, in demselben Zug und mit demselben ersten geänderten Befehl wie beim vollständigen Kundschafter. Auf je 14 Sitzen stimmen die Prüfsummen der ganzen Aktionsreihen überein.

Die archivierten Daten enthalten die Eingriffsprotokolle, die kontrollierten Zählwerte für beide Spieler und die Prüfsummen der Gesamtbefehle. Einzelne unveränderte Befehle lassen sich aus diesen Prüfsummen nicht zurücklesen. Bei der Nachrechnung wurde kein Spiel gestartet. [Plan](PLAN.md) · [Prüfcode](nachrechnung.py) · [Nachrechnung mit Sitzwerten](nachrechnung.json) · [Roharchiv](partien.jsonl.gz)
