# Wie V16 ein leeres Feld als sicher punktend eintrug

Drei gezielt ausgewählte V16-Partien sind mit dem Originalpaket reproduziert. Für zwei stimmen alle 303 eigenen Befehle und die drei Matchstände mit dem Entwicklungsarchiv überein. Für die dritte stimmen der Befehlsfingerabdruck beider Teams und die Matchstände der vorausgegangenen Vergleichspartie. Alle drei Fehlmarkierungen entstanden beim Auflösen der ursprünglichen Punktegleichungen.

| Karte, Sitz, Gegner | Erste falsche Markierung | Züge mit falschem Wissen | Eigene Schiffszüge auf solchen Feldern |
|---|---:|---:|---:|
| 162000169, P1, Solution | Match 2, Zug 71 | 131 | 13 |
| 162000431, P0, V16 | Match 3, Zug 74 | 27 | 46 |
| 162640027, P1, Solution | Match 3, Zug 64 | 37 | 38 |

Auf der ersten Karte kamen sechs Punkte hinzu, fünf davon waren schon erklärt. Ein tatsächlich zahlendes Feld hatte V16 noch als leer gespeichert. Unter dieser falschen Voraussetzung blieb nur ein anderer Ort übrig und V16 erklärte ihn zum sicheren Punktefeld. In den beiden anderen Spielen entstanden die Fehlschlüsse beim Weiterrechnen bereits gespeicherter Gleichungen. Ein falsch gesetztes Feld blieb teilweise mehrere Dutzend Züge besetzt. Eine verlorene Partie hatte auch der separat geprüfte positive Feldbeweiser vollständig identisch gespielt.

Bei 95 der 97 Schiffszüge auf einer falschen Markierung konnten wir bereits aus den bis dahin öffentlichen Beobachtungen beweisen, dass das Feld leer war. V16 gab in 86 dieser 95 Fälle einen Wartebefehl. Für die drei Karten waren es 11, 46 und 38 öffentlich erkennbare Schiffszüge. Ein eigener Versuch prüft jetzt, was die ursprünglichen Netze nach Rücknahme der widerlegten Markierung tun. [Widerlegung je Spielzug](widerspruch.json) · [Prüfung im echten Spiel](KORREKTURPLAN.md)

Die Zählungen stammen aus bekannten Fehlerfällen. Für eine Aussage über die Häufigkeit braucht es unabhängig gewählte Karten. [Reproduzierte Aufrufe und Spielzüge](ursachen.json) · [Prüfung der öffentlichen Widerlegbarkeit](WIDERSPRUCH.md)
