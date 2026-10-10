# Checkliste Review 16.10.2026 (benotet, 1/3 der Note)

Abgleich der Vorgaben aus den Kursfolien („Reinforcement Learning“) mit unserem Stand vom 10.10.2026.
Folienentwurf: Artifact „Team Lux Review 16.10.“ (17 Folien, Sprechernotizen auf jeder Folie, Export als PPTX/PDF möglich).

## Folie 9 – Inhalt der Review-Präsentation (~20 min, Slot auf Moodle)

| Vorgabe | Wo | Status |
|---|---|---|
| Algorithmus als Pseudocode | Folie „Algorithmus“; README; Docstring `agents/team_lux/main.py` | ✅ |
| Netzarchitektur | Folie „Architektur“ (MLP 79 → 256 → 256, Dueling) | ✅ |
| RL-Algorithmus | Double DQN, Replay Buffer, Target-Netz (Folie „Algorithmus“) | ✅ |
| Trainings-Konfiguration | Folie „Training“; `agents/team_lux/config.py` | ✅ |
| Feature Engineering | Folien „Belief“, „Features“, „Abgleich Folie 50“ | ✅ |
| Trainingsablauf: Anzahl Spiele, Gegner | 3000 Spiele/Lauf, 63 000 insgesamt, Curriculum default → Solution_92 | ✅ |
| Ausgewählte Spiele zeigen | `docs/presentation/replays/` (4 Replays), Folie „Replays“ | ⚠️ Beobachtungen pro Replay noch eintragen (Platzhalter auf der Folie) |
| Beobachtungen, Hypothesen, Erkenntnisse | Folien „Ergebnisse“, „Ablation“, „Lernkurven“, „Erkenntnisse“ | ✅ |
| Fragen, nächste Schritte | Folien „Grenzen“, „Fragen“ (mögliche Fragen in den Notizen) | ✅ |
| Slot auf Moodle buchen | – | ❌ **Team** |

## Folie 11 – Bewertungsraster

| Kriterium | Wie wir es abdecken | Offen |
|---|---|---|
| Klare Kernaussage | eigene Folie direkt nach dem Titel, am Ende wiederholt | – |
| Logischer Aufbau | Problem → Lösung → Training → Ergebnisse → Erkenntnisse → Ausblick | – |
| Verständliche Erklärungen | Belief an einem Zwei-Schritt-Beispiel; Begriffe in den Notizen erklärt | – |
| Frei, in eigenen Worten sprechen | Notizen sind Stichwortgeber, nicht zum Ablesen | ❌ **proben**, Folien unter den Teammitgliedern aufteilen |
| Hilfreiche Folien | eine Idee pro Folie, Diagramme mit Konfidenzintervallen | Platzhalter (Namen, Gruppe, Replay-Beobachtungen) füllen |
| Originalität / eigener Beitrag | Punkte-Tile-Inferenz, Spiegelung, Ablationsstudie, Fund „Env-Reward ≠ Folie 45“ | – |

## Folie 51 – agent.zip (Abgabe erst 27.11., für den 16.10. schon erfüllt)

| Vorgabe | Stand |
|---|---|
| Ordner = Teamname, leere `__init__.py` | ✅ `scripts/build_submission.py --team-name …` (relative Imports, beliebig umbenennbar) |
| `main.py` mit `Agent_x` | ✅ |
| `name: str='Team Name Agent_X'` | ⚠️ jetzt `Team Lux Agent_X`; echten Teamnamen eintragen |
| `act`, `update`, `set_to_eval_mode`, `set_env_cfg`, `save_agent`, `load_agent` | ✅ (Test `tests/test_runner.py`, Prüfung im Build-Skript) |
| trainierte `.pth` | ✅ `agents/team_lux/weights/agent_p0.pth`, `agent_p1.pth` (`full_s0`) |
| `agents.yaml` | ✅ `agents/team_lux/agents.yaml` (und im Zip) |
| `paths.csv` mit Moodle-Gruppe | ⚠️ Gruppe `4` ist Platzhalter |

## Technische Prüfungen (10.10.2026)

| Prüfung | Ergebnis |
|---|---|
| Frischer `git clone` → `pytest` | 52/52 grün |
| Kurs-Runner `train=False`, beide Seiten, vs default / Solution_92 / Prof-DQN | läuft; Replays werden geschrieben |
| Kurs-Runner `train=True` | läuft; Agent speichert nach jedem Spiel selbst (Speicher-Bug umgangen) |
| Rechenzeit `act()` | Ø 0,5 ms, max 0,9 ms pro Step |
| `dist/agent.zip` entpackt in frische Kopie laden | ok, beide Seiten |
| README: alle Befehle und Links | geprüft |
| Ergebnisse reproduzierbar | Replays und `evaluate.py` reproduzieren die Testwerte exakt |

## To-do Team vor dem 16.10.

1. Slot auf Moodle buchen.
2. Echten Teamnamen und Moodle-Gruppennummer nennen; Agent-Name, `Paths.csv` und die Titelfolie werden angepasst.
3. Replays auf <https://s3vis.lux-ai.org/> ansehen und pro Spiel eine Beobachtung auf der Folie „Replays“ eintragen.
4. Folien aufteilen, zweimal mit Uhr proben (Ziel 17–18 min plus Fragen).
5. Jede Person kann Belief, Reward Shaping, Double DQN und die Ablation in eigenen Worten erklären (Folie 50: „Make sure you understand what you submit!“).
