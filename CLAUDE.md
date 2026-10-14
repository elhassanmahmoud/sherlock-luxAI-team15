# Projekt: Lux AI Season 3 – RL-Agent (HTW Berlin, Anwendungen KI, WS 26/27)

## Gemeinsame Arbeitsweise: Claude Code und Codex

- Diese Datei ist die gemeinsame Quelle für Projektregeln und fachlichen Überblick. Codex wird über [AGENTS.md](AGENTS.md) hierher verwiesen.
- Zu Arbeitsbeginn den jüngsten Eintrag in [docs/ARBEITSSTAND.md](docs/ARBEITSSTAND.md) lesen: letzter Stand, freigegebener Umfang und offene Punkte. Aktuelle ausdrückliche Team-Anweisungen haben Vorrang vor älteren Einträgen.
- Nach abgeschlossenen Arbeiten dort Änderung, Grund, tatsächlich durchgeführte Prüfungen und offene Punkte ergänzen. Keine geplanten Tests als bestanden oder Vorschläge als umgesetzt darstellen.
- Experimente und Auswahlentscheidungen weiterhin in [docs/EXPERIMENT_PROTOKOLL.md](docs/EXPERIMENT_PROTOKOLL.md) dokumentieren; bestehende Rohdaten und historische Resultate erhalten.
- Vor Änderungen den Git-Status prüfen und Änderungen des anderen Teammitglieds erhalten. Getrennte Arbeitszweige für eigene Änderungen verwenden, sobald die nächste Codearbeit beginnt; gemeinsame Dateien beim Zusammenführen abgleichen.
- Aktueller Auftrag vom 14.10.: gemeinsame Dokumentation, README und Checkliste; anschließend SSH-Zugriff einrichten und diese Dokumentationsänderungen auf GitHub hochladen. Keine Änderung an Agent, Trainingsskripten oder Gewichten. Weitere Korrekturen sind als offen dokumentiert, nicht zur Umsetzung freigegeben.

## Kontext
- Das ist UNSER eigenes Projekt (Kopie des Dozenten-Templates). Originale vom Dozenten liegen unverändert in `~/Documents/01_RL`, `02_LuxAI`, `AnwendKiLux` → dort nichts ändern.
- Team baut einen RL-Agent (DQN/PPO/A2C, PyTorch) für Lux AI S3. Abgabe muss trainierte Gewichte (.pth) enthalten → rein regelbasiert reicht NICHT.
- Kurs-Regel: 3 Matches pro Spiel à 100 Steps (in `.venv/.../luxai_s3/params.py`: `match_count_per_episode = 3`).
- Spielregeln: `lux/specs.md`, Obs/Actions: `lux/Instructions.md`, Schnittstelle: `Interface_runner_Agent.pdf`, Runner-Doku: `README.md`.
- `lux/runner.py` ist vom Prof → nicht ändern. Eigene Trainingslogik in eigenen Dateien.
- Benchmark-Gegner: `agents/default` (schwach), `agents/Solution_92_Kaggle` (regelbasiert, stark).

## Termine
- 16.10. Review (benotet): erster lauffähiger, trainierter Agent + Präsi (Pseudocode, Architektur, Features, Training, Replays, Erkenntnisse)
- Submission 1: ungefähr **10 Minuten Vortrag**, Upload der Präsentation bis **16.10.2026, 08:00 Uhr** (Moodle-Aufgabe). Laut Moayed sind die Slots **20 Minuten** lang; Fragen/Puffer in der übrigen Zeit sind eine plausible, noch nicht bestätigte Aufteilung. Die genaue Vortragsdauer späterer Termine ist noch zu bestätigen.
- 06.11. Zwischenpräsi + Battle (benotet)
- 27.11. Finale + Turnier + Abgabe agent.zip (benotet)

## Historische Probleme im Dozenten-Template

Punkte 1 und 2 wurden im Projekt bereits behoben; Punkt 3 wird durch die eigene Trainingslogik umgangen. Aktuelle offene Befunde stehen im Arbeitsstand.

1. `main.py` nutzt Gruppen 7 vs 4, `Paths.csv` kennt nur 1–3 → crasht.
2. `requirements.txt` fehlt (luxai-s3, torch, numpy, pandas, gymnasium).
3. Runner erzeugt Agents in JEDEM Spiel neu und ruft `save_agent()` VOR dem Spiel auf → Gelerntes wird nie gespeichert. Außerdem schreiben P0 und P1 in dieselbe .pth.
4. DQN-Baseline: nur Bewegung (kein Sap), kein Replay Buffer, kein Target Network, Reward nur am Matchende, 17 Features ohne Gedächtnis.

