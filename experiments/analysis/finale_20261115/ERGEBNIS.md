# Drei Ansätze für Energie und Bewegung

Vergleich vom 15. November, Quelle `915736b`. Für jeden Agenten zwölf neue Karten, beide Seiten, native Einstellung des Kaggle-Gegners und Solution_92. Insgesamt 192 vollständige Partien über je drei Matches. Dazu kamen 24 getrennte Spiele zum Lernen und Diagnostizieren der Scout-Bewegungen. Beide V14-Gewichte hatten vor und nach dem Vergleich denselben SHA-256-Wert `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.

| Agent | Ganze Siege gegen Kaggle | Ganze Siege gegen Solution | Gewonnene Matches Kaggle / Solution (je 72) |
|---|---:|---:|---:|
| V14 | 2/24 | 24/24 | 6 / 68 |
| Früher tanken und gemeinsam schießen bei Energierückstand | 2/24 | 21/24 | 4 / 60 |
| Bewegungen zum Schutz der Energiereserve | 0/24 | 24/24 | 4 / 68 |
| Gelernte Scout-Bewegungen | 2/24 | 23/24 | 6 / 64 |

Auf keinem einzelnen Spielschlüssel (Karte, Gegner und Sitz) hat eine der drei Varianten eine Niederlage von V14 in einen Sieg verwandelt. Der Tankmodus wurde in allen 24 Kaggle-Spielen und in sechs Solution-Spielen aktiviert. Die Kontaktregel änderte 512 Bewegungen gegen Kaggle und 24 gegen Solution, der gelernte Scout 1.092 bzw. 1.044. Diese drei Mechanismen kamen also tatsächlich zum Einsatz. Der kleine Kartensatz erlaubt keine genaue allgemeine Siegquote. Keiner der drei Agenten erreicht die vorher festgelegte Auswahlbedingung, deshalb kein weiterer Bestätigungsblock und keine neue Abgabe.

[Vergleichsregeln](VERGLEICH.md) · [Geprüfte Schlüssel und Resultate](selection/selection.json) · [Modell und Diagnose](../final_learning_20261115/ERGEBNIS.md). Die vier Unterordner in `selection/` enthalten Einzelspiele, Quellenprüfsummen und Abschlussdateien. Nachrechnung mit:

```sh
python -m scripts.final_battle_select --root experiments/analysis/finale_20261115/selection --diagnosis experiments/analysis/final_learning_20261115/diagnosis.json
```
