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
