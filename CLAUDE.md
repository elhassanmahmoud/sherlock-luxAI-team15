# Projekt: Lux AI Season 3 – RL-Agent (HTW Berlin, Anwendungen KI, WS 26/27)

## Gemeinsame Arbeitsweise: Claude Code und Codex

- Diese Datei ist die gemeinsame Quelle für Projektregeln und fachlichen Überblick. Codex wird über [AGENTS.md](AGENTS.md) hierher verwiesen.
- Zu Arbeitsbeginn den jüngsten Eintrag in [docs/ARBEITSSTAND.md](docs/ARBEITSSTAND.md) lesen: letzter Stand, freigegebener Umfang und offene Punkte. Aktuelle ausdrückliche Team-Anweisungen haben Vorrang vor älteren Einträgen.
- Nach abgeschlossenen Arbeiten dort Änderung, Grund, tatsächlich durchgeführte Prüfungen und offene Punkte ergänzen. Keine geplanten Tests als bestanden oder Vorschläge als umgesetzt darstellen.
- Experimente und Auswahlentscheidungen weiterhin in [docs/EXPERIMENT_PROTOKOLL.md](docs/EXPERIMENT_PROTOKOLL.md) dokumentieren; bestehende Rohdaten und historische Resultate erhalten.
- Moayeds Arbeitspräferenz (20.10.): Codex koordiniert geeignete unabhängige Teilaufgaben mit Subagents, prüft ihre Ergebnisse selbst und führt Änderungen kontrolliert zusammen. Zuständigkeiten und Schreibbereiche vorab trennen; auf dem M3/8GB insgesamt maximal zwei Evaluationsprozesse. Laufende Vergleichsreihen behalten denselben Code, auch während paralleler Reviews.
- Änderungen in sinnvollen, abgeschlossenen Arbeitsschritten committen: zusammengehörige Umsetzung, Tests und Dokumentation gemeinsam; abgeschlossene Messreihen und ihre Auswertung separat. Keine Sammel-Commits über unabhängige Aufgaben und keine künstliche Aufteilung pro Datei. Vor dem Push passende Prüfungen durchführen und den Remote-Stand abgleichen.
- Freigabe vom 20.10.: Ein nach den festgelegten Tests nachweislich besserer Kandidat darf selbstständig die Abgabe-Gewichte ersetzen. Vorher beide bisherigen Dateien mit Hash und Herkunft versioniert sichern; Vergleich, Kursprüfung, neue Hashes und Wiederherstellung für Mahmoud dokumentieren. Bei unklarem Vorteil bleibt die Abgabe bestehen. Training schreibt weiterhin ausschließlich in Experimentverzeichnisse; der Überschreibschutz bleibt aktiv. Aktuelle Abnahmeregeln: [autonomer Plan](docs/superpowers/plans/2026-10-20-autonomous-improvement.md).
- Vor Änderungen den Git-Status prüfen und Änderungen des anderen Teammitglieds erhalten. Getrennte Arbeitszweige für eigene Änderungen verwenden, sobald die nächste Codearbeit beginnt; gemeinsame Dateien beim Zusammenführen abgleichen.
- Historischer Präsentationsstand vom 15.10.: Ursprüngliches Design mit Agenda als Folie 2. Zwölf Vortragsfolien plus drei ausgeblendete Reservefolien (13–15, neu: Belohnung im Training), Ziel 11:10 Minuten (maximal zwölf). Moayed übernimmt den leichter zugänglichen Teil einschließlich Agenda (5:35), Mahmoud die Technik (5:35). Folie 11 zeigt seit 15.10. den belegten Fortschritt 12/60 → 28/60 gegen Solution_92. [Vortragsplan](docs/presentation/VORTRAGSPLAN_1610.md) und aktuelle PowerPoint/PDF sind die gemeinsame Arbeitsgrundlage. Die damalige Beschränkung lautete: Gewichte, Agentenlogik, Trainingsbelohnung und Kurs-Runner unverändert lassen. Für heutige Arbeit gelten die späteren Freigaben oben.

