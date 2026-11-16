# Sherlock R3 für das Finale am 27. November

**Für die Abschlussabgabe von Team 15 ist der ursprüngliche R3 mit einer Kartenansicht ausgewählt.** Das fertige [agent.zip](agent.zip) enthält den Ordner `sherlock/`, die eigenen Gewichte und die Kurskonfiguration. Beide Startseiten laden dieselbe Datei. Die ZIP hat die SHA-256-Prüfsumme `8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d`.

| Angabe für den Kursrunner | Wert |
|---|---|
| Gruppe | 15 |
| Agentenklasse | `agents.sherlock.main.Agent_x` |
| Gewichte für beide Spieler | `agents/sherlock/weights/agent.pth` |

## Warum R3?

Die 36 V14-Netze, ihre Aktionsmaske und die Kampfregeln bilden weiter die Basis. Wenn V14 eine Bewegung oder Halten wählt und der zusätzliche, durch Nachahmung trainierte Berater eine zulässige Bewegung mit mindestens 0,70 Sicherheit empfiehlt, kann der Berater den Befehl ändern. V14-Schüsse behalten ihre Zielkoordinaten. [Implementierung des Beraters](../../../scripts/selective_advice_agent.py)

Auf denselben 400 Karten und beiden Sitzen gewann R3 gegen die originale Solution **788/800 (98,5 %)**, V14 **767/800 (95,875 %)** und V15 **764/800 (95,5 %)**. Der gepaarte R3-Vorsprung gegenüber V14 beträgt 2,625 Prozentpunkte (95-%-Intervall +1,00 bis +4,38). Gegen den Kaggle-Dritten gewannen alle drei 12/800. Die Untergrenze des über beide Gegner gemittelten Vorteils liegt bei +0,25 Prozentpunkten. Damit sind beide vorab festgelegten externen Leistungsbedingungen erfüllt. R3 gewann außerdem 88/120 direkt gegen V14. V15 gewann seinen gesonderten Direktvergleich gegen R3 mit 36/48. Gegen andere Kursteams bleibt die Leistung offen. [Gemeinsamer Kartenvergleich](../../analysis/movement_soft_20261115/shared_400/ERGEBNIS.md) · [R3 gegen V15](../../analysis/r3_v4_mixed_duel_20261115/ERGEBNIS.md)

## Ausliefern und prüfen

Das Archiv ist die bytegleiche Kopie des geprüften ursprünglichen R3-Kandidaten. Unter Python 3.10 und in der Projektumgebung stimmten die vollständigen 606 Befehlsmatrizen beider Startseiten auf der Kurskarte 7271000 mit dem Forschungsagenten überein. Die Tests erfassten alle drei Matches, die Updates, die Paketgewichte und die Fehlerzähler. [Beide Kursprüfungen](../../analysis/movement_soft_20261115/candidate_package/README.md) · [Dateihashes](release.json)

Vom Projektordner aus erstellt der Standardaufruf die lokale Ausgabedatei und prüft beide Sitze im Kursrunner.

```sh
python -m scripts.build_submission
shasum -a 256 dist/agent.zip
```

## V14 wiederfinden

Die [gesicherten Originalgewichte](../20261101_v14_baseline/README.md) und die Forschungsreferenz unter `agents/sherlock/weights/` enthalten weiter V14. Die ursprüngliche November-Abgabe `Gruppe15.zip` verwendet das frühere Battle-Format und hat die SHA-256-Prüfsumme `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Im Desktopprojekt liegt außerdem eine bytegleiche Sicherung unter `experiments/releases/20261101_v14_baseline/Gruppe15_Battle_0611.zip`.

Für einen neuen lokalen Vergleich mit V14 im Standard-Kursformat kann Mahmoud die gesicherten Startgewichte explizit als eigenen Lauf verpacken. Für eine Rückkehr zum exakt damals eingereichten Battle-Format steht das gesicherte November-ZIP bereit.
