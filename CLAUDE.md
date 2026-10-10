# Projekt: Lux AI Season 3 – RL-Agent (HTW Berlin, Anwendungen KI, WS 26/27)

## Kontext
- Das ist UNSER eigenes Projekt (Kopie des Dozenten-Templates). Originale vom Dozenten liegen unverändert in `~/Documents/01_RL`, `02_LuxAI`, `AnwendKiLux` → dort nichts ändern.
- Team baut einen RL-Agent (DQN/PPO/A2C, PyTorch) für Lux AI S3. Abgabe muss trainierte Gewichte (.pth) enthalten → rein regelbasiert reicht NICHT.
- Kurs-Regel: 3 Matches pro Spiel à 100 Steps (in `.venv/.../luxai_s3/params.py`: `match_count_per_episode = 3`).
- Spielregeln: `lux/specs.md`, Obs/Actions: `lux/Instructions.md`, Schnittstelle: `Interface_runner_Agent.pdf`, Runner-Doku: `README.md`.
- `lux/runner.py` ist vom Prof → nicht ändern. Eigene Trainingslogik in eigenen Dateien.
- Benchmark-Gegner: `agents/default` (schwach), `agents/Solution_92_Kaggle` (regelbasiert, stark).

## Termine
- 16.10. Review (benotet): erster lauffähiger, trainierter Agent + Präsi (Pseudocode, Architektur, Features, Training, Replays, Erkenntnisse)
- 06.11. Zwischenpräsi + Battle (benotet)
- 27.11. Finale + Turnier + Abgabe agent.zip (benotet)

## Bekannte Probleme im Template
1. `main.py` nutzt Gruppen 7 vs 4, `Paths.csv` kennt nur 1–3 → crasht.
2. `requirements.txt` fehlt (luxai-s3, torch, numpy, pandas, gymnasium).
3. Runner erzeugt Agents in JEDEM Spiel neu und ruft `save_agent()` VOR dem Spiel auf → Gelerntes wird nie gespeichert. Außerdem schreiben P0 und P1 in dieselbe .pth.
4. DQN-Baseline: nur Bewegung (kein Sap), kein Replay Buffer, kein Target Network, Reward nur am Matchende, 17 Features ohne Gedächtnis.

## Plan

### Phase 0 – Setup (heute)
- [x] `requirements.txt` angelegt — [x] venv aufsetzen, `params.py` auf 3 Matches (`scripts/set_match_count.py`)
- [x] `main.py` auf 15 (Sherlock) vs 2 umgestellt — [x] ein Spiel mit Replay laufen lassen
- [x] Agent-Ordner `agents/sherlock/` (Skelett, Klasse `Agent_x`), Eintrag Gruppe 15 in `Paths.csv` (Agent Sherlock)

### Phase 1 – Training, das wirklich speichert
- [x] Eigenes `train.py`: Env direkt (`LuxAIS3GymEnv(numpy_output=True)`), Agent EINMAL erzeugen, viele Spiele, Gegner wählbar (default / Solution_92 / Self-Play)
- [x] Speichern am Spielende, getrennte Pfade pro Seite oder seitenunabhängige Features (Spiegelung für player_1)
- [x] Logging: Winrate, Punkte, Loss, Epsilon pro Spiel (CSV)
- [x] `evaluate.py`: N Spiele gegen festen Gegner, feste Seeds, beide Seiten → Winrate

### Phase 2 – DQN verbessern (Ziel bis 16.10.)
- [x] Replay Buffer + Target Network (Double DQN), Epsilon-Decay
- [x] Reward Shaping pro Einheit: + Zuwachs Team-Punkte pro Step, + Annäherung an Relic/unbekannte Kandidaten-Tiles, − Stacking auf demselben Tile, − Energie < Bewegungskosten, + Match-Sieg
- [x] Belief/Gedächtnis (eigene Klasse): gesehene Relic Nodes über Matches merken, Kandidaten-Tiles (5×5 um Relics), bewiesene Punkte-Tiles (aus Punktzuwachs ableiten), erkundete Tiles, Asteroiden/Nebel
- [x] Features erweitern um diese Infos (Abstand zum nächsten bekannten Punkte-Tile, ob Tile schon besetzt, lokales Energiefeld usw.)
- [x] Training gegen default → dann gegen Solution_92, Replays für Präsi speichern

### Phase 3 – bis 06.11.
- [x] Sap-Aktion ins Action-Space (Ziel: sichtbarer Gegner in Reichweite, Aktionsmaske)
- [ ] CNN auf Karten-Kanälen (24×24) statt Einzel-MLP, oder PPO mit Action-Masking
- [ ] Self-Play / Gegner-Pool

### Phase 4 – bis 27.11.
- [ ] Feinschliff, Turnier-Tests, agent.zip nach Folie 51 (agents.yaml, paths.csv, .pth, alle Pflichtmethoden)

## Stand 10.10.2026 (Details: docs/ERGEBNISSE_20261010.md)
- Abgabe-Gewichte = `full_s0` (Auswahl nach Validierung). Test: vs default 85–88 %, vs Solution_92 ≈ 19 %; Prof-DQN 0 %.
- Experimente: `scripts/experiment.py` / `run_experiments.py` / `report.py`, Protokoll in `docs/EXPERIMENT_PROTOKOLL.md` (Test-Seeds 900000+ nur für finale Auswertung!).
- Nachtraining (`finetune.py`) hat verschlechtert: Replay Buffer wird nicht gespeichert → vor nächstem Versuch fixen.
- Ablation: Belief größter Hebel, Shaping stabilisiert, Sap hilft vs Sol92, guided_explore/Spiegelung ohne belegten Effekt.
- Offen für 16.10.: Präsentationsfolien, Slot buchen, Replays ansehen, proben. Team 15 (Mahmoud El-Hassan, Moayed Shawesh), Agent Sherlock (`agents/sherlock/`, umbenannt von team_lux).

## Konventionen
- Arrays `[x][y]`, unsichtbare Werte = -1, Aktionen Shape `(max_units, 3)`: 0 stay, 1 up, 2 right, 3 down, 4 left, 5 sap(dx, dy).
- Kleine, überprüfbare Schritte; nach jeder Änderung ein kurzes Testspiel laufen lassen.

## Ordnerstruktur (eigener Code)
- `agents/sherlock/main.py` – Agent_x (runner-API, Workaround: speichert bei terminated)
- `agents/sherlock/belief.py` – Gedächtnis (Relics, Punkte-Tiles, Karte)
- `agents/sherlock/features.py` – Features pro Einheit
- `agents/sherlock/reward.py` – Reward Shaping
- `agents/sherlock/model.py` – Netze
- `agents/sherlock/replay_buffer.py` – Replay Buffer
- `agents/sherlock/weights/` – .pth (P0/P1 getrennt)
- `scripts/train.py`, `scripts/evaluate.py` – eigenes Training/Evaluation
- `logs/`, `replays/` (gitignored), `docs/presentation/`
