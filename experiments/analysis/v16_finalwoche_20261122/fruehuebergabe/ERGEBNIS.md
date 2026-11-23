# Die R3-Eröffnung rettet zwei Solution-Spiele

**V16 bleibt die Abgabe.** In 400 neuen Partien gewann die R3-Eröffnung gegen Solution zwei Spiele mehr. Gegen den Kaggle-Dritten gingen vier ganze Siege verloren, und direkt gewann der Kandidat 28 von 80 Partien. Damit erfüllt die Staffel eine von drei Auswahlbedingungen. Die 1.040 Spiele zur Bestätigung wurden entsprechend dem Plan nicht gestartet. [Feste Hypothese und Grenzwerte](PLAN.md) · [Technischer Nachweis der Übergabe](TECHNIK.md).

Die 40 Karten hatten vorab ausgewählte öffentliche Sensorreichweiten 1–2. Sie bilden einen gezielten Test kurzer Sicht. Die Prozentanteile beschreiben diese Karten. Auf beiden Sitzen wurden jeweils eine Original- und eine Staffelpartie gegen jeden externen Gegner gespielt. Im direkten Duell wechselten die Agenten ebenfalls die Seite.

| Gegner | Ganze Siege V16 | Ganze Siege Staffel | Matchsiege V16 / Staffel | P0 / P1 für die Staffel |
|---|---:|---:|---:|---:|
| Solution_92 | 76/80 | 78/80 | 225 / 226 von je 240 | 38 / 40 von je 40 |
| Kaggle-Dritter | 6/80 | 2/80 | 30 / 18 von je 240 | 1 / 1 von je 40 |
| V16 direkt | 52/80 | 28/80 | 154 / 86 von 240 | 14 / 14 von je 40 |

Gegen Solution gewann der Kandidat alle 76 zuvor gewonnenen Sitze und zusätzlich die P1-Partien auf 160362065 und 160362073. Die Differenz der Siegquoten beträgt **+2,5 Prozentpunkte**; das 95-%-Kartenbootstrapintervall reicht von **0 bis +6,25**. Gegen Kaggle verlor die Staffel alle sechs bisherigen Gewinnsitze und gewann zwei andere, eine Differenz von **−5 Prozentpunkten** (Intervall **−15 bis +5**). Der durchschnittliche Punkteanteil gegen Kaggle sank um **2,58 Prozentpunkte** (Intervall **−5,30 bis −0,04**). Im direkten Duell gewann die Staffel auf 14 Karten beide Sitze, auf 26 beide Male V16.

## Wo trat die Veränderung auf?

Die Aufschlüsselung nach Sichtweite dient der nachträglichen Erklärung. Sie verändert die Auswahlbedingungen nicht.

| Sicht | Karten | Solution, V16 → Staffel | Neue / verlorene Solution-Sitze | Kaggle, V16 → Staffel | Neue / verlorene Kaggle-Sitze | Staffel direkt gegen V16 |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 22 | 41 → 43 von 44 | 2 / 0 | 6 → 0 von 44 | 0 / 6 | 20/44 |
| 2 | 18 | 35 → 35 von 36 | 0 / 0 | 0 → 2 von 36 | 2 / 0 | 8/36 |

Beide neuen Kaggle-Sitze stammen von Karte 160362030. Auf 160362049, 160362057 und 160362066 verlor die Staffel jeweils beide zuvor gewonnenen Sitze. Eine Einschränkung auf Reichweite eins hätte in diesen Beispielen die sechs Kaggle-Rückschritte erhalten. Eine Einschränkung auf Reichweite zwei hätte keine der beiden Solution-Rettungen erfasst. Aus den Tabellen allein geht nicht hervor, welcher der ersten 40 Befehle für den späteren Ausgang verantwortlich war. [Alle Sitzpaare nach Reichweite](sichtgruppen.json) · [Erste öffentliche Reliktsichtung in zwei Technikbeispielen](TECHNIK.md).

## Laufzeit und Belege

In der laufenden Messumgebung dauerte eine Partie gegen Solution im Median 18,18 Sekunden mit V16 und 20,27 Sekunden mit Staffel. Gegen Kaggle waren es 34,92 und 37,53 Sekunden. Dies sind Zeiten kompletter Partien einschließlich Gegner und Engine bei paralleler Rechnerlast. Die beiden benötigten Original-ZIPs zusammen sind 37,06 MB groß, V16 allein 9,47 MB. [Herkunft und Größen in Bytes](herkunft.json).

Alle 400 Ergebnisse wurden auf vollständige 303 Schritte, exakten Seed, Sitz, Gegner, Variante, öffentliche Sicht und drei Matchentscheidungen geprüft. Es gibt keine doppelten Sitzaufträge. Die Zusammenfassung lässt sich aus dem komprimierten Archiv ohne Spielwiederholung berechnen. SHA-256 des Roharchivs: `6379d063531bea987518b256fe5f1e8815b04c266b32f5ac1be57d4e9ea7c1a0`. [400 Spieldatensätze](auswahl_partien.jsonl.gz) · [Primärauswertung mit Kartenintervallen](auswahl_ergebnis.json) · [Wiederholung](TECHNIK.md).