## Plan

### Phase 0 – Setup (abgeschlossen)
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
- [x] Self-Play / Gegner-Pool untersucht (`full_sp`, 11.10.); in diesen Versuchen kein klarer Gewinn, nicht in die Abgabe übernommen

### Phase 4 – bis 27.11.
- [ ] Feinschliff, Turnier-Tests, agent.zip nach Folie 51 (agents.yaml, paths.csv, .pth, alle Pflichtmethoden)

## Stand 14.10.2026 (Historie: docs/EXPERIMENT_PROTOKOLL.md)
- Abgabe-Gewichte seit 11.10. = `old3_sym3`: Ensemble aus 6 Netzen (3 × `full` + 3 × `full_sym`, `scripts/build_ensemble.py`) + Spiegelsymmetrie im Belief (`use_symmetry`) + Erkundungsgedächtnis über Matches (`explore_memory`). **Benchmark: vs default 100 %, vs Solution_92 46,7 %** (`full_s0`: 85 % / 20 %). Vorher `full_s0` (Tag `abgabe-review-full_s0`). Vorgehen: Niederlagen analysieren (`scripts/analyze_losses.py`) → gezielte Änderung → auf neuen Val-Seeds prüfen (`compare_weights.py`/`compare_report.py`). Weitertraining und Self-Play brachten in den untersuchten Varianten keinen klaren Gewinn; das ist keine allgemeine Aussage über diese Verfahren.
- Experimente: `scripts/experiment.py` / `run_experiments.py` / `report.py`, Protokoll in `docs/EXPERIMENT_PROTOKOLL.md`. Testkarten 900000–900029 wurden bereits für mehrere Stände ausgewertet; sie sind kein unberührter Testsatz mehr. Für November neue Testkarten vorab festlegen und bis zur finalen Entscheidung zurückhalten.
- Nachtraining (`finetune.py`): Buffer wird jetzt gespeichert/aufgefüllt (11.10.). Weitertrainieren bringt trotzdem keinen klaren Gewinn – einzelne DQN-Checkpoints schwanken stark; Ensemble glättet das.
- Historische Einzelnetz-Ablation: Gedächtnis in den Netzmerkmalen größter Hebel, Shaping stabilisiert, Sap hilft vs Sol92. Für guided_explore und kanonische Koordinaten kein eindeutiger Effekt nachgewiesen; das beweist keine Wirkungslosigkeit und betrifft nicht die spätere Symmetrie-Inferenz im Belief.
- 12.10.: Folien auf `old3_sym3` aktualisiert (19 Folien), neue Replays. Match 1 = Schwachpunkt (Relic zu spät gefunden, `scripts/analyze_timing.py`). Neue Schalter (Default aus): `early_inference`, `explore_grid`, `scripted_explore`, `explore_stale`. **Kandidat für die nächste Abgabe (erst nach dem 16.10.): `m1_early` = `old3_sym3` + `early_inference`** (bestätigt auf 120 neuen Seeds: +7,9 pp vs Solution_92, +2,9 vs default). Val-Seeds bis 500 659 verbraucht.
- Die Notiz vom 12.10. zu 19 Folien beschreibt einen externen Entwurf; ein aktueller PPTX-/PDF-Folienexport liegt nicht im Repository und wurde hier nicht geprüft.
- Offen für 16.10.: Präsentationsfolien exportieren/prüfen, Slot/Buchung bestätigen, Replays ansehen, auf etwa zehn Minuten proben. Team 15 (Mahmoud El-Hassan, Moayed Shawesh), Agent Sherlock (`agents/sherlock/`, umbenannt von team_lux).
- Prüfung vom 14.10. in separater Kopie desselben Dateistands: 62 Tests bestanden, 120 Ensemble-Spiele reproduziert (60/60 gegen default, 28/60 gegen Solution_92; 30 Karten × beide Seiten je Gegner). Offene Mess-/Trainingsfehler und Prüfgrenzen: [Arbeitsstand](docs/ARBEITSSTAND.md).

## Konventionen
- Arrays `[x][y]`, unsichtbare Werte = -1, Aktionen Shape `(max_units, 3)`: 0 stay, 1 up, 2 right, 3 down, 4 left, 5 sap(dx, dy).
- Kleine, überprüfbare Schritte. Für Codeänderungen passende Tests und bei spielrelevanten Änderungen ein kurzes Testspiel ausführen; dabei Abgabe-Gewichte schützen. Bei reinen Dokumentationsänderungen genügen Diff-, Inhalts- und Linkprüfung, ohne Training oder neue Spiele.

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
