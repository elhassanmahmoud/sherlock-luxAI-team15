# Entwicklungsmessung vom 20.10.2026

Fünf vorab festgelegte Einstellungen, jeweils 60 Karten (500720–500779), beide
Seiten, default und Solution_92: **240 Spiele pro Einstellung, 1.200 insgesamt**.
Kein Training; derselbe Checkpoint `all18_v3` und Code `975b3aa` für alle Läufe.
Quellen: `development_state.json`, `development_report.json` und die fünf
`dev_*.csv` unter `experiments/compare/autonomous_20261020/`.

| Variante | Siege default | Siege Solution_92 | Differenz zu V3 | 95%-Intervall der Differenz |
|---|---:|---:|---:|---:|
| V3 unverändert | 120/120 | 102/120 (85,00 %) | Referenz | – |
| Sap-Reserve 30 | 120/120 | 101/120 (84,17 %) | −0,83 pp | [−5,83; +4,17] pp |
| Sap-Reserve 60 | 120/120 | 96/120 (80,00 %) | −5,00 pp | [−12,50; +2,50] pp |
| Gegnerdistanz 6 | 120/120 | 101/120 (84,17 %) | −0,83 pp | [−5,00; +3,33] pp |
| Gegnerdistanz 14 | 120/120 | 100/120 (83,33 %) | −1,67 pp | [−6,67; +3,33] pp |

Auswahlmetrik: mittleres `result` (Sieg 1, Remis 0,5, Niederlage 0). Hier keine
Remis. Gepaarter Bootstrap über ganze Karten, jeweils beide Seiten gemeinsam,
5.000 Wiederholungen, Zufallsseed 0, wie in `scripts.compare_report`.
Alle 240 Schlüssel pro Datei, beide Seiten und Punktzählversion 2 wurden geprüft;
keine unvollständigen Zeilen oder fehlenden Karten. Beide Abgabegewichte und V3
blieben bytegleich.

**Entscheidung:** Keine Variante übertrifft V3. Nach der vorab festgelegten Regel
wird kein Herausforderer ausgewählt. Die Intervalle enthalten jeweils null:
Auch eine sichere Verschlechterung ist mit diesen Stichproben nicht belegt.
Diese bereits wiederholt verwendeten Entwicklungskarten sind kein unabhängiger
Nachweis einer allgemeinen Siegquote.

**Nächster Vergleich:** Wegen Moayeds neuer Freigabe wird ausschließlich der
bereits vorhandene Kandidat V3 gegen die gesicherte alte Abgabe `old3_sym3`
auf dem reservierten neuen Block 502420–502619 geprüft. Diese Auswahl erfolgt
vor Sichtung des Blocks. Ein verbesserter Abgabestand wäre zunächst die Übernahme
von Mahmouds bereits entwickeltem Kandidaten, keine erfolgreiche neue Variante
aus dieser Messreihe.

Der letzte Lauf dauerte 585 Sekunden statt rund 170 Sekunden für die Referenz.
Die mediane Zeit pro Spiel stieg von 1,38 auf 4,24 Sekunden; beide Worker liefen
und der Lauf endete regulär. Der Mac verwendete anschließend rund 6,8 GB Swap.
Das ist ein Hinweis auf Ressourcenknappheit, kein Beleg für eine bestimmte
Ursache oder einen spielerischen Unterschied. Laufzeiten werden deshalb nicht
als isolierter Geschwindigkeitsvergleich der Varianten interpretiert.
