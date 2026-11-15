# V14 gegen den Kaggle-Platz-3-Agenten (15.11.2026)

**Anlass:** Im Battle vom 06.11. wurde Sherlock Dritter; im Halbfinale verlor es 0:3 gegen den späteren Zweiten.
Laut Mahmoud spielten Platz 1 und 2 koordiniert, schossen unsere Units gezielt ab und eroberten unsere Felder.
Gegen Solution_92 (rund 95 % Siege) sieht man diese Schwächen nicht mehr. Deshalb haben wir einen deutlich
stärkeren Testgegner eingebunden.

**Testgegner:** lux3-bot 0.4.8_fn, Platz 3 im Kaggle-Wettbewerb Lux AI Season 3. Er lernte per Imitation
Learning aus Replays starker Kaggle-Teams (zwei U-Nets). Lizenz Apache-2.0, Quelle
[andreyd41/lux3-bot](https://github.com/andreyd41/lux3-bot/releases/tag/0.4.8). Laden und prüfen mit
`python -m scripts.fetch_kaggle3` (SHA-256 des Archivs und beider Gewichte sind festgelegt); er landet im
gitignorierten Ordner `experiments/opponents/` und wird **nie Teil der Abgabe**. Ausgeführt erst nach
Mahmouds ausdrücklicher Freigabe (15.11.).
Im Kursformat ist er Gegner `kaggle3` in `scripts.common.make_opponent`. Er läuft mit seiner nativen
Einstellung `NUM_MATCHES_IN_GAME = 5`. Mit 3 hält er das Spiel nach zwei Matchsiegen für entschieden und
spielt Match 3 im Sparmodus (`GameOverParams`).

**Kartensätze (vor den Messungen festgelegt):** Dev A `seeds_devA.json` 7150000–7150099 (Auswahl),
Dev B `seeds_devB.json` 7151000–7151099 (zweite Prüfung ausgewählter Varianten),
Bestätigung `seeds_confirm.json` 7158000–7158399 (zurückgehalten bis zur Entscheidung). Jede Karte wird auf
beiden Seiten gespielt.

## Befund: Wie V14 verliert

| Messung | Ergebnis |
|---|---|
| `v14_devA.csv` (Dev A, 200 Spiele je Gegner; Gegner noch mit 3 Matches, also Sparmodus in Match 3) | gegen kaggle3 **6/200 Spiele (3 %)**, gegen Solution_92 auf denselben Karten 94 % |
| `screen1/baseline.csv` (Dev A, Gegner mit nativen 5 Matches) | 4 % Spiele, 5 % Matches, 29 % Punkteanteil |
| `trace_v14_k3_first20.csv` (20 Karten, Sparmodus) | Match 1: 0/40 gewonnen (Punkte 82:275), Match 2: 2/40 (224:461), Match 3: 40/40 nur wegen des Sparmodus |
| `trace_v14_k3_30maps.csv` (30 Karten, nativ) | Match 1 0/60, Match 2 0/60, Match 3 4/60 gewonnen |

In Match 1 (30 Karten, 60 Spiele) verliert V14 im Mittel **23 Units, der Gegner 1,2**. Am Matchende hat
V14 rund 400 Energie in allen Units zusammen, der Gegner rund 3.350. Er schießt etwa 29-mal pro Match,
V14 11-mal. Den ersten Punkt holt V14 sogar etwas früher (Median Schritt 39 gegen 43).

Die Zahlen für verlorene Units in Match 2/3 in `trace_v14_k3_30maps.csv` enthalten noch einen Zählfehler:
Units, die beim Matchwechsel verschwinden, wurden als Tote gezählt. `scripts/match_trace.py` ist korrigiert;
die Werte für Match 1 betrifft das nicht.

`tools/death_energy.py` (12 Karten, 24 Spiele, nativ):
- Mittlere Energie pro lebender Unit in Match 1, Sherlock gegen Kaggle: Schritt 10: 91 : 103,
  Schritt 30: 74 : 130, Schritt 50: 82 : 171, Schritt 99: **49 : 215**.
- Todesursachen unserer Units (Näherung aus Positionen und Aktionen beider Seiten): Kollision mit einer
  stärkeren Unit 29 %, Beschuss 13 %, Energie-Sog 9 %, nicht zugeordnet 49 %. Darin stecken noch die
  Scheintode beim Matchwechsel, rund 14 pro Spiel. Laut Spezifikation können nur gegnerische Units Energie
  unter 0 drücken, Nebel und Energiefelder nicht.

**Schluss:** Der Gegner gewinnt über Energie. Wer mehr Energie hat, gewinnt Kollisionen, saugt Nachbarn aus
und kann öfter schießen. Mehr Schüsse helfen V14 erst, wenn genug Energie da ist.

## Werkzeuge

- `scripts/match_trace.py`: eine Zeile pro Match mit Punkten, Sieger, erstem Punkt, verlorenen Units,
  Schüssen, lebenden Units und Energie am Ende (nur Messung).
- `scripts/variant_compare.py`: Varianten gegen eine Referenz, gepaarter Bootstrap über Karten, mit
  Spielen, Matches und Punkteanteil.
- Screens: `screen1/` testet vorhandene Schalter, `screen2/` die neuen Kampftechniken aus
  `agents/sherlock/combat.py`. Beide liefen auf eingefrorenen Kopien des Codes. Ergebnisse folgen nach
  Abschluss.
