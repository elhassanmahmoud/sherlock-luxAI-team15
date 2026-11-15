# Nachtraining verändert die Entscheidungen in beide Richtungen

Beide neuen Netze starteten mit demselben R3 und bekamen je 1.024 AdamW-Updates mit 256 Einheitsentscheidungen. Die Hälfte jeder Stichprobe bestand aus exakt denselben historischen Beispielen. Für die zweite Hälfte bekam R8 Lehrerbeispiele aus tatsächlich gespielten R3-Partien, die Kontrolle aus weiteren historischen Partien. Die gemeinsame Stichprobe wurde anhand der tatsächlich verarbeiteten Zeilen abgeglichen.

| Korrekte Lehrerbefehle | R3 | Historische Warmkontrolle | R8 |
|---|---:|---:|---:|
| 24 Karten mit R3-Stellungen, 160.863 Entscheidungen | 109.585 | 109.571 | **109.838** |
| 24 Karten mit älteren Stellungen, 156.243 Entscheidungen | 98.938 | **99.296** | 98.774 |

R8 gewinnt auf den neuen Stellungen netto 253 richtige Befehle gegenüber R3 und 267 gegenüber der Kontrolle hinzu. Auf dem älteren Satz verliert es 164 gegenüber R3. Das verfehlt eine der drei vorab festgelegten Bedingungen. R8 geht daher in diesem Versuch nicht in den Spielvergleich.

Für den Vergleich bekamen die drei Netze dieselben gespeicherten Zahlen. Der gespeicherte, seinerzeit wirklich ausgeführte R3-Befehl weicht in 164 von 160.863 neuen Zeilen vom auf komprimierten Eingaben rekonstruierten R3 ab. Verglichen mit den tatsächlich gespielten Befehlen bleibt R8 dort mit 247 zusätzlichen richtigen Aktionen vorn. Alle 96 Sitzarchive wurden nachgezählt. Die Trainingsgewichte und ihre Herkunft lassen sich auch für die Weiterarbeit laden.

[Auswertung pro Karte](validation.json) · [Trainierter R8](../../candidates/r8_warm_20261115/r8.pth) · [Trainierte Kontrolle](../../candidates/r8_warm_20261115/control.pth) · [Versuchsplan](PLAN.md)
