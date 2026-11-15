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

| Version | Daten | Netz | Validierung (gleicher Zug / Schussziel genau / ±1 Feld) | Spieltest |
|---|---|---|---|---|
| v1 | b1 | ch 64, 6 Blöcke, alter Trainer (Lehreraktion erzwungen erlaubt, Eigenfeld nie Ziel) | nach 4/6 Epochen 81,1 % / 74 % / 91 % | folgt |
| v2 | b1+b2+b3 | ch 64, 6 Blöcke, gemeinsamer Trainer (nur im Spiel ausführbare Lehrerbefehle, Eigenfeld legales Ziel) | folgt | folgt |

Code: `scripts/imitate.py` (collect, dagger, train, ensemble), `agents/sherlock/imitation_agent.py`,
`agents/sherlock/imitation_net.py`. Moayed/Codex prüfte und korrigierte am 15.11. die Zughistorie des
DAgger-Lehrers und die gemeinsame Zielmaske für Training, Messung und Spiel.
Daten und Gewichte liegen nur lokal unter `experiments/imitation/` (gitignoriert, reproduzierbar).
