# Der unmittelbare Punktegewinn bestätigt sich, ein Gesamtsieg geht verloren

Die unabhängige Bestätigung auf 120 weiteren Sicht-1-Karten und 720 vollständigen Partien zeigte 28 zusätzliche eigene Punkte auf dem geänderten Zug. Das entspricht 0,117 Punkten pro gepaartem Sitz [0,071; 0,167]. Direkt gegen Original-V16 gewann die Feldprobe 123/240 Spiele (51,25 Prozent [47,50; 55,00]). Gegen Original-Solution gewann sie 231/240, das ursprüngliche V16 auf denselben Sitzen 232/240. Karte 162800176 P0 wechselte von Sieg zu Niederlage. Damit verfehlt die Feldprobe eine der fünf Bestätigungsbedingungen. Die ungefilterte allgemeine Prüfung entfällt. [Vollständige Bestätigung](bestaetigung/sicht1/ERGEBNIS.md) · [Zugweiser Vergleich des verlorenen Sitzes](bestaetigung/verlust/ERGEBNIS.md)

## Vorangegangene Auswahl auf 48 Karten

Auf 48 neuen Sicht-1-Karten gewann die gelernte Feldprobe gegen Original-Solution 88 von 96 ganzen Spielen. Original-V16 gewann dieselben 88 Sitze. Im direkten Vergleich gewann die Feldprobe 48 von 96 Partien, das 95-Prozent-Kartenintervall beträgt 43,75 bis 56,25 Prozent. Damit erreicht sie die vorab festgelegten Auswahlgrenzen und qualifiziert sich für die unabhängige Bestätigung.

| Auswahlmaß | Ergebnis |
|---|---:|
| Ganze Siege gegen Solution, Original-V16 und Feldprobe | jeweils 88/96 |
| Gesamtsiegdifferenz gegen Solution, gepaart | 0,00 Prozentpunkte [0,00; 0,00] |
| Direkte Siege gegen Original-V16 | 48/96 |
| Eigene Zusatzpunkte unmittelbar auf dem geänderten Zug | +11 über 96 Sitze |
| Mittlere unmittelbare Zusatzgutschrift pro Sitz | +0,115 [0,042; 0,198] |
| Geänderte Sitze gegen Solution / gegen V16 | 28/96 / 28/96 |
| Am tatsächlichen Ziel gepunktet gegen Solution / V16 | 13/28 / 19/28 |

Von den 28 Solution-Eingriffen verbesserte sich die tatsächliche unmittelbare eigene Gutschrift bei elf, bei 17 blieb sie gleich. Ein erreichtes Punktefeld ergibt nur dann einen zusätzlichen Mannschaftspunkt, wenn sich die Mannschaftssumme gegenüber der echten V16-Referenz erhöht. Auf keinem Sitz sank die unmittelbare eigene Gutschrift. Die gegnerische Gutschrift blieb auf diesem Zug in allen Fällen gleich. Gegen Solution gewann Original-V16 89, 85 und 83 einzelne Matches in den drei Runden. Die Feldprobe gewann dort 89, 85 und 84, direkt gegen V16 waren es 45, 49 und 49.

Eine unabhängige Nachrechnung verglich sämtliche 288 archivierten Spiele mit den 288 endgültigen Einzeldateien. Für jeden Sitz wurden drei Matchwertungen aus 303 tatsächlichen Punkteänderungen und der Gesamtsieg rekonstruiert. Bei einem Eingriff gegen Solution stimmen die Befehlsprüfsumme beider Seiten vor dem Zug und sämtliche bisherigen Gutschriften mit dem zugehörigen Originalspiel überein. Auf Sitzen ohne Eingriff stimmen die vollständigen Befehlsprüfsummen und Punkteprofile überein. Der laufende Monitor verglich auf jedem Kandidatenzug alle 16 eingesandten Befehle mit dem ursprünglichen V16-Vorschlag. Das Auswahlarchiv enthält diese Prüfsummen, die Einzelheiten des einen Wechsels und alle Punkteschritte. Ein vollständiger nachträglicher Vergleich jeder einzelnen Befehlszeile allein aus diesem Archiv erfordert die Wiederholung der Partie.

Ein technischer Erststart endete im gemeinsamen Monitor mit der Meldung „Candidate skipped V16 proposal“. Nur die zwei Originalkontrollspiele auf Karte 162400000 wurden zuvor gespeichert. Diese beiden Dateien liegen unter einer anderen Quellenidentität im separaten Erstlauf. Die abschließenden 288 Spiele stammen vollständig aus dem neu gestarteten Lauf.

Der ursprüngliche Vergleich steht in `duell.json` und `ganze_partien.jsonl.gz`, die unabhängige Nachrechnung in `bestaetigung/auswahl_nachweis.json`. Eigen- und Gegnersicht sowie die Spiele auf beiden Startplätzen sind jeweils getrennt ausgewiesen. Die zweite Stufe verwendet zusätzliche Karten gemäß `bestaetigung/PLAN.md`.
