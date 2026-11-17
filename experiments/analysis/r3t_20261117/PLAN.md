# Test der Taktikschicht über R3 (festgelegt am 17.11.2026 vor dem ersten Testspiel)

**Was getestet wird:** Die neue Taktikschicht `agents/sherlock_r3t/` setzt auf die fertigen Befehle des
unveränderten R3-Pakets auf und ändert einzelne Units. Grundlage ist die
[Energie- und Todesanalyse](../r3_kaggle_20261117/ERGEBNIS.md). Ohne Schalter spielt sie exakt wie R3 (geprüft auf
12 Spielen, alle Spalten gleich).

| Variante | Schalter | Idee |
|---|---|---|
| R3 | – | Referenz, unverändertes Paket (`r3zip:`) |
| GRANATE | `r3t:granate` | Schüsse nach erwartetem Schaden samt Streuung auf vorhergesagte Positionen, im Team abgestimmt, Abschüsse zählen extra; stehende Units mit Reserve feuern zusätzlich |
| SOG | `r3t:sog` | Züge meiden, die durch Sog oder Zusammenstoß mit stärkeren Gegnern wahrscheinlich tödlich sind |
| TANKEN | `r3t:tanken` | wartende Units ohne Punktefeld ziehen auf ein deutlich besseres Energiefeld nebenan |
| ALLE | `r3t:granate,sog,tanken` | alle drei zusammen |

**Karten:** Dev D = 7256100–7256199, beide Seiten, bisher von niemandem benutzt (aus Mahmouds Bereich ab 7253000).
Gegner Solution und Kaggle, je Variante 400 Spiele, zusammen 2.000. Eingefrorene Quelle (Commit dieses Plans),
10 Prozesse, streng nacheinander ([Skript](run_screen.sh)).

**Vorab festgelegte Leseregel:** Gepaart nach Karte gegen R3 (10.000 Ziehungen, Seed 2711,
[compare_dev.py](../umbau_20261115/tools/compare_dev.py)). Eine Variante gilt als **vielversprechend**, wenn

1. sie gegen Solution und Kaggle zusammen mindestens +2 Prozentpunkte gewonnene Spiele über R3 liegt **oder** ihr
   Punkteanteil gegen Kaggle (eigene Punkte durch alle Punkte, je Karte gepaart) mindestens 3 Prozentpunkte über R3
   liegt, und
2. sie gegen Solution im Mittel nicht mehr als 1 Prozentpunkt unter R3 liegt.

Vielversprechende Varianten und ihre Kombinationen gehen in eine zweite Prüfung auf frischen Karten 7256200–7256399
mit derselben Regel. Erst danach käme eine frische Bestätigung auf 7159000–7159399 in Frage, die vorher eigens
festgelegt wird und ein Ja von Mahmoud und Moayed braucht. Bis dahin bleibt R3 die Abgabe. Dev D wird nach diesem
Test nur noch für Varianten benutzt, die hier ausdrücklich nachgetragen werden.

Zur Erklärung (nicht zur Auswahl) läuft für jede Variante zusätzlich die Energie- und Todesanalyse auf den
Analysekarten 7256000–7256029 gegen Kaggle.

**Nachtrag 1, 17.11.2026, 07:27, vor dem ersten Dev-D-Spiel dieser Varianten:** Vier weitere Taktiken aus Mahmouds
Liste laufen nach dem ersten Durchgang mit derselben Leseregel auf Dev D ([Skript](run_screen2.sh)):

| Variante | Schalter | Idee |
|---|---|---|
| NEBEL | `r3t:granate,nebel` | Granaten auch auf unsichtbare Halter: Erklärt der Punktgewinn des Gegners mehr besetzte Punktefelder als sichtbar, gelten die unsichtbaren Punktefelder als besetzt |
| EROBERN | `r3t:erobern` | eine Unit ohne eigenes Punktefeld zieht auf das Feld eines schwächeren gegnerischen Halters daneben (Zusammenstoß zerstört ihn) |
| SPAREN | `r3t:sparen` | Halter feuern nicht, wenn danach weniger als ein Schuss Energie bleibt, außer bei sicherem Abschuss |
| WECHSEL | `r3t:wechsel` | ein schwacher Halter tauscht mit einer starken eigenen Unit daneben, das Feld bleibt besetzt |

**Nachtrag 2, 17.11.2026, 07:52, vor dem ersten Dev-D-Spiel dieser Varianten:** Der Imitations-Schüler aus DAgger-Runde 5
(Ensemble v8 + v8L) spielt jetzt auf R3 statt auf V14: Units mit sichtbarem Gegner im Umkreis 5 und Units ohne
Punktefeld-Aufgabe spielen den Schüler, die übrigen R3 (wie der Hybrid "mixed"). Gleiche Leseregel, Dev D, nach dem
zweiten Durchgang ([Skript](run_screen3.sh)):

| Variante | Schalter | Idee |
|---|---|---|
| SCHUELER | `r3t:schueler=ens8` | R3 + Schüler im Kampf und ohne Punktefeld-Aufgabe |
| SCHUELER_ALLE | `r3t:schueler=ens8,granate,sog,tanken` | dazu die drei Taktiken des ersten Durchgangs |
| HYB_ENS8 (Vergleich) | gepackter Hybrid V14 + Ensemble v8 + v8L (SHA `f021f63d…`) | bisheriger Schüler-Hybrid auf denselben Karten |
