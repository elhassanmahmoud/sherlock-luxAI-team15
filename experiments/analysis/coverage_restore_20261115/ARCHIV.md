# Wie oft R2 ein eigenes Punktefeld ungedeckt lässt

Auf zwölf Diagnosekarten (beide Spielseiten, 7.200 Zugbilder) haben wir die Befehle des neuen Schülers R2 mit dem tatsächlich gespielten R1 verglichen. Als Ausgangspunkt dient jeweils dieselbe aufgezeichnete Spielstellung. Gesucht wird ein einziger ausführbarer eigener Zug, der die geplante letzte Deckung eines bestätigten Punktefelds wiederherstellt und die Deckung anderer eigener Felder erhält. Ein sichtbarer Gegner in Schussreichweite schließt die Wiederherstellung auf diesem Feld aus.

| Gegner der aufgezeichneten Partie | Wiederherstellbare Feld-Zug-Paare R1 | R2 |
|---|---:|---:|
| Solution_92 | 121 | 239 |
| Kaggle, nativer Drittplatzierter | 74 | 128 |
| V14 | 126 | 202 |
| Gesamt | 321 | 569 |

R2 zeigte auf jeder der zwölf Karten mindestens eine Gelegenheit. Keine Wiederherstellung entfernte die geplante letzte Deckung eines anderen Punkts. Zur Kontrolle ließen sich die 8.035 abweichenden Befehle des tatsächlich gespielten R1 und seine 321 Wiederherstellungen nachbilden. Bei der Hauptauswertung wurde jede beobachtete gegnerische Einheit als mögliche Bedrohung gezählt. Das ist konservativ, weil die gespeicherte Kartenebene Energie null und negative Energie nicht zuverlässig trennt.

Ein Feld kann im nächsten Zug durch Treffer oder eine Kollision trotzdem verloren gehen. Auch die späteren Züge ändern sich mit der gegnerischen Reaktion. Deshalb bewertet der folgende reale Vergleich vollständige Spiele gegen dieselben Gegner.

[Plan und Entscheidungsregel](PLAN.md) · [Bericht je Spiel und Eingabeprüfsummen](r2_archive/summary.json) · [Einzelne wiederherstellbare Felder](r2_archive/fields.jsonl).
