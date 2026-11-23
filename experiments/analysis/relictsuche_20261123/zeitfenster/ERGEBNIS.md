# Früher dort gewesen, beim Erscheinen wieder fort

**Auf 58 von 160 Originalkarten lag mindestens einer der beiden künftigen ersten Reliktorte schon vor seiner Aktivierung im tatsächlichen Sichtfeld von V16.** Auf 29 dieser Karten sah die Flotte den Ort auch beim Erscheinen. Auf den anderen 29 war er zu diesem Zeitpunkt wieder verborgen. Hätte ein gerade abfahrendes freies Schiff bis zu drei Züge an seinem Standort bleiben können, wäre das erste Relikt auf sechs Karten früher sichtbar geworden. Die feste öffentliche Halteregel traf keines dieser Fenster und verlor in zwei anderen Eröffnungen die Gelegenheit zum ursprünglichen ersten Blick. [Ergebnisse für beide Startseiten und Gegner](train/ergebnis.json)

| Auf 160 unterschiedlichen Sicht-1-Karten | Karten | Gegen Solution | Gegen V16 |
|---|---:|---:|---:|
| Späterer erster Reliktort vor Aktivierung tatsächlich im Team-Sichtfeld | 58 | 28 | 30 |
| Davon beim Erscheinen wieder aus dem Blick geraten | 29 | 14 | 15 |
| Rechtzeitige Abfahrt eines freien Schiffs, das zum bisherigen Blick beitrug | 20 | 10 | 10 |
| Ein Halt von höchstens drei Zügen hätte den ersten echten Blick vorgezogen | 6 | 3 | 3 |
| Öffentlich gewählter Halt mit früherem Fund | 0 | 0 | 0 |
| Öffentlich gewählter Halt verpasst den Original-Erstblick in seinem Haltefenster | 2 | 0 | 2 |

Auf allen sechs mechanischen Gelegenheiten verlor die Mannschaft die Stelle schon im unmittelbar folgenden Originalzug vollständig aus der Sicht. Unter den ansonsten aufgezeichneten Flottenbewegungen hätte der geeignete Halt den Fund um **4, 7, 9, 10, 14 oder 44 Züge** vorgezogen. Der Median auf den sechs betroffenen Karten ist 9,5. Die rückblickend bestmögliche Wahl von Schiff und Zeitpunkt entspricht 0,55 Zügen über alle 160 Karten. Auf `162000462/P0` hätte etwa ein Halt ab Zug 48 das bei Zug 50 aktivierte Relikt sofort sichtbar gemacht. Die Originalflotte fand es erst bei Zug 94. Das ist der längste Vorsprung im Panel. [Alle tatsächlichen Zeitfenster und Alternativen](train/fenster.jsonl.gz)

Die öffentliche Regel wählte auf 141 Karten genau ein Schiff und einen Beginn zwischen Zug 20 und 48. Auf 97 davon lag der Beginn noch vor dem tatsächlichen Spawn und auf sechs fiel die Aktivierung in die folgenden drei Züge. Auf keiner dieser sechs Karten hielt die Regel das richtige Gebiet im Blick. Auf zwei weiteren Karten gegen V16 verpasste der öffentlich gewählte Halt einen ursprünglichen Fund während seines Dreizugfensters. Der weitere Verlauf einer aktiv geänderten Partie wurde nicht gespielt. [Vorab festgelegtes Verhalten](PLAN.md) · [Öffentliche Zielwahl](halten.py)

Für die 160 unveränderten Eröffnungen wurden 16.000 vollständige ursprüngliche Sichtmasken, die tatsächlichen Aktivierungszüge und die öffentlich gemeldeten Reliktfunde kontrolliert. Für jede mögliche Abreise im letzten Dreizugfenster mit vorherigem physischem Blick und für alle öffentlich bestellten Aufenthalte wurden die Sensoren der restlichen Flotte unverändert beibehalten. Die originale Kursfunktion und die unabhängige Rechnung stimmten auf 498 alternativen Sichtbildern überein. Auch eine großzügigere Annahme über das Überleben des festgehaltenen Sensors lieferte zusammen nur dieselben sechs Karten. [Kursvergleich](spawn.py) · [Unabhängige Nachrechnung](auswertung.py)

Die frühere Standsuche schickte ein bereits länger wartendes Schiff los. Hier wurde die Abfahrt eines bereits fahrenden Schiffs kurz verschoben, damit sein bestehendes Sichtfeld während eines möglichen Spawns erhalten bleibt. Drei der sechs Vorbedingungen wurden erreicht. Die benötigten acht Karten mit mechanischem Vorteil, vier öffentlich getroffene Spawnfenster und die Schutzbedingung gegenüber verlorenen Erstblicken wurden verfehlt. Die getrennten 48 Prüfpartien und aktive Gegenfortsetzungen wurden nicht geöffnet. [Frühere Standsuche](../standsuche/PLAN.md)
