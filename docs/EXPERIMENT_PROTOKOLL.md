# Experiment-Protokoll

Festgelegt am **10.10.2026, vor dem Start der Trainingsläufe** (Commit, mit dem der Batch gestartet wurde: siehe `git` in jeder `manifest.json`).
Änderungen am Protokoll nach Ansicht der Testergebnisse werden unten im Abschnitt *Änderungen* mit Datum und Grund eingetragen.

## 1. Fragestellung

1. Ist unser Agent (`full`) besser als die DQN-Baseline des Dozenten?
2. Kommt ein Vorsprung von der **besseren Methode** oder nur von **mehr Training**?
   Dafür gibt es zwei Baselines: die mitgelieferten Gewichte (`baseline_prof`) und denselben Prof-Code, gleich lang mit unserem Trainingsablauf trainiert (`baseline_prof_retrained`).
3. Welche Bausteine tragen wie viel bei? (Ablationen: jeweils genau ein Baustein aus)

Vorab notierte Erwartungen (zum späteren Abgleich, nicht als Ergebnis):

- `full` > `baseline_prof_retrained` > `baseline_prof` gegen `default`.
- Gegen `Solution_92_Kaggle` (stark, regelbasiert) erwarten wir bei allen Varianten Winraten nahe 0. Dort sind Punkte und Match-Siege die aussagekräftigeren Kennzahlen.
- Den größten Verlust erwarten wir bei `no_guided_explore` und `no_belief`. Bei `no_sap` und `no_canonical` erwarten wir kleine Effekte, deren Vorzeichen offen ist.

## 2. Varianten

| Variante | Code | Unterschied zu `full` |
|---|---|---|
| `baseline_prof` | `agents/DQN` unverändert, `agents/DQN/agent.pth` | keine; nur Evaluation |
| `baseline_prof_retrained` | `agents/DQN` unverändert hinter `ProfAdapter` (`scripts/variants.py`) | Prof-Methode, gleich viele Trainingsspiele, gleicher Ablauf |
| `full` | `agents/sherlock`, `AgentConfig()` | – |
| `no_belief` | `use_belief=False` | Netz sieht nur die aktuelle Beobachtung (`MemorylessBelief`) |
| `no_shaping` | `use_shaping=False` | Reward = `w_point` (Eigentümer eines bewiesenen Punkte-Tiles) + `w_match` · Matchergebnis |
| `no_sap` | `use_sap=False` | 5 statt 6 Aktionen |
| `no_guided_explore` | `guided_prob=0.0` | Exploration rein uniform zufällig |
| `no_canonical` | `canonical=False` | keine Spiegelung, ein eigenes Netz pro Seite |

Die Abbildung Variante → Config steht in `scripts/variants.py`. `tests/test_variants.py` prüft, dass sich jede Ablation in genau einem Feld von `full` unterscheidet.

Was die Ablationen genau bedeuten:

- **`no_belief`**: Der volle Belief läuft intern weiter. Er wird gebraucht für den Reward (bewiesene Punkte-Tiles), die Aktionsmaske und die geführte Exploration. Gemessen wird also nur der Wert des Gedächtnisses **als Netz-Eingabe**. Ohne Gedächtnis kann die Sicht keine Punkte-Tiles ableiten; diese Features sind dann immer 0.
- **`no_shaping`** entfernt alle Formungsterme: Potential, Explore, Discovery, Stack, Energie, Tod und Sap-Treffer. Übrig bleibt das, was direkt Punkte bzw. Siege bedeutet.
- **`no_canonical`**: Jedes der beiden Netze bekommt nur die Spiele seiner Seite, also **halb so viel Erfahrung**. Genau das ist der Preis, den die Spiegelung vermeiden soll. Die Gesamtzahl der Trainingsspiele ist gleich.
- **`baseline_prof_retrained`**: Der Prof-Code bleibt unverändert, d. h. konstantes ε = 0.1, Online-TD ohne Replay Buffer, Env-Reward wie geliefert. Vermieden wird nur der Speicher-Bug des Runners: Ein Agent wird einmal erzeugt und am Ende gespeichert.

## 3. Seeds (`scripts/protocol.py`)

| Menge | Seeds | Verwendung |
|---|---|---|
| Training | `run_seed · 10 000 + Spiel // 2`, alle < 100 000 | Training; jeder Seed einmal von jeder Seite |
| Validierung | 500 000 … 500 007 (8 Seeds) | Lernkurven, Tuning, Auswahl von Hyperparametern |
| Test | 900 000 … 900 029 (30 Seeds) | **nur** finale Auswertung |

