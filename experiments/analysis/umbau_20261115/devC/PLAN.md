# Gegenprobe der Schüler-Hybride auf Dev C (festgelegt am 17.11.2026, 03:13, vor dem ersten Spiel)

**Warum:** Auf Dev A liegen alle neuen Hybride 1 bis 2 Prozentpunkte über R3 (Solution und Kaggle zusammen). Dev A
wurde aber schon oft für Auswahlen benutzt. Dev C (Karten 7164000–7164099, beide Seiten) ist Mahmouds bisher
unbenutzter zweiter Entwicklungssatz. Er zeigt, ob der kleine Vorsprung auch auf neuen Karten auftaucht.

**Was gespielt wird** ([Skript](run_e.sh), eingefrorene Quelle `8324845`, 10 Prozesse, nach dem Ensemble-Lauf):

| Agent | Gegner |
|---|---|
| R3 (Abgabe, unverändertes Paket) | Solution, Kaggle |
| V15 (bisheriger Kandidat, SHA `28933a3b…`) | Solution, Kaggle, R3 |
| Hybrid v7L | Solution, Kaggle, R3 |
| Hybrid Ensemble v7 + v7L | Solution, Kaggle, R3 |

**Vorab festgelegte Leseregel:** Dev C ist keine Bestätigung. Ein Kandidat kommt nur dann für eine spätere
Bestätigung auf 7159000–7159399 in Frage, wenn er zwei Bedingungen erfüllt. Erstens liegt er auf Dev C gegen
Solution und Kaggle zusammen mindestens +2 Prozentpunkte über R3, gepaart nach Karte mit dem Werkzeug
[compare_dev.py](../tools/compare_dev.py). Zweitens liegt er gegen Solution nicht unter R3. Die Bestätigung müsste
vorher eigens festgelegt werden und braucht zusätzlich ein Ja von Mahmoud und Moayed. Ohne beides bleibt R3 die
Abgabe. Dev C wird nach dieser Gegenprobe nicht mehr für Auswahlen zwischen diesen Kandidaten verwendet.

**Nachtrag 17.11.2026, 03:38, vor dem ersten Dev-C-Ergebnis:** Zusätzlich spielt der reine Ensemble-Schüler v7 + v7L
(ohne V14, Schalter Stay-Bias 1,5 und Entstapeln) gegen Solution, Kaggle und R3 ([Skript](run_e2.sh)). Grund: Auf
Dev A gewann er 197/200 gegen Solution, 8/200 gegen Kaggle und 196/200 direkt gegen R3. Für ihn gilt dieselbe
Leseregel.

**Nachtrag 2, 17.11.2026, 05:58, vor dem ersten Dev-C-Spiel dieses Kandidaten:** Nach DAgger-Runde 5 spielt
zusätzlich der Hybrid aus dem Ensemble v8 + v8L (gepackt, SHA `f021f63d…`) auf Dev C gegen Solution, Kaggle und R3
([Skript](run_e3.sh)). Grund: Auf Dev A lag er gegen Solution und Kaggle zusammen +2,25 [−0,75; +5,25] Prozentpunkte
über R3 (Solution 198/200, Kaggle 10/200), der höchste Wert aller Schüler. Ausgewählt wurde er nur nach den
Dev-A-Zahlen. Es gilt dieselbe Leseregel. Einschränkung: Die R3-Zahlen auf Dev C sind schon bekannt, und er ist der
fünfte Kandidat auf diesen Karten. Ein Bestehen hieße deshalb nur, dass Mahmoud und Moayed eine frische Bestätigung
auf 7159000–7159399 festlegen können. Danach wird Dev C für keinen weiteren Kandidaten benutzt.
