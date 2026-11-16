# Wie viele Punkte verändert der Eingriff unmittelbar?

Bei jedem tatsächlich veränderten Teamzug der vier Diagnosepartien speichert der Beobachter den Ausgangszustand der Spielengine und nutzt deren funktionalen Einzelschritt zweimal mit demselben Zufallsschlüssel. Der Kontrollzweig spielt beide tatsächlichen Befehlsmatrizen. Alle Werte seines Folgezustands und der nächste Zufallsschlüssel müssen mit dem regulären Spiel übereinstimmen. Der zweite Zweig setzt nur die veränderten eigenen Befehle auf die R3-Empfehlungen derselben Stellung zurück. Die Befehle von Solution bleiben für diesen Zug identisch. Der reguläre Spielverlauf und die Spielagenten erhalten ausschließlich das reguläre Ergebnis.

Für jede Verzweigung werden die offiziellen Punkte beider Teams nach der Aktion und die dafür tatsächlich gewerteten Felder geprüft. Positive verhinderte Punkte bedeuten, dass Solution mit dem übernommenen Teamzug weniger Punkte erzielte als mit den ursprünglichen R3-Befehlen auf derselben Stellung. Die Energiedifferenz bezieht sich auf die Summe der Energie lebender Einheiten nach diesem Zug. Mehrere Übernahmen in einem Teamzug werden gemeinsam betrachtet.

Die Summen beschreiben die unmittelbaren Wirkungen entlang des tatsächlich besuchten Kandidatenverlaufs. Folgen späterer Bewegung, Energieverluste in Folgezügen und andere Gegnerentscheidungen erfordern die separate Auswertung ganzer Spiele. Die vier ausgewählten Fälle liefern keine allgemeine Siegquote.


## Ergebnisse der vier Wiederholungen

Die 1.212 regulären Züge ergaben exakt dieselben vier Endstände, Matchsiege und Routingzähler wie die Hauptreihe. Bei allen 79 Zügen mit einem abweichenden Teambefehl wurde der unveränderte Kontroll-Folgezustand vollständig reproduziert. Die 108 geänderten Einheitsaktionen bewirkten zusammen unmittelbar 34 gegnerische Punkte weniger. Diese Zahl ist die Summe von 79 einzelnen Ein-Schritt-Vergleichen entlang der gespielten Verläufe. Die vier Wiederholungen werden nicht erneut in der Siegquote gezählt.

| Karte / Sitz | Eingriffszüge | Geänderte Einheitsaktionen | Unmittelbar verhinderte Gegnerpunkte, netto | Davon zuvor von Solution gehalten, netto |
|---|---:|---:|---:|---:|
| 7158016 / P0 | 1 | 1 | 1 | 1 |
| 7158020 / P0 | 10 | 10 | 2 | 2 |
| 7158020 / P1 | 12 | 14 | 2 | 2 |
| 7158030 / P1 | 56 | 83 | 29 | 24 |
| Gesamt | 79 | 108 | 34 | 29 |

In 24 Zügen bekam Solution gegenüber den ursprünglichen R3-Befehlen weniger Punkte. 55 Züge ergaben dieselbe gegnerische Punktzahl. Bei den 79 Paaren entfielen 36 gegnerische Feldgutschriften, zwei kamen auf anderen Feldern hinzu. Die eigenen tatsächlich gewerteten Feldkoordinaten stimmten bei allen Vergleichen exakt überein. Der unmittelbare Effekt dieser Eingriffe lag folglich auf gegnerischen Feldern. Für die Haltezeit über folgende Züge enthält die separate vollständige Replayanalyse die passenden Messwerte.

Auf 7158030/P1, Match eins, Zug 56 war der ursprüngliche R3-Befehl für Einheit 2 „stehen bleiben“. Die Verteidigungsregel spielte V15s Schuss mit Abstand (−6, −7). Mit ansonsten identischen Aktionen erhielt Sherlock in beiden Varianten drei Punkte. Solution erhielt mit Schuss vier und mit Halten sechs Punkte; die beiden verhinderten Gutschriften lagen auf den Weltkoordinaten (1,2) und (2,3).

[Alle Abzweigungen samt Befehlen und Felddifferenzen](daten/games.jsonl) · [Zusammenfassung je Sitz](auswertung.json). Reproduktion mit dem Projekt-Python und der eingefrorenen Laufzeit: `wiederholen.py --runtime LAUFZEIT --out NEUER_ORDNER`, anschließend `auswerten.py NEUER_ORDNER/games.jsonl`.