- Die Mengen sind disjunkt; `train_seed()` prüft das per Assertion.
- Die Test-Seeds werden pro Lauf genau einmal gespielt, am Ende. Danach werden auf ihrer Basis keine Hyperparameter mehr geändert. Wird doch nachjustiert, muss das unter *Änderungen* stehen, und die alten Testzahlen gelten dann als „gesehen“.
- `np.random`/`random` werden pro Spiel mit dem Spiel-Seed gesetzt, weil `default` und der Prof-DQN globale Zufallszahlen nutzen. Damit ist jedes Testspiel reproduzierbar.

## 4. Ablauf eines Laufs (`scripts/experiment.py`)

1. torch/numpy/random werden mit `run_seed` gesetzt; die Netz-Initialisierung hängt davon ab.
2. **Training**: 3000 Spiele. Die Seite wechselt jedes Spiel.
   **Curriculum**: Die ersten 25 % der Spiele laufen gegen `default`, danach abwechselnd (je Seed-Paar) gegen `default` und `Solution_92_Kaggle`. Für alle trainierbaren Varianten ist der Ablauf identisch.
3. **Lernkurve**: Vor dem Training und alle 250 Spiele: 8 Validierungs-Seeds × 2 Seiten × 2 Gegner, mit ε = 0 und ohne Lernen.
4. **Test**: Die finalen Gewichte (kein „bester Checkpoint“, damit keine Auswahl auf Rauschen stattfindet) spielen 30 Test-Seeds × 2 Seiten × 2 Gegner = **120 Spiele**, mit ε = 0 und ohne Lernen.
5. **Trainingsstarts**: Für jede trainierbare Variante gibt es 3 Starts (`run_seed` 0, 1, 2), die sich in Netz-Initialisierung, Exploration und Trainings-Seeds unterscheiden. `baseline_prof` ist deterministisch und läuft einmal.

## 5. Kennzahlen pro Spiel

Die Kennzahlen stehen in `train.csv` und `eval.csv`; berechnet werden sie in `scripts/metrics.py` und `scripts/common.py`.

| Kennzahl | Definition |
|---|---|
| `result` | 1 Sieg, 0,5 Remis, 0 Niederlage (nach gewonnenen Matches) |
| `game_win`, `point_win` | Spielsieg; mehr Punkte als der Gegner, summiert über alle 3 Matches |
| `our_wins`/`opp_wins` | gewonnene Matches (0–3) |
| `our_points`/`opp_points` | Punkte, über die Matches summiert |
| `wait_frac` | Anteil der Unit-Steps mit Aktion 0 |
| `invalid_frac` | wirkungslose Aktionen: Rand, sichtbarer Asteroid, zu wenig Energie, Sap außer Reichweite |
| `greedy_masked_frac` | wie oft das unmaskierte argmax Q illegal war und die Maske eingreifen musste (nur Sherlock) |
| `sap_attempts`, `sap_hits` | Sap-Aktionen; davon mit sichtbarem Gegner im 3×3-Zielbereich |
| `stack_frac` | Anteil der Unit-Steps auf einem Tile mit weiterer eigener Unit |
| `relics_found` | bekannte Relics am Spielende (Belief; beim Prof-DQN: gesehene Relics) |
| `known_point_tiles` | bewiesene Punkte-Tiles am Spielende (nur Sherlock) |
| `epsilon`, `mean_loss` | pro Trainingsspiel (`train.csv`) |

`manifest.json` enthält Config, Seeds, Curriculum, Git-Commit (inkl. `dirty`), Paketversionen und Laufzeiten.

## 6. Statistik (`scripts/report.py`)

- **Primärer Endpunkt**: Winrate (`result`) der finalen Gewichte auf den Test-Seeds, getrennt nach Gegner.
- **Sekundär**: Match-Winrate, Punkte, Punktedifferenz.
- **Winrate einer Variante**: Mittelwert über alle Testspiele aller Starts. Dazu kommen:
  - **Mittelwert ± Standardabweichung über die 3 Starts**. Das zeigt, wie stark das Ergebnis vom Trainingsstart abhängt.
  - **95-%-Bootstrap-Konfidenzintervall** mit zwei Ebenen: Starts mit Zurücklegen ziehen, dann Test-Seeds mit Zurücklegen ziehen (beide Seiten eines Seeds bleiben zusammen). 10 000 Wiederholungen, Perzentil-Methode. So gehen die Streuung über Trainingsstarts und die über Karten beide ein.
