# Bekannte Reliktgebiete schränken die Punktesumme ein

Wenn Sherlock alle in diesem Match möglichen Reliktpaare bereits gesehen hat, können die Punkte nur in deren bekannten 5×5-Gebieten liegen. Der öffentliche Gesamtpunktestand kann dadurch einen positiven Ort eindeutig machen, selbst wenn gerade viele eigene Schiffe auf der Karte verteilt sind.

| Originalkarten bei Sichtweite eins | Zusätzlich sichere, V16 noch unbekannte Punkte auf mindestens vier aufeinanderfolgenden Zügen | Davon mit freiem Schiff in höchstens vier Schritten |
|---|---:|---:|
| 160 Entwicklungskarten | 93 Karten | 68 Karten |
| 48 getrennte Prüfkarten | 27 Karten | 21 Karten |

Jeder positive und jeder aktuell negative Schluss wurde in sämtlichen 303 Beobachtungen jeder Karte mit der echten Spielwertung verglichen. Auf den 48 Prüfkarten ergab die Gebietsgrenze allein bereits alle 27 nutzbaren Karten. Aus der sichtbaren gegnerischen Belegung allein ergab sich dort keine vier Züge nutzbare Ergänzung. Die vorher festgelegte kombinierte Methode erfüllt ihre beiden Voraussetzungen. Im anschließenden aktiven Vergleich traf das erweiterte Feldwissen auf das ursprüngliche V16 und auf den Kandidaten, der allein aus eigenen Punktezuwächsen Felder erkennt. [Entwicklung](train.json) · [Getrennte Prüfung](valid.json) · [Vorab festgelegte Kriterien](PLAN.md)

## 480 ganze Spiele auf 48 neuen Sicht-1-Karten

Das erweiterte Wissen gewann 91/96 gegen Solution, genauso viele wie V16. Es rettete ein ursprünglich verlorenes Spiel und gab einen ursprünglichen Sieg ab. Das einfachere Feldwissen gewann auf den identischen Sitzen 93/96. Gegenüber dieser Variante gewann die Erweiterung kein bisher verlorenes Spiel und verlor zwei bisher gewonnene. Direkt gewann sie 46/96 gegen V16 (95-%-Kartenintervall 38,54–57,29 %) und 44/96 gegen das einfache Wissen (37,50–54,17 %). Der erweiterte Nachweis lieferte auf 58 Solution-Sitzen bestätigte Informationen und änderte auf 55 tatsächlich die Befehlsfolge. Mehr richtige Feldeinträge reichten hier nicht für mehr Siege. [Ergebnis nach vorab festgelegten Bedingungen](duell.json) · [480 vollständige Sitzverläufe](duell_karten.jsonl.gz)
