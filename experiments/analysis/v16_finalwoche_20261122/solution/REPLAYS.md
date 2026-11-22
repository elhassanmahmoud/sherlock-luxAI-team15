# Wo Solution-Partien kippen

**Bei den untersuchten Niederlagen war V16 meist schon vor der Schlussphase im Rückstand.** Auf vier Spielsitzen mit R3-Sieg und V16-Niederlage verlor V16 acht Einzelmatches. In sieben davon lag V16 bei Zug 70 hinten, im achten gleichauf. Bis dahin lautete das Punktesaldo gegen Solution in Summe **−745**. In den letzten zwanzig Zügen war das Saldo sogar **+179**. V16 nutzte seine bis Zug 70 bereits erreichten Felder spät zu 88,0 % (915 von 1.040 Feldzügen), Solution zu 58,5 % (925 von 1.580). Für diese Niederlagen greift die [Beobachtung gegen Kaggle](../FELDVERLAUF.md) zu kurz.

## Derselbe Startplatz, anderes Paket

Die Tabelle umfasst nur Einzelmatches, die auf einem Spielplatz mit unterschiedlichem Ausgang in Richtung des jeweiligen **Spielsiegers** kippten. Dadurch werden die Eröffnungs- und Schlussphasen eines von V16 verlorenen Matches mit den entsprechenden Phasen eines von R3 gewonnenen Matches auf derselben Karte, demselben Sitz und derselben Matchnummer verglichen. Die beiden Partien entwickeln sich ab der jeweils ersten abweichenden Aktion eigenständig.

| Wer holt das entscheidende Einzelmatch? | Paket | Bis Zug 70 erreichte Felder, eigenes Team / Solution | Punktsaldo bis Zug 70 | Punktsaldo Zug 71–80 | Punktsaldo Zug 81–100 |
|---|---|---:|---:|---:|---:|
| Nur R3, 7 Matches | V16 | 47 / 68 | −503 | −75 | +210 |
| Nur R3, dieselben 7 | R3 | 61 / 62 | −70 | +231 | +588 |
| Nur V16, 6 Matches | V16 | 64 / 59 | +23 | +209 | +799 |
| Nur V16, dieselben 6 | R3 | 56 / 65 | −365 | −24 | −22 |

Alle Werte sind Summen über die angegebene Matchzahl; jedes Feld zählt innerhalb eines Matches einmal als erreicht, sobald das Team dort gepunktet hat. Die Zeilen für sieben bzw. sechs Matches dürfen wegen der verschiedenen Fallzahlen nicht unmittelbar miteinander verglichen werden. Auf den vier R3-Siegessitzen kippt außerdem ein Einzelmatch zugunsten von V16. Alle 48 Einzelmatchergebnisse stehen in den Rohdaten.

**Konkretes Spielbeispiel.** Karte 7261020, Player 0, Match 3. Bei Zug 70 lag V16 mit **139 Punkten** zurück, R3 mit **8 Punkten**. In den letzten 20 Zügen machte V16 sogar 31 Punkte gut, R3 nur 18. Beim Schlusspfiff verlor V16 das Match dennoch um 132 Punkte, R3 gewann es um 10. Karte 7267009, Player 1, Match 2 zeigt die andere Richtung: V16 stand bei Zug 70 unentschieden und verlor die Schlussphase mit −12, R3 lag mit −25 zurück und gewann die Schlussphase mit +110.

**Folgetest.** Für Solution lohnt es sich, zuerst auf unabhängigen Entwicklungskarten Fälle zu zählen, in denen bereits vor Zug 70 ein öffentlich bekanntes, freies Feld erreichbar war und R3 bzw. der Lehrer es früher anlief. Gründe getrennt halten: ein Feld erstmals finden, es nach der Entdeckung ansteuern oder gegnerische Punkte durch Druck verhindern. Eine zusätzliche Bewegungspräferenz ist erst sinnvoll, wenn solche tatsächlich handlungsfähigen Fälle nachgewiesen sind. Die Schlussstärke von V16 auf den Gegenbeispielen dient als Kontrollgröße.

## Auswahl und Reproduktion

Aus [den 51 Sitzen mit unterschiedlichen Spielsiegern](unterschiedliche_sitze.csv) wurde deterministisch je Panel (3 oder 5), Sieger (nur R3 oder nur V16) und Sitz (Player 0 oder 1) der kleinste Seed gewählt. Das ergab acht verschiedene Karten und acht gleiche Starts pro Agent. Beide unveränderten Original-ZIPs spielten nacheinander gegen die unveränderte Solution_92. Die 16 Partien umfassten 4.848 Schritte. Eigene und gegnerische Endpunkte, Matchsiege und Spielsieger stimmten in **allen 16 Fällen** mit den vier anhand ihres SHA-256 geprüften Quellarchiven überein. Die extern aus dem Enginezustand ermittelten Punktefelder stimmten zugweise mit dem Punktezuwachs beider Spieler überein. Der Enginezustand war für die Auswertung nach dem Zug verfügbar. Die Agenten erhielten ihre üblichen Spielbeobachtungen.

Die Auswahl erfolgte ausdrücklich **nach bekanntem Ergebnis** und deckt je Kategorie nur zwei Spielsitze pro Panel ab. Sie darf weder die Gesamtquote schätzen noch einen Wechsel von V16 zu R3 begründen. Die Zahlen belegen, wann der Rückstand auf diesen Karten entstand. Sie belegen noch keine Ursache und keine allgemein gültige Regel.

[Messskript](replays.py) · [Alle 16 Spiele, Matchstände und Feldzahlen](replays.json) · [Gesamtauswertung von 1.600 Sitzen](ERGEBNIS.md)

```sh
python experiments/analysis/v16_finalwoche_20261122/solution/replays.py
```