- **Unterschied zu `full`**: gepaarter Bootstrap. In jeder Wiederholung wird **dieselbe** Seed-Stichprobe für beide Varianten gezogen; verglichen wird also Seed s, Seite p gegen Seed s, Seite p. Die Starts werden je Variante unabhängig gezogen. Berichtet werden Differenz und 95-%-KI. Ein KI, das 0 einschließt, heißt: **kein belegter Unterschied**.
- Bei 3 Starts und 30 Seeds sind die Intervalle breit. Unterschiede unter etwa 10 Prozentpunkten können wir nicht sicher auflösen, und das schreiben wir auch so in die Ergebnisse.
- Es gibt keine Korrektur für Mehrfachvergleiche (6 Ablationen × 2 Gegner). Einzelne knapp „signifikante“ Ergebnisse sind deshalb mit Vorsicht zu lesen.

## 7. Rechenbudget

Gemessen am 10.10.2026 auf dem Laptop (Apple Silicon, 5 Performance- und 10 Effizienz-Kerne, 24 GB RAM):

| Messung | Ergebnis |
|---|---|
| 1 Lauf allein | ≈ 1,0 s pro Trainingsspiel (inkl. Lernschritte) |
| 14 Läufe parallel (je 1 Thread) | ≈ 1,5 s pro Trainingsspiel, ≈ 350 MB RAM pro Prozess (Buffer noch nicht voll; voll ≈ +200 MB) |
| Evaluationsspiel (ohne Lernen) | ≈ 0,3–0,8 s |

Daraus ergibt sich bei 11 parallelen Prozessen und 22 Läufen (7 trainierbare Varianten × 3 Starts + 1):

- Ein Lauf: 3000 × ≈ 1,4 s ≈ 70 min Training, 13 × 32 Validierungsspiele ≈ 5 min, 120 Testspiele ≈ 1,5 min, zusammen ≈ 80 min.
- Bei 2 Wellen ergibt das **≈ 2,7 h Gesamtlaufzeit**, mit RAM-Spitze ≈ 11 × 0,6 GB ≈ 7 GB.

Warum 3000 Spiele: ε fällt nach ≈ 200 Spielen auf 0,05 (`eps_decay_steps = 60 000` Env-Steps). 3000 Spiele sind also rund 15-mal die Explorationsphase, und der 300k-Replay-Buffer wird ≈ 40-mal umgewälzt. Der gesamte Batch passt so bequem in eine Nacht und lässt Puffer für einen zweiten Durchlauf, falls ein Lauf abbricht. Mehr Spiele pro Lauf oder mehr Starts wären möglich. Wir halten das Budget trotzdem klein, um vor dem 16.10. noch iterieren zu können.

## 8. Befehle

```bash
.venv/bin/python -m pytest -q                                   # Tests müssen grün sein
.venv/bin/python -m scripts.run_experiments --games 3000 --workers 11
.venv/bin/python -m scripts.report                              # Tabellen + Diagramme + Markdown
```

## 9. Änderungen am Protokoll