- Sichtbare Hauptfolien enthalten nur publikumsrelevante Inhalte. Interne Vortragsanweisungen, Zeitplanung und Hinweise auf Reservefolien gehören in Sprechernotizen und Vortragsplan. Fachliche Erläuterungen zu Daten, Auswertung und Grenzen bleiben auf den Folien.

## Kontext

### Aktuelle Orientierung nach dem Review (21.10.2026)

- Abschluss des begrenzten V4-Programms am Abend des 21.10.: [Bericht für den 22.10.](docs/MORGENBERICHT_20261022.md). Paar-Koordinator, Zielpilot, 240 CNN-Trainingsspiele und Artillerie-Bestätigung lieferten in insgesamt 3.336 neuen Spielen keinen qualifizierten V3-Ersatz. Der letzte frische Vergleich ergab 301/400 statt 292/400 gegen Solution, aber +2,25 pp mit Intervall [−0,25; +4,75] verfehlt die vorab festgelegten Gates. Neue Evidenz wird von Mahmouds bereits gestarteten Gefahrmerkmale-/PPO-Studien erwartet; nicht doppelt starten. Alle Details und aktueller Abschlussstatus im Bericht.

- Erste Präsentation abgeschlossen; laut Moayed Note **1,3**. Die Präsentationsvorbereitung vom 14./15.10. unten ist historisch.
- **Aktuelle Abgabe seit 22.10., 09:21: V10 `v10_V8st`**: dieselben 18 V3-Netze, Config V7 + `reach_assign` + `sap_no_overkill` + `safe_moves` + `collision_guard` + `sap_still`; beide Dateien SHA-256 `03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`. Frisch auf 800 Karten 507420–508219: **Solution_92 90,3 %** statt 82,8 % bei V7 (Δ +7,5 [+5,4; +9,6]), default 99,75 %, direkt gegen V7 58,1 % [53,1; 62,75] aus 800 Spielen. [Übernahmebericht](experiments/analysis/release_20261022_v10/RELEASE.md), Rückweg zu V7 unter `experiments/releases/20261022_v7_Bsnpd/`.
- Vorherige Abgabe 22.10., 05:27–09:21: V7 `v7_Bsnpd`: dieselben 18 V3-Netze, Config V3 + `art_sap` 3 + weiche Nebel-Meidung + `nebula_infer` + `drift_track` + `path_fix`; beide Dateien SHA-256 `c394acba84f7a298f8f1e6107328d8e6ce151b367a28997b059aa82fc8a895e6`. Frisch auf 400 Karten 505420–505819: Solution_92 83,5 % statt 76,5 % (Δ +7,0 [+4,0; +10,0]), default 99,75 %, direkt gegen V3 68,0 % [61,5; 74,25]. [Übernahmebericht](experiments/analysis/release_20261022_v7/RELEASE.md), Rückweg zu V3 unter `experiments/releases/20261022_all18_v3/`.
- Kandidat V8 (durch V10 erledigt, V10 enthält V8): V7 + `reach_assign` + `sap_no_overkill` + `safe_moves` + `collision_guard`, frisch auf 800 Karten 89,1 % gegen Solution_92 (V7 84,6 %), Direkt-Gate gegen V7 knapp verfehlt (56,5 % [49,5; 63,5]); nachträgliche Info-Duelle 59,9 % [55,0; 64,75] gegen V7. Übersicht und Übernahmeweg: [Nachtbericht V7/V8](docs/NACHT_V7_V8_20261022.md).
- Vorherige Abgabe 20.–22.10.: **`all18_v3`**, 18 DQN-Netze, beide Dateien SHA-256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`. Bestätigt gegen die gesicherte alte Abgabe auf 200 neuen Karten 502420–502619: Solution_92 313/400 statt 170/400, default 400/400 statt 382/400; direkt 96/120 gegen alt. [Übernahmebericht](experiments/analysis/autonomous_20261020/RELEASE.md), Rückweg unter `experiments/releases/20261020_old3_sym3/`. CNN/PPO und weitere DQN-Varianten werden separat untersucht.
- [Review-Erkenntnisse und nächste Schritte](docs/REVIEW_NAECHSTE_SCHRITTE_20261020.md) enthalten die Vergleichsdaten, Prüfgrenzen, Prof-Fragen und priorisierten Vorschläge. Der damalige Bericht ist ein historischer Review; der anschließend autorisierte autonome Verbesserungsplan und jüngste Arbeitsstand bestimmen die aktuellen Aufgaben und Seedreservierungen.
- [Morgenbericht vom 21.10.](docs/MORGENBERICHT_20261021.md): unabhängige V4-Bestätigung ohne eindeutigen Vorteil; V3 bleibt Abgabe. Eigene zusätzliche 18.800 Trainingsspiele lieferten keinen qualifizierten Ersatz. Der [nächste Trainingsentwurf](docs/NAECHSTER_TRAININGSVERSUCH_20261021.md) wird umgesetzt: Gegnerplan, isolierte Zwischenvalidierung, Studienrunner und Gates implementiert, getestet und unabhängig geprüft; der Vergleich `20261021_early_contact_v1` wurde am 21.10. nach 9.750 protokollierten Trainingsspielen aus Ressourcengründen unvollständig beendet. Kein abschließender Methodenbefund und keine neue Abgabe; der vorab geplante direkte Gegnerenergie-Vergleich wird vorgezogen. Tatsächlichen Fortschritt ausschließlich dem jüngsten Arbeitsstand bzw. Studienstate entnehmen. Die 18 V3-Quellläufe dokumentieren 66.000 abgeschlossene Spiele; das ist weder das gesamte Projektbudget noch ein Nachweis der genauen Auswahlzeitpunkte fehlender Einzelcheckpoints.
- Für laufende Arbeiten immer den neuesten Arbeitsstand lesen; dieser Überblick ersetzt weder Laufmanifeste noch aktuelle Messergebnisse.

### Projektgrundlagen
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
- [x] CNN auf Karten-Kanälen (24×24) und PPO mit Action-Masking implementiert und untersucht (19./20.10.); weitere Validierung und Auswahl offen, siehe aktuellen Arbeitsstand
- [x] Self-Play / Gegner-Pool untersucht (`full_sp`, 11.10.); in diesen Versuchen kein klarer Gewinn, nicht in die Abgabe übernommen

### Phase 4 – bis 27.11.
- [ ] Feinschliff, Turnier-Tests, agent.zip nach Folie 51 (agents.yaml, paths.csv, .pth, alle Pflichtmethoden)

## Stand 14.10.2026 (Historie: docs/EXPERIMENT_PROTOKOLL.md)
- Abgabe-Gewichte seit 11.10. = `old3_sym3`: Ensemble aus 6 Netzen (3 × `full` + 3 × `full_sym`, `scripts/build_ensemble.py`) + Spiegelsymmetrie im Belief (`use_symmetry`) + Erkundungsgedächtnis über Matches (`explore_memory`). **Benchmark: vs default 100 %, vs Solution_92 46,7 %** (`full_s0`: 85 % / 20 %). Vorher `full_s0` (Tag `abgabe-review-full_s0`). Vorgehen: Niederlagen analysieren (`scripts/analyze_losses.py`) → gezielte Änderung → auf neuen Val-Seeds prüfen (`compare_weights.py`/`compare_report.py`). Weitertraining und Self-Play brachten in den untersuchten Varianten keinen klaren Gewinn; das ist keine allgemeine Aussage über diese Verfahren.
- Experimente: `scripts/experiment.py` / `run_experiments.py` / `report.py`, Protokoll in `docs/EXPERIMENT_PROTOKOLL.md`. Testkarten 900000–900029 wurden bereits für mehrere Stände ausgewertet; sie sind kein unberührter Testsatz mehr. Für November neue Testkarten vorab festlegen und bis zur finalen Entscheidung zurückhalten.
- Nachtraining (`finetune.py`): Buffer wird jetzt gespeichert/aufgefüllt (11.10.). Weitertrainieren bringt trotzdem keinen klaren Gewinn – einzelne DQN-Checkpoints schwanken stark; Ensemble glättet das.
- Historische Einzelnetz-Ablation: Gedächtnis in den Netzmerkmalen größter Hebel, Shaping stabilisiert, Sap hilft vs Sol92. Für guided_explore und kanonische Koordinaten kein eindeutiger Effekt nachgewiesen; das beweist keine Wirkungslosigkeit und betrifft nicht die spätere Symmetrie-Inferenz im Belief.
- 12.10.: Folien auf `old3_sym3` aktualisiert (19 Folien), neue Replays. Match 1 = Schwachpunkt (Relic zu spät gefunden, `scripts/analyze_timing.py`). Neue Schalter (Default aus): `early_inference`, `explore_grid`, `scripted_explore`, `explore_stale`. **Kandidat für die nächste Abgabe (erst nach dem 16.10.): `m1_early` = `old3_sym3` + `early_inference`** (bestätigt auf 120 neuen Seeds: +7,9 pp vs Solution_92, +2,9 vs default). Val-Seeds bis 500 659 verbraucht.
- Die Notiz vom 12.10. zu 19 Folien ist historisch. Am 14.10. neu aufgebaut: `docs/presentation/Sherlock_Review_16-10-2026.pptx` und `.pdf`, zwölf Vortragsfolien plus zwei Reservefolien, mit Sprechernotizen und gemeinsamer Vorbereitung. Ziel 11:10 Minuten, Obergrenze zwölf; Moayed 5:35, Mahmoud 5:35. Agenda am 15.10. als zweite Folie ergänzt, danach Erkenntnisfolie und Reservefolie 15 (siehe Arbeitsstand).
- Offen für 16.10.: Folien und Aufteilung gemeinsam bestätigen, Darstellung auf dem Präsentationsrechner prüfen, Slot/Buchung bestätigen, zweimal auf 10–12 Minuten proben und bis 08:00 Uhr auf Moodle hochladen. Team 15 (Mahmoud El-Hassan, Moayed Shawesh), Agent Sherlock (`agents/sherlock/`, umbenannt von team_lux).
- Prüfung vom 14.10. in separater Kopie desselben Dateistands: 62 Tests bestanden, 120 Ensemble-Spiele reproduziert (60/60 gegen default, 28/60 gegen Solution_92; 30 Karten × beide Seiten je Gegner). Offene Mess-/Trainingsfehler und Prüfgrenzen: [Arbeitsstand](docs/ARBEITSSTAND.md).

## Konventionen

- `compare_report` resampelt ganze Karten (beide Seiten zusammen) und vergleicht nur gemeinsame vollständige Karten. Alte Konfidenzintervalle dieses Skripts nicht weiter als aktuelle Ergebnisse verwenden; korrigierte Beispiele und Grenzen stehen in [Statistikprüfung 14.10.](docs/STATISTIK_20261014.md). `report.py` bleibt die separate Zwei-Ebenen-Auswertung für Trainingsstarts.

- Neue Punktemessungen tragen `point_counting_version=2`: vollständige Matchpunkte einschließlich des letzten Zuwachses vor dem Reset. CSVs ohne diese Spalte sind historische Version 1 und bleiben unverändert. Punktevergleiche nur innerhalb derselben Version; alte Spiele mit denselben Gewichten, Seeds und Gegnern in neue Dateien auswerten. Die Rekonstruktion aus `info["final_state"]` ist reine externe Messung und darf nicht als Agentenwissen oder Reward verwendet werden.

- `scripts.train` schreibt pro Aufruf in einen neuen Run-Ordner; ein optionales `--output-dir` darf noch nicht existieren. `--resume CHECKPOINT` liest ein vorhandenes Einzelnetz und schreibt in einen neuen Lauf. Ensemble-Resume wird abgewiesen. Quelle und Abgabe-Dateien nicht ersetzen; der einfache Trainer stellt den Replay Buffer nicht wieder her.
- `scripts.build_submission --from-run` verpackt die angegebenen Gewichte direkt, ohne sie in `agents/sherlock/weights/` zu installieren. Eine neue Version der Abgabe-Gewichte muss separat ausdrücklich beauftragt werden.
- Der Schutz gilt für diese beiden Skripte, nicht für beliebige Dateioperationen. `main.py` zur Vorführung bei `train=False` belassen; direkten Runner-Trainingsaufrufen oder anderen Schreibwerkzeugen niemals die Abgabe-Dateien als Ausgabe geben.
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
