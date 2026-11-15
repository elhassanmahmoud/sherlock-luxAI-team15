# R7 schützt mehr richtige V14-Befehle

R7 ist ein einzelnes Bewegungsnetz mit 85 Eingaben. Es sieht den letzten tatsächlich ausgeführten Befehl der Einheit und lernte zusätzlich aus den relativen Bewegungsbewertungen des Lehrers. Fünf Epochen, 958.870 ausführbare Lernzeilen je Epoche, davon 656.134 mit weichen Bewegungszielen. Für die Auswertung wurde die letzte Epoche verwendet.

| 24 gemischte Diagnosekarten | R3 | R5 | R7 |
|---|---:|---:|---:|
| Richtige V14-Befehle nach Eingriff verloren | 2.343 | 3.181 | **2.252** |
| Frühere V14-Fehler korrigiert | 18.700 | **20.662** | 19.687 |
| Netto zusätzliche Lehrerübereinstimmungen | 16.357 | **17.481** | 17.435 |

R7 erzielt 1.078 mehr Nettoübereinstimmungen als R3. Gegenüber R5 fehlen 46 der zuvor für die Spielauswahl verlangten 17.481. Auf den acht älteren Karten sind es netto +4.702 gegenüber V14 (R3 +4.634, R5 +4.885). Die Gewichte sind separat gesichert. Der Spielvergleich auf 7284000 wurde nicht gestartet. Über R7s tatsächliche Siegquote liegt deshalb keine Aussage vor. [Trainiertes Netz](../../candidates/movement_dagger_20261115/r7_soft_own_command.pth) · [Tatsächliches Trainingslog](train.log) · [64 Sitzprotokolle und Zulassungsentscheidung](paired_validation.json) · [Vorheriger Plan](PLAN.md).