| Datum | Änderung | Grund | Testdaten schon gesehen? |
|---|---|---|---|
| 10.10.2026 | Verbesserungsrunde `full_ft`: Weitertraining der 3 `full`-Starts (3000 Spiele, 70 % Solution_92, eigene Trainings-Seeds ab 200 000), Checkpoint-Auswahl nach Validierungs-Score, danach einmal Test | Testergebnis des Batches: gegen Solution_92 nur 18,9 %, Lernkurve steigt bis zum Ende | **ja** – die Entscheidung *dass* nachtrainiert wird, folgt aus den Testzahlen. Die `full_ft`-Testzahlen sind deshalb kein unabhängiger Vergleich mit dem Batch, sondern nur ein Hinweis. |
| 10.10.2026 | Agent-Ordner umbenannt: `agents/team_lux` → `agents/sherlock` (Teamname), Moodle-Gruppe 15. Die Läufe vom 10.10. liefen noch unter dem alten Namen; der Code ist sonst identisch. | Teamname festgelegt | nein |
| 10.10.2026 | Auswahl des Abgabe-Agenten: `full`-Start mit bestem Validierungs-Score (s0: 0,75 > s2: 0,60 > s1: 0,58) | Abgabe braucht einen konkreten Gewichtssatz | nein (Auswahl nur auf Validierung) |
| 11.10.2026 | Verbesserungsrunde 2 `full_ft2`: 3 Starts (Seeds 0–2) ab den Abgabe-Gewichten `full_s0`. Neu gegenüber `full_ft`: Replay Buffer wird vor dem Lernen mit 120 Spielen der eingefrorenen Policy aufgefüllt (ohne Lernen), Lernrate 1e-4 statt 3e-4, 50 % statt 70 % Solution_92, 16 statt 8 Validierungs-Seeds für die Checkpoint-Auswahl. Ab jetzt speichern `experiment.py` und `finetune.py` den Buffer (`*.buffer.npz`). | `full_ft` hat verschlechtert: Validierung schon nach 250 Spielen klar unter dem Startwert, weil mit leerem Buffer nur auf wenigen frischen Transitions gelernt wurde. Validierung mit 16 Spielen pro Gegner war zu verrauscht für die Auswahl. | **ja** (wie `full_ft`). Die Auswahl, ob die neuen Gewichte die Abgabe ersetzen, erfolgt nur über den Validierungs-Score; der Startpunkt (nach 0 Spielen) ist immer Kandidat. |
| 11.10.2026 | Neuer Abgabe-Agent: **Ensemble** `full_s012` (Q-Werte der 3 `full`-Starts gemittelt, eine .pth, `scripts/build_ensemble.py`). Auswahl auf 120 Validierungs-Seeds × 2 Seiten × 2 Gegner (`scripts/compare_weights.py`, gepaart mit `compare_report.py`): vs `full_s0` +3,7 pp gegen default (KI [−1,3; +8,3]), **+7,5 pp gegen Solution_92 (KI [+2,5; +12,9])**. Danach einmal Test (30 Seeds): default 91,7 % (`full_s0`: 85,0 %), Solution_92 20,0 % (`full_s0`: 20,0 %). | Einzelne DQN-Checkpoints schwanken stark (Validierung vs Solution_92 im Training zwischen 0 und 31 %); Mitteln mehrerer Netze glättet das. Backup der alten Abgabe: Tag `abgabe-review-full_s0`, `experiments/backup_abgabe_full_s0/`. | Auswahl nur auf Validierung; Test erst nach der Entscheidung. |
| 11.10.2026 | Ergebnis `full_ft2` (3 × 3000 Spiele ab `full_s0`): bester Validierungs-Score 0,688 (s0 nach 2250, s2 nach 2500 Spielen), s1 ohne Verbesserung (0,667). Ensemble aus 5 Netzen (`full_s012` + `full_ft2_s0` + `full_ft2_s2`) gegen `full_s012` auf 120 Validierungs-Seeds: −0,4 pp gegen default (KI [−4,6; +3,7]), +1,7 pp gegen Solution_92 (KI [−2,9; +6,7]) → **nicht belegt, Abgabe bleibt `full_s012`**. | Weitertraining derselben Methode bringt keinen messbaren Gewinn mehr; nächster Hebel ist Self-Play / Gegner-Pool. | Auswahl nur auf Validierung. |
| 11.10.2026 | Ergebnis Self-Play / Gegner-Pool `full_sp` (3 × 3000 Spiele ab `full_s0`, Gegner: 35 % Solution_92, 15 % default, 50 % Pool aus `full_s012`-Ensemble, `full_s1`, `full_s2` und eigenen Schnappschüssen alle 250 Spiele): bester Validierungs-Score 0,682 / 0,667 / 0,672 (Start 0,667). Ensemble `full_s012` + `full_sp_s1` + `full_sp_s2` gegen `full_s012` auf 120 Validierungs-Seeds: −2,1 pp gegen default (KI [−6,2; +2,1]), −0,4 pp gegen Solution_92 (KI [−5,4; +4,6]) → **kein Gewinn, Abgabe bleibt `full_s012`**. | Auch mit Gegner-Pool kein messbarer Fortschritt: Das MLP-DQN mit den jetzigen Features scheint ausgereizt. Nächster Hebel eher Architektur/Features (CNN auf Karten-Kanälen) oder gezielte Analyse der Niederlagen gegen Solution_92. | Auswahl nur auf Validierung. |
| 11.10.2026 | Niederlagen-Analyse gegen Solution_92 (`scripts/analyze_losses.py`, Ground Truth aus `env.state`, 80 Spiele): Gegner besetzt im späten Match ~1,7× so viele Punkte-Tiles, wir kennen am Matchende nur 1,8 / 3,4 / 5,0 Punkte-Tiles (Match 1/2/3, 100 % korrekt). Relics und aktive Punkte-Tiles sind zu jedem Zeitpunkt spiegelsymmetrisch (1818 Steps, 0 Verstöße), unser Belief nutzte das nicht. Neu: `use_symmetry` im Belief (Default aus). **Neuer Abgabe-Agent `full_s012_sym`** (gleiche Netze, Symmetrie an, kein neues Training): 120 Validierungs-Seeds vs `full_s012`: +0,8 pp gegen default (KI [−3,3; +5,0]), **+7,1 pp gegen Solution_92 (KI [+0,8; +13,3])**; bekannte Punkte-Tiles 3,4 / 6,5 / 8,6 (100 % korrekt). | Gezielte Ursachenanalyse statt mehr Training | Auswahl nur auf Validierung. |
| 11.10.2026 | `home_first` (Zielzuweisung: Ziele in gegnerischer Hälfte +600 Kosten) auf `full_s012_sym`, 120 Validierungs-Seeds: +1,3 pp gegen default (KI [−2,1; +4,6]), −1,3 pp gegen Solution_92 (KI [−5,8; +3,3]) → **kein Effekt, bleibt aus** (Schalter Default False). Danach keine weiteren Heuristik-Varianten auf denselben Validierungs-Seeds (Gefahr der Überanpassung an die Validierung). | Analyse: mit Symmetrie mehr eigene Tote (7,2 statt 5,8 pro Match), Verdacht: Ziele in gegnerischer Hälfte | Auswahl nur auf Validierung. |
| 11.10.2026 | Fehleranalyse Niederlagen gegen default (`full_s012_sym`): in 6 von 19 Niederlagen kein einziges Relic gefunden. Ursache: `explored` wird pro Match zurückgesetzt, der Agent erkundet jedes Match wieder zuerst dieselbe (falsche) Seitenecke; Relics in der anderen Seitenecke werden nie gesehen (mit Symmetrie häufiger, weil der Rest der Karte schneller als „erkundet“ gilt). Neu: `explore_memory` (Erkundungsziele, die in einem früheren Match schon gesehen wurden, +300 Kosten; `Belief.explored_ever`). **Neuer Abgabe-Agent `full_s012_sym_em`.** Entscheidung auf **120 neuen Validierungs-Seeds** (500 120–500 239, vorher nie benutzt): Spiele ohne gefundenes Relic 29 → 10 (McNemar exakt p = 0,0003), Winrate +2,1 pp gegen default (93,3 → 95,4 %, KI [−0,4; +5,0]), +3,3 pp gegen Solution_92 (28,7 → 32,1 %, KI [−1,7; +8,3]), beide Gegner gepoolt +2,7 pp (KI [0,0; +5,6]). | Gezielte Fehleranalyse; neue Seeds gegen Überanpassung an die bisherige Validierung | Auswahl nur auf Validierung (neue Seeds). |
| 11.10.2026 | Neutraining `full_sym` (3 × 3000 Spiele von Grund auf, `use_symmetry`, 16 Val-Seeds, ohne Test): Validierung schwankt stark (vs Solution_92 3–44 %). Kandidaten auf **120 neuen Seeds** (500 240–500 359) gegen die Abgabe `full_s012_sym_em`: `sym3` (3 neue Netze) +0,6 pp gepoolt (n. s.); **`old3_sym3` (6 Netze: 3 alte + 3 neue, Symmetrie + explore_memory)** −2,5 pp vs default (n. s.), +7,9 pp vs Solution_92 (KI [+1,7; +14,2]). Vorab festgelegte Bestätigungsregel (übernehmen, wenn auf weiteren 120 neuen Seeds vs default nicht signifikant schlechter und vs Solution_92 ≥ 0): Seeds 500 360–500 479: +0,8 pp vs default, **+19,6 pp vs Solution_92** (KI [+13,3; +26,3]) → erfüllt. Beide Runden (240 Seeds, 960 Spiele): default 95,0 → 94,2 % (−0,8, KI [−3,3; +1,7]), **Solution_92 27,9 → 41,7 % (+13,8, KI [+9,2; +18,3])**. **Neuer Abgabe-Agent `old3_sym3`.** Danach einmal Test (30 Seeds × 2 Seiten): **default 100 % (60/60), Solution_92 46,7 %** (`full_s0`: 85,0 % / 20,0 %). | Mehr unabhängig trainierte Netze im Ensemble glätten die DQN-Schwankungen weiter | Auswahl nur auf neuen Validierungs-Seeds, Test erst nach der Entscheidung. |
| 12.10.2026 | Niederlagen-Analyse des Abgabe-Agenten `old3_sym3` gegen Solution_92 (`analyze_losses.py`, Val-Seeds 500 000–500 039, 80 Spiele; nur Diagnose, keine Auswahl): Spiele gewonnen 47,5 % (`full_s012`: 20,0 %, `full_s012_sym`: 27,5 % auf denselben Seeds), bekannte Punkte-Tiles am Matchende 4,1 / 8,6 / 11,5 (100 % korrekt). Matchsiege je Match 46 / 44 / 40 %. Schwachpunkt Match 1: erster eigener Punkt im Median 7 Steps nach dem Gegner (Match 2: 2, Match 3: 0), 12 von 80 ersten Matches ohne eigenen Punkt; punkten wir zuerst oder gleichzeitig, gewinnen wir 53 % der Matches, sonst 34 %. Replays mit `old3_sym3` neu aufgenommen (`record_replay.py --weights`, 5 Testspiele, identisch mit `TEST_old3_sym3.csv`). | Ansatzpunkt für die nächste Verbesserungsrunde finden | Test-Seeds nur für Replays (bereits ausgewertete Spiele), keine Entscheidung daraus. |
| 12.10.2026 | Match-1-Schalter (Default aus, Abgabe unverändert): `early_inference` (Belief schließt vor match_step 50, sobald das Relic-Paar des Matches sicher gespawnt ist), `explore_grid` (Erkundungsziele je 4×4-Block), `scripted_explore` (Units mit reinem Erkundungsziel laufen heuristisch dorthin), `explore_stale=20` (Match 0: vor dem Relic-Fund gesehene Tiles veralten). Ursache aus `scripts/analyze_timing.py`: in Match 1 sehen wir das Relic im Median bei Step 42 (Solution_92: 32), in 12/80 nie; das Netz wartet am Matchanfang auf Energiefeldern. **Runde 1** (Seeds 500 480–500 539, je 120 Spiele/Gegner, gepaart vs `old3_sym3`): `m1_grid` +2,5 pp vs Sol92 (n. s.), `m1_grid_script` +1,7 (n. s.), **`m1_early` +0,8 vs default / +9,2 vs Sol92 (KI [+0,8; +17,5])**, **`m1_all` −0,8 / +15,0 (KI [+4,2; +25,8])**. **Vorab festgelegte Bestätigungsregel** für Runde 2 (neue Seeds 500 540–500 659, 120 Seeds × 2 Seiten × 2 Gegner): ein Kandidat gilt als bestätigt, wenn vs default nicht signifikant schlechter (KI-Obergrenze ≥ 0) und vs Sol92 Δ ≥ 0. Sind beide bestätigt, wird `m1_all` nur genommen, wenn es gepaart über beide Runden (180 Seeds) gegen `m1_early` vs Sol92 signifikant besser ist; sonst `m1_early` (einfacher: reine Logik im Belief, kein Eingriff in die Netz-Aktionen). Übernahme in die Abgabe erst nach dem Review am 16.10. | Fehleranalyse Match 1 | Auswahl nur auf neuen Validierungs-Seeds. |
| 12.10.2026 | **Runde 2** der Match-1-Schalter (neue Seeds 500 540–500 659, je 240 Spiele/Gegner, gepaart vs `old3_sym3`): `m1_early` +2,9 pp vs default (KI [+0,8; +5,0]), **+7,9 pp vs Sol92 (KI [+2,5; +13,3])**; `m1_all` +5,0 (KI [+2,5; +7,9]) / **+10,4 (KI [+3,3; +17,9])** → beide bestätigt. Beide Runden (180 Seeds, 360 Spiele/Gegner): Sol92 33,9 → 42,2 % (`m1_early`) bzw. 45,8 % (`m1_all`). `m1_all` vs `m1_early` gepaart: +0,8 vs default (KI [−0,8; +2,5]), +3,6 vs Sol92 (KI [−2,5; +9,7]) → nicht signifikant → nach der Regel **Kandidat für die nächste Abgabe: `m1_early`** (`python -m scripts.set_cfg experiments/ensembles/old3_sym3.pth experiments/ensembles/m1_early.pth early_inference=true`). Abgabe bleibt bis nach dem Review 16.10. `old3_sym3`; Test erst für den finalen Agenten zum 06.11. | Vorab festgelegte Bestätigungsregel | Auswahl nur auf neuen Validierungs-Seeds; Test-Seeds unberührt. |
