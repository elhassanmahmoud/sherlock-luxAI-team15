# Auf dem geretteten Solution-Sitz kippte der Feldbesitz im dritten Match

Alle acht Pilot-Sitze mit verändertem ganzen Gewinner wurden auf beiden Wegen erneut bis zum letzten Zug ausgespielt. Alle 16 Befehlsfolgen waren bytegleich zu den ursprünglich aufgezeichneten Pilotpartien. Die Prüfung rekonstruierte 2.770 Zustände nach der ersten Befehlsabweichung mit der echten Wertungsmaske. In jedem Zug erklärten die unterschiedlichen besetzten Punktefelder die öffentliche Gutschrift beider Teams vollständig. Die acht Fälle sind nach ihrem Ausgang ausgewählte Diagnosen. [Festlegung der Nachprüfung](DIAGNOSEPLAN.md) · [Wertungen jedes Weltfelds und öffentliche Punktekenntnis](ursachen/wertungen.jsonl.gz)

## Der zusätzliche Sieg gegen Solution

Auf `163420124/P0` kannte V16 das freie Punktefeld `(1,6)` bereits aus M1. In M2-Zug 25 wollte Schiff 5 warten. R3 schlug einen Schritt nach unten vor. Danach steuerte wieder V16 das ganze Team. Nach sechs Aktionen stand es in beiden Verläufen 23:44, nach zwölf 29:60. Vom Eingriff bis M2-Ende erhielt das Team drei zusätzliche Gutschriften auf `(1,6)`. Der Schlussstand verschob sich von 191:354 auf 206:385. Beide Verläufe verloren M2.

Am ersten aktiven Zug von M3 enthielt V16s öffentliche Punktekarte nach dem Eingriff zehn positive Felder, im Original acht. Hinzu kam ein echtes Spiegelpaar bei `(12,2)` und `(21,11)`. Die Wertungen im dritten Match veränderten sich besonders in einem Gebiet, das zuvor der Gegner besetzt hatte.

| Weltfeld | Original-M3, eigene / gegnerische Gutschriften | Nach dem Eingriff, eigene / gegnerische Gutschriften |
|---|---:|---:|
| (12,2), zu M3 zusätzlich bekannt | 0 / 33 | 41 / 0 |
| (21,11), zugehöriges Spiegelfeld | 0 / 49 | 0 / 49 |
| (10,3) | 0 / 20 | 44 / 0 |
| (9,3) | 0 / 25 | 35 / 0 |
| (1,6), ursprüngliches R3-Ziel | 82 / 0 | 78 / 0 |

M3 endete im Original 310:724, im veränderten Verlauf 521:512. Der Unterschied im Nettostand betrug +423, zusammengesetzt aus 211 zusätzlichen eigenen und 212 entfallenen gegnerischen Punkten. Der kausale Eingriff war der einzelne Befehl in M2. Die zwei vollständigen Verläufe zeigen gemeinsam verändertes Wissen, eigene Bewegungen und Reaktionen von Solution. Ihr jeweiliger Anteil am späteren Gebietserfolg ist damit noch offen. [Alle Felddifferenzen](ursachen/ergebnis.json)

## Sieben direkt gekippte Partien

Pro Karte sperrt der verlorene native Auftakt auf einem der beiden Sitze jede Beratung. Diese Partie enthält deshalb eine tatsächlich ausgespielte vollständige Selbstspielspur von Original-V16. Auf neun Karten ohne Eingriff auf beiden Sitzen waren beide vollständigen Befehls-Hashes identisch. Für alle sieben Karten mit verändertem ganzen Gewinner wurde das reine V16-Selbstspiel zusätzlich aus der Perspektive des ursprünglich siegreichen M1-Sitzes wiederholt. Die absoluten Befehlsreihenfolgen waren auch dabei identisch. Über alle 32 Karten gewann die Beratung gegenüber diesen echten nativen Verläufen ein direktes Spiel zusätzlich und gab sechs ab. In M2 gewann sie eines dazu und gab neun ab. In M3 gewann sie vier dazu und gab fünf ab. [Vollständige Gegenpaare](pilotpruefung/spiele.jsonl.gz) · [Wiederholte Quellenprüfung](ursache.py)

| Karte / Sitz | Ganze Partie | Nettodifferenz nach zwölf Aktionen | Am Ende von M2 | Am Ende von M3 |
|---|---:|---:|---:|---:|
| 163420023 / P0 | verloren | +10 | −112 | −45 |
| 163420032 / P0 | verloren | +2 | −98 | −293 |
| 163420051 / P0 | verloren | +9 | −28 | −102 |
| 163420070 / P0 | verloren | 0 | −18 | +24 |
| 163420082 / P0 | gewonnen | +3 | −26 | +264 |
| 163420111 / P1 | verloren | −3 | −286 | −70 |
| 163420127 / P0 | verloren | 0 | −11 | −73 |

Die letzte Spalte betrifft nur das dritte Match, dessen Punktestand neu beginnt. Auf allen sieben nach ganzem Gewinner ausgewählten Direktkarten war der Nettostand am Ende des zweiten Matches schlechter als auf der nativen Kontrollspur. Vier dieser Fälle hatten nach zwölf Aktionen einen Vorsprung, zwei standen noch gleichauf. Auf dem einzigen geretteten Direktsitz kam der ganze Sieg ebenfalls erst in M3 zustande. Die mittlere Zwölf-Züge-Wirkung über die unabhängigen 64 Mechanikkarten bleibt davon getrennt. [Mechanischer Vergleich aller Karten](GEGENFENSTER.md)
