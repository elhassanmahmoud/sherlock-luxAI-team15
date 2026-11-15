# Umbau: Sherlock lernt vom Kaggle-Platz-3-Agenten (ab 15.11.2026)

**Auftrag (Mahmoud, 15.11.):** großer Umbau, „neue starke Version“; bei Erfolg heißt sie V15.
**Plan mit vorab festgelegten Hürden:** [docs/superpowers/plans/2026-11-15-umbau-imitation.md](../../../docs/superpowers/plans/2026-11-15-umbau-imitation.md).
**Warum:** Gegen den Kaggle-Platz-3-Agenten gewinnt V14 nur 4 % der Spiele. 17 Handregel-Varianten und ein
Orakel mit allen Punktefeldern änderten daran nichts ([Befund](../kaggle3_20261115/README.md)).

## Was gleich bleibt, was neu ist

| Teil | V14 | Umbau |
|---|---|---|
| Gedächtnis (Relics, Punktefelder, Nebel, Drift, Symmetrie) | ja | **gleich**, dieselbe Konfiguration |
| Eingaben | 79 Merkmale je Unit | dieselben 79 Merkmale **plus 16 Kartenebenen** (ganze Karte) |
| Entscheidung | 36 DQN-Netze, Q-Werte gemittelt, dann Regeln | **ein CNN** (`ImitationNet`) wählt die Aktion je Unit |
| Schussziel | Heuristik, nur sichtbare Gegner | **gelernte Zielkarte**, auch in den Nebel |
| Lernsignal | eigene Belohnung (Reinforcement Learning) | **Imitation Learning:** Züge des Lehrers nachahmen, danach DAgger |
| Kursschnittstelle | `Agent_x` | **gleich**; `Agent_x` spielt Checkpoints mit `kind=imitation` über `ImitationAgent` |

Der Lehrer (lux3-bot 0.4.8_fn, Apache-2.0) wird nur als Lehrer und Testgegner benutzt und nie verpackt.
Das Agentenpaket `agents/sherlock/` importiert weder `scripts/` noch den Lehrer.

## Daten (Trainingskarten ab 7200000, getrennt von Dev A/B und Bestätigung)

| Runde | Spiele | Gegner des Lehrers | Unit-Entscheidungen | Lehrer gewinnt |
|---|---:|---|---:|---|
| `k3_b1` | 400 | 50 % er selbst, 25 % V14, 25 % Solution_92 | 1,87 Mio. (davon 8 % Validierung) | 107/108 gegen V14, 77/78 gegen Solution_92 |
| `k3_b2` | 800 | wie b1 | 4,17 Mio. | |
| `k3_b3` | 600 | 40 % er selbst, je 30 % V14 und Solution_92 | 3,02 Mio. | |

Prüfung der Labels: Über 99 % der aufgezeichneten Lehrer-Bewegungen passen auf beiden Seiten zur tatsächlichen
Positionsänderung (Spiegelung für player_1 korrekt). Der Lehrer schießt bei 2,4–3,8 % der Unit-Entscheidungen;
41 % seiner Schüsse treffen Felder ohne für Sherlock sichtbaren Gegner, viele auf 5–7 Felder Entfernung.
Er verschießt am Matchende kaum Restenergie (3 % in den letzten Schritten, obwohl 82 % der Units könnten).

## Schüler

| Version | Daten | Validierung (gleicher Zug / Schussziel genau / ±1 Feld) |
|---|---|---|
| v1 | b1 (1,87 Mio.), alter Trainer | 81,8 % / 74 % / 91 % |
| v2 | b1+b2+b3 (8,4 Mio. ausführbare Befehle), gemeinsamer Trainer | 82,2 % / 76 % / 91 % |
| v3 | wie v2 plus DAgger-Runde 1 (400 Spiele, 1,36 Mio., Lehrer mit gespielter Zughistorie) | 79,8 % / 75 % / 91 % (Validierung enthält DAgger-Lagen) |

## Spieltests auf Dev A (100 Karten, beide Seiten; Referenz V14 auf denselben Karten)

| Agent | default | Solution_92 | Kaggle-Agent | direkt gegen V14 |
|---|---:|---:|---:|---:|
| **V14** | 100 % | **94 %** | **4 %** | – |
| v1 pur | 95,5 % | 51 % | 0 % | 42 % |
| v2 pur | – | 49,5 % | 2 % | – |
| v2 + Stay-Bias 1,0 + Entstapeln | – | 75 % | 2 % | – |
| v2 + Stay-Bias 1,5 + Entstapeln | – | 78 % | 1 % | – |
| v2 + Stay-Bias 2,0 + Entstapeln | – | 69,5 % | 3 % | – |
| **v3 (DAgger 1) + Stay-Bias 1,5 + Entstapeln** | – | **89,5 %** | 2 % (Matches 5,3 %) | – |
| Hybrid v2 points | – | 90,5 % | 2 % (Matches 5,0 %) | – |
| Hybrid v2 combat (Radius 5) | – | 97 % | 3 % (Matches 6,7 %) | – |
| Hybrid v2 sap | – | 88 % | 1 % (Matches 3,3 %) | – |
| **Hybrid v3 points** | – | **97 %** (Matches +4,3 pp [+0,7; +8,2]) | **3 % (Matches 7,0 %, +2,0 pp [−0,7; +4,7])** | – |

Bei den Hybrid- und v3-Zeilen gelten für den Schülerteil Stay-Bias 1,5 und Entstapeln. Alle Werte stammen aus der
Auswahl auf Dev A und sind deshalb nach oben verzerrt; bestätigt wird erst auf dem zurückgehaltenen Satz.

**Diagnose (Match-Verläufe gegen Solution_92, 20 Karten):** Der Schüler kämpft und überlebt wie der Lehrer:
In Match 1 verliert er im Mittel 0,8 Units (V14 7,7), hat 4.726 Energie am Ende (V14 1.174) und vernichtet
19,2 gegnerische Units. Er punktet aber schlechter: 181 statt 292 Punkte in Match 1, erster Punkt bei Schritt 44
statt 37. Er bleibt in 58–67 % der Unit-Schritte stehen (Lehrer 46 %, V14 31–55 %) und stapelt mehr (17–19 %
statt 10–13 %). Grund: Die mehrschrittigen Pläne des Lehrers sind in den Eingaben nicht sichtbar. „Wiederhole den
letzten Zug“ träfe schon 69 % der Lehrerzüge; im Zweifel wählt das Netz „stehen“.

**Gegenmittel:** `imit_stay_bias` (weniger Stehenbleiben), `imit_unstack` (je Feld bleibt nur eine Unit stehen)
und `imit_sap_bias`, alle als Schalter. Dazu der Hybrid `HybridAgent`: V14 und Schüler entscheiden auf dieselbe
Beobachtung, gewählt wird je Unit (points: Halter und Units auf dem Weg zu bewiesenen Punktefeldern spielen V14,
sonst der Schüler; combat: bei Gegnern in der Nähe der Schüler; sap: Schüsse des Schülers). Tests laufen.

Code: `scripts/imitate.py` (collect, dagger, train, ensemble), `agents/sherlock/imitation_agent.py`,
`agents/sherlock/imitation_net.py`. Moayed/Codex prüfte und korrigierte am 15.11. die Zughistorie des
DAgger-Lehrers und die gemeinsame Zielmaske für Training, Messung und Spiel.
Daten und Gewichte liegen nur lokal unter `experiments/imitation/` (gitignoriert, reproduzierbar).
