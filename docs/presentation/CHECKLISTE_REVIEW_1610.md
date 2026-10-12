# Checkliste Review 16.10.2026 (benotet, 1/3 der Note)

Abgleich der Vorgaben aus den Kursfolien („Reinforcement Learning“) mit unserem Stand vom 10.10.2026.
Folienentwurf: Artifact „Sherlock – Review 16.10.“ (17 Folien, Sprechernotizen auf jeder Folie, Export als PPTX/PDF möglich).

## Folie 9 – Inhalt der Review-Präsentation (~20 min, Slot auf Moodle)

| Vorgabe | Wo | Status |
|---|---|---|
| Algorithmus als Pseudocode | Folie „Algorithmus“; README; Docstring `agents/sherlock/main.py` | ✅ |
| Netzarchitektur | Folie „Architektur“ (MLP 79 → 256 → 256, Dueling) | ✅ |
| RL-Algorithmus | Double DQN, Replay Buffer, Target-Netz (Folie „Algorithmus“) | ✅ |
| Trainings-Konfiguration | Folie „Training“; `agents/sherlock/config.py` | ✅ |
| Feature Engineering | Folien „Belief“, „Features“, „Abgleich Folie 50“ | ✅ |
| Trainingsablauf: Anzahl Spiele, Gegner | 3000 Spiele/Lauf, 63 000 insgesamt, Curriculum default → Solution_92 | ✅ |
| Ausgewählte Spiele zeigen | `docs/presentation/replays/sherlock_*.json` (5 Replays mit Abgabe-Agent `old3_sym3`, 12.10.), Folie „Replays“ | ✅ Beobachtungen aus den Replay-Daten eingetragen – im Viewer gegenprüfen |
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
| `name: str='Team Name Agent_X'` | ✅ `Sherlock Agent_X` |
| `act`, `update`, `set_to_eval_mode`, `set_env_cfg`, `save_agent`, `load_agent` | ✅ (Test `tests/test_runner.py`, Prüfung im Build-Skript) |
| trainierte `.pth` | ✅ `agents/sherlock/weights/agent_p0.pth`, `agent_p1.pth` (seit 11.10.: `old3_sym3` = Ensemble aus 6 Netzen + Symmetrie + Erkundungsgedächtnis; vorher `full_s0`) |
| `agents.yaml` | ✅ `agents/sherlock/agents.yaml` (und im Zip) |
| `paths.csv` mit Moodle-Gruppe | ✅ Gruppe 15 |

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

## Technische Prüfungen (11.10.2026, neuer Agent `full_s012_sym`)

| Prüfung | Ergebnis |
|---|---|
| Frischer `git clone` von GitHub → `pytest` | 55/55 grün |
| Kurs-Runner `train=False`: 15 vs 1/2/3/15 und 1/2/3 vs 15 (beide Seiten) | alle 7 ok |
| Kurs-Runner `train=True` | läuft; verändert die Gewichte (gewollt) → nach Tests wiederherstellen |
| Rechenzeit `act()` (3 Netze + Symmetrie) | Ø 0,7 ms, max 1,2 ms pro Step |
| `dist/agent.zip` aus frischem Clone gebaut und geprüft | „Check ok“, 3 Netze, Symmetrie an |
| gegen Prof-DQN (20 Seeds × 2 Seiten) | 100 % Spiele, 1072 : 2 Punkte |

**Folien aktualisiert (12.10., 19 Folien):** Kernaussage mit Testzahlen von `old3_sym3` (100 % / 46,7 %), neue Folien „Niederlagen-Analyse“ (Symmetrie, Erkundung über Matches) und „Vom Einzelnetz zur Abgabe“ (4 Schritte mit gepaarten Δ auf neuen Val-Seeds), Ensemble in „Architektur“, Negativ-Ergebnisse (Weitertraining, Self-Play) in „Erkenntnisse“, neue Replays, „Grenzen“ mit Befund Match 1. Siehe `docs/EXPERIMENT_PROTOKOLL.md` Abschnitt 9.

## To-do Team vor dem 16.10.

1. Slot auf Moodle buchen.
2. ✅ Teamname Sherlock, Gruppe 15 eingetragen.
3. Replays (`sherlock_*.json`) auf <https://s3vis.lux-ai.org/> ansehen und prüfen, ob man die Beobachtungen auf der Folie „Replays“ im Bild gut sieht; ggf. eigene ergänzen.
4. Folien aufteilen, zweimal mit Uhr proben (Ziel 17–18 min plus Fragen).
5. Jede Person kann Belief, Reward Shaping, Double DQN und die Ablation in eigenen Worten erklären (Folie 50: „Make sure you understand what you submit!“).
6. **Neu (11.10.):** Jede Person kann auch Ensemble, Spiegelsymmetrie und die Niederlagen-Analyse erklären – das ist jetzt der stärkste „eigene Beitrag“ (Bewertungskriterium Originalität, Folie 11).
