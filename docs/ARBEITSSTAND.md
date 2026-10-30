# Gemeinsamer Arbeitsstand

Dieses Protokoll dient der Übergabe zwischen Mahmoud, Moayed, Claude Code und Codex. Neueste Einträge stehen oben. Gemeinsame Regeln und fachlicher Überblick: [CLAUDE.md](../CLAUDE.md). Messreihen und Entscheidungen über Agentenvarianten: [EXPERIMENT_PROTOKOLL.md](EXPERIMENT_PROTOKOLL.md).

Pro abgeschlossener Arbeit knapp festhalten: Datum und Bearbeiter, Änderung und Grund, tatsächlich ausgeführte Prüfungen, offene Punkte. Frühere Messergebnisse als solche kennzeichnen. Ein geplanter Schritt ist noch kein Auftrag zur Umsetzung. Änderungen werden für das andere Teammitglied erst nach Übertragung über Git und Aktualisierung seiner Arbeitskopie sichtbar; Chatverläufe gehören nicht automatisch dazu.


## 30.10.2026, 09:45 Berlin – Claude Code mit Mahmoud: Regelsatz R (`art_splash` + `sap_still_splash`) besteht beide Gegenproben und geht in die Runde-2-Kandidaten

Nach dem Plan-Nachtrag 30.10., 08:13 (Commit `288f17a`, vor den folgenden Ergebnissen). Alles auf Dev B (801000–801299), gepaart, Code aus der getrennten Arbeitskopie:

| Lauf | gegen | Δ (pp) |
|---|---|---|
| `art_splash` + `art_low_off` | `art_splash` allein, Solution_92/`sol92_sq` | ±0,0 [−0,8; +0,8] → `art_low_off` entfällt |
| `art_splash` + `sap_still_splash` | `art_splash` allein | **+0,7 [+0,1; +1,3]**, bei Streufaktor 1,0 +2,7 [+0,3; +5,5] → kommt dazu (Regel: ≥ +0,5) |
| V10 + R | V10, Solution_92/`sol92_sq` | **+1,4 [+0,6; +2,3]** (Solution_92 +1,0, `sol92_sq` +1,8; Streufaktor 1,0 +5,8 [+2,7; +9,2]; umkämpfte Karten +2,7 [+1,3; +4,2]) |
| Gegenprobe 1: V10 + R | V10, übriges Panel | `sol92_weak` +0,5, `old3_sym3` +0,7, default ±0,0 → hält (keiner unter −1) |
| Gegenprobe 2: `mix36` + `art_splash` | `mix36`, Solution_92/`sol92_sq` | +0,5 [+0,0; +1,1] → hält (nicht darunter) |

- Bei Streufaktor 0,25 und 0,5 ändert R in keinem der 2.270 betroffenen Dev-B-Spiele das Ergebnis. Die Regeln greifen nur bei sicher geschätztem 1,0.
- **Gleichheitsprüfung:** Mit ausgeschalteten Schaltern liefert der neue Code auf 48 Dev-A-Spielen (800000–800011, Solution_92 und `sol92_sq`) in allen Kennzahlen dieselben Werte wie die V10-Basis `B_V10_dev800.csv`.
- Screens: `mix30v8` Mittel 76,8 %, direkt nur 55,7 % (< 59,5 %) → nicht zugelassen. `mixrl54` 76,3 % / 62,3 % → zugelassen. Zugelassen sind damit bisher `mix36c` und `mixrl54`; `mix48` läuft noch (bis etwa 10:45).
- **Ablauf bis Runde 2:** Nach dem `mix48`-Screen kommt der Code in den Hauptstand. Danach werden die zugelassenen Mischungen mit eingebranntem R gebaut (`battle_<name>_as.pth`) und Runde 2 gestartet. Der `mix30old`-Screen der Linie 4 startet gegen 10:30 und läuft dann teils mit dem neuen Code; laut Gleichheitsprüfung spielt der mit ausgeschalteten Schaltern genau wie der alte.
- Abgabe unverändert V10 (`03cf8bdc…`).

## 30.10.2026, 07:55 Berlin – Claude Code mit Mahmoud: Wo V10 verliert, neue Regel `art_splash` auf Dev B bestätigt, `mix36c` für Runde 2 zugelassen

- **v8-Linie fertig** (06:47): 12 Netze je 1.500 Spiele, `battle_ftv8_12` SHA-256 `515760dd885b8282`; `mix30v8` und `mix48` gebaut, ihre Screens laufen. Validierung gegen Solution_92 (je 16 Spiele, nur Hinweis): Mittel der 12 Netze 76,6 % am Start, 81,2 % nach 1.500 Spielen. Laufdaten im Repo (Commit `9d66897`). **Linie 4** läuft seit 06:47 sauber (12 Prozesse, keine Fehler, um 07:01 bei Spiel 75 von 1.500).
- **Screen `mix36c`** (Dev A, gepaart gegen V10): Mittel über 6 Gegner 77,8 statt 72,1 % (Δ +5,67 [+3,14; +8,11]); Solution_92 +3,33 [+0,33; +6,33], `sol92_sq` +3,67 [+0,33; +7,17], `league_nets6` 59,0 % (+7,0), `threat6` 85,7 % (+4,3), V3 +9,2, V7 +6,5; direkt gegen V10 61,7 % [56,0; 67,0]. Beide Werte liegen über `mix36b` (76,2 % / 59,5 %), also ist `mix36c` nach der Regel von 04:09 zugelassen. `mixrl36` (76,1 % / 59,3 %) liegt knapp darunter und ist nicht zugelassen. `mixrl54`, `mix30v8` und `mix48` laufen noch.
- **Wo V10 verliert** (keine neuen Spiele): 5.200 Spiele V10 gegen Solution_92 und `sol92_sq` (Dev A, Auswahl und Bestätigung Runde 1, zusammen 1.300 Karten), verknüpft mit den versteckten Spielparametern und der Relic-Lage jeder Karte aus `env.reset`. Skripte und Daten liegen unter `experiments/analysis/battle_params_20261030/`.

| Merkmal der Karte | Siegquote V10 |
|---|---|
| Sap-Streufaktor 0,25 / 0,5 / 1,0 (versteckt) | 89,1 / 84,5 / 78,9 % |
| Sap-Reichweite 3 / 4 / 5 / 6 / 7 | 91,7 / 87,7 / 79,8 / 82,2 / 79,3 % |
| Relic höchstens 5 Felder von der Mittellinie x + y = 23 (658 Karten, gleich weit von beiden Starts) / sonst | 76,4 / 92,1 % |
| Bewegungskosten 1 / 5 | 79,0 / 88,6 % |
| Sichtweite 1 / 2 / 3 / 4 | 81,4 / 81,5 / 84,3 / 89,8 % |
| Relic-Paare 1 / 2 / 3 | 90,7 / 81,2 / 80,4 % |

  Umkämpfte Karte mit starkem Sap (Streufaktor 1,0 oder Reichweite ≥ 5): 73 %. Keines von beiden: 97 %.
- **40 dieser Spiele nachgespielt** (gegen Solution_92 auf umkämpften Karten mit starkem Sap, je 20 verloren und gewonnen, Wahrheit aus dem Env-Zustand, `contested_probe.py`). Verlorene Spiele kippen in Match 2 und 3: Match 1 gewinnen wir dort noch in 60 %, Match 2 und 3 nur in 10 und 15 %. Je Match verlieren wir 16,6 und 15,9 Einheiten, der Gegner 11,8 und 12,0. Wir besetzen im Mittel 2,0 und 2,8 Punktefelder, der Gegner 3,2 und 4,1.
- **Frühere Dev-A-Tests nach Streufaktor neu ausgewertet** (keine neuen Spiele, gepaart gegen V10, Solution_92 und `sol92_sq`): aggressivere Artillerie (`art_safe=false` + `art_min_hits=2`) bei Streufaktor 0,25 / 0,5 / 1,0 **−6,5 [−10,9; −2,3] / −0,8 / +6,0 [+2,4; +9,5]** pp, insgesamt −0,2. Ihre Wirkung kehrt sich also mit dem Streufaktor um. Er steht nicht in `env_cfg`, `param_est` schätzt ihn aber aus den Energieverläufen der eigenen Einheiten. Nach Sichtweite, Bewegungskosten und Reichweite zeigt keiner der früheren Tests ein solches Muster.
- **Neue Regel `art_splash`** (Standard aus): Ist der Streufaktor laut `param_est` sicher 1,0, sappt die Artillerie schon ab 2 Treffern und auch in gegnerischer Reichweite, sonst wie V10. **Dev B** (801000–801299, von dieser Analyse unberührt, 1.200 Spiele gepaart gegen V10): **+0,8 pp [+0,2; +1,3]** (87,9 statt 87,2 %); Solution_92 +0,7 [−0,2; +1,5], `sol92_sq` +0,8 [+0,2; +1,7]. Bei Streufaktor 1,0 **+3,1 [+1,0; +5,5]**, bei 0,25 und 0,5 genau 0: Die Regel hat dort in 908 Spielen nie eingegriffen, es gab also keine falsche Schätzung „1,0“.
- **Wann die Schätzung sicher ist** (20 Spiele auf Dev-B-Karten mit Streufaktor 1,0): 4-mal in Match 1, 9-mal in Match 2, einmal in Match 3, 6-mal nie. Die Regel wirkt also vor allem in Match 2 und 3, wo die Spiele kippen. Ein Entwurf, der zusätzlich den Streuschaden eigener Saps an Gegnern auswertet, war nur in 4 von 48 Spielen früher sicher und wurde verworfen. Nebenbefund aus diesen 48 Spielen: Auch der heutige Schätzer ist in 3 Spielen zeitweise sicher falsch (zweimal 0,25 statt 0,5, einmal 0,5 statt 1,0), aber nie fälschlich 1,0. V10 nutzt die Streufaktor-Schätzung nicht.
- **Entwickelt in einer getrennten Arbeitskopie** (Basis `9d66897`), damit die laufenden Screens im Hauptstand unverändert bleiben. Patch `experiments/analysis/battle_params_20261030/art_splash.patch`, Tests `tests/test_art_splash.py` (89 Regeltests grün). Mit ausgeschalteten Schaltern ändert der Patch nichts am Verhalten: Er liest nur zusätzliche Schalter. Die Messungen auf Dev B liefen aus der Arbeitskopie (`DB_artsplash.csv`).
- **Laufen auf Dev B:** `art_low_off` (keine Artillerie, solange der Streufaktor sicher 0,25 ist), `sap_still_splash` (bei sicher 1,0 dürfen Halter auch ziehende Gegner sappen; die Engine bewegt vor dem Sap, ein Schritt neben dem Zieltile bekommt den vollen Schaden) und `art_splash` gegen den Rest des Panels (`sol92_weak`, `old3_sym3`, default).
- **Nächste Schritte:** Code nach dem Ende der Screens und vor Runde 2 in den Hauptstand übernehmen. Ob die Runde-2-Kandidaten mit eingebranntem `art_splash` laufen, legt ein Plan-Nachtrag fest, bevor auf 805000–807399 gemessen wird.
- Abgabe unverändert V10 (`03cf8bdc…`).

## 30.10.2026, 05:35 Berlin – Claude Code mit Mahmoud: Bestätigung von `mix36b` nicht bestanden, Abgabe bleibt V10

- **Bestätigung Runde 1** (803000–803799, je Gegner 1.600 Spiele; direkt 804000–804399, 800 Spiele; Ende 05:32, Log `experiments/pipeline_battle_gate.log`): R 88,7 statt 86,9 %, **Δ +1,77 pp [+0,64; +2,95]**. Die Hürde verlangt Δ ≥ +2 pp, deshalb **nicht bestanden**. Alle übrigen Hürden sind erfüllt: untere Grenze > 0, Solution_92 Δ +0,38 [−1,19; +2,00], default 99,9 % (Δ +0,06), direkt gegen V10 56,6 % [51,75; 61,5].

| Gegner (gepaart, 800 Karten) | V10 | `mix36b` | Δ (pp) |
|---|---|---|---|
| Solution_92 | 90,6 | 90,9 | +0,38 [−1,19; +2,00] |
| `sol92_sq` | 77,6 | 82,1 | +4,44 [+2,44; +6,50] |
| `sol92_weak` | 90,9 | 91,1 | +0,25 [−1,31; +1,75] |
| `old3_sym3` | 88,6 | 90,6 | +2,00 [−0,38; +4,50] |
| default | 99,8 | 99,9 | +0,06 |

- Einordnung: In der Auswahl lag `mix36b` bei +2,88. Dass der gewählte Kandidat auf frischen Karten schwächer abschneidet, war zu erwarten (der beste von vier Kandidaten wird überschätzt). Der Vorteil ist echt, aber kleiner als die vorab verlangte Mindestgröße, und er entsteht vor allem gegen `sol92_sq`. Gegen Solution_92 selbst ist kein Unterschied messbar.
- **Folgen laut Plan-Nachtrag 30.10., 04:09:** Referenz in Runde 2 bleibt V10. `mix36b` wird nicht auf neuen Karten wiederholt. Die für eine `mix36b`-Referenz vorgesehenen Änderungen (`--direct-opponent` in `league_gates.py`, `REF`/`REFNAME` im Gate-Skript) entfallen. `pipeline_battle_gate.sh` deckt Runde 2 mit V10 als Referenz schon ab (805000–807399).
- **Dev-A-Screen, nur Information** (300 Karten, gepaart gegen V10; `python -m scripts.screen_table`): Gegen den zurückgehaltenen RL-Gegner `league_nets6` gewinnen `mix36` und `mix36b` je **59,0 % statt 52,0 %** (V10). Mittel über die 6 Gegner: V10 72,1, `mix36` 76,9 (Δ +4,78 [+2,14; +7,33]), `mix36b` 76,2 (Δ +4,06 [+1,75; +6,39]). Gegen RL-Gegner bringen die Mischungen also mehr als gegen die Solution_92-Familie, die das Gate-Panel prägt. Das ist eine Beobachtung auf Entwicklungskarten, kein Nachweis.
- **Wo `mix36b` auf den frischen Karten gewinnt** (Bestätigungsdaten, keine neuen Spiele; Relic-Zahl einer Karte = größte Zahl gefundener Relics über alle 20 Spiele beider Agenten auf ihr): Gegen `sol92_sq` auf Karten mit 6 Relics **+8,3 pp [+4,0; +12,5]** (236 Karten), mit 4 Relics +3,5 [0,0; +7,2], mit 2 Relics +2,4 [−0,6; +5,4]. Gegen Solution_92 kein klares Muster (4 Relics −2,4 [−5,9; +0,7]). Die Häufung auf 4-Relic-Karten aus Dev A wiederholt sich also auch hier nicht; das Nachtraining hilft vor allem auf Karten mit vielen Relics gegen `sol92_sq`. Auf 68 Karten mit ungerader Zahl (ein Relic nie gefunden) gewinnt V10 deutlich seltener (74–79 %).
- **Gewichtung in den Mischungen geprüft** (20.000 Zustände aus dem Replay-Buffer von `20261029_ft_v10_s10`, keine Spiele): Die Spanne der erlaubten Q-Werte ist bei V10-Netzen (Mittel 1,18) und nachtrainierten Netzen (ft2 1,06, ft3 1,01, ftrl 1,08) ähnlich. Die Mischung wählt in 92,8 % der Zustände dieselbe Aktion wie V10 und in 91,6 % dieselbe wie ft2_18 allein; keine Hälfte überstimmt die andere. Eine Normierung der Q-Werte vor dem Mitteln lohnt sich deshalb nicht.
- **Werkzeuge für die nächsten Runden** (Commit `6bb2314`): `python -m scripts.screen_table --admit NAMEN` wendet die Zulassungsregel vom 04:09 mechanisch an (bricht ab, solange ein Screen oder Direktduell fehlt). `scripts/pipeline_battle_round.sh RUNDE NAME…` macht Auswahl je Kandidat, Wahl und Bestätigung; die Wahl wird nur aus Log-Zeilen nach dem eigenen Aufruf gelesen, damit kein altes `AUSWAHL:` greift. `pipeline_battle_gate.sh` kennt jetzt Runde 3 im Reserveblock (808000–809599), zu benutzen erst nach einem Plan-Nachtrag. Tests: `test_screen_table.py` und `test_league_gates.py` 8 bestanden; `bash -n` und die Argumentprüfungen beider Skripte ausprobiert.
- **Linie 4 „Altnetze“ vorbereitet** (Plan-Nachtrag 05:45, vor jedem Screen von `mix36c`, `mixrl54`, `mix30v8`, `mix48`): 12 nie abgegebene, nicht zurückgehaltene Quellnetze (6 × `full_rules_v6`, 6 × `full_rules_fo`) unter allen V10-Regeln wie die v8-Linie, je 1.500 Spiele, Seeds 0–9, 28, 29, Kartenversatz 0. `scripts/pipeline_battle_ftold.sh` läuft seit 05:47 und wartet auf das Ende der v8-Linie (gegen 07:05). Danach `battle_ftold12`, `mix30old` (V10 + ftold12) und ihr Dev-A-Screen. Rauchtest mit je 2 Spielen für `v6_s27` (Seed 0) und `fo_s35` (Seed 29): 300.000 Transitions geladen, V10-Regeln an, Trainingskarten 200000–200001 bzw. 490000–490001, Status `done`; Rauchtest-Ordner gelöscht.
- Abgabe unverändert V10 (`03cf8bdc…`).
- **Offen:** Screens von `mix36b` (Direktduell), `mixrl36`, `mixrl54`, `mix36c`, `mix30v8`, `mix48` bis etwa 10:30. Danach Zulassung zu Runde 2 nach den Regeln vom 04:09, Auswahl 805000–805399, Bestätigung 806000–807399. Linie 4 bis etwa 11:00, Screen danach. Folie 11 auf die Battle-Woche umstellen, sobald Runde 2 entschieden ist.

## 30.10.2026, 03:24 Berlin – Claude Code mit Mahmoud: Runde 3 fertig, v8-Linie und Morgen-Screen gestartet, `mix36c` als weiterer Screen-Kandidat

- **Runde 3 des Nachtrainings** ist um 03:15 fertig (18 Netze je +2.000 Spiele, Kartenversatz 2000): `battle_ft3_18`, SHA-256 `c556cd6cb0161708`, wie in Runde 1/2 aus den Endständen. Laufdaten (Manifest, Log, Trainings- und Validierungskurven) und `experiments/pipeline_battle_ft3.log` jetzt im Repo.
- **v8-Linie** um 03:16 automatisch gestartet: 12 Trainingsprozesse laufen, Pool-Gegner werden geladen, erste Validierung geschrieben. Der **Morgen-Screen** startete ebenfalls um 03:16 (zuerst V10 gegen die zurückgehaltenen Gegner).
- **Neuer Screen-Kandidat `mix36c`** = V10 + `ft3_18` mit V10-Config (SHA-256 `e8b0de223fee12f3`), festgelegt im Plan-Nachtrag 30.10., 03:23, vor jeder Messung mit `ft3_18`. Der Screen steht in der Entwicklungs-Warteschlange (`experiments/battle_queue.txt`) und läuft erst nach dem Nachtablauf, damit die Bestätigung nicht gebremst wird.
- Der Rechner ist voll ausgelastet (32 Rechenprozesse auf 15 Kernen). Das Ergebnis der Bestätigung von `mix36b` kommt deshalb eher gegen 06:00–07:00 als gegen 05:00. Die V10-Hälfte der Bestätigung (8.000 Spiele) war um 02:59 fertig.
- Abgabe unverändert V10 (`03cf8bdc…`).

## 30.10.2026, 01:50 Berlin – Claude Code mit Mahmoud: Auswahl Runde 1 wählt `mix36b`, Bestätigung läuft; dritte Trainingslinie vorbereitet

- **Auswahl Runde 1** (802000–802399, je Gegner 400 Spiele, direkt 400 Spiele auf 802200–802399; Hürden `scripts/league_gates.py`, Log `experiments/pipeline_battle_gate.log`):

| Kandidat | R (Δ zu V10) | Solution_92 | `sol92_sq` | `sol92_weak` | `old3_sym3` | default | direkt gegen V10 | Ergebnis |
|---|---|---|---|---|---|---|---|---|
| V10 (Referenz) | 88,5 % | 89,5 | 81,2 | 92,0 | 91,2 | 99,5 | – | – |
| `mix36` (V10 + ft18) | 89,9 (+1,44 [−0,62; +3,50]) | 94,8 | 82,3 | 92,5 | 90,2 | 99,8 | 58,5 [52,0; 65,0] | R-Hürde um 0,06 pp verfehlt |
| `ft2_18` (Runde 2 allein) | 90,0 (+1,50 [−0,69; +3,69]) | 90,0 | 85,3 | 91,7 | 93,0 | 99,5 | 63,5 [57,0; 70,0] | bestanden |
| **`mix36b`** (V10 + ft2_18) | **91,4 (+2,88 [+0,69; +5,06])** | 93,5 | 85,3 | 95,5 | 91,2 | 99,5 | 55,5 [48,5; 62,5] | **bestanden, gewählt** |
| `mix54` (V10 + ft18 + ft2_18) | 90,6 (+2,12 [+0,19; +4,00]) | 91,5 | 84,5 | 92,7 | 93,8 | 100 | 65,0 [58,5; 71,5] | bestanden |

  Gewählt wird nach der Regel der Kandidat mit dem größten R unter den bestandenen. Gegen Solution_92 liegt `mix36b` bei +4,0 pp [+0,75; +7,50]. Direkt gegen V10 sind Mischungen mit den V10-Netzen näher an 50 % als `ft2_18` oder `mix54`, weil sie V10 ähnlicher spielen.
- Die Code-Kennung im Log wechselt nach `mix36` von `cc8dba4` auf `1de55a8` (Commits während des Laufs). `git diff cc8dba4 1de55a8` für `agents/`, `lux/`, `par_eval`, `common` und `league_gates` ist leer; spielrelevant also derselbe Code.
- **Bestätigung `mix36b`** (803000–804399: 8.000 Spiele V10, 8.000 `mix36b`, 800 direkt) läuft seit 01:43, Ergebnis gegen 05:00. Die Abgabe bleibt V10, bis sie bestanden ist und die Übernahme mit `scripts/release_candidate.py` dokumentiert ist.
- **Wo die Gewinne entstehen** (Auswertung vorhandener Dev-A-Daten, keine neuen Spiele): Auf Karten mit 4 gefundenen Relics bringt das Orakel mit wahren Relics und Punktefeldern +11,5 / +8,9 pp (`sol92_sq` / Solution_92), nur Punktefelder +6,7 / +6,7, nur Relics +4,7 / +4,2. Auf Karten mit 2 Relics bringt das Orakel etwa nichts. `mix36` holt seinen Vorsprung an derselben Stelle: +9,6 / +6,8 auf 4-Relic-Karten, 0 auf 2-Relic-Karten. Die bisher getesteten Regeln für dieses Problem (`opp_point_infer`, `relic_scout`) brachten nichts; die nachtrainierten Netze schon. **Gegenprobe auf den Auswahlkarten** (802000–802199, `mix36b` gegen V10, Mittel über die 4 Panel-Gegner): 2 Relics +1,9, 4 Relics +1,6, 6 Relics +6,3 pp (je 58–65 Karten). Die Häufung auf 4-Relic-Karten wiederholt sich dort nicht; belastbar ist nur, dass das Nachtraining auf Karten mit mehreren Relic-Paaren eher mehr bringt.
- **Runde 4 der Hauptlinie entfällt** (Runde 2 ohne Zusatznutzen, Runde 3 mit flachen Trainingskurven). Stattdessen **dritte Trainingslinie „v8-Linie“** (Plan-Nachtrag 30.10., 01:50; `scripts/pipeline_battle_ftv8.sh`): die 12 Netze `full_rules_v8` vom 22.10. unter allen V10-Regeln, je 1.500 Spiele, Seeds 10–21, Kartenversatz 3000 (Bereich der gestrichenen Runde 4), Gegnermix der geplanten Runde 4. Startet automatisch nach Ende von Runde 3, 12 parallel. Danach `mix30v8` (V10 + ftv8_12) und `mix48` (V10 + ft2_18 + ftv8_12) im Dev-A-Screen; zusätzlich `mix36b` als Vergleich. Maßstab für Runde 2 ist jetzt `mix36b` statt `mix36` (festgelegt vor allen diesen Screens).
- Prüfungen: `bash -n`; Rauchtest `finetune` mit dem Init-Lauf `20261022_full_rules_v8_s70_sol70` und genau diesen Argumenten über 2 Spiele: lädt 300.000 Transitions, V10-Regeln an (`sap_still`, `reach_assign`), Trainingskarten 303000–303001, Status `done`. Der Rauchtest-Ordner wurde danach gelöscht. Der Kopfkommentar des laufenden Skripts nennt noch „02:10“ statt 01:50 (laufende Skripte werden nicht bearbeitet; Korrektur nach Ende). Die Startgrenze von `finetune` (Seed ≤ 29) erlaubt keine Seeds 30–41, deshalb Seeds 10–21 mit eigenem Kartenversatz.
- **Läuft Sherlock beim Prof?** Laut README der Kursvorlage nutzt er Windows mit Python 3.10+ und installiert Pakete ohne Versionsangabe. Neues Skript `scripts/xversion_replay.py`: `record` spielt mit der Battle-Zip ein echtes Spiel wie der Kurs-Runner mit `train=True` (Sherlock gegen Sherlock, beide Seiten) und zeichnet Beobachtungen und Aktionen auf. `replay` spielt dieselben Beobachtungen in einer anderen Umgebung nach und zählt abweichende Aktionen. Geprüft mit einer `mix36b`-Zip (nur Scratchpad, 22,2 MB, Prüfung von `build_submission --battle` bestanden) auf den Karten 4242 und 7311: **0 abweichende Aktionen in 303 Schritten** unter Python 3.10.15 mit torch 2.14.1/numpy 2.2.6 und mit torch 2.2.2/numpy 1.26.4 (eigene venvs im Scratchpad, Python-Build von python-build-standalone mit geprüfter SHA-256). Ebenso die `--half`-Zip (10,7 MB) mit torch 2.2.2. Der Agenten-Code nutzt keine plattformabhängigen Module und öffnet keine Textdateien. Windows selbst konnte ich nicht testen.
- Abgabe unverändert V10 (`03cf8bdc…`).
- **Offen:** Ergebnis der Bestätigung (gegen 05:00). Morgen-Screen (V10/`mix36` gegen die zurückgehaltenen Gegner, `mixrl36`, `mixrl54`). v8-Linie bis etwa 07:30, danach ihre Screens. Nachtrag mit höchstens 3 Kandidaten für Runde 2 vor deren Start.

## 29.10.2026, 23:55 Berlin – Claude Code mit Mahmoud: Runde 2 fertig, Auswahl Runde 1 läuft, Morgen-Screen mit zurückgehaltenen RL-Gegnern vorbereitet

- **Runde 2 vollständig** (18 Netze, je 2.000 Spiele, Ende 23:29), Ensemble `battle_ft2_18` (`0a05d938…`). Der Nachtablauf hat `mix36b` (V10 + ft2_18, 24,0 MB) und `mix54` (V10 + ft18 + ft2_18, 35,1 MB) gebaut und um 23:30 die **Auswahl Runde 1** gestartet. V10-Referenz auf 802000–802199 (je Gegner 400 Spiele): Solution_92 89,5 %, `sol92_sq` 81,2 %, `sol92_weak` 92,0 %, `old3_sym3` 91,2 %, default 99,5 %, also R 88,5 %. Tempo etwa 98 Spiele/min mit 8 Workern neben 12 Trainingsprozessen. Die Auswahl ist voraussichtlich gegen 02:00 fertig, danach folgt die Bestätigung des gewählten Kandidaten.
- **Trainingsverlauf der Einzelnetze** (ε = 0,05; erstes / mittleres / letztes Drittel der Spiele):
  - RL-Liga (6 von 18 Netzen fertig): Solution_92 59 / 64 / 67 %, `sol92_sq` 45 / 49 / 50 %, eigene Abgaben im Pool 29 / 34 / 35 %, `battle_mix36` 15 / 13 / 17 %.
  - Runde 3 (6 von 18 fertig): Solution_92 71 / 69 / 70 %, `sol92_sq` 56 / 59 / 54 %, Pool 46 / 51 / 47 %. Kein weiterer Anstieg gegenüber Runde 2 (Solution_92 66 / 67 / 66 %).
- **Neu, nur Entwicklung:** `scripts/battle_screen.sh` und `scripts/pipeline_battle_morning.sh` (Plan-Nachtrag 29.10., 23:55). Der Screen misst zusätzlich gegen zwei **zurückgehaltene RL-Gegner, gegen die nie trainiert wurde**: `league_nets6` (6 Netze vom 26.10., V10-Regeln) und `threat6` (6 Gefahr-Netze, V3-Regeln). Er startet automatisch nach Ende von Runde 3 mit V10 und `mix36`. Nach Ende der RL-Liga folgen `mixrl36` (V10 + ftrl18) und `mixrl54` (V10 + ft18 + ftrl18).
- Prüfungen: Auswertungscode des Screens auf vorhandenen Dev-A-Daten durchgelaufen (umbenannte Kopie im Scratchpad). Rauchtest V10 gegen beide zurückgehaltenen Gegner auf Karte 999990: beide laden mit 6 Netzen, 4/4 Spiele ohne Fehler. `bash -n` für beide Skripte.
- **Dateigröße, Vorsorge (noch nicht benutzt):** `python -m scripts.build_submission --battle --half` speichert die Netzgewichte als float16 und lässt den Optimierer-Zustand weg. Der Agent rechnet weiter in float32; `load_state_dict` wandelt beim Laden um, der Agenten-Code ist unverändert. Messung auf 50.000 Zuständen aus dem Replay-Buffer von `20261029_ft_v10_s10`: Die beste erlaubte Aktion ändert sich in 0,008 % der Fälle (`mix36`) bzw. 0,006 % (`mix54`), größte Q-Abweichung 0,007. `mix36` als Battle-Zip: **10,7 statt etwa 22 MB**. Kursprüfung in beiden Ordnerlagen bestanden, auch eingefroren mit `train=True` (nur Scratchpad). Standard bleibt ohne `--half`. Nur nutzen, wenn Moodle die Dateigröße begrenzt.
- **Auffälligkeit für die Fehlersuche** (vorhandene Dev-A-Daten, V10): Siegquote nach Zahl der gefundenen Relics (2 / 4 / 6): `sol92_sq` 87,0 / 69,9 / 77,8 %, Solution_92 92,7 / 84,1 / 92,4 %, V7 68,3 / 60,0 / 48,6 %. Gegen die Solution_92-Familie verliert V10 also vor allem auf Karten mit 4 Relics.
- Tests: ganze Suite 487 bestanden (ohne `test_early_curriculum_study`, Ressourcensperre), darunter 1 neuer Test für `--half`.
- Abgabe unverändert V10 (`03cf8bdc…`).
- **Offen:** Ergebnis von Auswahl und Bestätigung. Moodle-Dateigrenze klären (36 Netze ≈ 22 MB Zip, 54 Netze ≈ 33 MB, mit `--half` etwa die Hälfte).

## 29.10.2026, 21:05 Berlin – Claude Code mit Mahmoud: Runde 2 ohne Zusatznutzen, zweite Trainingslinie „RL-Liga“ gestartet

- **Runde 2 auf denselben 6 Netzen** (Dev A, gepaart): `ft2_6` gegen `ft6` (Runde 1) `sol92_sq` 79,8 statt 82,2 % (−2,3 [−5,8; +1,0]), Solution_92 89,0 statt 89,2 % (−0,2 [−3,2; +2,8]); gegen V10 +2,0 / −0,3. Weitere 2.000 Spiele derselben Art verbessern das Ensemble also nicht messbar, obwohl die Trainingskurven der Einzelnetze steigen.
- Deshalb **zweite Trainingslinie** (`scripts/pipeline_battle_ftrl.sh`, Plan-Nachtrag 21:00): dieselben 18 V3-Quellnetze wie Runde 1, je 1.500 Spiele, Kartenversatz 4000. **Die Hälfte der Spiele läuft gegen eigene RL-Abgaben** (V10, `old3_sym3`, `battle_mix36`, V3, V7), der Rest gegen Solution_92 0,20, `sol92_sq` 0,20, `sol92_weak` 0,05 und default 0,05. Ziel: vielfältigere Netze, und mehr Stärke gegen Agenten aus Netz und Regeln, wie sie andere Teams haben dürften. Seit 20:56 laufen 6 Netze, Ensemble `battle_ftrl18` voraussichtlich gegen 06:00.
- Erster Start um 20:55 abgebrochen: Kartenversatz 5000 verletzt die Schutzregel in `finetune` (`map_offset + games/2 <= 5000`, Grenze zu den Auffüllkarten). Es wurden keine Läufe angelegt. Log `experiments/pipeline_battle_ftrl_fehlstart.log`.
- Runde 4 startet nicht mehr automatisch. Die Entscheidung fällt nach der Auswahl Runde 1, die zeigt, ob `ft2_18` mehr bringt als Runde 1. Runde 3 läuft weiter.

## 29.10.2026, 19:45 Berlin – Claude Code mit Mahmoud: Gegenprobe Dev B für mix36, Runde 4 vorbereitet

- **`mix36` auf Dev B** (801000–801299, ganzes Panel, je Gegner 600 Spiele, gepaart gegen V10): `sol92_sq` 84,8 % (V10 83,2 %, +1,7 [−1,2; +4,7]), Solution_92 92,7 % (91,2 %, +1,5 [−1,0; +3,8]), `sol92_weak` 92,3 % (±0), `old3_sym3` 92,7 % (91,7 %, +1,0 [−2,7; +5,0]), default 100 %. Die Schwäche gegen `old3_sym3` auf Dev A (−3,3) bestätigt sich nicht. Der Vorsprung gegen `sol92_sq` ist kleiner als auf Dev A (+5,2). Gesamtbild beider Blöcke: R etwa +1,3 pp. Für die Bestätigungshürde (+2 pp) reicht das voraussichtlich nicht; deshalb weiteres Nachtraining.
- Trainingskurven (Einzelnetz, ε = 0,05): gegen Solution_92 61 → 72 %, `sol92_weak` 64 → 74 %, `sol92_sq` 48 → 52–56 %; gegen den Pool aus eigenen Ensembles bleibt es bei etwa 41–48 % ohne Anstieg. **Runde 4** (`scripts/pipeline_battle_ftn.sh 4 …`, startet automatisch nach dem Ende von Runde 2) deshalb mit mehr und vielfältigeren RL-Gegnern: Mix Solution_92 0,30, `sol92_sq` 0,25, `sol92_weak` 0,10, **Pool 0,25** (V10, `old3_sym3`, `battle_mix36`, **V3- und V7-Abgabe**), RushBot 0,05, default 0,05.
- **RL-Gegner und Direktduell** (Dev A, 4 Worker, nur Einschätzung, keine Auswahl; `par_eval --first 300000 --n 300`, Ausgaben `B_V10_rl.csv`, `D_mix36_rl.csv`, `D_mix36_direct.csv`): gegen die frühere Abgabe **V3** `mix36` 75,7 % statt 72,2 % (+3,5 [−2,7; +9,3]), gegen **V7** 66,7 % statt 60,2 % (+6,5 [−0,5; +13,2]); **direkt gegen V10 58,0 % [52,7; 63,7]** aus 600 Spielen. Gegen RL-Agenten mit ähnlicher Spielweise ist der Gewinn also größer als gegen die Solution_92-Familie.
- Upload: Mahmoud lädt **nur einmal am Ende** hoch (04.11., nach allem Training), keine Zwischenstände. Bis dahin ist `Gruppe15.zip` nur ein lokaler Prüfstand.
- Auslastung: 12 Trainings- und 8 Messprozesse auf 15 Kernen (5 Leistungs-, 10 Effizienzkerne). Training 115 statt 92 Spiele/min, Messung 86 statt 105 Spiele/min. Insgesamt etwa gleich, die Überbelegung kostet also nichts.

## 29.10.2026, 19:15 Berlin – Claude Code mit Mahmoud: 18 nachtrainierte Netze gemessen, Nachtablauf geplant, Battle-Abgabe gegen train=True abgesichert

- **Erste Nachtrainingsrunde fertig** (alle 18 Netze, je 1.500 Spiele). Dev A, alle mit V10-Config:

| Ensemble | `sol92_sq` | Solution_92 | `sol92_weak` | `old3_sym3` | default |
|---|---|---|---|---|---|
| V10 (Basis) | 77,8 % | 89,3 % | 89,5 % | 89,3 % | 99,8 % |
| `ft18` (nur nachtrainiert) | 77,7 (−0,2 [−4,0; +3,7]) | 90,3 (+1,0 [−2,0; +4,0]) | – | – | – |
| **`mix36`** (V10 + ft18, 36 Netze) | **83,0 (+5,2 [+1,7; +8,7])** | 90,8 (+1,5 [−1,5; +4,5]) | 92,0 (+2,5 [−0,2; +5,3]) | **86,0 (−3,3 [−7,7; +1,0])** | 100 (+0,2) |

  `mix36` ist auf Dev A die beste Mischung (R ≈ 88,0 statt 86,5 %), aber gegen unsere alte Abgabe `old3_sym3` schlechter. Ob das Zufall ist, prüft der laufende Dev-B-Lauf (ganzes Panel, zweiter von höchstens sechs Dev-B-Läufen). `relic_scout=2` −2,2 / −2,2 pp (Auswertung von Hand nachgetragen, weil das Messskript während des Laufs geändert worden war; die Spiele selbst waren vollständig).
- **Nachtablauf vorab festgelegt** (Plan-Nachtrag 29.10., 19:00, `scripts/pipeline_battle_night.sh` in der Warteschlange): Nach Runde 2 werden `mix36b` (V10 + ft2_18) und `mix54` (V10 + ft18 + ft2_18) gebaut. Danach läuft die Auswahl Runde 1 (802000–802399) für `mix36`, `ft2_18`, `mix36b` und `mix54`, anschließend die Bestätigung (803000–804399) nur für den gewählten Kandidaten. Die Abgabe ändert der Ablauf nicht.
- **Runde 3 des Nachtrainings** (`scripts/pipeline_battle_ft3.sh`, +2.000 Spiele je Netz, Kartenversatz 2000, Pool zusätzlich mit `battle_mix36`) läuft seit 18:51 für die Netze, deren Runde 2 fertig ist. Die übrigen Netze starten jeweils nach ihrer Runde 2. Der Nachtablauf startet Runde 3 nicht ein zweites Mal.
- **Risiko im Battle gefunden und behoben:** `lux/runner.py` erzeugt Agenten ohne `train`-Argument, und `run_agents` hat den Standard `train=True`. Mit `train=True` spielte Sherlock mit nur einem Netz, ohne die meisten Regeln und mit ε = 0,05. Außerdem überschriebe er seine `.pth` (Speichern vor Spiel 0 und am Spielende). Neuer Schalter `frozen` (Standard aus): Damit bleibt der Agent auch bei `train=True` im Spielmodus (alle Netze, alle Regeln, kein ε), lernt nicht und schreibt ohne ausdrücklichen Pfad nichts. `scripts.build_submission --battle` setzt `frozen` nur in der verpackten `.pth`; Gewichte und alle übrigen Einträge bleiben gleich. Die Prüfung der Zip simuliert jetzt zusätzlich den Runner mit `train=True` (ohne `set_to_eval_mode`, mit `save_agent()` und `update(terminated=True)`) und verlangt eine unveränderte Datei.
- Neu gebaut: `Gruppe15.zip` mit V10 (18 Netze, eingefroren), 11,9 MB, SHA-256 `b975fcd1…`, darin `agent.pth` `32daeda2…`. Die Abgabe-Dateien unter `agents/sherlock/weights/` sind unverändert (`03cf8bdc…`). Prüfung in der frischen Kursvorlage (Ordner unter `agents/` und in der Wurzel, je beide Seiten): bestanden.
- Prüfungen: ganze Testsuite 486 bestanden, darunter 2 neue zu `frozen`. Ausgenommen ist `test_early_curriculum_study`: Seine Ressourcensperre verweigert, solange Training läuft. Dabei aufgefallen und behoben: Die heutige `relic_scout`-Zeile in `features.make_context` las `agent.training` auch bei ausgeschaltetem Schalter. Mit echten Agenten änderte das nichts, aber 3 Tests in `test_active_targets` scheiterten an ihrem Test-Agenten ohne dieses Attribut. 4 V10-Spiele auf Dev A sind in allen Kennzahlen identisch mit der Basis. Rauchtest mit 5 statt 3 Matches pro Spiel (Env-Parameter nur im Testprozess): 4/4 Siege gegen Solution_92, Matches 19:1, kein Absturz.
- **Offen:** Dev-B-Ergebnis `mix36`. Für die 36- und 54-Netze-Kandidaten (Zip ≈ 22 bzw. 33 MB) die Moodle-Grenze für die Dateigröße prüfen (Mahmoud). Nach dem Nachtablauf Übernahme nur bei bestandener Bestätigung.

## 29.10.2026, 16:30 Berlin – Claude Code mit Mahmoud: Nachtraining wirkt, zweite Runde gestartet

- **Sauberer Trainingsvergleich auf Dev A** (gleiche 6 Netze, beide mit exakt der V10-Config, `scripts/build_ensemble.py --cfg-from`): vorher (`battle_orig6`) `sol92_sq` 77,5 %, Solution_92 86,0 %; **nach 1.500 Nachtrainingsspielen (`battle_ft6`) 82,2 % / 89,2 %**, gepaart **+4,7 pp [+1,0; +8,5]** und **+3,2 pp [0,0; +6,7]**. Schon diese 6 Netze liegen gegen Solution_92 gleichauf mit dem 18-Netz-V10 und gegen `sol92_sq` +4,3 pp [+0,7; +8,2] darüber. Erstmals bringt Training wieder messbar etwas: Die V3-Netze waren nie unter den späteren V10-Regeln und dem korrigierten Gedächtnis trainiert worden.
- Trainingskurven (ε = 0,05, je 500 Spiele) steigen am Ende noch: Solution_92 im Mittel 60 → 64 → 66 %, `sol92_sq` 48 → 51 → 53 %. Deshalb **zweite Runde** (`scripts/pipeline_battle_ft2.sh`): +2.000 Spiele je Netz ab dem Endstand der ersten Runde (Gewichte und Buffer), neue Trainingskarten (`finetune --map-offset 1000`), gleiche Gegnermischung. s10–s15 laufen seit 16:16, die übrigen starten jeweils nach ihrer ersten Runde; Ensemble `battle_ft2_18` voraussichtlich nachts.
- Erste Runde: Wellen 2/3 laufen, `battle_ft18` und `battle_mix36` (V10 + ft18) werden danach automatisch auf Dev A gemessen. V10-Basis auf **Dev B** (801000–801299, ganzes Panel) für die Gegenprobe in der Warteschlange.
- Regeln ohne Gewinn (Dev A, `sol92_sq` / Solution_92): `active_targets` −0,5 / +0,2, `mobile_seen` +0,3 / −0,3, `art_safe=false` +0,8 / −1,0, mit `art_min_hits=2` 0,0 / −0,5, `opp_point_infer` +0,5 / −1,0, `relic_scout=1` −1,3 / −1,0. Teil-Orakel: nur Relics +3,7 [+0,8; +6,5] / +1,0, nur Punktefelder +2,5 / +1,3. Relic-Entdeckung (60 Spiele): Verzögerung im Mittel 10 Schritte, in Match 2 drei von 40 neuen Paaren nie gefunden.
- Plan für 30.10. früh: bestes Ensemble (ft18, ft2_18, mix36) mit vollem Panel auf Dev A und Dev B prüfen, danach Auswahl Runde 1 (802000–802399) und bei Erfolg Bestätigung (803000–804399).

## 29.10.2026, 15:00 Berlin – Claude Code mit Mahmoud: erste Entwicklungsergebnisse der Battle-Vorbereitung

Alle Werte auf Dev A (800000–800299, je Gegner 600 Spiele), gepaart gegen die V10-Basis; nur Entwicklung, keine Übernahmeentscheidung.

| Variante | `sol92_sq` | Solution_92 |
|---|---|---|
| `opp_infer` | +0,3 [−1,8; +2,5] | −1,5 [−3,3; +0,3] |
| `contest_sap` | +1,2 [−1,3; +3,8] | −0,2 [−2,2; +2,0] |
| beide | +1,8 [−0,7; +4,5] | −1,8 [−4,3; +0,5] |
| **`home_reserve`** | **−24,0** [−28,7; −19,3] | **−23,8** [−28,3; −19,2] |
| Orakel: wahre Relics und Punktefelder | **+6,3** [+2,7; +10,0] | **+4,0** [+0,8; +7,2] |

- **`home_reserve` ist ein klarer Fehlschlag** und bleibt aus. Die Diagnose aus einem Einzelspiel (Einheiten laufen in die besetzte Festung) war nicht verallgemeinerbar: Punktefelder der Gegnerhälfte sind oft noch frei, dort holen wir viele Punkte (gewonnene Matches: mehr Einheiten auf dem Weg dorthin als verlorene). Die Tests `hrs`/`hrat` mit diesem Schalter wurden abgebrochen.
- **Orakel** (`scripts/oracle_probe.py`): Perfektes Wissen ist 4–6 pp wert. Teil-Orakel (nur Relics bzw. nur Punktefelder) laufen.
- **Gedächtnis gegen Wahrheit** (`scripts/belief_truth_check.py`, 60 Spiele, 18.000 Schritte): V10 hat nie falsche Punktefelder, aber in 553 Schritten echte Punktefelder als tot markiert. Ursache: Ein in Match 2 neu gespawntes Relic-Paar wird nicht gefunden (800004: 38–44 % der Punktefelder bekannt). Neue Schalter, alle Standard aus und getestet: `opp_point_infer` (Gleichungen aus dem Punktgewinn des Gegners, wenn jedes mögliche Punktefeld sichtbar ist; 299 Anwendungen ohne falsches Feld) und `relic_scout` (überzählige Einheiten suchen in Match 2/3 bis Schritt 60 das fehlende Paar).
- Weitere Einzelspiele: Gegnerfestung auf einem gemeinsamen Haufen (800180, 81:908 Punkte), unsere Einheiten treffen einzeln ein und schießen nicht zurück (`art_safe` verhindert Artillerie innerhalb gegnerischer Reichweite); Pendeln vor einem Haufen ohne bekanntes Punktefeld, weil `collision_guard` jeden Gegner für beweglich hält (800051).
- Warteschlange `scripts/battle_queue.sh` (`experiments/battle_queue.txt`): `active_targets`, `mobile_seen`, `art_safe=false` (±`art_min_hits=2`), `cand_rescue`, Teil-Orakel, `opp_point_infer`, `relic_scout` 1/2, sauberer Trainingsvergleich 6 Netze vor/nach dem Nachtraining.

## 29.10.2026, 14:30 Berlin – Claude Code mit Mahmoud: Battle-Vorbereitung gestartet (läuft bis 04.11.)

- **Auftrag Mahmoud:** bis 04.11. Sherlock „perfekt trainieren“ und vieles ausprobieren, damit wir die Agents der anderen Teams schlagen. [Plan mit Testkarten und Hürden](superpowers/plans/2026-10-29-battle-push.md) vor den Messungen festgelegt (Commit `b02ef7b`). Übernahme nur über `scripts/league_gates.py` auf frischen Karten, sonst bleibt V10.
- **Basis V10 auf Dev A** (800000–800299, beide Seiten, je 600 Spiele): default 99,8 %, Solution_92 89,3 %, `sol92_weak` 89,5 %, `old3_sym3` 89,3 %, **`sol92_sq` 77,8 %**. Datei `experiments/compare/battle/B_V10_dev800.csv`.
- **Niederlagen-Analyse** (`scripts/par_losses.py`, `scripts/mechanism_probe.py --opponent/--games`, 521 nachgespielte Spiele): In verlorenen Matches 2/3 feuert der Gegner etwa doppelt so viele Saps (40 statt 18 je Match, Streuschaden 1.269), wir verlieren 16,5 statt 9 Einheiten durch Energie, stehen auf weniger Punktefeldern (390 statt 550 Einheiten-Schritte) und kennen nur ~80 % der Punktefelder (gewonnen ~95 %). Gegner stehen viermal so oft auf Punktefeldern unserer Hälfte.
- **Fehler gefunden (800070, Match 3):** Kennt der Belief mehr Punktefelder als wir Einheiten haben, schickt die Zielzuweisung die übrigen Einheiten zu Punktefeldern der Gegnerhälfte, auch 25 Felder weit in die besetzte Festung. Sie sterben und laufen nach dem Respawn erneut los. Neue Schalter (Standard aus, Commit `2525d7b`): `home_reserve` (Reserve im Ring mit Abstand 2 um die eigenen Punktefelder) und `reserve_sap` (Reserve schießt wie ein Halter). Mit ausgeschalteten Schaltern 80 V10-Spiele in allen Kennzahlen identisch mit der Basis.
- **Nachtraining der 18 V3-Netze** unter allen V10-Regeln gegen gemischte Gegner (`scripts/pipeline_battle_ft.sh`, 6 parallel, je 1.500 Spiele) läuft seit 13:25. Erste Validierung der ersten 6 Netze nach 500 Spielen (je 16 Spiele, nur Hinweis): Solution_92 im Mittel 71 → 77 %, Matches 61 → 70 %.
- Entwicklungstests auf Dev A (`scripts/battle_dev.sh`, Log `experiments/battle_dev.log`): `opp_infer` ohne Gewinn (`sol92_sq` +0,3, Solution_92 −1,5 pp, n. s.). In der Warteschlange: `contest_sap`, beide zusammen, Orakel-Obergrenze (`scripts/oracle_probe.py`: wahre Punktefelder ins Gedächtnis), `home_reserve`, `+reserve_sap`, `active_targets`, `home_reserve+active_targets`.
- Für später vorbereitet: `scripts/pipeline_battle_gate.sh` (Auswahl, Wahl, Bestätigung je Runde; Log kompatibel mit `scripts/release_candidate.py`).
- Prüfungen: neue Tests `tests/test_finetune.py` (2), `tests/test_par_losses.py` (1), `tests/test_battle_rules.py` (4) grün; gesamte Suite 535 bestanden. Nur `tests/test_early_curriculum_study.py` schlägt fehl, und zwar ausschließlich an der eigenen Ressourcensperre („Another model job is active“, 81×), solange Training läuft. Abgabe-Gewichte unverändert `03cf8bdc…8c67`.
- Der Mac bleibt per `caffeinate` bis 04.11. wach; Laptop offen und am Netzteil lassen.

## 29.10.2026, 13:40 Berlin – Claude Code mit Mahmoud: Entwurf Präsentation Battle Session 06.11.

- Auftrag aus der Prof-Mail: 10 Minuten für die Kommilitonen, wie Sherlock funktioniert und trainiert wurde, dazu die Entwicklungen der letzten Woche; Bewertungsschema Kursfolie 11. Das Prof-Feedback vom 23.10. (Action Masking, Entscheidungsablauf, Rolle der 18 Netze) ist eingearbeitet.
- `Sherlock_Battle_06-11-2026.pdf` (Projektordner): 13 Vortragsfolien + 3 Reserve im Design vom 23.10. Quelle `docs/presentation/Sherlock_Battle_06-11-2026.html`, zusammengesetzt aus den geprüften Folien „Entscheidungsablauf“ (26.10.) und vom 23.10. Neu: Titel/Kernaussage, Agenda, Gedächtnis (aus der Reserve nach vorn), „Von 47 % auf 90 %“, „Neu seit letzter Woche“ (Liga-Training, Robustheitstabelle, Ladefehler), Erkenntnisse, Fazit mit Hinweisen fürs Replay.
- `Sherlock_Stichpunkte_06-11-2026.md` (Projektordner): Sprechtext je Folie, Vorschlag Moayed 5:10 (Folien 1–5, 10, 12–13), Mahmoud 4:20 (6–9, 11), zusammen 9:30; Rückfragen, Text für Moodle, Belege.
- Prüfungen: alle 16 Seiten als Bild angesehen, Umbrüche korrigiert. Zahlen aus Arbeitsstand 22./26.10., Übernahmeberichten V7/V10, `v10_mechanics_20261022/RESULTS.md` und `Sherlock_Entscheidungsprozess.md` übernommen. Keine neuen Spiele.
- Offen: Moayed prüft Aufteilung und Folien; Folie 11 vor dem 06.11. auf den neuesten Stand bringen; zweimal mit Uhr proben.

## 29.10.2026, 13:10 Berlin – Claude Code mit Mahmoud: Battle-Abgabe `Gruppe15.zip` gebaut und in der Original-Vorlage geprüft

- **Auftrag (Prof-Mail, von Mahmoud weitergegeben):** Agent bis Mittwoch Nacht auf Moodle (vermutlich 04.11.), der Prof bringt ihn am Donnerstag auf seinem Laptop zum Laufen. Gezippter Ordner mit Gruppennamen, Pfad zur Agent-Klasse, Pfad zu den Gewichten, dazu 10 Minuten Vortrag für die Battle Session.
- **Gefundenes Risiko:** Der Kurs-Runner legt `agents/` in den Suchpfad, der Gewichte-Pfad ist aber relativ zum Arbeitsverzeichnis. Liegt `Gruppe15/` unter `agents/` und der Prof übergibt `Gruppe15/agent.pth`, fand `Agent_x` die Datei nicht und spielte **still untrainiert mit Standard-Config** (nur eine Konsolenzeile).
- **Änderungen:**
  - `agents/sherlock/main.py`: `resolve_weights` nimmt bei fehlendem Pfad die gleichnamige `.pth` direkt neben `main.py`; vorhandene Pfade bleiben unverändert, im Repo liegen dort keine `.pth`. Zusätzlich `Agent = Agent_x`, weil das Beispiel des Profs `Gruppe21.main.Agent` lautet. Spielverhalten unverändert.
  - `scripts/build_submission.py --battle`: baut `Gruppe15.zip` im Projektordner mit `Gruppe15/` (Quellcode, `agent.pth`, `agents.yaml`, `LIESMICH.txt` mit Pfaden und Paths.csv-Zeile). Gleiche Gewichte für beide Seiten stehen einmal als `agent.pth` darin, sonst `agent_0.pth`/`agent_1.pth`. Die Prüfung entpackt in eine nachgebaute Vorlage (mit `agents/__init__.py`, das alle Unterpakete importiert) einmal unter `agents/` und einmal in der Wurzel. `dist/agent.zip` wie bisher.
  - `.gitignore`: `/Gruppe*.zip`. Neue Tests `tests/test_battle_submission.py` (7).
- **Für Moodle:** Datei `Gruppe15.zip` (11,9 MB), Agent-Klasse `Gruppe15.main.Agent_x`, Gewichte `Gruppe15/agent.pth` für Player 0 und Player 1. Enthaltene `agent.pth` = Abgabe V10, SHA-256 `03cf8bdc…8c67`.
- **Prüfungen:** gesamte Testsuite **559 bestanden** (+14 Untertests). `--battle`-Prüfung in beiden Ordnerlagen: 18 Netze, `env_steps=909000`, „Check ok“. Kopie der Original-Vorlage `~/Documents/AnwendKiLux` (nur im Scratchpad, Original unverändert), Zip nach `agents/`, Paths.csv-Zeile `15;Gruppe15.main.Agent_x;Gruppe15/agent.pth;Gruppe15/agent.pth`, unveränderter Runner mit `train=False`: 15 vs 2, 2 vs 15, 15 vs 1, 3 vs 15 je 2 Spiele, alle 8 mit 303 Schritten ohne Fehler, Sherlock gewann 7 (eine Niederlage 1:2 gegen Solution_92); reiner Funktionstest, keine Leistungsmessung. Agent-Code parst mit Python 3.9; Checkpoint lädt mit `weights_only=True` (nur Tensoren und einfache Werte). Abgabe-Gewichte vorher und nachher `03cf8bdc…8c67`.
- **Offen:** Hochladen und Pfade an den Prof schicken (Mahmoud/Moayed). Deadline-Datum im Team bestätigen. Wird bis dahin ein Kandidat nach den Gates übernommen, Zip mit `python -m scripts.build_submission --battle` neu bauen. Nicht getestet: Windows und CUDA (der Agent nutzt CUDA automatisch, falls vorhanden).

## 26.10.2026, 21:50 Berlin – Claude Code mit Mahmoud: Gegner-Liga abgeschlossen, kein Kandidat, V10 bleibt

- Die Studie lief vollständig nach dem [festen Plan](superpowers/plans/2026-10-26-league.md), der Code blieb durchgehend auf `6f5cde7`. Training: 6 × 4.000 Spiele `full_rules_v10` (Starts 73–78), 6 ok, 0 Fehler. Laufzeit 12:44–21:27 einschließlich der Zeit, in der der Laptop zugeklappt war; die Prozesse waren dann nur angehalten. Zeitangaben (`secs`, Laufdauer) enthalten deshalb Pausen.
- Trainingsverlauf der einzelnen Netze (ε = 0,05; Siege in den Spielen 1.000–1.999 / 2.000–2.999 / ab 3.000): Solution_92 57 / 60 / 62 %, `sol92_sq` 45 / 47 / 44 %, Pool V10 12 / 14 / 14 %, Pool V7 16 / 17 / 20 %, default 98–99 %, RushBot 100 %. Validierung nach 4.000 Spielen (16 Spiele je Netz): Solution_92 0,50–0,81, default 1,0.
- **Auswahl** auf 700000–700199 (200 Karten, beide Seiten). V10-Referenz: Solution_92 88,75 %, `sol92_sq` 80,75 %, `sol92_weak` 91,75 %, `old3_sym3` 89,5 %, default 100 %, R 87,69 %.
  - **L24** (V10 + 6 neue): R 88,50 %, Δ **+0,81 pp [−1,44; +3,12]** → Hürde +1,5 pp verfehlt. Je Gegner: Solution_92 +0,75 [−2,75; +4,25], `sol92_sq` +1,75 [−1,75; +5,25], `sol92_weak` −1,75 [−4,75; +1,25], `old3_sym3` +2,5 [−2,0; +7,0], default 100 %. Direkt gegen V10 52,5 % [45,5; 59,5] aus 400 Spielen.
  - **L6** (nur die 6 neuen): R 85,44 %, Δ −2,25 [−5,44; +0,75]; Solution_92 88,0 % (−0,75 [−5,0; +3,25]), `sol92_weak` −5,5 [−9,5; −1,75], default 99,5 %, direkt 40,0 % [33,5; 47,0] → R- und Direkthürde verfehlt.
- **Ergebnis nach Plan: kein Kandidat, Studie beendet, V10 bleibt Abgabe.** Abgabe-Dateien vorher und nachher `03cf8bdc…8c67`. Bestätigungsblock 701000–701799 und Direktblock 702000–702399 für Kandidaten unbenutzt. Auf 701000–701799 lief nur die V10-Referenz (je 1.600 Spiele: Solution_92 90,2 %, `sol92_sq` 78,9 %, `sol92_weak` 90,5 %, `old3_sym3` 89,9 %, default 100 %). Reserve 703000–703999 unbenutzt.
- Einordnung: Das Training gegen die gemischte Liga hat die Netze nicht messbar robuster gemacht. Die 6 neuen Netze allein liegen gegen Solution_92 fast gleichauf mit den 18 V3-Netzen, sind aber gegen `sol92_weak` und im Direktduell schwächer. Zusammen mit dem 22.10.: Zusätzliche DQN-Netze heben V10 nicht über das Plateau von rund 90 %. Schwächster Gegner bleibt `sol92_sq` mit 79–81 %.
- Daten im Repo: `experiments/pipeline_league.log`, `experiments/batch_20261026_league.log`, `experiments/compare/league/*.csv`, Logs, CSVs und Manifeste der 6 Läufe. Nur lokal (gitignored): Netzgewichte und die Ensembles `experiments/ensembles/league_mix24.pth` (`e3cc8c64…`) und `league_nets6.pth` (`357c3daa…`).
- Prüfungen: Pipeline mit Exit 0, alle Messdateien ohne ausgeschlossene Karten, Hürden mit `scripts/league_gates.py`, Werte je Gegner mit `compare_report.compare_results` nachgerechnet. Kein neuer Code.
- Offen, noch nicht begonnen: Vorschlag für den nächsten Schritt sind die Niederlagen von V10 gegen `sol92_sq` gezielt zu untersuchen, wie beim Weg von V3 zu V10.

## 26.10.2026, 12:45 Berlin – Claude Code mit Mahmoud: Gegner-Liga-Training gestartet (abgeschlossen, Ergebnis 21:50)

- Auftrag Mahmoud („ja los beginn“): weiter trainieren, damit Sherlock gegen die Agents der anderen Teams robuster wird. [Fester Plan mit Hürden](superpowers/plans/2026-10-26-league.md), Ablauf `bash scripts/pipeline_league.sh`, Log `experiments/pipeline_league.log`.
- Neu und getestet:
  - Gegnerplan `league` (`scripts/protocol.py`, `--opponent-plan league`).
  - Frühe Prüfung fehlender Pool-Dateien. Vorher spielte ein fehlender Checkpoint still untrainiert. Bei gleichen Dateinamen heißen Pool-Gegner nach ihrem Ordner, Pfad und SHA-256 stehen im Manifest.
  - Variante `full_rules_v10` und Schalter `rules_in_training_all`: `sap_still` und Nebel-Meidung jetzt auch im Training.
  - Prüfskript `scripts/league_gates.py`.
  - Tests `tests/test_league.py` (9) und `tests/test_league_gates.py` (6). Die zwei Trainings-Regeltests sind ohne die Änderung rot und mit ihr grün.
- Prüfungen: gesamte Testsuite **552 bestanden** (+14 Untertests). V10-Spielverhalten unverändert: Die 10 Diagnosespiele 690000–690004 lieferten mit dem neuen Code bitgleich dieselbe Auswertung (36.258 Entscheidungen samt Beispiel-Q-Werten). Probelauf mit je einem Trainingsspiel gegen `sol92_sq`, RushBot, V10-Pool und Solution_92 (Karten 495000–495003, nur Scratchpad). Panel-Messung, Direktduell und Prüfskript auf 2 Karten durchlaufen (nur Scratchpad).
- Läuft: Training (6 Prozesse) und parallel mit niedriger Priorität die V10-Referenz auf den Blöcken 700000–700199 und 701000–701799. Code bleibt bis Studienende eingefroren. Abgabe unverändert V10 `03cf8bdc…8c67`.

## 26.10.2026 Berlin – Claude Code mit Mahmoud: Review-Feedback, Erklärung des Entscheidungsablaufs

- **Feedback des Profs aus der Review (laut Mahmoud):** beim nächsten Mal genau erklären, (1) was Action Masking ist, (2) wie der Entscheidungsprozess abläuft (wer was bekommt und was liefert) und (3) wie die 18 Netze auf die Spiele verteilt werden. Außerdem weiter trainieren; bald folgen Kämpfe gegen die Agents der anderen Teams, dafür muss Sherlock stärker werden.
- Neu `Sherlock_Entscheidungsprozess.md` (Projektordner): Kurzfassung zum Sprechen, Antworten auf die drei Fragen, Ablauf eines Steps mit Dateien/Funktionen, 79 Merkmale, Netz und Ensemble, Maske (Training und Spiel), Regeln mit Häufigkeit, vier echte Entscheidungen mit Q-Werten, Training der drei Netzgruppen, mögliche Rückfragen. Kernpunkt zu (3): Die Netze werden **nicht** auf Spiele verteilt; alle 18 bewerten jede Unit in jedem Step, gemittelt wird je Aktion.
- Neu `scripts/decision_trace.py` (reine Diagnose, Gewichte nur gelesen) und `tests/test_decision_trace.py`. Messung `experiments/analysis/decision_trace_20261026.json`: 10 Diagnosespiele gegen Solution_92 (Karten 690000–690004 × beide Seiten, **kein Leistungsnachweis**), 36.258 Unit-Entscheidungen. Im Mittel 4,3 von 6 Aktionen erlaubt; die Lieblingsaktion des Ensembles war in 20,4 % verboten (Sap ohne Ziel 9,8 %, Züge 10,6 %); alle 18 Netze einig in 31,9 %, im Mittel 13,4 von 18; Mittelwert ≠ Mehrheitswahl in 7,7 %; **Netzwahl unverändert in 92,4 %**, Regeln ändern 7,3 % (vor allem `scripted_explore` 4,3 %, weiche Nebel-Meidung 1,2 %, `sap_no_overkill` 0,9 %, `path_fix` 0,6 %, `pt_sap` 0,5 %).
- Prüfungen: **gesamte Testsuite 537 bestanden** (+14 Untertests, darunter 3 neue); Messung zweimal (Entwurf und Repo-Skript) mit identischen Zahlen; Abgabe-Gewichte vorher und nachher `03cf8bdc…8c67`. Alle Zahlen der Erklärung gegen Code, Checkpoint (`cfg`, `ensemble_sources`), Laufmanifeste `20261019_full_rules_*` (Gegnerzählung aus `train.csv`) und Übernahmeberichte abgeglichen. Kein Training.
- Folien dazu: `Sherlock_Entscheidungsablauf_Folien.pdf` (Projektordner, 6 Folien + 1 Reserve im Design vom 23.10.), Quelle `docs/presentation/Sherlock_Entscheidungsablauf.html`. Sprechtext je Folie (zusammen etwa 3:30) in `Sherlock_Entscheidungsprozess.md`. Alle Seiten als Bild geprüft, Zahlen aus der Messung oben. Vorschlag: in den nächsten Hauptfoliensatz übernehmen, dort statt der Pseudocode-Folie „Sherlock heute“.
- Auf Mahmouds Wunsch („push alles“) außerdem nachgereicht: die lokalen Vorschaubilder `docs/presentation/bild_0611_*.png` vom 22.10. sowie Logs, CSVs und Manifeste der Läufe und Entwicklungsmessungen vom 22.10. Gewichte und Buffer bleiben per `.gitignore` lokal. Bewusst nicht übertragen: `.DS_Store` und die Dateien der laufenden Liga-Studie (folgen mit ihrem Ergebnis).
- Weiteres Training läuft, siehe Eintrag 12:45 oben.

## 22.10.2026, 17:40 Berlin – Codex mit Moayed: V10-Korrekturen abgeschlossen, V10 bleibt aktiv

- **Abschluss vor der Review auf Moayeds Wunsch.** Die bereits zugelassene Bestätigung wurde beendet; keine neuen Trainings, Direktduelle oder weiteren Gegnerblöcke. Alle eigenen Spielprozesse sind beendet. Keine Verbesserung als bestätigt ausgegeben, keine Abgabe ersetzt. [Vollständiger Bericht für Mahmoud](../experiments/analysis/v10_mechanics_20261022/RESULTS.md), [Reproduktion und Belege](../experiments/analysis/v10_mechanics_20261022/README.md).
- Zwei Fehler separat korrigiert und technisch geprüft: mögliche Energie-Erholung eines beschossenen Gegners (`sap_overkill_recovery`, Commit `75e71c0`) und veraltete Sichtmasken bei erkannter Terrain-Drift (`nebula_infer_drift_safe`, `9e5206b`). Beide bleiben **standardmäßig aus**. Regeln und Gedächtnis wurden als Versuchsoption erweitert; keine Netze neu trainiert.
- **8.800 Vergleichsspiele vollständig ausgewertet.** Auswahl: 200 Karten × beide Seiten, vier Varianten gegen Solution (1.600 Spiele), anschließend V10 und Energie-Korrektur gegen default (800). Nur Energie-Korrektur nominiert: 367/400 statt 363/400 gegen Solution, je 400/400 gegen default. Karten-Korrektur 359/400, Kombination 362/400; keine nachträgliche Kandidatenänderung.
- **Unabhängige Bestätigung auf 800 neuen Karten, beide Seiten:** je Variante 1.600 Spiele gegen Solution und 1.600 gegen default, zusammen 6.400. Solution: V10 **1.448/1.600 = 90,50 %**, Energie-Korrektur **1.437/1.600 = 89,8125 %**; Δ **−0,6875 pp**, gepaarter 95-%-Bereich **[−1,50; +0,125] pp**. Geforderter Gewinn nicht bestätigt; auch keine statistisch gesicherte Verschlechterung. Default jeweils **1.599/1.600 = 99,9375 %**. Somit keine qualifizierte neue Version, Ziel 100 % gegen Solution nicht erreicht.
- Unabhängige Datenprüfung bestätigt alle 6.400 geplanten Zeilen, Quellen-/Gewichtsbindung, Spielabschlüsse und Statistik. Bootstrap: 5.000 Ziehungen ganzer Karten, beide Seiten zusammen; Auswahl und Bestätigung getrennt. Alle Leistungsspiele unter eingefrorenem Commit `de2e95d`, 128 Quellen-/Umgebungsdateien und unveränderten Gewichten. Abschlussbegrenzung vor den Ergebnissen des Bestätigungskandidaten dokumentiert; Direkt-/Robustheitsblöcke wurden **nicht ausgeführt**, nicht als gescheitert gezählt.
- Technische Prüfungen: **527 Tests + 14 Untertests** vor den Messungen; acht Kompatibilitätsspiele mit identischen Aktionen und Nicht-Zeitmetriken bei ausgeschalteten Schaltern; acht Kurs-Runner-Spiele mit beiden Schaltern an; temporäres Paket „Check ok“; alle 264 Tensoren identisch. Nach Integration von Mahmouds Demo-/Präsentations-Commits bis `11c62f5`: **7 zusätzliche Demo-Integrationstests bestanden**. Präsentation und Stichpunkte für den 23.10. sind lokal aktuell und wurden in diesem Abschluss nicht verändert.
- Aktive V10-Dateien und Sicherung `experiments/releases/20261022_v10_baseline/` unverändert, SHA-256 **`03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`**. Die abgeschalteten Korrekturen verändern das vorgeführte V10-Verhalten nicht. Fremde lokale ungesicherte Dateien bleiben erhalten.
- **Für später, kein laufender Auftrag:** Kämpfe um gemeinsame Relic-Haufen gezielt untersuchen; Mahmouds `tactics.py`-Entwurf ist durch diese Arbeit nicht validiert. Keine weitere Studie vor der Review begonnen. Seeds 610100–610299 und 611000–611799 sind verbraucht; reservierte Direkt-/Robustheitsblöcke 612000–612399 und 613000–613099 wurden von dieser Studie nicht benutzt.

## 22.10.2026, 16:20 Berlin – Claude Code mit Mahmoud: Demo-Seite statt Dialogfenster

- Auf Mahmouds Wunsch die App „Sherlock Demo“ übersichtlicher gestaltet. Ein Doppelklick startet `scripts/demo_server.py` (nur 127.0.0.1:8615) und öffnet die Demo-Seite `scripts/demo_page.html` im Design der Folien. Dort Gegner (Solution_92, default, Prof-DQN) und Seite (Spieler 1 blau, startet oben links; Spieler 2 rot, unten rechts) wählen. Jedes Spiel läuft als eigener Prozess über `scripts.play_and_view` (unveränderter Kurs-Runner, `train=False`).
- Ergebnisleiste mit Sieger je Match, eingebetteter Lux-Viewer (an die Fenstergröße angepasst, Karte und Steuerung ohne Scrollen sichtbar), „Nochmal“, Verlauf aus `replays/demo_verlauf.jsonl` (gitignored), „Demo beenden“; sonst endet der Server nach zwei Stunden ohne Anfrage. Startet die Seite nicht, bietet die App das bisherige Spiel mit Dialogfenstern an. Eigenes App-Symbol; Bau mit `sh scripts/build_demo_app.sh`.
- `scripts.play_and_view`: neu `--json` und Sieger je Match; die bisherige Ausgabe bleibt gleich.
- Prüfungen: `tests/test_demo_server.py` (4) und `tests/test_play_and_view.py` (3) bestanden; **gesamte Testsuite 534 bestanden** (+14 Untertests). Echtes Spiel über die Schnittstelle (7 s). In Chrome durchgeklickt: Auswahl, Spiel starten, Ergebnis mit Viewer, Abspielen, „Nochmal“, Verlauf, „Demo beenden“; keine Konsolenfehler. Startlogik der App per `osascript` auf Ersatzport geprüft (Start in 1 s, zweiter Start nutzt laufenden Server). Dabei behoben: Der erste Startbefehl hielt `do shell script` bis zum Serverende fest. Gewichte unverändert `03cf8bdc…8c67`.
- Hinweis: Der erste Start der neu gebauten App fragt wieder nach Zugriff auf „Dokumente“.

## 22.10.2026, 15:50 Berlin – Claude Code mit Mahmoud: Demo per Doppelklick

- Neu `scripts/sherlock_demo.applescript`, gebaut als `Sherlock Demo.app` im Projektordner (seit 22.10., 15:55 mit im Repo; nach Änderungen am Quelltext neu bauen mit `osacompile -o "Sherlock Demo.app" scripts/sherlock_demo.applescript`). Doppelklick → Gegner wählen (default, Prof-DQN, Solution_92) → `scripts.play_and_view` läuft → Replay öffnet sich im Browser, Ergebnisfenster mit „Nochmal“.
- Prüfungen: Kompilieren ohne Fehler; Ordnersuche, Aufruf und Auswertung der App ohne Dialoge per `osascript` getestet (App im Projektordner, App auf dem Schreibtisch mit Standardpfad, Quelltext in `scripts/`), drei Spiele gegen Solution_92, Prof-DQN und default jeweils 3:0 gewonnen. Die Dialoge selbst nicht automatisch geklickt; beim ersten Start fragt macOS nach Zugriff auf „Dokumente“. **Mahmoud hat die App per Doppelklick erfolgreich ausprobiert.** Gewichte unverändert.

## 22.10.2026, 15:45 Berlin – Claude Code mit Mahmoud: Live-Demo mit automatischer Visualisierung

- Neu `scripts/play_and_view.py`: spielt ein Spiel über den unveränderten Kurs-Runner (`run_agents`, `train=False`), verpackt das Replay wie `luxai-s3 --output replay.html` in eine HTML-Datei mit dem offiziellen Viewer (s3vis.lux-ai.org, braucht Internet), gibt das Matchergebnis aus und öffnet die Datei im Browser. Optionen `--gegner default|solution|dqn`, `--seite 1`, `--no-open`. Ausgaben nur unter `replays/` (gitignored).
- Prüfungen: `tests/test_play_and_view.py` 2 bestanden; zwei echte Spiele (gegen Solution_92 als player_0, gegen default als player_1), beide 3:0 gewonnen; erzeugte HTML-Datei in Headless-Chrome mit geladenem Viewer kontrolliert; Abgabe-Gewichte unverändert `03cf8bdc…8c67`. README und Stichpunkte (Abschnitt „Live-Demo“) ergänzt.

## 22.10.2026, 15:25 Berlin – Claude Code mit Mahmoud: Präsentation für den 23.10.

- Laut Mahmoud ist die Präsentation am **23.10.** In `CLAUDE.md` steht für die Zwischenpräsentation der 06.11.; Termin bitte im Team bestätigen. Folien und Stichpunkte tragen deshalb das Datum 23.10.
- Folien `Sherlock_Review_23-10-2026.pdf` (Projektordner, 13 Vortragsfolien + 2 Reservefolien im Design vom 16.10.), Quelle `docs/presentation/Sherlock_Review_23-10-2026.html` mit Bildern `docs/presentation/folie_2310_*.png` und Diagrammskript `docs/presentation/source/fortschritt_2310.py`. Stichpunkte zum Üben `Sherlock_Stichpunkte_23-10-2026.md` (Vorschlag: Moayed Folien 1–4, 8–10 und 13 = 5:10, Mahmoud 5–7 und 11–12 = 4:30). Plan und Belege: `docs/presentation/VORTRAGSPLAN_2310.md`.
- Kernaussage gegenüber dem Entwurf vom Morgen korrigiert: 47 → 78 % kam aus Regeln, Neutraining mit aktiven Regeln und `reward_fix` sowie 18 statt 6 Netzen (Arbeitsstand 19./20.10.); 78 → 90 % kam aus der Fehlersuche mit denselben 18 Netzen. Danach brachten CNN/PPO, Gefahrmerkmale und weitere Netze keinen Gewinn.
- Prüfungen: alle 15 Seiten als Bild kontrolliert. Zahlen gegen Übernahmeberichte, Nachtbericht, Arbeitsstand, Checkpoint (79 Merkmale, 18 Netze, Mittelwert der Q-Werte) und Engine-Parameter (Sap-Kosten 30–50, Reichweite 3–7, Drift alle 7–40 Schritte) abgeglichen. Für ein mögliches Battle: unveränderter Kurs-Runner mit installierter V10 auf `main` `de2e95d` **8 Spiele bestanden** (`act` höchstens 11,4 ms), `scripts.build_submission` „Check ok“ (Zip nur in einem temporären Ordner). Gewichte unverändert `03cf8bdc…8c67`. Kein Training, keine neuen Messspiele.
- Offen: Moayed prüft seine Folien und probt mit Uhr. Keine PowerPoint-Fassung; präsentiert wird das PDF. Nur lokal bei Mahmoud, nicht übertragen: vierteilige Vorversionen `docs/presentation/bild_0611_*.png`.

## 22.10.2026, 13:54 Berlin – Codex mit Moayed: V10-Mechanikkorrekturen vorbereitet, Abgabe bleibt V10

- Auftrag: lokales Repo aktualisieren, zwei im Review reproduzierte Fehler korrigieren und gegen V10 messen. `main` zunächst auf `c78732f`, danach Mahmouds reinen Ergebniscommit `bb7e84b` übernommen (12 neue Netze ohne belegten Gewinn). Fremde unversionierte Dateien erhalten.
- Zwei getrennte, standardmäßig ausgeschaltete Schalter: `sap_overkill_recovery` berücksichtigt maximale mögliche Feld-Erholung vor dem Absagen weiterer Saps; `nebula_infer_drift_safe` unterbindet zeitlich falsche Nebel-Inferenz bei erkannter Terrain-Drift. Nicht erkannte Drift und bewegte Ziele bleiben dokumentierte Grenzen. Keine Netzparameter geändert.
- V10 bytegleich unter `experiments/releases/20261022_v10_baseline/` gesichert; beide aktiven Gewichte weiterhin `03cf8bdc…8c67`. Neue Schalter bleiben aus, bis ein Kandidat alle vorab definierten Bedingungen erfüllt.
- Technische Prüfung: Regressionen zunächst rot, anschließend grün; vollständige Suite **527 Tests + 14 Untertests bestanden**; unabhängiges Code-Review ohne blockierende Befunde. Original und neuer Code mit Schaltern aus: je vier Spiele, **1.212 Schritte**, sämtliche Aktionen beider Spieler und sämtliche Nicht-Zeit-Metriken identisch.
- [Fester Vergleichsplan](superpowers/plans/2026-10-22-v10-mechanics.md): vier Varianten auf 200 Auswahlkarten 610100–610299, höchstens ein Kandidat. Nur bei bestandener Auswahl: 800 frische Bestätigungskarten 611000–611799, 400 Direktkarten 612000–612399 und 100 Robustheitskarten 613000–613099. Diese Blöcke sind reserviert; nicht parallel verwenden. Höchstens zwei Worker, unveränderter Code über die gesamte Messung. **Noch kein Leistungsnachweis und keine Übernahme.**
- Prüfbelege und später Rohdaten: `experiments/analysis/v10_mechanics_20261022/`. Der vorhandene `tactics.py`-Entwurf ist durch diese Arbeit nicht validiert oder eingebunden; vor Nutzung sind seine Engine-Abweichungen separat zu prüfen.

## 22.10.2026, 13:50 Berlin – Claude Code mit Mahmoud: 12 neue Netze, kein Gewinn gegenüber V10

- Zweite Trainingsreihe `full_rules_v8` (Starts 60–62/90–92, je 3000 Spiele) abgeschlossen; damit 12 Netze unter V8-Bedingungen. Entwicklung (V10-Config): **18 alte + 12 neue (`v10mix30`) 79,2/95,8 % → geschätzt 90,3 % (= V10)**, nur die 12 neuen (`v10nets12`) 76,5/95,2 % → 89,1 % (6 neue: 86,8 %). Mit V8-Config `v8mix24b` siehe `experiments/pipeline_v8nets_b.log`.
- Schluss: Weder kleine Regeln (Plateau 90–91 %) noch zusätzliche Netze verbessern V10 klar. **V10 bleibt Abgabe.** Für einen weiteren Sprung bräuchte es einen größeren Ansatz für die Kämpfe um gemeinsame Relic-Haufen (z. B. Planung mit dem geprüften Ein-Schritt-Simulator `agents/sherlock/tactics.py`).
- Für die Präsentation am 06.11. lokal erzeugt, nicht gepusht: `docs/presentation/bild_0611_*.png` (Vorher/Nachher zu Kartenfehler, Sackgasse, Mehrfach-Saps; Fortschrittsbalken), Verweise im lokalen `VORTRAGSPLAN_0611_ENTWURF.md`.

## 22.10.2026, 12:15 Berlin – Claude Code mit Mahmoud: Plateau um 90–91 % gegen Solution_92

- Auf V10 gemessen (Entwicklung, geschätzt gesamt; V10 90,3 %): `cand_rescue` mit `rescue_after=30` **91,0 %** (bester Einzelschalter, rettet 0-Punkte-Spiele), V10 + 6 neue Netze 90,8 %, beides zusammen 91,0 % (nicht additiv), `dodge` mit Köder 90,5 %, `stage_attack` (gemeinsam in die Schusszone) 90,3 %, `sap_kill_safe` 90,1 %, `art_still` 90,0 %, `sap_reserve_k=0.5` 89,0 %. Kein Bündel liegt um +2 pp vor V10 → **kein Prüflauf, V10 bleibt**.
- Verbleibende Niederlagen sind vor allem Kämpfe: ein gemeinsamer Relic-Haufen, Solution_92 kommt mit mehr Units zuerst an, unsere Units werden einzeln abgeschossen (z. B. 361038). Pro Verlustspiel ~27 Tode durch Saps.
- Läuft: 6 weitere Netze (`pipeline_v8nets_b.sh`, Ende ~13:45), danach Ensembles aus 18 alten + 12 neuen bzw. 12 neuen Netzen.

## 22.10.2026, 11:25 Berlin – Claude Code mit Mahmoud: Robustheit von V10, nächste Kandidaten

- **Robustheit gegen andere Spielweisen** (neue Gegner in `scripts/style_opponents.py`, je 100 frische Karten 509220–509319, nur Information): Prof-DQN, Zufall, RushBot je **100 %**, Solution_92 mit Ziel „schwächster Gegner“ 90,5 %, alte Abgabe `old3_sym3` 89 %, CNN-PPO `cnn3_ppo0050` 88 %, **Solution_92 mit Sap im ganzen Quadrat 74,5 %** (Original auf denselben Karten 89 %). V3 fällt gegen die Quadrat-Variante gleich stark (78 → 62,5 %): dieser Gegner ist stärker, keine V10-spezifische Lücke. Auf 509420–509619 V10 gegen die Quadrat-Variante 83,5 %. `art_safe_cheb` (Artillerie-Sicherheit im Quadrat) ohne Gewinn.
- **`cand_rescue` mit `rescue_after=30`** (Kandidaten gezielt testen, nur wenn ein Relic seit ≥ 30 Steps bekannt ist und noch kein Punkte-Tile): rettet die 0-Punkte-Spiele 361050/361255, Entwicklung 78,8/97,0 % (geschätzt 91,0 %, V10 90,3 %). Ohne Verzögerung schlechter (78,9/94,9 %).
- Neue Netze allein (`v10nets6`, 6 Netze mit V10-Config) 73,6/93,3 % (geschätzt 86,8 %); gemischt mit den 18 alten (`v10mix24`) 79,2/96,4 % (90,8 %). Weitere 6 Netze trainieren seit 11:22 (`scripts/pipeline_v8nets_b.sh`); Bündel V10 + neue Netze + `cand_rescue` läuft (`D22_v10mix24cr`).
- Ein Nachfolger wird erst gegen V10 geprüft, wenn ein Bündel in der Entwicklung klar vorn liegt (die Gates verlangen +2 pp auf 800 frischen Karten).

## 22.10.2026, 10:40 Berlin – Claude Code (autonom): Training ausgewertet, Testsuite mit V10 sauber

- **Gesamte Testsuite ohne laufende Jobs: 495 bestanden** (V10 installiert, `03cf8bdc…8c67`). Damit ist der offene Prüfpunkt der V10-Übernahme erledigt.
- 6 Netze unter V8-Bedingungen trainiert (`full_rules_v8`, `rules_in_training`, Starts 70–72/80–82, je 3000 Spiele). Entwicklung gemischt mit den 18 V3-Netzen: `v8mix24` 75,3/96,4 % (V8 73,0/97,6, gesamt gleich), **`v10mix24` 79,2/96,4 % (geschätzt 90,8 %, V10 90,3 %)**, also +0,45 pp und damit unter der üblichen Schwelle von +0,5. Kein neuer Prüflauf. V10 bleibt.

## 22.10.2026, 09:50 Berlin – Claude Code (autonom): V10-Feinschliff ohne Gewinn, Training läuft

- Auf V10 ohne Gewinn: `art_still` (Artillerie nur auf stehende Ziele) 77,7/96,0 % (−0,3), `sap_reserve_k=0.5` 76,5/94,9 % (−1,5). V10 bleibt unverändert.
- Training `full_rules_v8` (6 Netze unter V8-Bedingungen) bei ~2000/3000 Spielen, Ende gegen 10:25. Danach automatisch: `v8mix24` (V8-Config) und `v10mix24` (V10-Config, 18 V3-Netze + 6 neue) auf den Entwicklungs-Sets (`experiments/pipeline_v8nets.log`, `experiments/dev_v10mix24.log`). Ein Nachfolger würde nur über einen neuen, vorab festgelegten Plan gegen V10 geprüft.
- Vortragsentwurf `docs/presentation/VORTRAGSPLAN_0611_ENTWURF.md` lokal auf V10 aktualisiert (Kernaussage „von 47 % auf 90 %“), **nicht gepusht**, wartet auf Mahmouds OK.

## 22.10.2026, 09:25 Berlin – Claude Code (autonom): **V10 als Abgabe übernommen – 90,3 % gegen Solution_92**

- **V10 (`v10_V8st`) = V8 + `sap_still`** hat alle vorab festgelegten Gates gegen V7 bestanden ([Plan](superpowers/plans/2026-10-22-v10.md), [Übernahmebericht](../experiments/analysis/release_20261022_v10/RELEASE.md)): frisch auf 800 Karten 507420–508219 **Solution_92 90,3 % statt 82,8 % (Δ +7,5 [+5,4; +9,6])**, default 99,75 % (Δ −0,2), **direkt gegen V7 58,1 % [53,1; 62,75] aus 800 Spielen**.
- Übernahme per `scripts/release_candidate.py`: V7 bytegleich gesichert (`experiments/releases/20261022_v7_Bsnpd/`, SHA-256 `c394acba…95e6`), V10 installiert (`03cf8bdc…8c67`), **Kurs-Runner unverändert: 8 Spiele bestanden** (`act` max. 11,3 ms).
- Testsuite nach der Installation: 463 bestanden, 31 Studientests von der Schutzsperre abgewiesen (Training `full_rules_v8` lief). Wiederholung ohne Jobs folgt nach Trainingsende.
- Damit erledigt: V8-Teamentscheidung (V10 enthält V8). Ziel ≥ 90 % gegen Solution_92 auf frischen Karten erreicht.

## 22.10.2026, 08:30 Berlin – Claude Code (autonom): V10 in Prüfung gegen V7

- Auf V8 nachgemessen: **`sap_still`** (Halter-Saps nur auf stehende Gegner) **77,9/96,4 % → geschätzt ≈ 90,3 %** gegen Solution_92 (V8 89,5); `art_min_hits=4` 72,1/96,9 (schlechter).
- **[V10-Plan](superpowers/plans/2026-10-22-v10.md)** vorab festgelegt: V10 = V8 + `sap_still` (`experiments/ensembles/v10_V8st.pth`, SHA-256 `03cf8bdc…8c67`), gegen **V7** auf den unbenutzten V9-Blöcken: Auswahl 507220–507419, frisch 507420–508219 (800 Karten), direkt 508220–508619 (800 Spiele). Läuft seit 08:24 (`experiments/pipeline_v10.log`).
- Abgabe-Pruefung `agent.zip` mit V7 lokal gebaut: „Check ok“ (Import über den Kurs-Runner-Lader, Pflichtmethoden, beide Seiten, ein Aktionsschritt). `agents/sherlock/tactics.py` als Entwurf committet (nicht eingebunden).
- Training `full_rules_v8` läuft (6 Netze, ~10:15 fertig, danach Messung `v8mix24`).

## 22.10.2026, 08:00 Berlin – Claude Code (autonom): kein V9, Bericht der Nacht

- **Zusammenfassung der Nacht für Mahmoud/Moayed: [Nachtbericht V7/V8](NACHT_V7_V8_20261022.md)** (Änderungen in einfacher Sprache, Zahlen, Entscheidungsvorlage V8 mit Übernahmeweg).
- [V9-Plan](superpowers/plans/2026-10-22-v9.md): `mobile_seen` (−0,2), `obey_target` (−0,8) und `neb_cand`+`idle_approach` (−0,8, Fix für den Nebel-Relic-Fall 361050) verbessern V8 nicht → kein V9-Ablauf, Blöcke 507220–508619 unbenutzt. Kleine Regeländerungen um V8 liegen alle zwischen −2 und +0,2 pp: V8 ist für diesen Ansatz ein Plateau.
- Info-Duelle **nur für die Teamentscheidung** (kein Gate, nach dem V8-Gate erhoben): **V8 gegen V7 59,9 % [55,0; 64,75] aus 800 Spielen**, V8 gegen V3 75,0 % [69,0; 81,0] aus 400 Spielen (`scripts/info_duels_v8.sh`). Empfehlung im [Nachtbericht](NACHT_V7_V8_20261022.md): V8 übernehmen, als bewusste Teamentscheidung.
- Training läuft: 6 Netze unter V8-Bedingungen (`full_rules_v8`, `rules_in_training`), danach Messung `v8mix24` gegen V8 (`scripts/pipeline_v8nets.sh`).
- Abgabe: **V7** (`c394acba…95e6`).

## 22.10.2026, 07:30 Berlin – Claude Code (autonom): V8 knapp nicht übernommen, Testsuite sauber

- **V8** ([Plan und Ergebnis](superpowers/plans/2026-10-22-v8.md)), frisch auf 800 Karten 506220–507019: **Solution_92 89,1 % statt 84,6 % bei V7 (Δ +4,5 [+2,6; +6,4])**, default 100 %. **Direkt gegen V7 56,5 % [49,5; 63,5]** → die vorab festgelegte Hürde „untere Grenze > 50 %“ um 0,5 pp verfehlt → **V7 bleibt Abgabe**. V8 = V7 + `reach_assign` + `sap_no_overkill` + `safe_moves` + `collision_guard`, Checkpoint `experiments/ensembles/v8_Bsnpdroc.pth` (lokal, SHA-256 `13023d74…d60c`, gitignored; bauen mit `python -m scripts.set_cfg experiments/ensembles/v7_Bsnpd.pth <ziel> reach_assign=true sap_no_overkill=true safe_moves=true collision_guard=true`). **Entscheidungsvorlage für Mahmoud/Moayed**: gegen Solution_92 und default nachweislich besser, im direkten Vergleich gegen V7 nicht nachweislich.
- **Gesamte Testsuite ohne laufende Messung: 491 bestanden** (07:25, V7 installiert). Damit ist der offene Prüfpunkt der V7-Übernahme erledigt.
- Nach V8 gemessen, ohne Gewinn: `window_infer_all` (72,0/97,3), `dodge` lethal (73,6/97,5, +0,1), `far_opp=6` (69,8/96,0).

## 22.10.2026, 06:45 Berlin – Claude Code (autonom): V8 in Bestätigung gegen V7

- **V8 = V7 + `reach_assign` + `sap_no_overkill` + `safe_moves` + `collision_guard`** (18 V3-Netze bitgleich; [Plan mit Nachtrag](superpowers/plans/2026-10-22-v8.md)). Entwicklung 73,0/97,6 % → geschätzt **≈ 89,5 %** gegen Solution_92.
- **Auswahlblock 506020–506219: V8 85,75 % gegen V7 78,0 % (Δ +7,75 [+3,5; +12,2])**, default 100 % → Hürde (+1 pp) bestanden. Läuft: frisch 506220–507019 (800 Karten) + direkt 507020–507219 (`experiments/pipeline_v8.log`).
- Ohne Gewinn (nicht in V8): `sap_still` +0,40, `safe_moves` allein +0,45, `explore_quota=1` −4,25, `sap_still_all` (schadet), `holder_guard` +0,2.
- Neu, Default aus: `window_infer`/`window_infer_all` (Punkte-Inferenz im Relic-Spawnfenster von Match 2/3). Prüfung gegen die Wahrheit: keine falschen Punkte-Tiles, etwas mehr bekannte, aber auch etwas mehr fälschlich tote. Entwicklungsmessung läuft (`D22_V8w`), danach `dodge` lethal und `far_opp=6` auf V8.
- V8-Verlustanalyse (Karten, die V8 beidseitig verliert, 54 von 330 schweren): Match 2 fast immer verloren; pro Match 15–16 eigene Tode gegen 13 bei Solution_92, die meisten durch Saps auf stehende Halter mit wenig Energie; ~2 eigene echte Punkte-Tiles pro Step bleiben ungetestete Kandidaten.

## 22.10.2026, 06:05 Berlin – Claude Code (autonom): nächste Verbesserungen für V8

- Entwicklungsmessungen auf V7 + `reach_assign` (63,6/94,9 %, geschätzt ≈ 84,6 %): `unstack`, `sap_reserve_k=1`, `sym_map` (Spiegelung der Karte im Gedächtnis), `sap_relevant` ohne Gewinn. **`sap_no_overkill`** (keine Saps auf Gegner, die schon durch geplante Saps desselben Steps sterben) **68,5/96,0 % → geschätzt ≈ 86,9 %**. Befund dahinter: Halter feuerten zu dritt auf einen Gegner mit 21 Energie; unsere Halter haben zu wenig Energie und sterben dann an Kollisionen (im Mittel 41 gegen 102 Energie) und Void.
- Kollisionstode genauer (Verlustspiele, je Spiel): 5,5 Gegner zieht auf unsere stehende Unit, 3,4 beide ziehen auf dasselbe Tile, 1,5 wir ziehen auf einen stärkeren Gegner; Gegner fast immer vorher sichtbar. Neue Schalter `collision_guard`, `sap_still` (Default aus, Tests grün, 42 in `tests/test_rules_2110.py`); Messungen laufen (`D22_Bsnpdr{q,m,c}`, `D22_Bsnpdros`).
- Erkenntnis Spielregeln: neue Relic-Paare spawnen in Match 2/3 je bei Step 0–49 (`relic_spawn_schedule`). In Match 3 kennen wir ~2,7 echte eigene Punkte-Tiles nicht (37 % ungesehene Relics, 38 % ungetestete freie Kandidaten, 15 % Kandidaten im Nebel); Test `explore_quota=1` läuft.
- [V8-Plan](superpowers/plans/2026-10-22-v8.md) vorab festgelegt: Referenz V7, 800 frische Karten, Δ ≥ +2 pp mit unterer Grenze > 0, direkt gegen V7.
- Training: die 6 Netze mit V6-Regeln helfen gemischt nicht (`v6mix24` 53,9/93,9), allein schwach (`v6nets6` 52,0/88,4); weiteres Training gestoppt zugunsten der Regel-/Gedächtnis-Messungen.

## 22.10.2026, 05:35 Berlin – Claude Code (autonom): **V7 als Abgabe übernommen**

- **V7 (`v7_Bsnpd`) hat alle vorab festgelegten Gates bestanden** ([Plan](superpowers/plans/2026-10-22-v7.md), [Übernahmebericht](../experiments/analysis/release_20261022_v7/RELEASE.md)): frisch 505420–505819 Solution_92 **83,5 % statt 76,5 % (Δ +7,0 pp [+4,0; +10,0])**, default 99,75 % (Δ 0), **direkt gegen V3 68,0 % [61,5; 74,25]**.
- Übernahme per `scripts/release_candidate.py`: V3 bytegleich gesichert (`experiments/releases/20261022_all18_v3/`, SHA-256 `aac1c910…d935`, Wiederherstellung im README dort), V7 in `agent_p0.pth`/`agent_p1.pth` (SHA-256 `c394acba…95e6`), **Kurs-Runner unverändert: 8 Spiele bestanden** (beide Seiten, default + Solution_92, `act` max. 10,5 ms).
- Testsuite nach der Installation: 452 bestanden; 31 Studientests (`tests/test_early_curriculum_study.py`) von der Schutzsperre „Another model job is active“ abgewiesen, weil gleichzeitig eine Entwicklungsmessung lief (wie am 21.10.). Wiederholung ohne laufende Messung folgt.
- `scripts/v5_gates.py`: Mindest-Δ über `MIN_DELTA` einstellbar (Default 0,05 unverändert, V6-Entscheidung damit reproduziert); Meldung „vs Referenz“ statt „vs V3“.
- Weiter: `reach_assign` (Zielzuweisung nach BFS-Weglänge) auf V7 in der Entwicklung 63,6/94,9 % (geschätzt ≈ 84,6 %); `unstack` ohne Zusatznutzen (63,8/94,6); `sap_reserve_k=1` läuft. Nächster Kandidat V8 wird vorab gegen **V7 als neue Referenz** festgelegt.

## 22.10.2026, 05:05 Berlin – Claude Code (autonom): V7 in Bestätigung, weitere Ursachen gefunden

- **Kartenkorrekturen gemessen** (`dev_hard330`/`dev_easy330`, Solution_92; V3 27,0/100 %): Bs 48,0/97,6; + `nebula_infer` 50,6/96,3; + `path_fix` 57,4/93,9; + `drift_track` **58,3/95,1** → geschätzt gesamt ≈ 82,9 % (Bs 81,2 %, V3 75,9 %).
- **V7 = Bs + die drei Korrekturen** ([Plan, vorab](superpowers/plans/2026-10-22-v7.md)): Auswahlblock 505220–505419 **82,25 % statt 78,0 % (Δ +4,25 [+0,3; +8,3])**, default 100 % → Hürde bestanden. Frische Bestätigung 505420–505819 + direkt 505820–506019 läuft (`experiments/pipeline_v7.log`). Bei bestandenen Gates Übernahme per `scripts/release_candidate.py`.
- PPO `cnn3b`: Stände 50/100/150 alle unter V3 (bester 72,0 % gegen 76,7 %) → beendet, Bestätigungsblöcke unbenutzt.
- 6 Netze mit V6-Regeln trainiert (Starts 27–29/37–39): gemischt mit den 18 V3-Netzen (`v6mix24`, gleiche Regeln wie Bs) `dev_hard330` **53,9 % statt 48,0 %**; leichte Karten laufen.
- **Neue Diagnosen** auf Karten, die V7 noch beidseitig verliert: Zielzuweisung schickt Units zu Punkte-Tiles unter Asteroiden (unerreichbar) → `reach_assign` (BFS-Weglänge, unerreichbare Ziele zuletzt); gestapelte Units warten → `unstack`; unsere Halter haben 60–84 statt 82–115 Energie, wir sappen 2–3× so oft wie Solution_92, 70 % der Toten auf Punkte-Tiles, 74 % mit weniger Energie als ein Sap kostet (Kollision, Void, direkter Sap) → `sap_reserve_k` (Regel-Saps nur mit Reserve). Alle Default aus, Tests grün (37 in `tests/test_rules_2110.py`). Messungen laufen (`D22_Bsnpdr*`, `D22_Bsnpdru*`, danach `D22_Bsnpdrk*`).
- Training: 6 Netze `full_rules_v7` (V6-Regeln + Nebel-Inferenz + Drift im Gedächtnis). Erster Start scheiterte an der Schutzprüfung (Starts ≥ 50 lägen über 500000); `protocol.train_seed` nutzt für Starts ≥ 50 jetzt das bisher unbenutzte Blockende ab Index 5000 (Test ergänzt), Neustart 04:59 (`experiments/pipeline_v7nets.log`).
- Abgabe weiterhin **V3** (`aac1c910…d935`).

## 22.10.2026, 04:30 Berlin – Claude Code (autonom): V6 knapp unter der Hürde, zwei Kartenfehler gefunden

- **V6 = Bs** frisch 504220–504619: Solution_92 81,6 % statt 77,75 % (Δ +3,88 pp [+1,5; +6,25]), default 100 %, direkt gegen V3 67,5 % [62,25; 72,75]. Nur die Mindestgröße +5 pp verfehlt → **V3 bleibt**. Bs erfüllt die allgemeine Regel der Spezifikation vom 20.10.; Übernahme wäre eine Teamentscheidung.
- PPO `cnn3b` Stand 50: 72,0 % gegen V3 76,7 % (−4,8). Stände 100/150 laufen automatisch (`scripts/pipeline_cnn3b_eval.sh`, Log `experiments/pipeline_cnn3b.log`).
- **Verlustanalyse** (40 Karten, die Bs auf beiden Seiten verliert): Match 1 meist gewonnen, Match 2/3 verloren. (1) Die Gedächtniskarte veraltet durch Drift: im Mittel ~20 falsche und ~20 fehlende Asteroiden, 18 % der bekannten Tiles falsch. Units sitzen hinter vermeintlichen Asteroiden fest (360014: ganzes Match 3 mit 0 Energie am Spawn). (2) Greedy-Falle: Netz läuft nach Luftlinie in Sackgassen an Asteroidenwänden und pendelt (360581).
- Neu, Default aus, Tests grün (`tests/test_rules_2110.py`, 33): `nebula_infer` (unsichtbar in Sensorreichweite ⇒ Nebel), `path_fix` (BFS-Schritt statt Sackgasse), `drift_track` (Drift erkennen, ganze Karte rollen: 210/210 Drifts in 6 Spielen erkannt, falsche Tiles 78,6 → 13,5 pro Step). Grobcheck auf den 8 schlimmsten Karten (ausgewählt, nur Hinweis): 0/16 → 2/16 Siege, deutlich mehr Punkte.
- **Läuft** (Ergebnisse `experiments/compare/regeln/D22_{Bsn,Bsnp,Bsnpd}_*`, Vergleich mit `D22_Bs_*`): Bs + `nebula_infer` / + `path_fix` / + `drift_track` auf `dev_hard330`/`dev_easy330`. Training `full_rules_v6` (6 Netze, Auswertung automatisch, `experiments/pipeline_v6nets.log`).
- **Offen:** Entwicklungsergebnisse auswerten. Den besten Kandidaten (vermutlich Bs + Kartenfixes) vorab mit neuem, noch nicht reserviertem Auswahl- und Bestätigungsblock festlegen und prüfen. `agents/sherlock/tactics.py` (Ein-Schritt-Simulator, gegen die Engine geprüft) ist ein Entwurf, nicht eingebunden. Abgabe weiterhin V3 (`aac1c910…d935`).

## 22.10.2026, 03:20 Berlin – Claude Code mit Mahmoud (autonom über Nacht): V5-B knapp unter der Hürde, V6 in Bestätigung

Auftrag des Users: selbstständig weiterarbeiten bis Nachmittag, Ziel ≥ 90 % gegen Solution_92, ganze CPU nutzen; Übernahme nur über vorab festgelegte Tests.

- **V5-B** (`art_sap` 3 + `nebula_avoid` Sperre 25, 18 V3-Netze bitgleich; [Plan/Ergebnis](superpowers/plans/2026-10-22-v5-combination.md)): frisch 503420–503619 Solution_92 **75,75 % statt 71,0 %, Δ +4,75 pp [+1,0; +8,25]**, default 99,75 %, **direkt gegen V3 62,0 % [56,5; 67,25]**, Kurs-Runner bestanden. Hürde Δ ≥ +5 pp um 0,25 pp verfehlt → **nicht übernommen**, Hürde nicht nachträglich geändert. Entscheidungsvorlage für Mahmoud/Moayed.
- **Training auf schweren Karten** (6 Netze, 660 Karten mit V3-Niederlage): `hard6` 70,5 % (−6,2 gegen V3, −4,3 gegen Kontrolle), `hard24` +2,5 → kein Gewinn.
- Große Entwicklungs-Sets `dev_hard330`/`dev_easy330`: Bs (V5-B mit **weicher** Nebel-Meidung, `nebula_avoid_mode=soft`) ≈ +5,3 gesamt, beste einfache Variante. Ohne Gewinn bzw. schädlich: `stack_guard` (blockiert Wege, leichte Karten 79 %), `relic_search` (leicht −5), `sap_dropoff_est`, `art_surplus`, `fog_sap` bei Sicht ≤ 2. Neu: `dodge_verify` (Online-Prüfung des Solution_92-Modells), `dodge_auto_max`, `dodge_bait`.
- **V6 = Bs** läuft nach [vorab festgelegtem Plan](superpowers/plans/2026-10-22-v6.md): Auswahl 504020–504219 (V3 dort 77,0 %), dann 400 frische Karten 504220–504619 + direkt 504620–504819 (`scripts/pipeline_v6.sh`, Log `experiments/pipeline_v6.log`).
- Training läuft: 6 Netze `full_rules_v6` (Regeln von Bs schon im Training), Starts 27–29/37–39, Auswertung automatisch (`scripts/pipeline_v6nets.sh`). PPO `cnn3b` fast fertig; Prüfung der Stände 50/100/150 folgt laut Plan.
- Abgabe weiterhin **V3** (`aac1c910…d935`).

## 22.10.2026, 00:45 Berlin – Claude Code mit Mahmoud: versteckte Parameter, Entwicklungs-Sets, V5-Kandidaten in Auswahl

**Kartenanalyse** (`experiments/analysis/hard_map_training_20261021/map_features*.{py,csv}`, wahre Startzustände der 2000 gescreenten Karten, reine Analyse): V3 gegen Solution_92 nach verstecktem Parameter – Sap-Streufaktor 0,25/0,5/1,0: **65,9/76,3/85,4 %**; Nebelabzug 25: 65,5 % (sonst ~78 %); Bewegungskosten 1/5: 69,1/84,4 %; ≥ 14 Punkte-Tiles nahe der Diagonale: 54,7 %.

**Schnellere Entwicklung:** deterministische Spiele → feste Entwicklungs-Sets aus der Kartensuche ohne V3-Neumessung: `dev_hard150` (V3 25,0 %), `dev_easy60` (100 %), `dev_neb25_100` (64,5 %), `dev_neb5_60` (71,7 %); `scripts/par_eval.py --seed-list`, Skript `dev_eval.sh`. Kennzahl für das Gesamtbild: 0,33·Δhard + 0,67·Δeasy (Anteil schwerer Karten 660/2000).

**Ergebnisse (alle Schalter aus in der Abgabe):** hard150/easy60 gegen Solution_92 – `art_sap` 3: 37,7/98,3 (≈ +3,0 gesamt); `dodge` always: 35,0/97,5 (≈ +1,6); beides 38,7/96,7 (≈ +2,3); `art_sap` nur bei Rückstand (`tactics_when_behind`): 33,0/100 (≈ +2,6); neues `sap_kill_safe` (korrigiert `sap_kill_first`, das schon tote Gegner mit Energie < 0 bevorzugte): 33,3/98,3; mit `art_sap` 37,3/97,5. `nebula_avoid` (neue Online-Schätzung, Schwelle 25): Nebel-25-Karten 69,5 % statt 64,5 %; mit Schwelle 5 auf Nebel-5-Karten −16,7 pp → Schwelle 25.

**Online-Parameterschätzung** `agents/sherlock/param_est.py` (aus eigenen Energieverläufen, nur Beobachtungen): Nebelabzug 60/60 richtig ab Schritt 202; Streufaktor nach Filtern für wanderndes Energiefeld und fehlende Schützen **0 Fehlschätzungen in 60 Spielen**, sicher bekannt bei Schritt 101/202/300 in 25/41/47 von 60 Spielen (sonst Annahme 0,5). `dodge_auto`: Ausweichen nur bei geschätztem Streufaktor ≤ 0,5 (Entwicklung: always bei 0,25/0,5/1,0: +5,9/+2,5/−2,2).

**V5-Auswahl läuft** nach [vorab festgelegtem Plan](superpowers/plans/2026-10-22-v5-combination.md) (Kandidaten B–E, je hard150/easy60), danach Zufallsblock 503820–504019 und einmalige frische Bestätigung. Training auf schweren Karten (Lauf `_hard`) bei ~2000/3000 Spielen, Auswertung automatisch. Keine Abgabeänderung ohne Rücksprache.

## 21.10.2026, 22:50 Berlin – Claude Code mit Mahmoud: Solution_92-Modell, Ausweichen, Training auf schweren Karten läuft

Ziel des Users jetzt: 99–100 % gegen Solution_92 und Platz 1 im Kursturnier. Neu (alle Schalter aus, Abgabe unverändert):
- `agents/sherlock/opp_model.py`: sagt aus unserer Sicht voraus, wen Solution_92 sappt (stehendes Schiff auf Punkte-Tile, Energie ≥ Sap-Kosten, Ziel = unsere höchste sichtbare Unit-ID in Manhattan-Reichweite, aus seinem Code). Gemessen in 20 Spielen (500720–500729): 97,2 % der Saps sichtbarer Schützen vorhergesagt, Ziel zu 98,5 % richtig; 38 % Fehlalarme (nur ziehende Schiffe), 25 % der Saps kommen von unsichtbaren Schützen.
- `dodge` (`dodge_mode` lethal/always): vorhergesagte Ziele weichen aus. Entwicklungskarten gegen V3 85,0 %: lethal −0,8 [−3,3; +1,7], always +1,7 [−1,7; +5,0]. Mechanismus wirkt (direkter Gegnerschaden Match 3 −41 %), Siegquote kaum.
- Sichtprüfung verlorener Spiele (`scripts/render_snapshots.py`): drei Fehlerbilder – Wettlauf um nähere Haufen verloren, neues Relic-Paar in Match 2/3 nicht gesucht, überzählige Units ungenutzt.
- **Training mit Schwerpunkt auf schweren Karten** ([Plan, vorab](superpowers/plans/2026-10-21-hard-map-training.md)): Kartensuche V3 gegen Solution_92 auf 2000 neuen Trainingskarten 360000–361999 (4000 Spiele, V3 76,0 %); 660 Karten mit mindestens einer verlorenen Seite (300 beide verloren) → `hard_seeds.json`. Neue Option `scripts.experiment --seed-file`: Solution_92-Spiele laufen auf diesen Karten. 6 Läufe `20261021_full_rules_v3_s40`–`s45_hard` (je 3000 Spiele) gestartet 22:44; Auswertung automatisch (`scripts/pipeline_hard.sh`) auf neuem Auswahlblock 503820–504019. PPO `cnn3b` läuft mit niedrigster Priorität weiter.

Tests: 376 bestanden + 14 Untertests (ohne die 88 prozessgesperrten Studientests, die bei laufenden Spielen absichtlich verweigern).

## 21.10.2026, 21:55 Berlin – Claude Code mit Mahmoud: Gefahr-Merkmale ohne Gewinn, PPO läuft weiter

Die 6 Läufe `20261021_full_rules_v3_threat_s40`–`s45_sol70` (je 3000 Spiele, 18.000 insgesamt, je ~116 min, alle fehlerfrei) wurden nach dem [vorab festgelegten Plan](superpowers/plans/2026-10-21-threat-features.md) ausgewertet (`scripts/pipeline_threat.sh`, Log `experiments/pipeline_threat.log`). Auswahlblock 503220–503419, 200 Karten, beide Seiten, je 400 Spiele: V3 Solution_92 76,7 %, default 98,8 %; Kontrolle `v3nets6` 73,3 % (Δ −3,5 [−8,7; +1,5]); `threat6` 72,8 % (Δ −4,0 [−9,5; +1,3]); `mix24` = `threat6` + 18 V3-Netze 78,2 % (**Δ +1,5 [−2,8; +5,8]**), default 99,0 %. Methodenfrage `threat6` gegen Kontrolle: **−0,5 [−6,0; +4,8]** – kein messbarer Effekt der Gefahr-Merkmale. Vorab-Regel (+3 pp vor V3) verfehlt: Versuch beendet, **frische Blöcke 503420–503819 unbenutzt**, keine Abgabeänderung. Hashes `threat6` `7a26f21b…8d53`, `mix24` `ace788eb…8034` (lokal, gitignored).

Vorab festgelegter Nachtrag `mix24_art3` (`mix24` + `art_sap`, 3 Treffer) auf demselben Auswahlblock: 78,2 % (Δ +1,5 [−3,0; +6,0]), default 99,3 % → ebenfalls beendet, frische Blöcke weiter unbenutzt.

PPO `cnn3b` läuft weiter (Iteration 50 von 150, Trainings-WR gegen Solution_92 bisher flach ~0,71–0,73); Prüfung der Stände 50/100/letzter erst nach Laufende auf 503220–503419 laut Plan. Gesamte Testsuite nach Trainingsende **459 bestanden + 14 Untertests** (offener Punkt vom 19:33-Eintrag erledigt, inklusive Moayeds Ensemble-Korrektur `b359bd6`).

## 21.10.2026, 21:17 Berlin – Codex: V4-Programm ausgewertet, V3 bleibt Abgabe

[Abschlussbericht für den 22.10.](MORGENBERICHT_20261022.md). **Kein qualifizierter stärkerer V4.** Paar-Koordinator, Zielpilot, begrenzte CNN-Fortsetzung und Artillerie-Bestätigung ergeben zusammen **3.336 neue Spiele: 240 Training und 3.096 Auswertungs-/Kontroll-/Kursprüfspiele**. Historische Referenzen und frühere Nachtversuche nicht erneut mitgezählt. Der letzte Kandidat gewinnt frisch gegen Solution **301/400 statt V3 292/400**, Δ +2,25 Prozentpunkte, gepaartes 95%-Kartenintervall [−0,25; +4,75]. Beide Solution-Übernahmegates verfehlt; default jeweils 399/400. Kein direkter frischer Folgetest, kein zusätzlicher Trainingslauf, kein Gewichtswechsel.

[Artillerie-Archiv mit allen 2.208 Spielen](../experiments/analysis/art_sap_confirm_20261021/README.md): unabhängige Abschlussprüfung vollständig, Root-Nachrechnung und erneuter Audit erfolgreich. Originalzustand zum Auditzeitpunkt erhalten; danach `completed_negative`. Alle 83 Quell-/Runtime-, fünf Eingabe- und acht Schutzdatei-Hashes unverändert. Experimentdaten und Kandidat in main; erfolgloser Koordinationscode bleibt auf `improvement/v4-joint-20261021`.

Abgabe unverändert `all18_v3` (`aac1c910…8d935`), alte Sechser-Sicherung unverändert (`3788fb72…d158`). Artillerie-Karten 523000–523199 jetzt verbraucht; 523200–523399 und der finale 100%-Audit wurden in diesem Programm nicht gespielt. Die [unabhängige Abschlussentscheidung](../experiments/analysis/art_sap_confirm_20261021/next_step_review.md) empfiehlt keine weitere unbegründete Variantenrunde. Nächste neue Evidenz sind Mahmouds bereits gestartete 101-Merkmal-DQN-/PPO-Läufe unter ihrem festen Plan und den reservierten Karten 503220–503819. Diese Trainings nicht duplizieren.

Der begrenzte Auftrag wird nach Veröffentlichung vorzeitig abgeschlossen; das Ziel einer deutlich stärkeren V4-Version bleibt offen. Mindestens 30 % Nutzerkontingent erhalten, kein Reset. Tatsächliche Abschlussprozesse, Remote-Stand und Restkontingent stehen im Abschlussbericht.


## 21.10.2026, 20:43 Berlin – Codex: Artillerie-Kandidat in frischer Bestätigung

Vorgeschaltete Prüfung abgeschlossen: 480 Reproduktionsspiele stimmen für V3 und `art_sap=True, art_min_hits=3` in sämtlichen 23 Nichtzeitfeldern mit den historischen Referenzen überein. Solution **108/120 statt 102/120** (Δ+5 pp, gepaartes Kartenintervall [+0,833;+10]); default beide 120/120. Direkt auf denselben Entwicklungskarten **80 Siege/40 Niederlagen gegen V3** (66,67%, Kartenintervall [58,33;75]%). Unabhängiger Datenreview der 600 Vergleichsspiele bestanden. Zusätzlich acht Kursprüfspiele bestanden: exakte Ladung aller 18 Netze, frisches Belief, 303 Schritte; größte p95-Aktionszeit 2,326 ms, Maximum 10,946 ms. Der Kurscheck prüft Aktionsformat, keine vollständige semantische Legalitätsgarantie.

Die unveränderten 18 V3-Netze im Versuchskandidaten wurden rekursiv und nach Laden geprüft; unabhängiger Bytevergleich aller 264 Tensor-Speicherblöcke ebenfalls identisch. Kandidat SHA `e392f20c60d51817591ee4c0061bc8150e7ec8aa312b42e704004538ead45497`. Die zwei gespeicherten Configänderungen sind die einzige Veränderung gegenüber V3. **Noch keine Freigabe als stärkere Abgabe.**

Jetzt fester Vergleich auf 200 neuen Karten 523000–523199, beide Seiten, beide Gegner, jeweils V3/Kandidat = 1.600 Spiele. Erst nach vollständiger Auswertung aller vorher festgelegten Gates gegebenenfalls 400 direkte Spiele auf 523200–523399. Finaler Seed-Abgleich: 2.109 zugängliche CSV-Dateien mit Seedspalte, 1.485.640 Zeilen, kein Treffer im reservierten Bereich. Mahmouds 503220–503819 bleiben frei für seine Studie. Arbeitszweig `improvement/v4-joint-20261021`, eingefroren auf `9c1efc7`; aktuelle Daten dort unter `experiments/analysis/art_sap_confirm_20261021/`. main erhält den fertigen Bericht erst nach Abschluss.

Neue ausdrückliche Budgetgrenze von Moayed: mindestens 30 % Codex-Kontingent übriglassen. Root beginnt Abschluss bei 35 % Rest; kein Reset. Bei letzter Kontrolle 79 % Rest. Beide aktiven Automationen übernehmen diese Grenze. Die Frist 22.10. um 06:00 Berlin gilt nur, sofern die Budgetgrenze nicht früher greift. V3 und alte Sicherung bleiben unverändert.


## 21.10.2026, 20:30 Berlin – Codex: gemeinsame Integration geprüft

Mahmouds Artillerie-/Gefahrmerkmale und die Korrektur der Ensemble-Dimensionen sind im Arbeitszweig zusammengeführt. Der erste Gesamtlauf zeigte 14 überholte Testfixtures (517 bestanden): Frühablehnung beschädigter Checkpoints, fehlende Breitenangaben in inerten Curriculum-Mocks und ein Zielpilot-Mock ohne Eingabedimension. Nur die Testverträge angepasst; Produktionsprüfung nicht abgeschwächt. Unabhängiger Review der Korrektur und Fixtures ohne offene Blocker.

Root-Gesamtlauf im V4-Arbeitszweig: **531 Tests und 14 Untertests bestanden in 82,52 s**. Die Tests des Zielpiloten gehören ausschließlich zum Arbeitszweig; main erhält Werkzeugkorrektur und gemeinsame Testfixtures. [Review](ENSEMBLE_DIMENSIONEN_REVIEW_20261021.md). Kein Trainings-/Agentenverhaltenswechsel und keine Gewichtsänderung durch die Fixture-Korrektur. Nächster Schritt: festgeschriebene Artillerie-Reproduktion, noch keine Stärkeverbesserung belegt.


## 21.10.2026, 20:23 Berlin – Codex: ältere Ensemble-Testdaten an strikte Ladeprüfung angepasst

Nach Roots Integrationslauf zwei Testverträge korrigiert: Der Kandidatenrunner-Test verlangt jetzt die frühe Ausnahme bei falscher Eingabebreite und prüft weiterhin unabhängig Tensor-/Config-/Architekturabweichungen. Die inerten Curriculum-Prüfnetze erhalten einen Tensor mit der deklarierten Eingabebreite; sämtliche Herkunfts- und Gate-Prüfungen bleiben bestehen. **2 gezielt reproduzierte Fehler vor der Anpassung, danach 98 Tests aus beiden betroffenen Dateien bestanden** (44,30 s). [Nachweis](ENSEMBLE_DIMENSIONEN_20261021.md). Nur Tests und Dokumentation geändert, Rechenplatz freigegeben; erneute vollständige Integrationsprüfung durch Root offen.

## 21.10.2026, 20:15 Berlin – Codex: Ensemble-Dimensionen gegen stillen Netzverlust abgesichert

[Korrektur und Prüfnachweis](ENSEMBLE_DIMENSIONEN_20261021.md): Beim Erweitern eines gespeicherten homogenen Ensembles blieb bisher eine zu kurze Dimensionsliste bestehen; der Loader ließ dadurch Netze aus. Der Builder schreibt jetzt immer alle Dimensionen. Gemeinsame Prüfung von Listenlänge, ganzzahligen positiven Grenzen und tatsächlichen Tensorbreiten weist fehlerhafte Checkpoints ab. Fehlende/`None`/leere Altformat-Metadaten und gültige 101/79-Ensembles bleiben unterstützt.

TDD auf isoliertem Zweig: **23 Fehler/5 bestanden vor der Korrektur**, danach **28 neue Tests bestanden**; abschließend **32 fokussierte Tests bestanden** inklusive bestehender Persistenz- und Mischensemble-Prüfung. Rechenplatz erst nach Freigabe benutzt, anschließend freigegeben. Keine Aktionsregel-, Trainingscode- oder Gewichtsänderung. Vollständige Testsuite und unabhängiger Review des zusammengeführten Stands durch Root noch offen; kein Push aus diesem Arbeitszweig.



## 21.10.2026, 20:16 Berlin – Codex: CNN-Fortsetzung beendet, Artillerie-Prüfung vorbereitet

[724 neue registrierte Spiele, Rohdaten und unabhängiger Abschlussreview](../experiments/analysis/cnn3_sol90_s20_20261021/README.md): 240 Trainingsspiele ab Original-PPO60 in 38:50 Minuten, 240 Original-Referenzspiele, vier V3-Kontrollen und 240 Endstand-Spiele. Auf den bekannten 60 Karten gewinnt der einzige finale CNN-Kandidat gegen Solution **89/120**, Original-PPO60 **96/120**, V3 **102/120**; default alle120/120. Gegenüber V3 Δ−10,83 pp, gepaartes95%-Kartenintervall[−20;−2,5]. Vorgegebene Solution-Gates verfehlt; dieser Kandidat ist beendet. Keine frischen Tests, keine Zwischenstand-Auswahl und keine Übernahme. Alle V3-/Sicherungshashes unverändert.

Root-Tensor-/Ladeprüfung und unabhängige CSV-/Hash-/Statistikprüfung bestanden. Quellen während des Versuchs eingefroren auf `47388d4`; 30 von32 Policy-Tensoren geändert, Architektur und effektive Konfiguration erhalten. Neuer kleiner Minibatch und frischer Adam erlauben keine isolierte Aussage über den Gegner-Mix. Die Spielzahlen werden nicht mit den parallel auf Mahmouds Rechner laufenden Trainings vermischt.

Mahmouds Commits `f540da4` bis `baef7a8` gelesen und nach Ende der eigenen Modelljobs ins lokale main übernommen. [Unabhängiger Code-/Datenreview und separater Vorabplan](superpowers/plans/2026-10-21-art-sap-confirmation.md) für genau den bereits ausgewählten Artillerie-Schalter3: historisch108/120 statt102/120, aber sieben Varianten auf bekannten Karten und fehlende vollständige Run-Manifeste. Deshalb zuerst vollständige Reproduktion mit exakt18 unveränderten V3-Netzen, dann direkte/Kursprüfung und nur bei bestandenen Gates frische Karten. Noch keine eigenen Artillerie-Spiele. Mahmouds503220–503819 bleiben für seine Studien reserviert, Root523000–523399 ist noch unbenutzt.

Separater Werkzeugfehler beim Wiederaufbau gespeicherter homogener Ensembles gefunden: veraltete `ensemble_dims` können beim Laden zusätzliche Netze unterschlagen. Gezielte Reproduktion/Korrektur in eigenem Zweig; unabhängiger Review und endgültige gemeinsame Integrationssuite stehen noch aus. Die Artillerie-Kopie verwendet diesen Builder nicht. Nachtauftrag läuft weiter bis spätestens22.10.06Berlin; spätestens05:15 Abschlussreserve. Aktuelle Abgabe bleibt V3.


## 21.10.2026, 19:33 Berlin – Claude Code mit Mahmoud: Festungs-Diagnose, zwei Trainings laufen

**Diagnose** ([Mechanismus-Probe](../experiments/analysis/mechanism_probe_20261021/README.md), neues Messwerkzeug `scripts/mechanism_probe.py`, reine Messung, V3 unverändert, Entwicklungskarten 500720–500779): Verlorene Matches 3 liegen auf Karten mit vielen Punkte-Tiles. In den deutlichsten Niederlagen kippt das Sap-Verhältnis in Match 3 (z. B. 500753: 6 : 68 Saps, 23 : 4 Tote): Solution_92 sitzt mit vielen Units auf einem umkämpften Relic-Haufen („Festung“) und sappt alles in **Manhattan**-Reichweite; unsere wiedergeborenen Units laufen einzeln hinein. Die Engine erlaubt Saps im ganzen Quadrat.

**Neue Schalter, alle Default aus, Abgabe unverändert:** `art_sap` (Sap aus Manhattan-sicherer Position bei ≥ n Treffern) und `siege` (Festungsziele aus der Ferne belagern, `rules.SiegePlan`). Auswahl auf Entwicklungskarten gegen V3 (85,0 %): `art_sap` 2/3/4 Treffer +2,5/+5,0 [+0,8; +10,0]/−0,8; Nachbarvarianten ±1 → nicht robust, kein Kandidat. `siege` **−17,5** [−25,8; −10,0] → verworfen (Units geben umkämpfte Tiles auf). Default jeweils 120/120.

**Training (läuft, noch keine Ergebnisse):** (1) PPO `cnn3b`: Start `cnn3/ppo_0060`, 150 Iterationen × 80 Spiele, Gegner 80 % Solution_92 / 15 % V3 / 5 % default, Seed 5, Trainingskarten 250000+ (`experiments/ppo/cnn3b/`), auf Mahmouds Rechner mit dem damaligen `ppo_train` vor `14469f2` gestartet; unabhängig von Codex' begrenztem 10-Iterationen-Lauf `cnn3_sol90_s20` auf Moayeds Rechner. (2) Neuer Schalter `threat_feats` (+22 Netzeingaben: je Tile sapfähige Gegner in Manhattan-/Quadrat-Reichweite, Gegnerenergie auf/neben dem Tile, bester Sap, besetzte Punkte-Tiles), Variante `full_rules_v3_threat` = `full_rules_v3` + Gefahr-Merkmale: 6 Läufe `20261021_full_rules_v3_threat_s40`–`s45_sol70`, je 3000 Spiele, 70 % Solution_92 – gleiche Starts/Einstellungen wie die Kontrolle `v3nets6` vom 20.10. Alte Checkpoints/Abgabe laden unverändert (79 Eingaben).

**Auswertung vorab festgelegt:** [Plan](superpowers/plans/2026-10-21-threat-features.md) mit Auswahl auf 503220–503419, Bestätigung 503420–503619 und direktem Vergleich 503620–503819, Abnahmeregeln wie V4-Strategie. Dazu `build_ensemble --mixed`: V3-Netze (79 Eingaben) und Gefahr-Netze (101) in einem Ensemble, alte Netze bekommen die ersten 79 Merkmale (`ensemble_dims`). Kurs-Runner-Prüfung und `train.py --resume` akzeptieren Gefahr-Checkpoints. Tests zu `92ece27` (während die Trainings liefen): 400 bestanden + 14 Untertests; die 31 Tests in `tests/test_early_curriculum_study.py` verweigern absichtlich, solange `scripts.experiment`-Prozesse laufen (Prozessprüfung „Another model job is active“), Datei unverändert – Wiederholung nach Trainingsende steht aus.

**Seeds reserviert (Mahmoud):** 503220–503419 Auswahl unter PPO-/Threat-Ständen, 503420–503619 einmalige frische Bestätigung genau eines vorher gewählten Kandidaten, 503620–503819 Reserve. Vor Nutzung in 524 CSVs ohne Treffer geprüft.

**Prüfungen:** gesamte Testsuite 422 Tests + 14 Untertests bestanden (davon 13 neu in `tests/test_rules_2110.py`), Trainings-Probelauf mit 101 Eingaben gespeichert/geladen. Abgabe-Hash unverändert.

## 21.10.2026, 19:28 Berlin – Codex: begrenztes CNN3-Training läuft

Die geprüfte PPO-Zufallsbindung ist als `14469f2` in main veröffentlicht: 489 Tests plus 14 Untertests im Arbeitszweig, danach acht fokussierte Tests im Hauptcheckout. Vorabplan und unabhängige Reviews unter [CNN3-Fortsetzung](superpowers/plans/2026-10-21-cnn3-bounded-continuation.md). Die V3-Abgabe bleibt unverändert.

240 neue Referenzspiele auf 60 bekannten Karten 500720–500779: Original-PPO60 gewinnt **96/120 gegen Solution_92** und **120/120 gegen default**. V3-Referenz **102/120 bzw. 120/120**; vier neue Kontrollspiele reproduzieren alle 23 gespeicherten Nichtzeitfelder. Keine frischen Bestätigungskarten verwendet.

Der einzige geplante Trainer läuft seit etwa 19:28 Berlin: 240 Spiele, 10 Iterationen, Startseed 20, letzter Originalstand PPO60, festes Gegnerprogramm mit 211 Solution- und 29 Default-Spielen. Das sind geplante Trainingszahlen, noch kein abgeschlossenes Ergebnis. Endstand allein wird ausgewertet; keine Auswahl eines günstigen Zwischenstands. Maximal 90 Minuten Training, Quellen- und Gewichtskontrolle, Speicher- und Fehlerüberwachung. Bei negativem Entwicklungsgate keine weitere Verlängerung dieses Kandidaten.

Aktive Arbeitskopie auf Moayeds Rechner: `/Users/moayedshawesh/Desktop/KI/sherlock-v4-joint`, eingefrorener Commit `47388d4`. Livezustand dort unter `experiments/analysis/cnn3_sol90_s20_20261021/execution_state.json`; kein zweites Training oder paralleler Modelltest auf dem 8-GB-Mac. main darf getrennt aktualisiert werden; der aktive Versuch übernimmt neue Quellen erst nach Abschluss. Der Remote-Wächter meldet Mahmouds neue Commits. Späteste Gesamtfrist 22.10.2026 06:00 Berlin, Abschlussreserve ab 05:15.

## 21.10.2026, 19:16 Berlin – Codex: Zielpilot beendet, CNN3-Folgeversuch vorbereitet

[Acht Spiele und unabhängiger Datenreview](../experiments/analysis/v4_target_pilot_20261021/README.md): Kontroll- und Wiederholungsverläufe identisch, aber in 32 festen Situationen keine geeignete Zielalternative. Festes Gate verfehlt; kein Zielbewerter, keine frischen Tests, keine Änderung an V3. Daraus folgt keine allgemeine Wirkungslosigkeit von Zielzuweisung. Zusammen mit dem Paar-Koordinator 404 neue Spiele; weiterhin kein qualifizierter V4.

Mahmouds Commit `718a298` in Haupt- und Arbeitskopie am sicheren Phasenübergang integriert. Originale CNN3-Gewichte per Hash geprüft. [Separater begrenzter Fortsetzungsplan](superpowers/plans/2026-10-21-cnn3-bounded-continuation.md): nach technischer Prüfung einmal 240 PPO-Trainingsspiele ab PPO60, 90-Minuten-Grenze und feste Entwicklungsgates. Noch nicht gestartet. Vorher wird eine reproduzierte Lücke geschlossen: gleicher Spielseed bindet bisher den Torch-Zufall der PPO-Aktionswahl nicht; auch der Lernprozess setzt ihn nicht. Eine kleine Korrektur samt unabhängigem Review läuft. Keine Architektur- oder Rewardänderung und keine Gewichtsübernahme.

## 21.10.2026, 19:10 Berlin – Claude Code mit Mahmoud: CNN3-Originalgewichte geteilt

Auf Codex' offene Bitte (Morgenbericht): Original-Checkpoints des Laufs `cnn3` (`scripts/pipeline_cnn3.sh`, 20.10.) liegen jetzt versioniert in `experiments/candidates/`: `cnn3_bc.pth` (Start nach BC, SHA-256 `1879c991…f62a2`), `cnn3_ppo0050.pth` (auf Val 720 bester Stand, frisch 502020–502219 getestet; `5c16f62d…617b3`) und `cnn3_ppo0060.pth` (letzter Stand; `0efe4d39…0fb0bef`). Volle Hashes, Ergebnisse und Lehrer (`all18_fo10.pth`, identisch mit `experiments/ensembles/all18_fo10.pth`) in [Kandidaten-README](../experiments/candidates/README.md). `bash scripts/install_candidates.sh` kopiert sie nach `experiments/ppo/cnn3/` und prüft die Hashes; lokal ausgeführt, alle OK. Config/Architektur stecken im Checkpoint (`cfg`, `arch`, `feature_dim` 79). Lehrerdaten `bc_data.npz` (4,9 GB) bleiben lokal bei Mahmoud. Keine Code-, Gewichts- oder Abgabeänderung; Abgabe weiter `all18_v3` (Hash geprüft).

## 21.10.2026, 18:53 Berlin – Codex: erster gemeinsamer V4-Zug ohne Stärkegewinn

[396 neue Spiele, vollständige Daten und unabhängige Prüfung](../experiments/analysis/v4_joint_pairs_v1_20261021/README.md). Auf 60 bekannten Karten 500720–500779 gewinnt der Koordinationskandidat gegen Solution_92 **101/120 statt V3 102/120**, Δ −0,83 pp, gepaartes Kartenintervall [−2,5; 0]. Default beide120/120. Direkt gegen V3 62Siege/58Niederlagen, Resultat51,67%, Intervall[50;54,17]%. Vorgegebenes Solution-Gate verfehlt; keine frischen Bestätigungsspiele, kein Gewichtswechsel.

48 fokussierte Tests, insgesamt457 Tests plus14 Untertests, unabhängiger Codereview, acht Kurs-Runner-Spiele und Hashkontrollen bestanden. Die technische Umsetzung und der Kandidat bleiben auf `improvement/v4-joint-20261021`; main erhält Ergebnisse und Übergabe. Die 18 Netze entsprechen exakt V3. Quellen waren während sämtlicher Versuche eingefroren.

Die passive Folgeprüfung reproduziert vier Entwicklungsverläufe. In120 abgetasteten Situationen erlauben alle legalen Bewegungen sieben mögliche Belegungsgewinne, die zwei besten Netzvorschläge noch zwei und die15%-Bewertungsgrenze keinen. Das erklärt die geringe Aktivierung dieser Stichprobe; kein Beweis, dass Lockerung sinnvoll wäre. Kandidat beendet. Nächste eigenständige Machbarkeitsfrage: Kann eine Zielwahl anhand von Erreichbarkeit/Energie/Bedrohung die tatsächlich ausgeführte V3-Aktion verändern? Erst bei nachgewiesenem Einfluss und korrekter Simulator-Isolation ist ein kleiner gelernter Zielbewerter sinnvoll. User hat eigenständige Folgearbeit bis22.10.06Berlin autorisiert; Root schreibt den separaten Versuch vor neuen Daten fest.


## 21.10.2026, ab 18:25 Berlin – Codex: V4-Koordination wird umgesetzt

Moayed hat die selbstständige Umsetzung samt Subagents und Tests bis **22.10.2026 spätestens 06:00 Berlin** beauftragt. [Fester Implementierungs- und Versuchsplan](superpowers/plans/2026-10-21-v4-joint-prototype.md), Arbeitszweig `improvement/v4-joint-20261021` in eigener Arbeitskopie. Implementer baut einen standardmäßig deaktivierten, nur bei Auswertung aktiven Paar-Koordinator; unabhängiges Review folgt. Root prüft Daten, integriert und führt Tests aus; ein eigener Remote-Wächter meldet neue Commits, ohne Quellen zu verändern.

V3-Gewichte und alte Sicherung zu Beginn per Hash unverändert. Keine aktiven Modelljobs aus früheren Versuchen, keine Wiederaufnahme der abgebrochenen Curriculumstudie. 523000–523399 als neuer Bestätigungsbereich vorgeprüft (520 Seed-CSVs ohne Treffer), Nutzung nur nach erneutem Remote-Abgleich und bestandenem Entwicklungsgate. Zunächst neue Entwicklungs- und direkte V3-Spiele, keine bestätigte Verbesserung und noch kein neuer trainierter Kandidat. Deadline-Auftrag und Repo-Abgleich auf den neuen Zeitraum aktualisiert. Nächste Berichte unterscheiden tatsächliche Umsetzung, laufende Versuche und abgeschlossene Ergebnisse.

## 21.10.2026 – Codex: neue V4-Strategie nach ausbleibendem Zusatzgewinn

Auf Moayeds erneuten Planungswunsch: [V4-Strategie](V4_STRATEGIE_20261021.md). Zwei unabhängige, ausschließlich lesende Reviews prüfen Entscheidungsarchitektur und Lernwege. Priorität ist eine kleine gemeinsame Auswahl von V3-Aktionsvorschlägen für interagierende Schiffe; zunächst Bewegung/STAY, keine neue Trainingsserie. Erst ein positiver Entwicklungsvergleich rechtfertigt eine Bestätigung auf neuen Karten oder einen kleinen lernenden Bewerter. Ziel bleibt 100 % auf einem vorher festgelegten Testsatz, ohne Garantie für alle Karten. Bereits vorhandene, nicht qualifizierte V4-Dateien bleiben getrennt.

Begründung aus Code und vorhandenen Daten: eindeutige strategische Ziele werden bereits verteilt, die tatsächlichen Aktionen aber weitgehend pro Einheit gewählt. Das ist eine neue Hypothese, noch kein nachgewiesener Engpass. CNN/PPO übernehmen ebenfalls die sechs Aktionsklassen und lösen die gemeinsame Planung nicht automatisch. Vorhandene Verlusttraces enthalten nicht alle legalen Modellinputs; keine versteckten Zustandsdaten für Lernmerkmale benutzen.

Nur Strategie und Übergabe geändert; Quellenstellen, historische Zahlen und relative Links geprüft. Kein Agentencode, keine Gewichte, keine neuen Spiele oder Trainings in dieser Planung. Letzter aktiver Versuch bleibt der abgeschlossene Gegnerenergie-Vergleich unten. Die zwischenzeitlichen automatischen Git-Abgleiche waren keine kontinuierliche Entwicklungsarbeit; dieser Stillstand wurde Moayed ausdrücklich mitgeteilt. Nächster konkreter Liefergegenstand: begrenzter Koordinationsprototyp samt vollständigem Vergleich. Die bisherige V3 bleibt Abgabe.






## 21.10.2026, 14:53 Berlin – Codex: direkter Gegnerenergie-Vergleich abgeschlossen

[480 vollständige Vergleichsspiele und unabhängiger Audit](../experiments/analysis/enemy_tie_energy_20261021/README.md). V3 mit `enemy_tie_energy=True` gewinnt gegen Solution_92 **105/120 statt 102/120**; Differenz +2,5 Prozentpunkte, gepaartes 95%-Kartenintervall **[−2,5; +8,33]**. Default jeweils 120/120. Positiver Punktschätzer, aber kein vorab geforderter Vorteilsnachweis: Variante beendet, keine frischen oder direkten Folgespiele, kein Austausch der Abgabe.

Vorher 439 Tests und 14 Untertests sowie acht Kurs-Runner-Spiele bestanden; sämtliche 18 Netze und alle übrigen Checkpointfelder identisch mit V3, nur gespeicherter Schalter verändert. Die 240 V3-Referenzspiele reproduzieren alle Nichtzeitfelder. Root und unabhängiger Reviewer bestätigen vollständige Schlüssel, Rechnung, Quellen- und Gewichtsidentität.

Implementierung und nicht qualifizierter Kandidat bleiben auf `improvement/enemy-tie-20261021`, Ergebniscommit **694eda3**. main erhält ausschließlich Rohdaten/Prüfungen und diesen Bericht; die nicht belegte Funktionsänderung wird nicht in den Abgabe-Agenten übernommen. Nächste begrenzte Diagnose ist die bereits offene Konsistenzfrage von PPO-Aktionswahl und gespeicherten Kartenebenen, zunächst ohne Spiele oder Optimizer-Schritte. Keine neue breite Trainingsreihe.

## 21.10.2026, 14:39 Berlin – Codex: Ressourcen neu priorisiert, Curriculum unvollständig beendet

Moe kritisiert den langen Aufwand ohne zusätzlichen Stärkegewinn. Root hat die weitere Priorität nach einer unabhängigen, begrenzten Ressourcenprüfung geändert: Die laufende Curriculumstudie wird **unvollständig beendet**, der bereits vorbereitete direkte V3-Gegnermerkmale-Vergleich vorgezogen. Noch etwa zweieinhalb Stunden wären allein bis zur Grundauswertung angefallen. [Begründung, tatsächliche Spielzahlen und vollständiges Abbrucharchiv](../experiments/analysis/continuous_20261021/curriculum_progress/cancellation/README.md).

Der negative erste Start war bereits bekannt. Deshalb ausdrücklich keine vorgeplante statistische Ablehnung und keine Aussage, dass die vollständige Methode widerlegt sei. Ursprüngliche Gates/Seeds werden nicht umgeschrieben; keine historischen Kontrollen ersetzt, kein Teilcheckpoint ausgewählt. Zwei erneut trainierte Kontrollen reproduzierten sämtliche 3.000 historischen Trainingszeilen außerhalb der Laufzeit exakt ([Beleg](../experiments/analysis/continuous_20261021/curriculum_progress/historical_control_reproduction_s47_s48.json)). Das belegt Reproduzierbarkeit, ist aber kein neuer Stärkegewinn.

Kontrollierter SIGTERM nur an den nach PID/Kommando überprüften eigenen Supervisor; seine registrierte Trainingsgruppe ist beendet, State `active=null`, geschützte Gewichte unverändert. Der alte State bleibt als Original erhalten; `train_48_early` ist unvollständig und darf nicht durch manuelle Statusänderung fortgesetzt werden. Drei vollständige Trainingsarme plus 750 Spiele des vierten: insgesamt 9.750 Trainingsspiele, 544 Zwischenvalidierungen und 480 finale Testspiele. Keine s49-Läufe.

Nächster Schritt: getrennten Gegnerenergie-Zweig mit main abgleichen, einmal passende Modellintegration prüfen, Quellen/Gewichte einfrieren und 480 vorab festgelegte Entwicklungsspiele ausführen. Keine neue Trainingsreihe. Eigene Wachhaltung bleibt für diese aktive Folgearbeit bestehen.

## 21.10.2026, 13:39 Berlin – Codex: erstes Curriculum-Paar vollständig ausgewertet

[Archiv und Prüfungen](../experiments/analysis/continuous_20261021/curriculum_progress/s47/README.md):6.000 Trainings-,320 Zwischenvalidierungs- und480 finale Testspiele fertig. Früher Gegnerkontakt s47 gegen Solution_92 **62/120 statt86/120** der Kontrolle, Δ−20pp, gepaartes95%-Kartenintervall[−32,5;−7,5]. Default119/120 statt120/120. Die beiden Einzelnetze werden miteinander verglichen, nicht mit der18-Netz-Abgabe.

Unabhängiger Subagent prüfte Daten/Initialidentität/Gegnerplan/Hashbindungen ohne Modellimporte; Root reproduzierte Resultate und Kartenintervalle separat und kontrollierte alle Archivkopien. Laufquellen und Gewichte unverändert. Rohdateien, Prüfbericht und abgeschlossene Phasen archiviert; `.pth`-Laufkopien nur lokal gemäß bestehender Git-Regel, Buffer in der eingefrorenen Arbeitskopie.

Die feste Studie läuft mit s48Kontrolle weiter, anschließend s48früh und s49beide. Ein einzelner negativer Start beendet den vorher festgelegten Vergleich nicht. Keine geänderten Gates, keine nachträgliche Best-Seed-Auswahl und kein Abgabeersatz.

## 21.10.2026, 12:58 Berlin – Codex: Folgeversuch vorab operativ geprüft

Der [unabhängige Operationsreview](../experiments/analysis/continuous_20261021/representation_probe/protocol_review.md) prüft den vorbereiteten Gegnerenergie-Vergleich. Ein Ressourcenfehler wurde vor jedem neuen Spiel korrigiert: Zwei Stunden passen nicht zur festgelegten konservativen Zeitrechnung. Historische Maximaldauer6,43Sekunden ergibt mit Sicherheitsfaktor und Reserve20.833Sekunden für alle möglichen2.480Spiele. Die interne Obergrenze beträgt deshalb jetzt sechs Stunden; Seeds, Spielzahlen und statistische Gates bleiben unverändert. Root hat die drei historischen Laufzeitmaxima und Dateihashes separat bestätigt.

Weitere Ausführungshinweise sind dokumentiert: absoluter gemeinsamer Pythonpfad, tatsächlich gespeicherter Configschalter, vollständige CSV-Prüfung und separate Direktanalyse für522200–522399. Kein neuer Supervisor, keine zusätzlichen Modelle/Spiele gestartet. Laufende Curriculumquellen bleiben eingefroren; dieser Folgeversuch beginnt erst danach.

## 21.10.2026, 12:38 Berlin – Codex: erster Trainingsarm vollständig geprüft

Kontrolle s47 fertig: 3.000 Trainings- und160 Zwischenvalidierungsspiele, Trainingsprozess3186,54Sekunden, anschließender Tensorcheck3,21Sekunden, beide Returncodes0. Alle gespeicherten Q-/Target-Tensoren endlich; geschützte Gewichte unverändert. [Technischer Phasennachweis](../experiments/analysis/continuous_20261021/curriculum_progress/s47_control_training.json).

Der frühe Gegnerarm s47 läuft. Root hat seine tatsächliche Anfangsidentität mit der Kontrolle verglichen: vollständig gleich, einschließlich Netzen, Optimizer, leerem Replay und Zufallszuständen. Auch sämtliche Nichtzeitfelder der32 Startvalidierungen und der ersten100 Trainingsspiele sind exakt gleich; erst danach beginnt der geplante Gegnerunterschied. Die finalen240-Spiele-Auswertungen beider Arme und der vollständige Vergleich aller drei Starts stehen noch aus. Keine Stärke-/Übernahmeentscheidung aus diesem Zwischenstand.

## 21.10.2026 – Codex: Gegnerenergie-Tiebreak auf getrenntem Zweig geprüft

Commit `1b3f6a7` auf `improvement/enemy-tie-20261021`: acht Produktionszeilen ergänzen den ausgeschalteten Schalter und seine Auswahl. [Umsetzung](../experiments/analysis/continuous_20261021/representation_probe/implementation.md), [unabhängiger Review](../experiments/analysis/continuous_20261021/representation_probe/code_review.md) ohne wichtigen Befund. 34 leichte Tests bestanden; im selben Prozess keine Torch-/JAX-/Engineimporte. Root hat die505 Bewegungen und beiden Konvergenzereignisse separat aus Rohaktionen reproduziert ([Zählprüfung](../experiments/analysis/continuous_20261021/representation_probe/root_counts.json)).

Code noch nicht in main integriert: vollständige Modellintegration und tatsächliche Spiele warten auf das Ende der laufenden Curriculumstudie. Danach einmal passende Integrationstests, Quellenfreeze und der festgelegte Einzelvergleich. Kein Wirksamkeitsnachweis und keine Gewichtsänderung. Der Zweig erlaubt Mahmoud/Claude bereits die Vorbereitung nachzulesen; keine parallelen Modelljobs auf diesem Rechner starten.

## 21.10.2026 – Codex: ein separater Gegnermerkmal-Versuch vorbereitet

Der [Repräsentationscheck](../experiments/analysis/continuous_20261021/representation_probe/README.md) bestätigt eine konkrete Informationslücke: nur einer von mehreren gleich nahen sichtbaren Gegnern wird einzeln beschrieben. Zwei nominelle Konvergenzen in den fest ausgewählten84Übergängen zeigen den Kontext, keine Kausalität oder Verbesserung. Root lässt deshalb genau eine standardmäßig ausgeschaltete Auswahlvariante vorbereiten: bei gleicher Entfernung höhere Gegnerenergie bevorzugen.

[Vergleich und Gates vorab festgelegt](superpowers/plans/2026-10-21-enemy-tie-energy.md). Neue reservierte Karten522000–522399, keine Kollision im vorliegenden CSV-Bestand. Umsetzung in separater Arbeitskopie; während der laufenden Curriculumstudie nur leichte Tests/Review, keine zusätzlichen Modelljobs. Gewichte und Curriculum bleiben unverändert. Diese zusätzliche Vorbereitung ist keine bisher ausgeführte Evaluation oder Übernahme.

## 21.10.2026, 11:44 Berlin – Codex: neue Trainingsstudie läuft

Der freigegebene Vergleich `20261021_early_contact_v1` ist tatsächlich gestartet: 21.10.2026 11:44:34 Europe/Berlin, feste Studienfrist 23:44:34 desselben Tages. Eingefrorener Commit **`a5d2e61b0e8654bad64e31c29447ada1e439174d`** in `sherlock-counterplay`; Supervisor 63520, erster Trainer 63533. Zustand und Joblogs liegen dort unter `experiments/analysis/early_curriculum_20261021_early_contact_v1/`. Prozessnummern sind nur die lokale Momentaufnahme, vor jedem Eingriff erneut mit Kommando/Ownership prüfen.

Unabhängiger [Anlaufcheck](../experiments/analysis/continuous_20261021/planning/curriculum_start_audit.md): tatsächliche Initialidentität, CLI, Konfiguration, Gegnerplan, 32 Startvalidierungs- und erste 225 vollständige Trainingszeilen geprüft; keine technischen Auffälligkeiten. Das ist keine Stärkeprüfung.

Aktuell beginnt Kontrolle s47; erst danach früher Gegnerkontakt s47 und die vollständigen Paarprüfungen, anschließend Starts48/49. Geplant sind18.000 Trainingsspiele plus960 Zwischenvalidierungs- und1.440 finale Einzelnetzauswertungsspiele; weiterführende Ensemble-/Frisch-/Direktprüfungen sind bedingt. Aus einem laufenden Training lässt sich noch keine Verbesserung ableiten.

Den eingefrorenen Arbeitszweig, seine Pythonquellen, Pläne, Gewichte und die benutzte Venv nicht verändern. Hauptcheckout und Remote dürfen separat abgeglichen werden; fremde Änderungen werden während des Source-Freeze nicht in den Versuch übernommen. Alte Deadlines06/09 gelten nicht mehr, der Benutzer hat kontinuierliche Arbeit ohne feste Enduhrzeit beauftragt. Der konkrete Versuch behält trotzdem seine vorab festgelegte Ressourcenfrist. V3-Abgabe und Sicherungen bleiben unverändert.

## 21.10.2026 – Codex: Curriculumstudie vollständig geprüft und zum Start bereit

Alle vier Umsetzungsschritte inklusive unabhängiger Nach- und Integrationsprüfung fertig. Statistikauswertung `a5ce6d8`, bedingte Bestätigung `9c5c06d`, periodische Prüfung erzeugter Eingaben `2da04b3`. Vollsuite vor der engen letzten Korrektur: 406 Tests plus 14 Teilprüfungen; danach 88 betroffene Tests. [Nachweise und Grenzen](../experiments/analysis/continuous_20261021/planning/README_CURRICULUM.md).

Nächster tatsächlicher Schritt: sechs frische Läufe (Starts 47–49, je Kontrolle/früher Gegnerkontakt, je 3.000 Spiele), feste Zwischenvalidierungen und abschließende Vergleiche. Genau eine fachliche Änderung: 100 Solution-Spiele früher, Gesamtgegnerzahlen gleich. Keine Auswahl des besten Zwischenstands. Ein 21-Netze-Kandidat entsteht nur nach positivem Methodengate; neue Karten und direkte V3-Prüfung erst nach ihren vorgeschalteten Gates.

Studien-ID `20261021_early_contact_v1`, Quellenfreeze nach dieser Dokumentation in der separaten Arbeitskopie `sherlock-counterplay`. Der Runner setzt die feste 12-Stunden-Frist beim wirklichen Start. Hauptrepo kann getrennt aktuell gehalten werden. Noch kein stärkerer Agent aus dieser Studie nachgewiesen; V3 und alte Sicherung unverändert, Bestätigungskarten unbenutzt. Keine Agenten-/Reward-/Architekturänderung.

## 21.10.2026 – Codex: lokale Wiederbesetzung als begrenzte Diagnose

Der [Folgecheck](../experiments/analysis/continuous_20261021/loss_observation/locality_followup/README.md) betrachtet ausschließlich die vier größten späten Belegungslücken in vorhandenen Traces. Weit entfernte oder gegnerisch besetzte bekannte Punkte erklären, warum der globale freie-Felder-Zähler sofortige Chancen überschätzt. Konkrete Sequenzen zeigen negative Energie, Maskenverluste und längere erneute Anreise; die verursachenden Schadensquellen und mögliche bessere Aktionen sind damit nicht isoliert.

Keine neuen Spiele, kein Agentenpatch. Root prüfte feste Auswahl, Quellenhashes, Fenster und Partitionen; die Arbeitshypothese bleibt ausdrücklich begrenzt. Vorhandene Energiepuffer-/Zuweisungsvarianten nicht blind wiederholen. Das getrennt festgelegte Curriculumtraining und seine Gates bleiben unverändert.

## 21.10.2026 – Codex: Studienrunner geprüft, statistische Auswertung folgt

Der exklusive Studienrunner (`4332d6b`, korrigiert in `0ec929e`) ist unabhängig freigegeben: sechs neue Läufe, feste Reihenfolge, tatsächliche Anfangsidentitäten, vollständige Trainings-/Validierungs-/Auswertungsdateien und eine ursprüngliche Zwölfstundenfrist. Ein globaler Lock für unsere Studien verhindert konkurrierende Modelljobs über Arbeitskopien hinweg; fremde manuell gestartete Werkzeuge werden zusätzlich per Prozessprüfung erkannt, aber nicht durch diesen Lock gesteuert.

Der Review fand zunächst fehlende Spaltenprüfungen, eine Lücke bei der Prozesssperre und vererbte Signalsperren. Alle drei sind korrigiert und nachgeprüft; 62 gezielte Tests bestanden. [Erster Review](../experiments/analysis/continuous_20261021/planning/curriculum_runner_initial_review.md), [Freigabe der Korrektur](../experiments/analysis/continuous_20261021/planning/curriculum_runner_fixed_review.md).

Noch keine neuen Trainingsspiele: Als nächstes werden die festgelegten statistischen Gates und bedingten Ensembleprüfungen umgesetzt. Vorbereitung der technischen Abgabeprüfung ist dokumentiert; sie ist keine bereits durchgeführte Übernahmeprüfung. V3 und die bestehende alte Sicherung bleiben unverändert.

## 21.10.2026 – Codex: Trainingsvergleich, Eingaben unabhängig geprüft

Der frühe Gegnerplan und die isolierten Zwischenmessungen sind implementiert (`bc7d3b1`) und unabhängig freigegeben. 267 Tests plus 14 Teilprüfungen bestanden. Standardaufrufe behalten ihr bisheriges Verhalten. Neue Studienaufrufe zeichnen die vollständige Gegnerfolge, die tatsächliche Anfangsidentität der Learner und rohe Zwischenvalidierungsspiele auf; die Validierung erhält den relevanten Lern- und Zufallszustand.

Noch kein neues Langtraining gestartet: Der exklusive Studienrunner, seine vollständigen Ergebnisprüfungen und die festgelegten statistischen Gates werden als nächste getrennte Schritte umgesetzt und geprüft. Die abgeschlossene Verlustdiagnose liegt mit Rohdaten unter `experiments/analysis/continuous_20261021/loss_observation/`. Aktuelle V3-Abgabe und alte Sicherung bleiben unverändert. Remote vor Veröffentlichung abgeglichen; keine neuen fremden Commits gefunden.

## 21.10.2026 – Codex: Verlustdiagnose abgeschlossen, kein neuer Regelpatch

[Archiv und Ergebnis](../experiments/analysis/continuous_20261021/loss_observation/README.md) der 20 fest ausgewählten Partien vollständig: 6060 Übergänge, 60 Matchabschlüsse und 240 zeitlich ausgerichtete Schnappschüsse. Alle 460 nichtzeitlichen Referenzwerte identisch; Root prüfte 41 ursprüngliche Dateihashes sowie Matchsiege und die zentralen Belegungswerte unabhängig nach. Die ergebnisgeschichtete Stichprobe ist keine neue Siegquotenmessung.

Matchsiege 16/20, 6/20, 3/20; alle 13 verlorenen Spiele verlieren Match 2 und 3. Dort sind spät viele Punktefelder bekannt, aber weniger produktiv besetzt als beim Gegner. Das unterscheidet Anreise, Zuweisung, Energie und Gegnerdruck noch nicht kausal. Kein erneuter pauschaler Reserve-/Zuweisungspatch. Die falsche Sap-Kollisionsannahme ist auch im engen echten Engine-Test widerlegt: gleiche Kollisionsmasken bei STAY/SAP, unterschiedliche Restenergie. Fünf enge beobachtete Eintrittskontexte behalten unmittelbar das produktive Feld. Kostenindikatoren bleiben deskriptiv.

Nächster Schritt ist deshalb der getrennt vorab festgelegte Curriculumvergleich, bei unveränderter Agentenlogik. Seine erste Werkzeugänderung ist implementiert und wird unabhängig geprüft; vollständiger Studienrunner und Gates folgen, noch kein neues Langtraining gestartet. V3 und Sicherung unverändert.

## 21.10.2026 – Codex: Diagnosewerkzeug geprüft, erste Ursache widerlegt

Observer `4503dba` und Korrektur `525060f` sind in main veröffentlicht. Tests: 231 plus 14 Teilprüfungen bestanden; nach unabhängig gefundenem Koordinatenfehler der Aufzeichnung neun fokussierte Tests bestanden, Review freigegeben. Anschließend genau 20 vorab ausgewählte Partien unveränderter V3 aufgenommen: 6060 Übergänge, alle 460 nichtzeitlichen Referenzwerte und 41 Ergebnisdatei-Hashes geprüft. Das ist Reproduktion, keine Verbesserung; fachliche Auswertung und Rohdatenarchiv folgen.

**Wichtige Korrektur zum ursprünglichen Solution-Review:** Der behauptete unmittelbare Kollisionsnachteil durch Sapkosten war falsch. Die installierte Engine speichert die Energie nach Bewegung, aber vor Sap (`env.py:293`) und nutzt diese gespeicherte Energie zur Kollisionsaggregation (`:462`). Ein Sap ändert daher nicht den Gewinner derselben Kollision. [Ursprünglicher Review mit vorangestellter Rücknahme](../experiments/analysis/continuous_20261021/planning/sherlock-solution-counterplay-20261021.md). Kein Agentenpatch daraus. Eine weitere kurze Engineprüfung wird separat dokumentiert; der Fehler betraf eine Hypothese, nicht Sherlocks ausgeführte Aktionen oder Gewichte.

Lokaler Git-Abruf war durch eine ungültig benannte Zusatzreferenz `refs/remotes/origin/main 2` blockiert. Ihr Inhalt zeigte auf den vorhandenen Commit b008252. Die Datei wurde unverändert außerhalb des Referenzbaums unter `.git/codex-ref-backups/20261021-main-2.txt` gesichert; anschließend Abruf, Fast-forward und Push erfolgreich. Ursache der Zusatzdatei nicht behauptet; keine Projektdateien oder fremden ungesicherten Änderungen entfernt.

## 21.10.2026 – Codex: neuer autonomer Verbesserungsauftrag

Moayed hat nach dem Abschluss um 09:00 erneut kontinuierliche Arbeit ohne feste Enduhrzeit freigegeben: gezielte Niederlagenanalyse, Gegenstrategien, Training, unabhängige Bestätigung und geprüfte Pushes. [Aktueller Plan](superpowers/plans/2026-10-21-continuous-improvement.md). Die vorigen Abschlussnotizen bleiben historische Belege. V3 bleibt zunächst Abgabe; bisherige Sicherung bleibt erhalten.

Remote-Vorprüfung: b008252 lokal/remote identisch, keine laufenden Modelljobs. Drei unabhängige Agenten prüfen Verlustdaten, Solution-Code und Remote/Seedkollisionen. Neuer finaler Auditblock 520000–520999 reserviert; 511000–511399 bleibt Curriculumreservierung. Der Drei-Stunden-Abgleich ist reaktiviert, andere alte Abschlussautomationen bleiben pausiert. Arbeitskopie für neue Quellen: ../sherlock-counterplay, Branch improvement/counterplay-20261021. Noch keine neue Trainings- oder Stärkeaussage.

## 21.10.2026, 09:00 – Codex: Auftrag bis 09:00 abgeschlossen

Morgenbericht `07dbe71` und konkretisierter Curriculumplan `34fc59f` sind gepusht. Beim letzten Abruf vor dem Abschlusscommit stimmen lokales `main` und `origin/main` überein; keine neuen fremden Commits. Die abschließende Dokumentation einschließlich dieser Zeile wird in einem eigenen Abschlusscommit veröffentlicht; dessen Identität ist in der Git-Historie nachvollziehbar.

[Abschlussprüfung](../experiments/analysis/autonomous_20261020/closing_checks_20261021.json): V3-Dateien und alte Sicherung weiter mit den erwarteten Hashes; keine Python-/Gewichtsänderungen seit `6ab3109`. Eigene Trainings und Auswertungen sind beendet, alle delegierten Prüfaufträge abgeschlossen. Der eigene bis 09:00 befristete Wachhalteprozess ist beendet. Alle drei Nacht-Automationen sind deaktiviert (Status PAUSED); kein automatischer weiterer Studienstart. Fremde ungesicherte Dateien und lokale Trainingsgewichte/Buffer bleiben erhalten.

Ergebnis und Grenzen: [Morgenbericht](MORGENBERICHT_20261021.md). V3 bleibt Abgabe; zusätzliche Trainingsversuche und V4-Bestätigung ergaben keinen weiteren qualifizierten Ersatz. Der [nächste Plan](superpowers/plans/2026-10-21-early-opponent-curriculum.md) ist geprüft, aber nicht implementiert oder gestartet. Die Fortsetzung benötigt ein neues ausreichendes Arbeitszeitfenster; dieser Abschluss startet keine Hintergrundjobs.

## 21.10.2026, 08:49 – Codex: nächste einzelne Studie verbindlich geplant, nicht gestartet

Der Morgenbericht wurde als `07dbe71` erfolgreich nach `origin/main` gepusht. Danach den [Curriculumplan](superpowers/plans/2026-10-21-early-opponent-curriculum.md) konkretisiert und unabhängig prüfen lassen: drei neue Paare mit bekannten Starts 47–49, gleiche Gegnergesamtzahlen, feste Zwischenmessungen und getrennte Methoden-/Ensemblegates. Neu reserviert 511000–511199 (bedingte Gegnerbestätigung), 511200–511399 (bedingter Direktvergleich); 507 versionierte CSVs mit 358.716 Zeilen ohne Kollision, jüngster Remote-Abgleich ohne neue fremde Commits. Vor einem späteren Start nochmals prüfen.

Planreview korrigiert: Audits eindeutig an Studien-ID/State binden, tatsächliche Initialidentität vor Validierung erfassen, Zwischenvalidierung samt RNG isolieren und Rohschlüssel sichern, exklusive Ausgaben und atomare Phasengrenzen testen. Die heutigen Werkzeuge unterstützen die neuen Optionen noch nicht. Keine Implementierung, kein weiterer Modelllauf und keine Verlängerung des Auftrags über 09:00. [Prüfbelege](../experiments/analysis/autonomous_20261020/early_curriculum_planning/README.md).

## 21.10.2026, 08:43 – Codex: Morgenbericht und gemeinsame Orientierung geprüft

[Morgenbericht](MORGENBERICHT_20261021.md) mit Ergebnisgrafik, Spielzahlen, Grenzen, Abgabe/Sicherung und tatsächlich gepushten Arbeitsschritten erstellt. V3 bleibt installiert; zusätzliche 18.800 Trainingsspiele und der unabhängige 2.400-Spiele-V4-Vergleich liefern keinen weiteren qualifizierten Ersatz. Bericht, Grafikwerte, Quelllaufbudget und nächste Schritte unabhängig geprüft. Zwei sprachliche Übertreibungen, ein relativer Link und veraltete nächste Schritte korrigiert. Historische Erstpräsi-Läufe (`full`/`full_sym`) ausdrücklich von den heutigen 66.000 V3-Quelllaufspielen getrennt; teilweise gleiche Karten bedeuten keine identischen Trainingsläufe.

README, CLAUDE, Experiment-Einstieg und Hauptplan auf den Stand vom 21.10. gebracht. Künftiger Curriculumversuch bislang nur Entwurf; genaue Umsetzung und Studie werden separat geplant. Keine neuen Modellversuche während des Abschlusses. Das Nutzungslimit unterbrach die aktive Koordination nachts; bereits gestartete Programme liefen unabhängig fertig. Der Bericht behauptet keine durchgängige LLM-Arbeit.

Prüfung: Quellen und Gewichte seit dem vollständig getesteten Stand `6ab3109` unverändert; damalige Suite 223 Tests plus 14 Subtests bestanden. Für diesen reinen Dokumentationsschritt Dateilinks, Format, Grafik und Archivhashes geprüft, keine zusätzlichen Modelltests nötig. Aktuelle V3-Dateien und alte Sechser-Sicherung stimmen mit ihren dokumentierten SHA-256 überein. Remote-Beobachter und Root bestätigten vor diesem Berichtscommit lokales `main` = `origin/main` auf `5dda0a3`, ohne neue Mahmoud-Commits. Eigene Trainings-/Evaluationsprozesse sind beendet; Wachhaltung bis 09:00 und Abschlussautomationen werden beim tatsächlichen Abschluss separat geprüft. Fremde ungesicherte Dateien bleiben unangetastet.

## 21.10.2026, 08:27 – Codex: Aktionsfluss von V3 passiv geprüft

[20 Beobachtungsspiele](../experiments/analysis/autonomous_20261020/v3_action_source_observation/README.md), bekannte Karten 500720–500729, beide Seiten gegen Solution_92. Alle 23 nichtzeitlichen Spielkennzahlen exakt gegen zwei vorhandene Referenzen reproduziert. Keine Agenten-, Gewichts- oder Aktionsänderung; lediglich Methoden-Ein-/Ausgänge beobachtet. 13 Tests vor Start; danach Root und unabhängiger Review: Quellen-/Input-/Gewichtshashes identisch, komplette Aktionsketten und Nenner nachgerechnet.

70.200 aktive Unitentscheidungen, davon 8.320 mit nur einer legalen Aktionsklasse und 61.880 mit mindestens zwei. Bei Wahlmöglichkeit blieb die maskierte Greedyklasse **56.352/61.880 = 91,07 %** bis zur Ausgabe erhalten. 3.702 Änderungen durch Erkundung, 1.826 durch späte Nachbearbeitung; keine Änderung durch die allgemeine Regel und keine Rückänderung in dieser Stichprobe. Negative Energieslots und Matchstart-No-ops separat gezählt. Das zeigt Entscheidungsfluss, **keinen kausalen Netzbeitrag oder Stärkenachweis**; Features/Masken/Sap-Zielwahl sind bereits regelgestützt. Individuelle Masken/Energien wurden zur Laufzeit geprüft, nicht nachträglich aus Aggregaten rekonstruiert. Lauf vollständig um 08:21:17 beendet; V3 und alte Sicherung bleiben unverändert.

## 21.10.2026, 08:09 – Codex: nächste Trainingsfrage vorbereitet, keine Agentenänderung

[Übergabe für Mahmoud](NAECHSTER_TRAININGSVERSUCH_20261021.md): langsame Exploration blieb auf allen drei Starts schwächer; geringere Trainingsresultate auch nach gemeinsam erreichtem Epsilonminimum, keine allgemeine Aussage gegen Exploration. Deskriptive Phasenmittel über 18.000 Logzeilen unabhängig mit Stdlib reproduziert; fehlende anfängliche Losswerte gezählt und ausgeschlossen. Gleiche Gegnergesamtzahlen in beiden Armen. Q-Margen und Beobachtungen liefern Hypothesen, keine isolierte kausale Erklärung.

Priorisierter späterer Versuch: 100 frühere Solution_92-Spiele gegen 100 spätere tauschen, sonst ursprünglicher schneller Epsilon-Abfall und gleiche 1.426/1.574 Gegnerzahlen. Gegnerfolge rechnerisch geprüft, **noch nicht implementiert oder trainiert**. Vor Start feste Zwischenmessungen, Seedreservierungen, Tests und vollständigen Studienplan ergänzen. Rund 5,2 Stunden reine Trainingszeit plus Auswertung einplanen. Keine weiteren gleichartigen Netze, langsamen Decays oder Kombinationen von Inferenzschaltern ohne neue belastbare Hypothese. CNN3-Fortsetzung benötigt zunächst die lokal fehlenden Originalcheckpoints. Installierte V3, Sicherung und Pythonquellen unverändert. Ergänzend alle 18 V3-Quelllaufmanifeste und 66.000 lückenlose Trainingslogzeilen geprüft: sechs × 3.000 plus zwölf × 4.000 Spiele; verschiedene Reward-/Gegnerkonfigurationen. Das ist ein dokumentiertes Quelllaufbudget, nicht die gesamte Projektentwicklung; individuelle Quellgewichte fehlen lokal, daher kein neuer Tensor-Herkunftsnachweis.

## 21.10.2026, 08:06 – Codex: unabhängige V4-Bestätigung beendet, V3 bleibt Abgabe

Alle vorab festgelegten **2.400 Spiele** abgeschlossen (07:35–08:04 Berlin), Quellenstand `6ab3109`. Neue Karten 510400–510799 direkt V4 gegen V3: **408/800 = 51,0 %**, Karten-KI **[48,125; 54,0] %**. Neue Karten 510800–510999, beide Seiten: Solution_92 V3 **311/400**, V4 **313/400**, Δ **+0,5 pp**, gepaartes Karten-KI **[−3,0; +4,0]**; default beide **400/400**. Keine Remis. Beide geforderten Vorteilsnachweise fehlen: **keine Übernahme und keine Erweiterung der Stichprobe**. Alte V4-Ergebnisse nicht gepoolt. Das beweist keine Gleichwertigkeit, rechtfertigt unter den vorherigen Regeln aber keinen Austausch.

[Ergebnisse, Rohdaten, Audits und historische Werkzeuge](../experiments/compare/autonomous_20261020/v4_independent_20261021/README.md). Root und unabhängiger Subagent bestätigen alle Spielschlüssel, vollständige Kurslänge, Punktezählversion 2, Resultatkonsistenz, unveränderte Quellen/Inputs/HEAD und unabhängig nachgerechnete 5.000 Kartenbootstrapziehungen (Seed 0). Die vorherige vollständige Suite bestand: 223 Tests plus 14 Subtests. Keine Pythonquellen seitdem geändert. Aktuelle Abgabe bleibt `all18_v3`, beide SHA-256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`; alte Sechser-Sicherung unverändert. Die zusätzliche technische Übernahmeprüfung wurde mangels qualifizierten Kandidaten nicht gestartet. Nun Archivierung, Übergabe und Abschluss bis 09:00; keine neuen langen Trainings.

## 21.10.2026, 07:31 – Codex: Diagnose abgeschlossen, Arbeit bis 09:00 verlängert

Moayed hat die autonome Arbeit bis 09:00 verlängert. Nach der Nutzungslimit-Unterbrechung liefen die bereits gestarteten Programme selbstständig fertig; aktive LLM-Reviews und Pushes wurden erst nach Wiederaufnahme abgeschlossen. Die 40 Beobachtungsspiele reproduzieren sämtliche nichtzeitlichen Referenzwerte. [Punktfeld-Review](../experiments/analysis/autonomous_20261020/post_exploration_point_flow/point-flow-final-review.md): unerreichbare nahe Ziele betreffen 6,20%/7,62% freier bekannter eigener Feld-Schritte bei V3/V4; unter dem vorher gesetzten 10%-Arbeitsfilter. Null enge Stillstandssegmente. Kein Zuweisungspatch. Blockierte Fernziele nicht nachträglich zum Bestehen des Gates hinzurechnen. Bereits besetzte Asteroidenfelder können weiter punkten; ein späterer Filter müsste aktuelle direkte Sicht und Belegung beachten.

Als einmaligen nächsten Schritt V4 gegenüber V3 auf neuen Karten prüfen: [vorab veröffentlichter Plan](superpowers/plans/2026-10-21-v4-independent-confirmation.md). Reserviert 510400–510799 für 800 direkte Spiele und 510800–510999 für 1600 gepaarte Gegner-Spiele. Alte Daten werden nicht gepoolt, keine ergebnisabhängige Stichprobenverlängerung. Übernahme nur bei allen festgelegten Gates und technischen Prüfungen. Bisherige Abgabe und Sicherung unverändert. Dies ist eine Planung, noch kein Testergebnis.

## 21.10.2026, 07:27 – Codex: Exploration vollständig, kein Kandidat zur Übernahme

Die vorab festgelegten Starts47–49 wurden jeweils mit Kontrolle (Epsilon-Abfall60000 Schritte) und langsamem Abfall454500 vollständig trainiert: **18000 Trainingsspiele,1440 Einzelnetz-Auswertungen,1200 Ensemble-Auswertungen**. Gleiches Curriculum und gleiche Anfangstensoren je Paar; kein Start und kein Trainingshorizont nach Ergebnissen ausgewählt. [Aggregation](../experiments/analysis/autonomous_20261020/exploration_aggregate.md): langsamer Abfall gegen Solution_92 im Mittel48,06% statt61,11%, **Δ−13,06pp**, Karten-KI[−19,17;−6,94]; default93,89% statt97,78%, Δ−3,89pp. **0/3 Starts positiv**, Methodengate verfehlt.

Feste Ensembles ohne Auswahl einzelner Netze: auf500720–500779 gegen Solution_92 V3-Referenz85%, control3 75%, slow3 66,67%, V3+control3 85%, V3+slow3 81,67%; default Referenz/beide21-Netz-Ensembles100%, beide3er98,33%. V3+control3 Δ0pp (KI[−7,5;+7,5]), V3+slow3 Δ−3,33pp (KI[−10;+3,33]): **kein Entwicklungskandidat**, deshalb keine frische/direkte Bestätigung und keine Übernahme. Der frische Block510200–510399 blieb unbenutzt. Q-Margen-Diagnose und Bauprovenienz gespeichert, keine nachträgliche Umgewichtung.

Alle Paaraudits und Prozessphasen erfolgreich. Vor Archivierung unabhängig alle CSV-Zeilen/Schlüssel/Initialidentitäten, Hashes und5000/Seed0-Kartenintervalle nachgerechnet; sechs train.csv plus sechs val.csv byteerhalten, ebenso alle elf Evaluations-CSVs. Keine Modelle beim Archivcheck geladen; endliche Q-/Target-Tensoren sind bereits separat auditierte Befunde. Karten-KI gilt bedingt auf diese drei Starts, nicht als allgemeine Trainingsunsicherheit. [Historische Werkzeuge und Prüfbeleg](../experiments/analysis/autonomous_20261020/historical_exploration_tools_20261021/README.md) als bytegleiche Textsnapshots archiviert; absolute Pfade, alte Fristen und Hashes sind keine allgemeine Wiederstartanleitung. Gewichte/Buffer bleiben ignoriert, installierte V3 und Sicherung unverändert. Separate Punktfeld-Diagnose wird noch ausgewertet und ist nicht Teil dieses Abschlusses.

## 20.10.2026, 23:09 – Codex: Explorationspaar 47 vollständig geprüft, Restfolge unverändert

Beide frischen Einzelnetze mit Seed 47 jeweils 3.000 Spiele trainiert, danach je 240 vollständige Auswertungsspiele auf bekannten Karten 500720–500779. Einziger Konfigurationsunterschied: Epsilon-Abfall 60000 gegen 454500 Schritte. Default Kontrolle 120/120, langsamer Abfall 112/120 (Δ −6,67 pp, Karten-KI [−13,33; −1,67]); Solution_92 86/120 gegen 57/120 (Δ −24,17 pp, KI [−35,00; −13,33]). [Technischer Audit und Grenzen](../experiments/analysis/autonomous_20261020/exploration_pair_audit_s47.md).

**Tatsächlich geprüft:** vollständige 6.000 Trainings- und 480 Evaluationszeilen, identische Anfangstensoren/RNG und Gegnerfolge, exakter Configdiff, endliche gelernte Q-/Target-Tensoren, Quellen-/Plan-/Gewichtsidentität; unabhängig nachgerechnete CSV-Schlüssel und Kartenintervalle. Ein negativer Start ist kein Methodenurteil über die drei vorab festgelegten Starts. Keine Änderung der Trainingslänge, keine Best-Seed-Auswahl und kein Austausch der Abgabe. Rohdaten, Manifeste, Identitäten und Audit versioniert; lokale Modelle und Replay Buffer bleiben ignoriert. CSV-Rohbytes werden je Run über `.gitattributes` erhalten.

Mahmouds sieben ausschließlich Daten/Dokumentation enthaltende Commits bis `146c1f8` per Fast-forward übernommen; keine Python-, Plan- oder Gewichtsänderung. Anschließend ist die unveränderte, zeitgeprüfte Folge für 48/49, Audits, Aggregation und feste Ensemble-/Bestätigungsgates vorgesehen. Der nächste Lauf ist zum Zeitpunkt dieses Eintrags noch nicht gestartet. Währenddessen bleiben HEAD, Pythonquellen, Präregistrierungsplan und Abgabegewichte eingefroren; vorbereitete Helfer bleiben außerhalb des Repositorys.

## 20.10.2026, 22:25 – Claude Code mit Mahmoud: CNN `cnn3` (Nachahmung + PPO) und Plan für 21.10.

**`cnn3`** (`scripts/pipeline_cnn3.sh`, Log `experiments/pipeline_cnn3.log`): 1200 Lehrerspiele von `all18_fo10` (4,27 Mio. Unit-Schritte, Lehrer 74 % vs Solution_92 in der Datensammlung), BC 6 Epochen (48 Kanäle × 4 Blöcke, Trefferquote 88,4 %), PPO 60 Iterationen. Val 720 vs Solution_92 (gespeicherte Lehrer-Config, ohne `pt_sap`): BC 74,0 %, PPO 10/20/30/40/50/60 = 78,0 / 74,5 / 77,0 / 74,5 / **83,5** / 78,5 %; default immer 100 %. **Frische Karten 502 020–502 219** (vorab reserviert, bester Val-Stand `ppo_0050` gegen den Lehrer): `cnn3/ppo_0050` 99,5 % / 73,0 %, `all18_fo10` 99,5 % / 73,25 % (−0,25, KI [−5,0; +4,5]) → **das CNN erreicht das Lehrer-Niveau, nicht mehr**; der Val-Spitzenwert war Auswahlglück. `cnn3/ppo_0050` + `far_cand`/`pt_sap`/`opp_infer`: Val 81,0 % (−2,5). Auf demselben frischen Block **`all18_v4` 99,25 % / 76,25 %** (+3,0 vs `all18_fo10`, KI [−2,2; +8,3]; +3,25 vs CNN). PPO-Checkpoints liegen gitignored unter `experiments/ppo/cnn3/`.

**Vorher/nachher auf denselben Karten 501 620–501 819** (200 Karten, beide Seiten; Block war schon Bestätigungsblock für `far_opp`, daher nur Illustration): Solution_92 `all18` 296/400 (74,0 %) → `all18_fo10` 320/400 (80,0 %) → **`all18_v4` 324/400 (81,0 %)**, V4 gegen `all18` +7,0 (KI [+1,8; +12,2]); default jeweils 400/400 (`G_v4_1620.csv`).

**Stand heute Abend:** beste bestätigte Variante `all18_v4` (Solution_92 auf frischen Blöcken 80,4 % / 400 Karten und 76,25 % / 200 Karten; default 98,5–99,25 %; gegen alte Abgabe 106/120). Abgabe ist laut Codex `all18_v3`. Mehr oder neu trainierte DQN-Netze (`fo6`, `all24fo`, `v3nets6`, `all24v3`) und PPO-Weitertraining brachten heute nichts.

**Diagnose Relics auf der Diagonale** (`all18_v4` vs Solution_92, die 33 Karten mit ungerader Relic-Zahl aus 502 820–503 219, beide Seiten, Ground Truth): Zone um das Diagonal-Relic ≈ 10 Punkte-Tiles (4,5 je Hälfte + 1,1 auf der Diagonale). Besetzt bei Step 30/50/75/95: wir 1,0 / 1,9 / 3,7 / 3,2, Solution_92 1,3 / 2,2 / 1,8 / 2,4. Eigener Teil (4,5 Tiles): wir 1,0 / 1,4 / 2,2 / 2,0, Gegner dort 0,0 / 0,4 / 0,5 / 0,6 → rund 2 eigene Tiles der Mittelzone bleiben frei; früh ist Solution_92 schneller. Freie eigene Tiles der Zone je Schnappschuss (Step 40–90): 2,7, davon 1,5 bekannt, 1,05 noch Kandidat, 0,5 mit Gegner, 0,3 Asteroid; 2,35 sind einer Unit zugewiesen, die meist noch weit weg ist (≥ 4 Felder: 1,7) und läuft (75–85 % Bewegung) → kein Fehler, sondern Wegzeit; kein schneller Hebel erkennbar.

**Letzter Test 20.10.:** `pt_walk` + `pt_walk_own` (BFS-Weg zu eigenen Punkte-Tiles) auf `all18_v4`, Val 720 gegen 84,5 %: ab Match 1 −1,5, ab Match 2 −3,0 → bleibt aus. Arbeit für heute beendet (Mahmoud: „heute nur noch kurze Sachen, Rest morgen“); keine Prozesse laufen.

**Plan 21.10. (Mahmoud/Claude):**
1. Schwachstelle Relics auf der Diagonale / umkämpfte Mittelzone (V4 dort 67 %) gezielt diagnostizieren.
2. Große Karten im 3. Match: Besetzung der eigenen Hälfte (Solution_92 ~8 von 10, wir ~5–6).
3. Modellauswahl für PPO auf einem eigenen, größeren Validierungsblock statt Val 720 (100 Karten sind für die Auswahl zu verrauscht; Val 720 ist stark wiederverwendet).
4. Mit Moayed abstimmen, ob `all18_v4` die Abgabe ersetzen soll (Solution_92 +2,4 auf 400 Karten, alte Abgabe 106 vs 96/120, direkt gegen V3 unentschieden).

**Seeds:** Val 502 020–502 219 (cnn3), 502 620–502 819 (v3nets), 502 820–503 219 (V4) verbraucht; Moayed 502 420–502 619. Nächster freier Index für Mahmoud: 3220.

## 20.10.2026, 21:50 – Claude Code mit Mahmoud: Netze mit V3-Regeln im Training – kein Gewinn

`scripts/pipeline_v3nets.sh`: 6 × `full_rules_v3` (`pt_sap`, `far_cand`, `far_opp=10`, `keep_dead_fast` schon im Training; je 3000 Spiele, 70 % Solution_92, 128 min; Läufe `20261020_full_rules_v3_s40`–`s45_sol70`). Val 720 gegen `all18_v3` (83,0 %): `v3nets6` (nur die 6 neuen Netze) 75,5 % (−7,5, KI [−14,0; −1,0]), `all24v3` (18 + 6, V3-Schalter) 81,5 % (−1,5). **Frische Karten 502 620–502 819** (200 Karten, je 400 Spiele): `all18_v3` default 99,75 %, Solution_92 71,0 %; `v3nets6` 100 % / 70,0 % (−1,0, KI [−5,2; +3,5]); `all24v3` 100 % / **71,0 % (±0, KI [−4,3; +4,8])** → mehr bzw. neu trainierte DQN-Netze bringen nichts; die Gewinne heute kamen ausschließlich aus Regeln. Log: `experiments/pipeline_v3nets.log`.

**V4 gegen alte Abgabe** (für Moayeds Übernahmeregel, gleiche 60 Entwicklungskarten 500 720–500 779, beide Seiten, Gegner `self:experiments/releases/20261020_old3_sym3/agent_p0.pth`): **`all18_v4` 106/120 (88,3 %)**; Codex hatte für `all18_v3` dort 96/120 (80,0 %) gemessen (`U_v4_vs_old_720.csv`). **Relics auf der Diagonale:** ungerade `relics_found` (66 von 800 Spielen auf 502 820–503 219) heißt, ein Relic liegt auf der Spiegelachse (eigenes Spiegelbild); diese Karten gewinnt V4 nur zu 67 % (sonst 82 %) – umkämpfte Mittelzone, kein Belief-Fehler.

## 20.10.2026, 21:14 – Codex: kontrollierter Explorationsvergleich vorbereitet

Nach negativem Reward-Pilot eine getrennte, begründete Trainingsfrage: Der bisherige Epsilon-Abfall endet schon im 199. Spiel, während das 3.000er-Curriculum Solution_92 erst nach 750 Default-Spielen einführt. Neue Variante `full_rules_v3_slowexplore` ändert ausschließlich `eps_decay_steps` von 60000 auf 454500 (= 1500 Spiele). Alle experimentellen Reward-/Inferenzschalter bleiben aus. Dies verändert auch den Anteil geführter Aktionen und Regeln im Greedy-Zweig; kein isolierter Test uniformen Zufalls. [Diagnose](../experiments/analysis/autonomous_20261020/TRAINING_DIAGNOSIS.md), [vorab festgelegter Plan](superpowers/plans/2026-10-20-exploration-replication.md).

Geplant: drei frische gepaarte Starts 47–49, jeweils 3000 Spiele pro Arm; Karten 470000–471499, 480000–481499, 490000–491499. Alle sechs finalen Netze vergleichen, keine Zwischencheckpoint-/Best-Seed-Auswahl. Neue Bestätigung 510200–510399 reserviert; 510000–510199 bleiben unbenutzt. Methodenurteil und konkrete Ensembleauswahl getrennt; feste Vergleichsregeln im Plan.

**Tatsächlich geprüft:** zunächst erwartete Fehler wegen fehlender Variante, danach **16 Tests plus zehn Untertests bestanden**, acht Runner-Selbsttests und unabhängige Quellenreviews. Vier vollständige Rauchtestspiele mit echter Optimiereraktivität, endlichen Q-/Target-Tensoren und null gezählten ungültigen Aktionen. Keine Aussage zur Spielstärke aus diesem Rauchtest. Abgabe und Sicherung bytegleich. Maximal ein Trainer bzw. zwei Evaluationsworker; Quellen pro Paar eingefroren. Laufzeit wird vor jedem Paar zugelassen, spätestens 06:00 Ende; kein späterer Wechsel der Trainingslänge nach Resultaten.

## 20.10.2026, 21:11 – Codex: zweite Inferenzrunde ohne belastbaren Gewinner

720 vollständige Spiele auf bekannten Karten 500720–500779: V3, ausschließlich `active_targets`, ausschließlich `sap_geometry`, je 60 Karten × beide Seiten × zwei Gegner. Referenz reproduziert alle 240 nichtzeitlichen Kennzahlen des früheren V3-Laufs exakt. Alle Daten-/Quellen-/Gewichtsprüfungen bestanden. Default jeweils 120/120; Solution_92 V3 102/120, active 104/120, sap 103/120. Gepaarte Kartenintervalle: active +1,67 pp [−2,50; +5,83], sap +0,83 pp [−2,50; +5,00]. **Keine Variante erfüllt die vorab gesetzte Auswahlregel**, keine frische Bestätigung oder Übernahme gestartet. Schalter bleiben aus, Abgabe/Sicherung unverändert. [Bericht](../experiments/analysis/autonomous_20261020/inference_development2_analysis.md), Rohdaten und Auswertung archiviert. 510000–510199 wurden nicht benutzt.

## 20.10.2026, 20:58 – Codex: Mahmouds aktuelle Änderungen integriert

Remote bis `7ae858f` zusammengeführt: `sap_kill_first=False`, `energy_pref=0.0`, zugehörige Tests und die negativen Ergebnisse bleiben erhalten. Gemeinsamen Protokollkonflikt durch Erhalt beider Einträge gelöst. **217 Tests plus vier Untertests bestanden (43,74 s)**; Abgabe und Sicherung unverändert. Das ähnlich gute Gesamtergebnis beider Spielseiten in Mahmouds Notiz ist ein Plausibilitätscheck, allein kein Beweis, dass jeder Spiegelungsfehler ausgeschlossen ist. Vor der nächsten Variantenbewertung wird V3 auf allen 240 Entwicklungsspielen neu reproduziert.

## 20.10.2026, 20:56 – Codex: tatsächlicher Reward-Pilot verworfen

Zwei frische Einzelnetze mit identischen Anfangstensoren und identischer Karten-/Gegnerfolge jeweils **400 Spiele trainiert**, danach jeweils 240 feste Auswertungsspiele. Einziger Unterschied: `terminal_death_potential`. Vollständiger Audit bestanden: Quellen/HEAD unverändert, gleiche Initialisierung, vollständige Spielschlüssel, endliche gelernte Tensoren und geschützte Abgabe/Sicherung. Details: [Pilotbericht](../experiments/analysis/autonomous_20261020/reward_pilot_analysis.md).

Kontrolle gegen default 120/120, Korrektur 106/120; gegen Solution_92 43/120 statt 15/120. Differenz Korrektur minus Kontrolle **−23,33 Prozentpunkte**, gepaartes Kartenintervall [−34,17; −13,33]. Beide vorab festgelegten Schadensgrenzen verletzt: **keine große Reward-Replikation starten**, Schalter bleibt aus, Abgabe V3 bleibt unverändert. Ein Trainingsstart und bekannte Entwicklungskarten erlauben keine allgemeine Aussage über jede Trainingslänge; der konkrete Pilot reicht aber zum Stoppen dieses Versuchs. Kein Nutzen allein aus der mathematischen Motivation ableiten.

Der vor Auswertung geschriebene bedingte Replikationsplan bleibt als Historie erhalten (SHA im Audit). Rohdaten/Manifeste und Initial-/Finalidentitäten versioniert; lokale experimentelle Checkpoints und Replay Buffer bleiben in ihren getrennten Run-Verzeichnissen. Das tatsächlich ausgeführte Audit-Skript ist unverändert als `tools/source_snapshots/reward_pilot_analysis_original.py` archiviert: historischer Rechnerpfad und exakte damalige HEAD-Prüfung, kein universeller Wiederausführungsbefehl auf aktuellem main. Nächster Schritt: zwei separat vorab festgelegte Inferenzvarianten prüfen, parallel Ursachenanalyse des Reward-Rückschritts.

## 20.10.2026, 20:36 – Codex: Integration geprüft, Trainingsstart vorbereitet

Mahmouds `d41d1bf` normal gemergt (`05db41d`); seine deaktivierte Erkundungsquote und alle gemeinsamen Notizen erhalten. Danach **215 Tests plus vier Untertests bestanden (36,34 s)**. 24 kurze Spiele: V3 und die zwei einzeln aktivierten Inferenzvarianten auf je zwei Entwicklungskarten, beiden Seiten/Gegnern. V3 reproduziert alle acht bisherigen Spielzeilen außer Laufzeit. Varianten nur auf Lauffähigkeit geprüft, kein Stärkeurteil. Abgabe V3 und alte Sicherung bytegleich.

Audit: `experiments/analysis/autonomous_20261020/pretraining_checks.json`, Rohdaten `pretraining_*_smoke.csv`. Separater Reward-Pilot bereit für tatsächlichen Start: zwei frische Einzelnetze, je 400 Spiele, einziger Unterschied Terminal-Potentialkorrektur. Alle drei Flags standardmäßig aus; der Reward-Pilot aktiviert ausschließlich seinen Reward-Schalter im zweiten Arm. Während seines Laufs bleibt der lokale Code einschließlich HEAD eingefroren; Remote-Beobachter meldet weiterhin neue Commits, Integration erst danach.

**Reservierung für danach:** Eigene Inferenzvarianten einzeln auf bekannten 500720–500779 prüfen; vorab festgelegte Auswahlregeln im Plan. 510000–510199 für höchstens einen Gewinner zur frischen Bestätigung reserviert. Mahmouds Trainings-/Bestätigungsblöcke werden nicht mitbenutzt.

## 20.10.2026 abends – Codex: aktive Zielbesitzer als getrennte Testvariante

In der rein beobachtenden V3-Diagnose wurden 425 unbesetzte eigene Punktefelder in 38/40 Spielen einer Einheit mit negativer Energie zugeordnet; die Schattenzuweisung übergab sie einer lebenden Einheit. 139 dieser wiederholten Situationen hatten eine lebende Einheit in Manhattan-Distanz höchstens zwei mit Bewegungsenergie. Insgesamt änderten sich 2.729 Zielzuweisungen lebender Einheiten über 699 Schritte. Das sind Häufigkeiten, keine unabhängigen Ereignisse oder nachgewiesenen verlorenen Punkte.

Neuer Schalter `active_targets=False`: Nur für die Zielzuweisung werden Einheiten mit negativer Energie herausgefiltert. Null Energie bleibt zulässig. Belegung, `first_on_tile`, sonstige Merkmale und Lebenszykluserkennung bleiben unverändert. **Prüfung:** zwölf Tests plus vier Seiten-/Koordinaten-Untertests bestanden, zuvor erwartete RED-Fehler. Rohdiagnose, Vergleich sämtlicher nichtzeitlicher Spielkennzahlen und portables Diagnosewerkzeug sind separat dokumentiert. Spielstärkeprüfung folgt; keine Gewichte geändert.

## 20.10.2026 abends – Codex: Sap-Geometrie als getrennte Testvariante

40 reine Beobachtungsspiele mit V3 auf 500720–500739 (Solution_92, beide Seiten) reproduzieren sämtliche vorhandenen Kennzahlen außer Laufzeit. In 218 von 4.168 geeigneten ausgeführten Sap-Angriffen, verteilt über 32/40 Spiele, liefert ein freies Zielfeld einen höheren bestehenden Energiescore. Das ist ein beobachteter Ansatzpunkt, keine Messung tatsächlichen Schadens oder gewonnener Spiele.

Neuer Schalter `sap_geometry=False`: Nur wenn ein bisheriges legales Sap-Ziel vorhanden ist, werden zusätzliche freie Zentren geprüft. Ausschließlich ein strikt besserer Score ersetzt das alte Ziel; alte Gleichstände bleiben erhalten. Bei sichtbaren Gegnern mit negativer Energie bleibt der alte Pfad. Keine Änderung der Aktionsverfügbarkeit; neue leere Zentren erhalten keinen Gegner-auf-Punktefeld-Bonus.

**Prüfung:** 12 gezielte Tests, zuerst vier erwartete Fehler, danach alle bestanden. Abgedeckt sind Cluster, Kartenrand/Reichweite, Spiegelung, Gleichstände, fehlende Ziele, negative Energie und Punktefeld-Priorität. Die Variante ist ausgeschaltet und noch nicht auf Spielstärke geprüft; keine Gewichte geändert.

## 20.10.2026 abends – Codex: kontrollierter Reward-Pilot vorbereitet

Beim bereits erkannten Tod einer Einheit fehlte im potenzialbasierten Shaping der Abschluss `-w_shape * phi(s)`. Der neue Schalter `terminal_death_potential` ergänzt nur diesen Term, ohne die Lebenszyklus-/Done-Erkennung zu verändern. Standardmäßig aus: alte Checkpoints und laufende Trainings behalten ihre bisherige Belohnung. `full_rules_v3_terminal` unterscheidet sich genau in diesem Flag von `full_rules_v3`; vorhandene Basis-Overrides werden nicht verändert.

**Prüfung:** Neue Reward-/Registry-Tests zunächst 10 erwartete Fehler, nach Umsetzung zusammen mit bestehenden Reward-Tests **32 bestanden**. Tests umfassen entfernte Einheiten, Wiederauftauchen, gleichzeitiges Matchende, ausgeschaltetes Shaping, vollständige diskontierte Übergangsfolgen und Config-Kompatibilität. Das ist eine Konsistenzkorrektur, noch kein belegter Spielstärkegewinn.

**Trainingsplan:** Je 400 Spiele aus identischen Anfangsgewichten (Seed 46, Karten 460000–460199), anschließend ausschließlich finale Checkpoints auf bekannten Entwicklungskarten vergleichen. Keine Wiederaufnahme alter Replay Buffer; keine Zwischencheckpoint-Auswahl. Der geprüfte Ablauf `experiments/analysis/autonomous_20261020/tools/reward_pilot.py` dokumentiert Start-/Endgewichte, Config, Quellcode und Ergebnisse, schützt V3/Sicherung und beendet eigene Prozesse spätestens um 06:00 Berlin. Vor dem tatsächlichen Start noch Gesamttests und kurze Reproduktion nach Integration der getrennten Diagnosevarianten. Noch kein Trainingsergebnis.

## 20.10.2026, 20:35 – Claude Code mit Mahmoud: Relic-Suche im 2./3. Match (`explore_quota`) verworfen

**Diagnose** (`all18_v3`, Val 720–759): In 13 von 57 verlorenen Matches haben wir mindestens ein Relic nie gefunden (davon 6, in denen Solution_92 alle fand). Ursache: In Match 2/3 gibt es mehr bekannte Ziele als Units, dann bekommt keine Unit ein Erkundungsziel.

**Neuer Schalter `explore_quota`** (+ `explore_until=75`, Default aus, Test in `tests/test_rules_1910.py`): solange das Relic-Paar des Matches fehlen kann, suchen so viele Units (nicht auf Punkte-Tiles, zuerst ohne Ziel/mit Gegnerziel) lange nicht gesehene Tiles der eigenen Hälfte ab. Val 720 gegen `all18_v4` (84,5 %): Quote 1 **−8,0 (KI [−14,0; −2,0])**, Quote 2 **−9,5** → bleibt aus. Units vom Punktesammeln abzuziehen kostet mehr, als gefundene Relics bringen.

**`sap_kill_first`** (Sap-Ziel bevorzugt Gegner, die der Treffer zerstört): Val 720 **−8,0 (KI [−14,5; −1,5])** gegen `all18_v4` → aus; die bisherige Wahl (größte getroffene Gegnerenergie) ist besser.

**`energy_pref`** (Punkte-Tiles mit hoher Feldenergie bevorzugen) 2 / 5: −1,5 / −3,5 → aus. **Seitenvergleich** über 3600 Spiele gegen Solution_92 (7 Messreihen): player_0 77,2 %, player_1 77,3 % – kein Spiegelungsfehler.

Hinweis an Moayed/Codex: Moayeds V4-Direktvergleich gelesen; V3 bleibt Abgabe. Zielvergabe-/Sap-Geometrie-Diagnose und Reward-Trainingspilot sind bei Codex – Claude startet dazu nichts Paralleles.

## 20.10.2026, 20:25 – Codex: V4-Direktvergleich abgeschlossen, V3 bleibt Abgabe

V4 enthält exakt dieselben 18 Netze wie V3; nur `contest_sap` und `opp_infer` sind zusätzlich aktiv. Mahmouds positive Bestätigung gegen Solution_92 bleibt gültig. Das vorab zusätzlich festgelegte direkte Gate ist jedoch **unklar**: V4 gewinnt gegen V3 **61/120 Spiele** auf 60 bekannten Entwicklungskarten 500720–500779, beide Seiten; Kartenbootstrap 95 % [43,33; 58,33] % bei 5.000 Wiederholungen. Die untere Grenze liegt nicht über 50 %. Deshalb keine automatische Übernahme, keine Behauptung, V4 sei schlechter. V3 bleibt die feste Ausgangsbasis für die nächsten eigenen Versuche.

Rohdaten: `experiments/compare/autonomous_20261020/v4_vs_v3.csv`; Identitätsprüfung und Auswertung: `experiments/analysis/autonomous_20261020/v4_identity.json` und `v4_direct_gate.json`. Weitere V4-Kurs-/Reproduktionsprüfungen werden erst bei einer erneuten begründeten Übernahmeentscheidung benötigt. Keine Gewichtsdatei geändert. Als Nächstes: rein beobachtende Diagnose von Zielvergabe/Sap-Geometrie und kontrollierter Reward-Trainingspilot.

## 20.10.2026, 20:20 – Claude Code mit Mahmoud: neuer Kandidat `all18_v4` bestätigt (Hinweis an Moayed/Codex)

**Mahmoud/Claude arbeiten weiter, heute bis 0:00 Uhr**, morgen geht es weiter (die Notiz „Mahmoud/Claude arbeitet derzeit nicht weiter“ ist überholt). Moayeds Reservierungen 502 420–502 619 werden nicht benutzt.

**`all18_v4`** = `all18_v3` + `contest_sap` + `opp_infer` (Config im Checkpoint, `experiments/candidates/all18_v4.pth`, SHA-256 `3465225733bbbfbf05adc577f7af5f76cb2d886ff2ed895498434fac979ededd`, in `scripts/install_candidates.sh`). **Bestätigung auf 400 frischen Karten 502 820–503 219** (Kombination vorab festgelegt, nur Solution_92, je 800 Spiele, gleiche Karten/Seiten): `all18_v3` 78,0 %, **`all18_v4` 80,4 % (+2,4, KI [+0,1; +4,6])**. Default auf 502 820–502 919: v4 197/200, v3 198/200 (−0,5 pp; beide Niederlagen-Karten ohne gefundenes Relic). 3 Karten × 2 Seiten: gespeicherte Config identisch mit `--set`. Laut Moayeds Abnahmeregel (positiver Bereich gegen Solution_92, default höchstens −2 pp) wäre **v4 der bessere Kandidat für eine Übernahme als v3**; eine eigene Bestätigung gegen die alte Abgabe auf Moayeds Block fehlt noch. Abgabe-Gewichte von Claude **nicht** verändert (Mahmoud hat noch nicht „ja, einsetzen“ gesagt).

**Läuft bei Mahmoud:** `pipeline_cnn3.sh` (Messung auf 502 020–502 219), `pipeline_v3nets.sh` (502 620–502 819). Beide enden vor 0:00.

## 20.10.2026 abends – Codex: V3 gegen bisherige Abgabe bestätigt

**Messung:** Auf vorab reservierten 200 neuen Karten 502420–502619 gewinnt `all18_v3` gegen Solution_92 **313/400 (78,25 %)**, die bisherige Abgabe `old3_sym3` **170/400 (42,5 %)**. Gepaarte Differenz +35,75 Prozentpunkte, 95%-Kartenbootstrap [29,00; 42,25]. Default 400/400 gegen 382/400. Direkter Vergleich auf 60 bekannten Entwicklungskarten: V3 96/120, Intervall [70; 90] %. Alle vorab festgelegten Stärkekriterien bestanden und unabhängig nachgerechnet. [Bericht, Quellen und Grenzen](../experiments/analysis/autonomous_20261020/RELEASE.md).

**Einordnung:** Bestätigung von Mahmouds bereits vorhandenem Kandidaten; kein neues Training und kein Gewinn durch die vier verworfenen Codex-Varianten. 1.728 Spielausführungen im Übernahmebatch einschließlich acht Reproduktionsspielen; zusätzliche technische Reproduktion umfasst 16 bereits ausgewertete Spiele.

**Integration und Prüfung:** Remote bis `3a4f32f` normal gemergt; Messcode `14d239f` bleibt in der Historie. Beide Checkpoints einschließlich sämtlicher Netzparameter und effektiver Config geprüft; `cand_boost=0`, `contest_sap=False`, `pt_walk=False`. Alle Kennzahlen außer Zeit der 16 Schlussprüfspiele identisch. Gesamte Testsuite **169 bestanden (46,44 s)**. Sicherung und beide bisherigen Abgabedateien weiterhin bytegleich; Installation und anschließende Kursprüfung stehen als eigener Schritt an.

**Anschließende Übernahme:** Beide Abgabedateien durch den geprüften V3-Kandidaten ersetzt, SHA-256 jeweils `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`. Danach acht Kurs-Runner-Spiele bestanden, beide Seiten/Gegner, je 303 Schritte, explizit verifizierte 18 Netze und frisches Belief. Maximale gemessene Entscheidungszeit 39,82 ms, keine Aussage zu einem unbekannten Turnierlimit. Manifest: `experiments/releases/20261020_all18_v3.json`. Alte Sicherung unverändert. Nach Installation zusätzlich 41 Lade-/Runner-/Gewichtsschutztests bestanden (22,05 s). README und gemeinsamer Überblick beschreiben nun V3; Präsentationsdateien bleiben historisch.

**Datenintegrität:** Git hatte wegen `core.autocrlf=input` die CSV-Zeilenenden beim Einchecken normalisiert. Eine ordnerlokale `.gitattributes` erhält jetzt die exakten Messbytes, damit Audit-Hashes auch nach einem Clone stimmen. Alle elf CSVs im Arbeitsordner gegen ihre zuvor eingecheckten Fassungen geprüft: identische geparste Daten, nur Zeilenenden geändert.

**Weitere Arbeit:** Moayed verlangt ausdrücklich auch neues Training und laufende Koordination mit Subagents. Ein Agent beobachtet neue Remote-Commits, ohne selbst zu mergen. Geplant sind ein kontrollierter Reward-Trainingsvergleich und getrennte Tests zur Zielvergabe sowie Sap-Geometrie; noch nicht als Verbesserungen bestätigt. Mahmouds zusätzliche Reservierungen 502620–502819 und 502820–503219 beachten. Kein zweites CNN3-/V3nets-Training starten.

## 20.10.2026 – Codex mit Moayed: selbstständiger Prüf- und Verbesserungszyklus

**Auftrag:** Moayed hat die selbstständige Planung, Umsetzung, Prüfung und das Pushen freigegeben, einschließlich längerer lokaler Läufe. Laut Moayed arbeitet Mahmoud/Claude derzeit nicht weiter. Abgabe-Gewichte bleiben ausdrücklich unverändert. [Plan und Fortschritt](superpowers/plans/2026-10-20-autonomous-improvement.md), [Auswahlregeln und Grenzen](superpowers/specs/2026-10-20-autonomous-improvement-design.md). Moayed hat den Zeitraum anschließend bis **21.10., 06:00 Berlin / 04:00 UTC** verlängert und einen Morgenüberblick beauftragt. Seit 19:39 verlangt Moayed fortlaufende aktive Arbeit ohne Intervallsteuerung; Automation daher nur noch für den Morgenbericht um 06:00, danach deaktivieren. Weitere begründete Arbeit nach dem ersten Zyklus ist autorisiert; ab 05:30 Abschluss priorisieren.

**Neue Freigabe und Sicherung (20.10., nach Start des Zyklus):** Moayed erlaubt jetzt ausdrücklich, die Abgabe durch einen nach den Tests nachweislich besseren Kandidaten zu ersetzen. Das frühere Änderungsverbot oben ist damit für eine geprüfte Übernahme aufgehoben. Beide bisherigen Dateien sind unter `experiments/releases/20261020_old3_sym3/` mit Manifest und Rückweg bytegleich gesichert; Hash jeweils `3788fb72…d158`. Noch kein Austausch erfolgt. Spec und Plan enthalten zusätzlich einen gepaarten Vergleich mit der alten Abgabe auf dem vorab reservierten frischen Kartenblock, Kursprüfung und Rückfall bei Fehlern. Der Trainings-Überschreibschutz bleibt aktiv.

**Commit-Präferenz:** Moayed wünscht dauerhaft mehrere fachlich zusammengehörige, geprüfte Commits an abgeschlossenen Arbeitsschritten. In gemeinsamer Anleitung und Plan festgehalten. Sicherung und Übernahmeregeln bilden einen eigenen Meilenstein; eine tatsächliche Übernahme bekommt später einen separaten geprüften Commit.

**Aktualisierung:** `1cadc18` übernommen, `all18_v3` installiert und als Referenz gewählt. Vorhandene Tests: 153 bestanden. Acht Entwicklungsspiele von V3 stimmen in allen Kennzahlen außer Zeit mit `M_fo10_ptsap_fc_720.csv` überein. Kein neues Training; die im Protokoll erwähnte CNN3-Pipeline wird nicht dupliziert.

**Kursbetrieb:** Neues `scripts/check_candidate_runner.py` prüft Kandidaten mit dem unveränderten Kurs-Runner in einem temporären Arbeitsverzeichnis. Acht Spiele auf Seeds 500720/500721, zwei pro Seite/Gegner; Gewichte kopiert, Original-Paths.csv unverändert. Gemessen werden Entscheidungszeiten, frisches Belief bei neuer Instanz und das Aktionsformat. Der Gegner Solution_92 wird wie im Kurs-Runner nicht zusätzlich zwischen Spielen zurückgesetzt. Die Prüfung ist kein Siegquoten-Benchmark und zertifiziert kein unbekanntes Zeitlimit.

**Review:** Unabhängige Prüfung des neuen Prüfwerkzeugs fand einen möglichen falschen Erfolg bei still abgewiesenem Checkpoint. Behoben: Architektur, Config und sämtliche geladenen Netzparameter werden jetzt gegen den Checkpoint verglichen; Regressionstest erst fehlgeschlagen, danach bestanden. Keine Agentenänderung. Bewertung strategischer Stärke, vollständiger Spiellegalität und unbekannter Kurs-Zeitlimits bleiben außerhalb dieser Integrationsprüfung.

**Abschlussprüfung:** 163 Tests bestanden. Erneute acht Kurs-Runner-Spiele mit explizit geprüfter Checkpoint-Identität erfolgreich; [Bericht](../experiments/analysis/autonomous_20261020/runner_verified.json). Abgabe- und Kandidatenhashes unverändert.

**Remote-Abgleich:** Commits `790997a` und `96bbf6f` übernommen. Gesamte Testsuite: **167 bestanden in 129,41 s** mit begrenzten numerischen Threads. Ein vorheriger Lauf wurde während JAX-Kompilierung nach 88 erfolgreichen Tests abgebrochen und vollständig wiederholt; er zählt nicht als bestandene Suite. Kein Agentencode durch Codex geändert.

**Entwicklungsmessung abgeschlossen:** 1.200 Spiele mit unverändertem Code `975b3aa`: V3 102/120 gegen Solution_92, Reserve30 101/120, Reserve60 96/120, far6 101/120, far14 100/120; gegen default alle 120/120. Alle 240 Zeilen je Variante und Seitenpaare/Punktzählversion geprüft. Keine Variante übertrifft V3, daher keine Änderung aus dieser Suche. Unsicherheitsintervalle und Quellen: `experiments/analysis/autonomous_20261020/development_report.json`. Die Abgabeübernahme wird stattdessen ausschließlich für V3 geprüft.

**Nächster Schritt / Reservierung:** Entwicklungsmessung auf 500720–500779: Referenz V3, Sap-Energiereserve 30/60 und `far_opp` 6/14, vier einzelne Varianten. Auswahl anhand mittlerem `result`, eindeutiger Gewinner, default höchstens −2 Prozentpunkte. **502420–502619 für die Bestätigung genau eines Herausforderers reserviert**; nicht für andere Versuche benutzen. 502020–502219 bleiben Mahmouds CNN3-Block. Neue CSVs und Status unter `experiments/compare/autonomous_20261020/` bzw. `experiments/analysis/autonomous_20261020/`.

## 20.10.2026 spätabends – Claude Code mit Mahmoud: `pt_sap` + `far_cand`, neuer Kandidat `all18_v3`

**Diagnosen** (Val 720–779, `all18_fo10` vs Solution_92, Skripte im Arbeitsverlauf): Matchsiege 90 / 75 / 57 %; 42 von 109 verlorenen Matches mit mehr als 200 Punkten Rückstand. Bekannte eigene Punkte-Tiles in Match 2/3 (Step 40–95): 4,9 besetzt, 1,2 frei (davon 0,39 mit Gegner darauf, Rest meist von einer Unit angesteuert). Zielwechsel: 15–24 % aller Unit-Schritte, altes Ziel meist noch gültig. **Sap-Gelegenheiten:** steht eine Unit auf einem eigenen Punkte-Tile und hat ein Sap-Ziel, wählt das Netz nur in 9–12 % Sap, sonst meist „stehen“ (Solution_92 sappt in dieser Lage immer, `harvest()`).

**Neue Schalter (Default aus, Tests in `tests/test_rules_1910.py`):**
- `sticky` (Kostenabzug für das bisherige Ziel): Val 720 **−6,0 / −8,5 pp** (Stärke 3 / 6) → aus.
- `far_cand`: entfernte Kandidaten der Gegnerhälfte (mit `far_opp`) hinter die eigenen Kandidaten: Val 720 82,0 % (+1,5, n. s.).
- `pt_sap` (+ `pt_sap_reserve`): Unit auf eigenem Punkte-Tile sappt statt zu stehen, wenn ein Ziel in Reichweite ist: Val 720 81,0 % (+0,5, n. s.).
- `pt_sap` + `far_cand`: Val 720 83,0 % (+2,5, n. s.). **Bestätigung auf frischen Karten 502 220–502 419** (200 Karten, 400 Spiele/Gegner, Kombination vorab festgelegt): default 100 % → 100 %, **Solution_92 71,75 → 78,5 % (+6,75, KI [+1,8; +12,0])**.

**Weitere Versuche auf Basis `all18_v3`** (Val 720, Referenz `O_v3_720` 83,0 %; alle Schalter bleiben aus): `sap_pt_first` (Sap-Ziel bevorzugt Gegner auf Punkte-Tiles) ±0; `pt_hold` −2,0; `idle_sap` (jede stehende Unit sappt, Reserve 30) **−9,5**; `pt_sap_reserve` 25 / 60: −0,5 / −4,5; `fog_sap` (Reserve 0 / 30) −1,0 / −1,5; `pt_sap_zone` (auch gestapelt / Kandidaten-Tiles) ±0. CNN `cnn2/ppo_0040` mit `far_opp`, `far_cand`, `pt_sap` (in `PPOAgent` jetzt nur im Eval-Modus aktiv): 81,0 % (+1,0 n. s.). Diagnose `all18_v3` (Val 720–789): Matchsiege 91 / 81 / 69 % (vorher 90 / 75 / 57 %), Saps in Match 3 37,6 statt 19,4 je Spiel; Todesfälle je Spiel wir 56, Solution_92 66, überwiegend stehende Units (Kollision 14, wenig Energie 18, sonst 19, Sap 5).

**Später getestet (Val 720 gegen `O_v3_720` 83,0 %, alle aus):** `safe_moves` (kein Zug auf Tile mit gleich starkem sichtbaren Gegner) −1,0; `ram` −1,5; `cand_boost` 10 / 30 (eigene Kandidaten auf einer Stufe mit Gegner-Punkte-Tiles) −2,5 / −3,0. **Diagnose fehlende eigene Punkte-Tiles** (`all18_v3`, Val 720–759): Match 3 Step 60/90 fehlen 1,54 / 1,24 von 8,2 – davon ungetestete Kandidaten 1,00 / 0,82, Relic unbekannt 0,49 / 0,36, fälschlich tot nur 0,04. Solution_92 kennt in Match 3 ohne neues Relic 97 % seiner Tiles, wir 84 %. Relic-Funde: gleich schnell wie Solution_92 (Match 3 neues Relic Median Step 37 vs 41), aber in 17 % vs 12 % der 3. Matches nicht alle Relics gefunden.

**Noch später (Val 720 gegen 83,0 %):** `stale_all` −0,5; `opp_infer` +1,5; neuer Schalter `contest_sap` (steht auf dem Ziel-Tile ein Gegner, den die Unit per Kollision nicht schlägt, sappt sie dieses Tile aus der Entfernung) +1,5; `contest_sap` + `opp_infer` +1,5 (alle n. s.). Bestätigung der vorab festgelegten Kombination `all18_v3` + `contest_sap` + `opp_infer` läuft auf **400 frischen Karten 502 820–503 219** (nur gegen Solution_92, je 800 Spiele).

**Neuer Kandidat `all18_v3`** = `all18_fo10` + `pt_sap` + `far_cand` in der Config (`experiments/candidates/all18_v3.pth`, SHA-256 `aac1c910…d935`, auch in `scripts/install_candidates.sh` und im Manifest); 3 Karten × 2 Seiten × 2 Gegner identisch mit `--set`. Keine neue Abgabe.

**Läuft:** `scripts/pipeline_cnn3.sh` (BC von `all18_fo10`: 1200 Lehrerspiele, 4,27 Mio. Unit-Schritte, Lehrer-WR 74 % vs Solution_92; danach PPO 60 Iterationen; Messung auf Val 720 und frischen Karten 502 020–502 219).

**Prüfungen:** 153 Tests bestanden (neu: `far_cand`, 2 × `pt_sap`). Val-Seeds: 502 020–502 219 für cnn3 reserviert, 502 220–502 419 verbraucht; **502 420–502 619 sind für Moayeds Bestätigungslauf exklusiv reserviert** (sein Plan `docs/superpowers/plans/2026-10-20-autonomous-improvement.md`), nächster freier Index für Mahmoud 2620. Abgabe-Gewichte unverändert (`3788fb72…d158`).

## 20.10.2026 – Codex mit Moayed: lokale Umgebung und all18_fo10-Funktionstest

**Auftrag und Einrichtung:** Auf Moayeds Mac (M3, 8 GB, arm64) eine eigene `.venv` im Projekt angelegt, `requirements.txt` installiert und ausschließlich in dieser Umgebung die Kursregel auf drei Matches gesetzt. Ausgangsstand `5ec86ae`. Python 3.13.13, PyTorch 2.14.1, LuxAI-S3 0.2.1, NumPy 2.5.4, JAX/JAXlib 0.12.0. Vollständige Paketversionen, Befehl und Prüfsummen: [Umgebungsnachweis](../experiments/analysis/local_moe_environment_20261020.json). `.venv` bleibt lokal und gitignored; weder System-Python noch Agentenquellen geändert.

**Prüfung:** `pip check` ohne Konflikte; `scripts.set_match_count --check` bestätigt drei Matches. `scripts.par_eval` mit `all18_fo10`, `--first 720 --n 2 --workers 2`: Seeds 500720/500721, beide Seiten, default und Solution_92, insgesamt acht Spiele. Ergebnis: default 4/4 Siege, Solution_92 2/4 Siege. [Lokale Messdaten](../experiments/compare/local_moe_all18_fo10_20261020.csv) stimmen in allen erfassten Feldern außer `secs` mit den zugehörigen Zeilen von `F_a18_fo10_720.csv` überein (numerische Vergleichstoleranz 1e-9). Vom Evaluator gemessene Laufzeit 32 Sekunden; erste Python-/Bibliotheksinitialisierung kommt zusätzlich hinzu. Kein neuer Leistungsvergleich auf unbekannten Karten, keine neuen Seeds verbraucht.

**Synchronisierung während der Arbeit:** Mahmouds neuer Commit `2524f0c` (standardmäßig ausgeschalteter `sticky`-Schalter, CNN3-Pipeline) vor dem Hochladen übernommen. Dieselben acht Spiele anschließend erneut ausgeführt: alle Kennzahlen außer Laufzeit weiterhin identisch, Evaluator-Laufzeit 11 Sekunden. Beide Abgabe-Dateien und der Kandidat auch danach unverändert. Insgesamt 16 Spielausführungen auf denselben zwei bekannten Karten; keine unabhängige zusätzliche Stichprobe.

**Schutz und Grenzen:** Kein Training, keine Codeänderungen, keine vollständige Testsuite und kein zusätzlicher Kurs-Runner-Test. Beide Abgabe-Dateien vor/nach dem Test SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`; Kandidat `all18_fo10` unverändert `b2b7ffcc506d71a4657bb8990a71c0b25c4535f0f41564054ff687a1fa7b4607`. Die Python-/JAX-Versionen weichen von Mahmouds Trainingsmanifest ab; auf diesen acht Spielen wurden dennoch identische Kennzahlen reproduziert. Das ist keine Garantie für sämtliche Trainings- und Auswertungspfade.

**Weiterarbeiten:** Befehle im Projekt mit `.venv/bin/python` ausführen oder die Umgebung mit `source .venv/bin/activate` aktivieren. Die vier geteilten Kandidaten sind bereits an den Originalpfaden installiert. Für einen erneuten Test einen neuen CSV-Ausgabepfad wählen. Umfangreichere Runner-Prüfung und Auswahl des nächsten Verbesserungsversuchs bleiben offen; Nachttraining ist möglich, wurde aber noch nicht gestartet.

## 20.10.2026 abends – Claude Code mit Mahmoud: Pipeline-Ergebnisse und PPO-Prüfpunkt

**Ausgangslage:** Moayeds Review `d0db18c` per Fast-Forward übernommen; danach Pipeline-Ergebnisse geprüft (Punkt 1 der Arbeitsliste). Mac war 09:58–16:54 zugeklappt im Akkubetrieb (Clamshell Sleep), die Trainings pausierten in dieser Zeit.

**Pipeline `pipeline_2010.sh`** (Log `experiments/pipeline_2010.log`):
- PPO `cnn2c` (ab `cnn2/ppo_0040`, `w_opp_points=1`, nur Reward geändert, kein Pool): Val 720 Iteration 10/20/30/40 = 78,0 / 78,0 / 75,0 / 77,0 % gegen 80,0 % am Start → kein Gewinn.
- `fo6` (6 Netze `full_rules_fo`, `far_opp=10` schon im Training, je 4000 Spiele mit 70 % Solution_92): Val 720 77,0 % (−3,5 vs `all18_fo10`, n. s.).
- `all24fo` (`all18` + `fo6`, `far_opp=10`): Val 720 78,0 % (−2,5, n. s.).
- **Frische Karten 501 820–502 019** (200 Karten, 400 Spiele/Gegner, vorab in der Pipeline festgelegt): default alle 100 %; Solution_92 `all18_fo10` 74,75 %, `fo6` 75,75 % (+1,0, KI [−3,7; +5,5]), `all24fo` 77,5 % (+2,75, KI [−1,0; +6,5]) → **kein belegter Unterschied, `all18_fo10` bleibt Referenz.** `all18_fo10` auf zwei frischen Blöcken: 80,0 % und 74,75 %; die Kartenblöcke streuen deutlich.
- Weitere Val-Tests: `all18_fo10` + `ram` 80,0 % (−0,5).

**PPO-Prüfpunkt aus dem Review** (int8-Kartenebenen im Update): 2 Spiele mit `cnn2/ppo_0040` gegen Solution_92 (Seeds 123 401/123 402, Trainingsbereich), 7183 Unit-Schritte, gleiches Netz: Ratio neu/alt im Mittel 1,00005, mittlere Abweichung |r−1| 0,0015, Maximum 0,10, kein Schritt jenseits der Clip-Grenze 0,15. Die Rundung erklärt den späteren Leistungsabfall also nicht; Ebenen liegen in [−0,3; 1,0], kein int8-Überlauf.

**Kandidaten-Manifest** `experiments/candidates_20261020.json`: SHA-256, Quellnetze (mit SHA-256), abweichende Config, Bauschritte und Ergebnisse für `all18_fo10` (SHA-256 `b2b7ffcc…4607`, 18 Netze) und `all24fo` (`e9ff09a6…8b03`, 24 Netze). Auf Wunsch von Moayed (über Mahmoud) liegen die Gewichte jetzt **versioniert in `experiments/candidates/`** (`all18_fo10.pth`, `all24fo.pth`, `cnn2_ppo0040.pth`, SHA-256 identisch mit den Originalen, README mit Ergebnissen und Befehl); Ausnahme in `.gitignore` vermerkt. Keine neue Abgabe. Kurs-Runner-Test `all18_fo10` (isolierte Kopie, 15 vs 2, 2 Spiele als player_0) ohne Fehler; der ausführlichere Runner-Test aus dem Review (beide Seiten, Laufzeit pro Zug) steht noch aus.

**Seeds:** Val bis 502 019 verbraucht, nächster freier Index 2020. Abgabe-Gewichte unverändert (`3788fb72…d158`).

## 20.10.2026 – Codex mit Moayed: Review-Erkenntnisse und nächste Schritte dokumentiert

**Auftrag:** Erkenntnisse aus der Prüfung von Mahmouds Commits und Vorschläge für die weitere Arbeit gemeinsam zugänglich machen. Ausschließlich Dokumentation; keine Änderungen an Agent, Gewichten, Training oder Runner. Laut Moayed erhielt die erste Präsentation die Note **1,3**.

**Übergabe:** Neuer [Review und priorisierte Arbeitsliste](REVIEW_NAECHSTE_SCHRITTE_20261020.md), geprüft gegen `2ed46e4`. Enthält nachgezählte Benchmark-Ergebnisse, Antworten auf die Prof-Fragen zu Reward/DQN/PPO/CNN und 18.000 Spielen sowie konkrete Prüfkriterien. Reihenfolge: aktuelle Pipeline-Ergebnisse prüfen und Kandidaten reproduzierbar sichern; Kurs-Runner prüfen; Match-3-Zielwahl verbessern; breiter mit zurückgehaltenen Karten bewerten; PPO-Konsistenz und Reward-Beiträge untersuchen. Vorschläge sind noch keine Umsetzung oder Freigabe für Agentenänderungen.

**Wichtige Abgrenzungen:** `all18_fo10` ist ein experimenteller Kandidat, keine neue installierte Abgabe. Seine Gewichte und die PPO-Checkpoints sind gitignored und müssen separat zwischen den Arbeitsumgebungen verfügbar gemacht werden. Die neue Pipeline `pipeline_2010.sh` reserviert bereits Karten 501820–502019; keine doppelten Versuche oder widersprüchlichen Seed-Zuweisungen starten. Historische Karten 900000–900029 sind kein unberührter Testsatz. Das CNN ist beobachtet ähnlich erfolgreich wie `all18`, aber weder als überlegen noch statistisch gleichwertig belegt. Reward-Strafe und Gegner-Pool wurden gemeinsam verändert und lassen sich daraus nicht einzeln bewerten.

**Prüfungen:** Verlinkte Ergebnis-CSVs nachgezählt, vollständige Seitenpaare/eindeutige Schlüssel und Punktemessversion geprüft; Dokumentlinks und Git-Diff geprüft. Keine neuen Spiele oder Trainings, keine Anwendungstests. Der Dokumentationscommit verändert ausschließlich Markdown-Dateien. Beide Abgabe-Dateien behalten SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`. Ausgangs-Arbeitskopie mit ihrem älteren Agentenstand nicht umgeschaltet; die Dokumentation wurde auf dem aktuellen GitHub-Stand in einer separaten Arbeitskopie erstellt.

**Offen für Mahmoud:** Zuerst aktuelle Pipeline-Ergebnisse und Verfügbarkeit der Kandidatengewichte prüfen, dann einen der vorgeschlagenen Versuche gemeinsam auswählen. Die Arbeitsliste enthält auch einen noch ungemessenen PPO-Prüfpunkt: unterschiedliche Rundung der Kartenebenen bei Rollout und Update. Keine der vorgeschlagenen Codeänderungen wurde hier umgesetzt.

## 20.10.2026 – Claude Code mit Mahmoud: Nacht-Ergebnisse, PPO-Stände, CNN-Ensemble

**Nacht Teil 2** (`scripts/overnight_2010.sh`, Log `experiments/overnight_2010.log`): 6 weitere `full_rules`-Netze mit 70 % Solution_92 (`*_s18`–`*_s23_sol70`, je 4000 Spiele, 138 min). 24er-Ensemble `all24` gegen `all18` auf frischen Karten 501 220–501 419: default beide 100 %, Solution_92 71,5 vs 72,0 % (−0,5, KI [−4,8; +3,7]) → **mehr Netze bringen nichts mehr**.

**PPO `cnn2`** (200 Iterationen ab BC, lr 1e-4, eigener Critic-Kopf), Val 720–819 vs Solution_92 (BC 73,0 %): Iteration 30 und 40 je **80,0 %**, 50 77,5 %, 60 72,5 %, 70 69,5 %, 100 70,0 %, 150 67,5 %, 200 68,0 % – PPO verbessert zuerst und verschlechtert sich danach (Entropie 0,38 → 0,12). Bestätigung auf frischen Karten 501 420–501 619 (200 Karten, 400 Spiele/Gegner): **`ppo_0040` default 100 %, Solution_92 72,8 %; `ppo_0030` 99,8 % / 72,8 %; `all18` 99,8 % / 71,0 %** (Δ +1,8, KI [−3,7; +7,2]) → ein einzelnes CNN nach 40 PPO-Iterationen ist so stark wie das 18er-DQN-Ensemble, aber nicht nachweisbar besser.

**`all18` auf allen frischen Karten** (501 020–501 619, 600 Karten, je 1200 Spiele): default 99,9 %, Solution_92 72,4 %.

**Neu: CNN-Policy-Ensemble** (`PPOAgent.extra_nets`, `scripts/build_cnn_ensemble.py`, Tests `tests/test_cnn_ensemble.py`): mittelt im Eval-Modus die log-Wahrscheinlichkeiten. Ensembles aus Ständen desselben Laufs (3, 5, 7 Netze) auf Val 720: 76,0 / 78,0 / 76,5 % gegen 80,0 % für `ppo_0040` allein → Stände eines Laufs sind zu ähnlich; Ensemble braucht unabhängige Läufe.

**Diagnose Match 3** (60 Karten × 2 Seiten, Ground Truth, Skripte `diag_m3`, `diag_m3b`, `diag_know3` im Arbeitsverlauf): Matchsiege 88 / 69 / 49 %. Verlorene 3. Matches sind Karten mit vielen Punkte-Tiles (10,1 je Hälfte, gewonnene 5,6). Dort besetzt Solution_92 bei Step 50 7,5 der 10 Tiles seiner Hälfte, wir 5,3 der 10 unserer Hälfte, obwohl 15 Units leben: 5,7 Units sind auf dem Weg zu Punkte-Tiles der Gegnerhälfte (im Mittel 18 Felder entfernt, nur 0,2 dort angekommen), 1,8 eigene Punkte-Tiles sind noch ungetestete Kandidaten, 0,9 außerhalb jeder Kandidatenzone. Wissen über die eigene Hälfte (alle Karten, Match 3 Step 50): wir 6,1, Solution_92 6,6 von 7,9 Tiles, beide ohne Fehler.

**PPO `cnn2b`** (ab `cnn2/ppo_0040`, lr 3e-5, Entropie 0,01, `--seed 1`, 80 Iterationen; `cnn2b/ppo_0040.pth` ist Iteration 40 dieses Laufs, nicht der Startpunkt): alle 16 Stände auf Val 720 zwischen 74,0 und 78,5 % gegen 80,0 % am Start → **Weitertrainieren mit PPO bringt nichts mehr.**

**Neuer Schalter `far_opp`** (Antwort auf die Match-3-Diagnose): Punkte-Tiles der Gegnerhälfte, die weiter als `far_opp` Felder von der Unit entfernt sind, rangieren in der Zielzuweisung hinter den Kandidaten-Tiles (`features.assign_targets`, Tests in `tests/test_rules_1910.py`). Val 720: `all18` + `far_opp=10` **80,5 % statt 76,5 %** (+4,0, KI [−1,0; +9,5]); CNN `ppo_0040` + `far_opp` 10 / 6: +0,5 / −0,5 pp. **Vorab festgelegte Bestätigung `far_opp=10` auf frischen Karten 501 620–501 819** (200 Karten, 400 Spiele/Gegner): default 100 % → 100 %, **Solution_92 74,0 → 80,0 % (+6,0, KI [+2,2; +9,8])**. Kandidat **`experiments/ensembles/all18_fo10.pth`** (gitignored) = `all18_kdf` + `far_opp=10` in der Config; 5 Karten × 2 Seiten × 2 Gegner identisch mit `--set`. `par_eval --set` wirkt jetzt auch auf CNN-Checkpoints.

**Läuft:** PPO `cnn2c` ab `cnn2/ppo_0040` mit Reward-Strafe für Gegnerpunkte (`w_opp_points=1`), 40 Iterationen.

**Prüfungen:** 148 Tests bestanden. Val-Seeds bis 501 819 verbraucht, nächster freier Index 1820. Abgabe-Gewichte unverändert.

## 19.10.2026 – Claude Code mit Mahmoud: Regeln, Reward-Korrekturen, CNN + PPO

**Auftrag:** Nach dem Review (lief laut Mahmoud gut) alles einbauen, was Regeln und Rewards hergeben, plus CNN/PPO (Empfehlung des Prof). Ziel bis 23.10.: default und Solution_92 möglichst immer schlagen. Commit/Push ausdrücklich erlaubt. Arbeitszweig `feat/regeln-rewards` (ab `b37aec3`, Präsi-Stand 15.10. vorher auf `docs/presentation-erkenntnisse` committet).

**Prof-Fragen beim Review und Antworten (belegt):** (1) „Warum 47 % nach 18 000 Spielen?“ – Der Agent ist hybrid: Gedächtnis, Zielzuweisung, Maske und Sap-Ziel sind Regeln, das Netz entscheidet laufen/stehen/sappen. Diagnose auf neuen Val-Karten 500 660–500 719 (`experiments/analysis/rules_vs_net_20261019*`): gleiche Regeln mit einfacher Regel statt Netz 95 % vs default (Netz 92 %), aber nur **3 % vs Solution_92 (Netz 38 %, Δ −34 pp, KI [−45; −23])**. (2) „Belohnung jeden Schritt?“ – Ja, pro Einheit und Schritt (`reward.py`), Matchsieg zusätzlich ±2.

**Ursachenanalyse gegen Solution_92** (Ground Truth, `scripts/analyze_losses.py --set`, Skript `diag_know` im Arbeitsverlauf): Solution_92 kennt die Punkte-Tiles viel früher (Match 1, Step 50: 2,6 vs 0,2). Grund: Es schließt Tiles aus, die von keinem *möglichen* Relic erreichbar sind. Danach bleibt Match 3 die Schwäche (mit allen Regeln Matchsiege 79 / 65 / 36 %).

**Neue Schalter (alle Default aus, alte Checkpoints unverändert):**

| Schalter | Wirkung | Ergebnis vs Solution_92 (100 Val-Karten, gepaart) |
|---|---|---|
| `relic_filter` | Belief ignoriert Units außerhalb jeder möglichen 5×5-Relic-Zone | **+11,0 pp** [+6,0; +16,0] |
| `subset_infer` | Differenzen von Teilmengen-Gleichungen, keine doppelten Gleichungen | +1,5 pp (n. s.), behalten |
| bestehende `explore_grid`, `scripted_explore`, `explore_stale=20` zusätzlich | Erkundung Match 1 | **+10,5 pp** [+2,5; +18,5] |
| `pt_walk`, `pt_hold` | BFS-Weg zu Punkte-Tiles, Punkte-Tile nicht verlassen | ±2 pp, aus |
| `home_penalty`, `home_last_only` | Gegnerhälfte meiden | −3 bis −15 pp, aus (Einheiten in der Gegnerhälfte stören Solution_92) |
| `smart_sap`, `fog_sap`, `fog_any` | abgestimmtes Sap / Sap in den Nebel | −3 bis +1,5 pp, aus |
| `keep_dead`, `cand_quota` | Null-Tiles über Matches merken / Kandidaten-Quote | −3 bis +1 pp, aus |
| `reward_fix` | 3 Reward-Fehler aus der Prüfung 14.10. behoben (ID-Wiederverwendung, negative Energie, terminales Potential) | nur Training |

**Bester Regelstand ohne neues Training** (`old3_sym3` + `early_inference relic_filter subset_infer explore_grid scripted_explore explore_stale=20`): Val 500 720–500 819: default 96,5 → 98,5 %, Solution_92 45,0 → 66,5 %. **Bestätigung auf neuen Karten 500 820–500 919:** default 96,5 → 99,0 % (+2,5 [0,0; +5,5]), **Solution_92 47,0 → 61,0 % (+14,0 [+4,0; +23,5])**.

**CNN + PPO (neu):** `agents/sherlock/cnn_model.py` (16 Kartenebenen 24×24 aus dem Belief → Conv + 3 ResBlocks → pro Unit lokales + globales Merkmal + 79er-Merkmale → Policy 6 Aktionen + Critic), `ppo_agent.py` (PPOAgent mit gleichen Leitplanken, Recorder mit GAE pro Unit-Trajektorie), `scripts/ppo_train.py` (`collect` Lehrer-Spiele, `bc` Nachahmung, `ppo`). Läufe unter `experiments/ppo/<run>/` (Gewichte/Rohdaten gitignored, Abgabe-Ordner gesperrt). Lauf `cnn1`: 800 Lehrer-Spiele (2,8 Mio. Unit-Schritte), BC 6 Epochen, 85 % Übereinstimmung. **BC-Policy allein: default 100 %, Solution_92 58 %** (Lehrer 66,5 %). PPO-Start mit gemeinsamem Critic verschob die Policy (KL 0,02 schon in der reinen Critic-Aufwärmphase) → abgebrochen, neu mit eigenem Critic-Kopf (`--detach-value`). Nach 10 Iterationen 61,5 % (+3,5 n. s.). DQN+CNN-Abstimmung (`cnn=` in `par_eval`): −2 bis −3,5 pp, n. s.

**Neu trainiert:** Variante `full_rules` (alle Regeln + `reward_fix`), 6 Starts × 3000 Spiele, `--no-test`, je 93 min. Ensemble **`rules6`** (`experiments/ensembles/rules6.pth`, gitignored) mit allen Regel-Schaltern: Val 720–819 **default 98,5 %, Solution_92 72,5 %**; neue Karten 820–919 **default 99,5 %, Solution_92 69,0 %** (gegenüber Ausgangsstand 47,0 %: +22,0 pp, KI [+12,0; +31,5]). 12er-Ensemble rules6 + old3_sym3: 68 % (schwächer). Zusätzlich `keep_dead_fast` (Null-Tiles wie Solution_92 über Matchgrenzen): 74,0 % (+1,5 n. s.), 0,02 falsche Punkte-Tiles pro Match 3. Kandidat **`rules6_kdf.pth`** = rules6 mit allen Schaltern in der gespeicherten Config; im Kurs-Runner (Kopie in temporärem Ordner, 15 vs 2) 2 Spiele fehlerfrei. Match-Siege rules6 vs Solution_92 (42 Karten): 85 / 71 / 49 % – Match 3 bleibt die Schwäche.

**Andere Gegner (50 Karten, beide Seiten):** Prof-DQN 100 %, alter Abgabe-Agent `old3_sym3` nur **60 %** (große Streuung, Punktedifferenz SD 607). Für fremde Teams ist Robustheit also nicht garantiert → Training mit Gegner-Pool (`--pool`, `--pool-frac`).

**Läuft/eingeplant (19.10. abends):** 6 × `full_rules` mit 70 % Solution_92, 4000 Spiele (`*_sol70`); PPO `cnn1` bis Iteration 150 (Iteration 50: 63 %); danach automatisch 6 × `full_rules_opp` (+ `keep_dead_fast`, Reward-Strafe `w_opp_points=1` für Gegner-Punkte, Gegner 60 % Solution_92 / 20 % Pool aus old3_sym3 + rules6 / 20 % default); CNN `cnn2` = BC vom Lehrer rules6 (800 Spiele, Lehrer-WR 65 % vs Solution_92 auf Trainingskarten), größeres Netz 48 Kanäle × 4 Blöcke.

**Weitere Ergebnisse 19.10. abends:** „Scharfschützen“-Regel (Ziele auf gegnerischen Punkte-Tiles durch Tiles ersetzen, die Solution_92 wegen seiner Manhattan-Reichweitenprüfung nicht beschießt): **22 % statt 74 %** – viele „gegnerische“ Punkte-Tiles liegen direkt an der Mittellinie und sind wertvoll; Code wieder entfernt. PPO `cnn1` bei Iteration 80 angehalten (Rechner überlastet, 285 s/Iteration): Iteration 50 63,0 %, 80 60,5 % vs Solution_92 (BC 58 %), default jeweils 100 % – kein belegter Fortschritt durch PPO.

**Spätere Tests 19.10.:** Kurs-Runner setzt die Klassenvariablen von Solution_92 (`Global`) zwischen Spielen nicht zurück; Nachstellung in einem Prozess (45 Spiele je Variante, Seeds 700 000+): rules6_kdf 71 % mit Zurücksetzen, 73 % ohne → kein nennenswerter Effekt. Neue Regel `ram` (auf Nachbar-Tile mit schwächerem Gegner fahren, Kollision zerstört ihn): Val 720–819 +2,5 pp (n. s.), neue Karten 920–1019 −3,5 pp (n. s.) → aus. `cand_quota=2` mit rules6: −4,5 pp → aus. Fehlende eigene Punkte-Tiles bei Step 95 in Match 3 (je Spiel): 0,62 ungetestete Kandidaten, 0,25 Relic unbekannt, 0,18 unter Asteroid, 0,08 fälschlich leer (`keep_dead_fast`). **Bester bestätigter Stand `rules6_kdf` auf neuen Karten 920–1019: default 98,5 %, Solution_92 70,0 %.** Val-Seeds jetzt bis 500 1019 verbraucht.

**Spät am 19.10.:** `opp_infer` (Null-Tiles aus dem Gegner-Punktgewinn) und `stale_all` (veraltete Erkundung in jedem Match, solange das Paar fehlt): +0,5 / +1,5 pp (n. s.), 0 falsche Punkte-Tiles. **Orakel-Diagnose** (echte Punkte-Tiles eingespeist, 40 Karten × 2 Seiten): 75,0 % vs 77,5 % ohne Orakel, Match 3 51 % vs 56 % → **Wissen ist nicht mehr der Engpass**, sondern das Besetzen (Match 3, Step 20–60: 3,8 Units auf Punkte-Tiles, 3,9 unterwegs zu gegnerischen Punkte-Tiles, 2,6 erkunden). `pt_walk` für alle Ziele −10 pp, ab Match 2 −6,5 pp, nur eigene Hälfte (`pt_walk_own`) +2,5 pp (n. s.). **CNN `cnn2`** (BC vom Lehrer rules6, 48 Kanäle × 4 Blöcke, 8 Epochen, 85,7 % Übereinstimmung): **default 100 %, Solution_92 73,0 %** (Val 720–819) – ein einzelnes CNN auf Lehrer-Niveau (+15 pp vs `cnn1`, KI [+7,5; +23]). Um 21:46 Notfall-Ruhezustand wegen Überhitzung (Deckel zu, Volllast), Prozesse liefen nach dem Aufwachen weiter.

**Nacht-Pipeline** `scripts/overnight_1910.sh` (Log `experiments/overnight_1910.log`): wartet auf die Trainings, baut `sol70_6`, `rules12`, `opp6`, `all18`, misst sie auf Val 720–819 gegen `N_r6_kdf_720` (rules6 + alle Regeln) und startet PPO für `cnn2` (200 Iterationen).

**Ergebnisse der Nacht-Pipeline (Val 720–819, alle mit denselben Regel-Schaltern wie `rules6_kdf`, Referenz 99,0 % / 74,0 %):** `sol70_6` (6 Netze, 70 % Solution_92 im Training) 98,5 % / 76,0 % (+2,0 n. s.); `rules12` (rules6 + sol70) 99,5 % / 75,5 %; `opp6` (Gegner-Punkte-Strafe `w_opp_points=1` + Pool) 100 % / **68,0 % (−6,0, KI [−14; +2])** → Gegner-Strafe und Pool helfen nicht; **`all18`** (alle 18 Netze) **100 % / 76,5 %** (+2,5 n. s.). CNN `cnn2` BC allein 100 % / 73,0 %. DQN `all18` + `cnn2`-Policy gemischt: Temperatur 0,2 −1,0 pp, 0,5 −3,0 pp (n. s.) → Mischung bringt nichts.

**Bestätigung auf frischen Karten 501 020–501 219 (200 Karten × 2 Seiten, `W_*_1020.csv`):** `rules6_kdf` default 98,8 %, Solution_92 67,2 %; **`all18` default 100 % (400/400), Solution_92 74,3 % → +7,0 pp, KI [+2,5; +11,7]** – erste signifikante Verbesserung seit `rules6`. Kandidat **`experiments/ensembles/all18_kdf.pth`** (gitignored) = `all18` mit `keep_dead_fast` in der gespeicherten Config; auf 10 Karten × 2 Seiten × 2 Gegner identische Ergebnisse wie mit `--set` (40/40). Kurs-Runner-Test für `all18_kdf` steht noch aus. PPO `cnn2` läuft (Rollout-WR vs Solution_92 schwankt 0,4–0,9 bei 34 Spielen je Iteration, kein klarer Trend bis Iteration 25); um 23:31 kurzer Ruhezustand, weil `caffeinate` an das Pipeline-Skript gebunden war – jetzt an den PPO-Prozess gebunden. Nichts davon ersetzt die Abgabe.

**Arbeitsweise:** Mahmoud möchte, dass gute Stände direkt auf `main` committet und gepusht werden (keine Pull Requests/Feature-Branches). Achtung: Der Projektordner wird synchronisiert; ein Branch-Wechsel erzeugte Kopien „… 2.csv“, die in `989cc3c` entfernt wurden.

**Werkzeuge:** `scripts/par_eval.py` (100 Karten × 2 Seiten × 2 Gegner in ~50 s, `--set` Schalter, PPO-Checkpoints automatisch erkannt), `analyze_losses.py --set`. Tests: 143 bestanden (neu `tests/test_rules_1910.py`).

**Seeds:** Val 500 660–501 219 verbraucht (Diagnose 660–719, Tuning 720–819, Bestätigung 820–919, 920–1019 und 1020–1219); nächster freier Val-Index 1220. Trainingsseeds PPO 100 000+. Test-Seeds 900 000+ nicht angefasst.

**Abgabe-Gewichte unverändert** (`agents/sherlock/weights/`, SHA-256 `3788fb72…d158`). Neue Abgabe erst nach ausdrücklicher Entscheidung.

## 15.10.2026 – Claude Code mit Mahmoud: Erkenntnisfolie und Reservefolie zur Belohnung

**Auftrag:** Moayeds Foliensatz prüfen und das Nötige verbessern. Ausgangspunkt `ba1578f`, Arbeitszweig `docs/presentation-erkenntnisse`.

**Änderung und Grund:** Design, Reihenfolge und alle übrigen Folien unverändert. Folie 11 zeigte nur einen negativen Befund; jetzt steht dort der belegte Fortschritt: gegen Solution_92 von 12/60 (altes Einzelnetz `full_s0`) auf 28/60 Siege (aktuelles Ensemble), gleiche 30 Testkarten auf beiden Seiten. Dazu „Mehr Training half kaum“ und Match 1 als nächster Schritt; interner Name `m1_early` nur noch in den Notizen. Folie 3 „Punkten: unsichtbare Felder besetzen“ als Brücke zum Gedächtnis, Folie 5 Belief-Zeile konkret (Punktezuwachs → Punktefelder), Folie 6 „6 Netze (3 + 3 mit Symmetrie)“ statt `full`/`full_sym`. Neue ausgeblendete Reservefolie 15 „Belohnung im Training“ mit allen Reward-Signalen und Gewichten für Rückfragen. Notizen 3/6/11/15, `slides.json`, Vortragsplan, Checkliste, Quellen, Prüfvermerk, README und CLAUDE.md abgeglichen. Folie 11 jetzt 65 statt 55 Sekunden: Plan 11:10, Moayed 5:35, Mahmoud 5:35.

**Prüfung:** Zahlen gegen `TEST_full_s0.csv` und `TEST_old3_sym3_points_v2.csv` nachgezählt (51/60 und 12/60 bzw. 60/60 und 28/60, Seeds 900000–900029). `compare_report` gepaart nach Karte: Solution_92 +26,7 pp, KI [+13,3; +41,7]; default +15,0 pp, KI [+3,3; +28,3]; ohne Korrektur für Mehrfachvergleiche/Modellauswahl, Karten mehrfach genutzt. Reward-Gewichte gegen `config.py`, `reward.py` und die Manifeste `full_s0`/`full_sym_s0`, Ensemble-Zusammensetzung gegen `ensemble_sources` im Checkpoint. Paketprüfung des PPTX-Skills bestanden. **Erstmals in nativem Microsoft PowerPoint (Mac) geöffnet** und daraus die PDF exportiert, ohne Reparaturmeldung; alle 15 Seiten gerendert und angesehen, Abstände auf Folie 11 nachgebessert. Dunkle Seiten 1/12: Hintergrund 2 pt über den Rand gemalt, alle Randpixel bei 1400 px `#102D35`. 131 Tests bestanden (vor der Folienarbeit, Code unverändert). Agent, Gewichte (SHA-256 weiterhin `3788fb72…d158`), Runner und Messdaten unverändert; keine neuen Spiele oder Training.

**Nachtrag:** Auf Mahmouds Wunsch Stichpunkte zum Ablesen für alle Folien, Reservefolien und typische Fragen, dazu eine einfache Projekterklärung und ein Wörterbuch aller Fachbegriffe von Folien und Vortrag, als `Sherlock_Stichpunkte_16-10-2026.md` im Projektordner (nicht versioniert), abgeleitet aus Notizen und Vortragsplan; Zeiten summieren sich auf 335 + 335 Sekunden.

**Offen:** Moayed über die geänderten Folien 3/5/6/11/15 informieren; gemeinsame Probe mit Uhr; Upload bis 16.10., 08:00 Uhr. Die PDF liegt zusätzlich als Arbeitskopie im Projektordner (`Sherlock_Review_16-10-2026.pdf`, nicht versioniert, identisch mit `docs/presentation/`).

## 15.10.2026 – Codex mit Moayed: Agenda als zweite Folie

**Auftrag:** Eine Agenda wie in der bereitgestellten Referenz einfügen, als Orientierung für das Publikum. Reserveinhalte und interne Hinweise nicht in der Agenda aufführen. Ausgangspunkt `b3c7e3d`, Arbeitszweig `docs/presentation-agenda`.

**Änderung:** Neue Folie 2 „Agenda“ mit sechs Themenblöcken: Spielidee/Ziel, Agent/Merkmale, Architektur/Lernverfahren, Training/Auswertung, Ergebnisse/Spielbeispiel, Erkenntnisse/Ausblick. Einfache nummerierte Liste, ursprüngliche Sherlock-Farben und Typografie. Bestehende Folien inhaltlich erhalten und ab alter Folie 2 um eins weiter nummeriert. Zwölf Vortragsfolien plus zwei ausgeblendete Reservefolien 13/14; Vortrag endet nach Folie 12. Pseudocode jetzt auf Folien 4/7, Trainingstabellen auf Folie 8, Ergebnisdiagramm auf Folie 9.

**Zeit und Übergabe:** Moayed übernimmt die Agenda mit 20 Sekunden zusätzlich. Neuer Plan 11:00 Minuten (Moayed 5:35, Mahmoud 5:25), weiterhin höchstens zwölf. Vortragsplan, Notizen/JSON, Checkliste, README, CLAUDE und Quellen auf neue Nummern abgestimmt; gemeinsame Probe steht noch aus. Die Reservefolien wurden aus der Agenda ausgelassen, nicht aus dem Anhang gelöscht. Frühere Protokolle beziehen sich auf die damalige Nummerierung.

**Prüfung:** Paket-, Layout-, Schrift-, native Tabellen-/Diagrammprüfung erfolgreich. Neue Agenda visuell geprüft. Vorhandene Folienkörper und Notizen unverändert; beim Rendervergleich nur die neuen Seitenzahlen unterschiedlich. Tabellen, Diagramm, eingebettete Datentabelle und Bilder bytegleich; dunkle PDF-Seiten 1/12 randlos. Kein Test in nativem PowerPoint. Agent, Skripte, Messdaten und Gewichte unverändert; keine neuen Spiele oder Training. Beide Gewichtshashes weiterhin `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## 14.10.2026 – Codex mit Moayed: Trainingspseudocode und publikumsfertige Hauptfolien

**Auftrag:** Folie 6 als Pseudocode wie Folie 3 gestalten, Tabellen auf Folie 7 nochmals auf gleiche Größe prüfen und interne Vortragsinformationen von den Hauptfolien entfernen. Ausgangspunkt `a86ef79`, Arbeitszweig `docs/training-pseudocode-cleanup`.

**Änderung:** Folie 6 mit hellem Codekasten, Courier New, eingerücktem Lernupdate und fachlichem Kommentar. Dargestellt sind Batch 256, Auswahl durch Online-Netz, Bewertung durch Target-Netz, Terminalfall, Batch-Update und Target-Kopie alle 500 Updates. Folie 7: beide Tabellen weiterhin 556 × 300 px, jetzt auch gleiche Spaltenbreiten 170/386 px; Hinweis „Weitere Einstellungen: Reservefolie 12“ entfernt. Alle elf Hauptfolien auf weitere reine Vortragsanweisungen durchgesehen; keine weiteren gefunden. Fachliche Kontextangaben wie wiederverwendeter Benchmark und vollständige Replay-Ansicht bleiben erhalten.

**Prüfung:** Pseudocode mit `agents/sherlock/main.py::_learn` abgeglichen. Paket-, Layout-, Schrift-, Tabellen-/Diagrammprüfung erfolgreich. Folien 6/7 visuell geprüft. Außenmaße im PowerPoint exakt gleich; Außenkanten der Tabellen zusätzlich im PDF gemessen, Rundungsabweichung unter 0,1 pt. Elf übrige PDF-Seiten pixelidentisch; außer Folien 6/7 alle PowerPoint-Paketbestandteile bytegleich. Sprechernotizen und Zeitbudget 10:40 unverändert. Kein Test im nativen PowerPoint.

**Übergabe:** Aktuelle PowerPoint/PDF verwenden, Vortragsplan und gemeinsame Präsentationsregel in CLAUDE.md beachten. Mahmoud behält Folie 6 mit 75 Sekunden; die Notizen passen weiter zum Lernablauf. Interne Hinweise stehen ausschließlich in Notizen/Plan bzw. im separaten Anhang, nicht im sichtbaren Hauptteil. Agent und Gewichte unverändert, keine neuen Spiele oder Training; beide Gewichtshashes `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158` bestätigt.

## 14.10.2026 – Codex mit Moayed: gleich große Tabellen auf Folie 7

**Änderung:** Beide Tabellen auf Folie 7 auf dieselbe Breite und Höhe gebracht, oben und unten bündig ausgerichtet und Kopfzeilen vereinheitlicht. Zeilenhöhen an die unterschiedliche Zeilenanzahl angepasst, Schriftgröße beider Tabellen vereinheitlicht. Hinweis auf die Reservefolie darunter neu ausgerichtet. Inhalte, Notizen, Sprecheraufteilung und geplante 10:40 Minuten unverändert. Ausgangspunkt `c5d0a30`, Arbeitszweig `docs/equal-training-tables`.

**Prüfung und Übergabe:** Paket-, Layout-, Schrift-, Tabellen-/Diagrammprüfung erfolgreich. Folie 7 nach PDF-Export visuell auf gleiche Außenmaße und lesbare Umbrüche geprüft. Zwölf andere PDF-Seiten pixelidentisch; alle PowerPoint-Paketbestandteile außer Folie 7 bytegleich. Aktuelle PowerPoint/PDF verwenden. Kein Test in nativem PowerPoint, keine neuen Spiele oder Training. Agent und Gewichte unverändert; beide Gewichtshashes weiterhin `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## 14.10.2026 – Codex mit Moayed: Pseudocode und Trainingsparameter ergänzt

**Auftrag:** Pseudocode auf Folie 3 anhand der bereitgestellten Designreferenz ergänzen und Trainingsparameter auf Folie 7 sichtbar machen; bestehendes Design, 10–12 Minuten und unveränderte Gewichte erhalten. Ausgangspunkt `2108ea8`, Arbeitszweig `docs/pseudocode-training-slides`.

**Änderung:** Folie 3 zeigt links „Merken / Bewerten / Handeln“ und rechts den eingerückten Spielablauf in einem hellen Codekasten mit Courier New. Gestaltung nach Folie 4 aus `team20-presentation3.pdf`, Inhalte aus Sherlock. Pseudocode ausdrücklich für die Auswertung mit festen Gewichten; Match-Reset, Sap-Zielwahl, Aktionsformat und Stapelverarbeitung sind vereinfacht. Auf Folie 7 stehen Trainingsablauf und Parametertabelle nebeneinander: Lernrate/γ, Batch/Buffer, ε-Abnahme und Target-Kopie. Eine weitere Folie war nicht nötig. Notizen zu beiden Folien, Vortragsplan, Checkliste, README und Quellen gemeinsam aktualisiert.

**Prüfung:** Spielablauf mit `act`/`_decide` und Parameter mit allen sechs abgeschlossenen Basislauf-Manifesten abgeglichen. Paket-, Geometrie-, Schrift-, native Tabellen-/Diagrammprüfung einschließlich eingebetteter Datentabelle erfolgreich. Beide geänderten PDF-Seiten einzeln angesehen, enge Umbrüche nachgebessert. Elf übrige Seiten pixelidentisch zum zuvor geprüften Export. Im PowerPoint-Paket nur Folien 3/7 und deren Sprechernotizen verändert; sonstige Bestandteile bytegleich. Dunkle Seiten 1/11 randlos; Reservefolien 12/13 ausgeblendet. Kein Test in nativem PowerPoint.

**Übergabe an Mahmoud/Claude Code:** Aktuelle PowerPoint/PDF und Vortragsplan verwenden. Weiterhin elf Vortragsfolien, Ziel 10:40, maximal zwölf Minuten. Moayed behält 5:15 Minuten und erklärt auf Folie 3 den Grundablauf, ohne jede Codezeile vorzulesen; Mahmoud behält 5:25 und erklärt die Parameter auf Folie 7. Beide Notizen sind auf diese Aufteilung abgestimmt. Gemeinsame Zeitprobe und Kontrolle auf dem Vortragsrechner stehen noch aus.

**Unverändert:** Agent, Skripte, Runner, Messdaten und Gewichte. Keine neuen Spiele oder Training. Beide Abgabe-Gewichte anhand SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158` bestätigt.

## 14.10.2026 – Codex mit Moayed: Aufzählungen mit mittigen Strichen

**Auftrag:** Auf Folie 2 die Punkte durch mittige kurze Striche ersetzen und auf Folien 8/9/11 wieder passende Aufzählungen ergänzen. Ausgangspunkt `f480083`, Arbeitszweig `docs/dash-presentation-lists`.

**Änderung:** Acht Textfelder auf Folien 2/8/9/11 verwenden native Aufzählungszeichen „–“ in derselben Schrift wie der Text (Helvetica Neue). Hängender Einzug mit Abstand zum ersten Wort; Folgezeilen am Text ausgerichtet. Auf Folie 8 nur die beiden Ergebnisangaben als Liste, die kleine Benchmark-Anmerkung bleibt ohne Strich. Das konkrete Fazit auf Folie 11 bleibt inhaltlich erhalten. Keine Änderung an Sprechernotizen, Aufteilung oder Zeitbudget.

**Prüfung:** Paket-, Geometrie-, Schrift-, Tabellen-/Diagrammprüfung mit eingebetteter Datentabelle erfolgreich. Alle vier geänderten PDF-Seiten einzeln angesehen; Abstand nach erster Sichtprüfung vergrößert. Neun übrige Seiten pixelidentisch zum zuvor geprüften Export. Im PowerPoint-Paket ausschließlich acht Textkörper geändert, alle übrigen Bestandteile bytegleich. Dunkle Folien 1/11 weiterhin ohne weißen Rand. Kein Test in nativem PowerPoint.

**Übergabe:** Aktuelle PowerPoint/PDF verwenden; Vortragsplan und Notizen weiterhin gültig. Änderungen rein gestalterisch. Agent, Gewichte, Skripte und Messdaten unverändert; keine neuen Spiele oder Training. Beide Gewichte weiterhin SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## 14.10.2026 – Codex mit Moayed: konkretes Fazit ohne Aufzählungspunkte

**Auftrag:** Aufzählungszeichen auf Folien 8, 9 und 11 entfernen und die zu abstrakte Abschlussfolie verständlicher machen. Ausgangspunkt `8373e1a`, Arbeitszweig `docs/clarify-presentation-conclusion`.

**Änderung:** Auf Folien 8/9 die vorhandenen Texte ohne Listenzeichen und Einzüge gesetzt; auf Folie 11 ebenfalls keine Liste mehr. Abschluss enthält jetzt „Gedächtnis + sechs Netze“, die bekannten Benchmark-Ergebnisse (60/60 gegen default, 28/60 gegen Solution_92) und den nächsten Schritt: frühe Erkundung verbessern, neue Testkarten nutzen. Keine neuen Ergebnisbehauptungen. Sprechernotiz der Abschlussfolie in PowerPoint, Vortragsplan und JSON gemeinsam angepasst. Ursprüngliches Design und kurze Überschriften erhalten; Folie 2 behält ihre Aufzählungen.

**Prüfung:** Paket-, Geometrie-, Schrift-, native Tabellen-/Diagrammprüfung einschließlich eingebetteter Datentabelle erfolgreich. Folien 8/9/11 aus dem finalen PDF gerendert und visuell geprüft; die zehn übrigen Seiten sind pixelidentisch zum zuvor geprüften Export. Nur sieben Textkörper und die Sprechernotiz 11 im PowerPoint-Paket verändert, alle übrigen Bestandteile bytegleich. Dunkle Seiten 1/11 weiterhin randlos. Reservefolien 12/13 ausgeblendet, Zeitplan weiterhin 640 Sekunden. Kein Test in nativem PowerPoint.

**Übergabe:** Mahmoud und Claude Code verwenden die aktuelle PowerPoint/PDF und den synchronisierten Vortragsplan. Moayed schließt auf Folie 11 in etwa 25 Sekunden mit Ansatz, Ergebnis und nächstem Schritt ab und eröffnet die Fragen. Gemeinsame Probe bleibt offen. Agent, Skripte, Messdaten und Gewichte unverändert; keine neuen Spiele oder Training. Beide Gewichte anhand SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158` bestätigt.

## 14.10.2026 – Codex mit Moayed: kurze Überschriften und klare Aufzählungen

**Auftrag:** Satzartige Überschriften durch kurze Themenüberschriften ersetzen und fehlende Aufzählungspunkte ergänzen, insbesondere auf Folien 8/9. Ausgangspunkt `f4d0889`, Arbeitszweig `docs/concise-slide-headings`.

**Änderung:** Zwölf Themenüberschriften gekürzt, z. B. „Spielidee und Ziel“, „Netzarchitektur und Ensemble“, „Benchmark-Ergebnisse“ und „Spielbeispiel“. Titel „Sherlock“ bleibt erhalten. Neun Textfelder auf Folien 2, 8, 9 und 11 als echte bearbeitbare Aufzählungsabsätze formatiert, insgesamt 16 Listenpunkte. Aussage auf Folie 9 zu „Stehenbleiben kann sinnvoll sein“ gekürzt. Auf Folie 11 die drei bisherigen Abschlussaspekte untereinander gesetzt und die Textbox passend erweitert. Nummerierte Abläufe, Tabellen, Diagramm und Bildbeschriftungen erhalten. PowerPoint/PDF, Titel in `source/slides.json` und Vortragsplan gemeinsam aktualisiert.

**Prüfung:** Paket-, Geometrie-, Schrift-, Tabellen- und Diagrammprüfung einschließlich eingebetteter Diagramm-Datentabelle erfolgreich. Alle 13 PDF-Seiten einzeln angesehen. Export mit ursprünglicher Helvetica Neue, Randkorrektur für dunkle Seiten 1/11 erneut angewendet und Außenpixel geprüft. Paketvergleich bestätigt: Nur 21 gezielte Textkörper und Position/Höhe einer Textbox verändert; alle übrigen Elemente, Bilder, Tabellen, Diagrammdateien, eingebettete Datentabelle und Sprechernotizen unverändert. Reservefolien 12/13 weiterhin ausgeblendet. Kein Test im nativen PowerPoint. Zeitplan weiterhin 640 Sekunden (Moayed 315, Mahmoud 325).

**Übergabe:** Aktuelle PowerPoint/PDF und Vortragsplan verwenden; beide sprechen dieselben Folien wie zuvor. Fachliche Aussagen und geprüfte Zahlen unverändert. Agent, Gewichte, Runner, Skripte und Messdaten nicht geändert; keine neuen Spieltests oder Training. Beide Abgabe-Gewichte weiterhin SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## 14.10.2026 – Codex mit Moayed: weiße Kante auf dunklen Folien entfernt

**Auftrag und Änderung:** Weißen Rand auf den dunklen Folien entfernen. Im PDF-Export waren Beschnitt und Hintergrundmalfläche minimal kleiner als die vollständig gerasterte Seite. Auf Seiten 1 und 11 reichen beide jetzt einen Punkt über den Seitenrand; die unveränderten Seitenboxen begrenzen die Ausgabe. Die PowerPoint besitzt bereits einen vollflächigen Folienhintergrund und bleibt unverändert.

**Prüfung:** Beide korrigierten Seiten gerendert und angesehen; sämtliche Außenpixel bei 1400 Pixel Renderbreite haben Hintergrundfarbe `#102D35`. Text und Seitenmaße auf allen 13 Seiten unverändert, Inhaltsströme der übrigen elf PDF-Seiten identisch. PowerPoint und beide Gewichte anhand der bisherigen Prüfsummen unverändert bestätigt. PDF-Prüfsumme und Exporthinweis unter `presentation/source/` aktualisiert. Keine Änderung an Inhalten, Aufteilung, Agent oder Gewichten; keine neuen Spieltests nötig.

**Übergabe:** Aktuelle PDF verwenden. Bei künftigem Neu-Export die Kanten der dunklen Seiten erneut prüfen; die Änderung betrifft den PDF-Export, nicht den Vortragsinhalt.

## 14.10.2026 – Codex mit Moayed: ursprüngliches Design wieder verbindlich

**Auftrag:** Moayed bevorzugt die ursprüngliche Gestaltung. Inhalte nochmals prüfen und das Repository auf diese Fassung zurückstellen. Ausgangspunkt `802ed46`, Arbeitszweig `docs/restore-original-presentation`.

**Ergebnis:** Ausschließlich [ursprüngliche PowerPoint mit Notizen](presentation/Sherlock_Review_16-10-2026.pptx) und [PDF](presentation/Sherlock_Review_16-10-2026.pdf) als aktueller Foliensatz. Beide Dateien sind unverändert. Gamma-PowerPoint, Gamma-PDF, Gamma-Anleitung und Gamma-Notizen-JSON aus dem aktuellen Repository entfernt. README, CLAUDE.md, Checkliste und [Vortragsplan](presentation/VORTRAGSPLAN_1610.md) wieder auf elf Vortragsfolien plus zwei Reservefolien abgestimmt. Ziel 10:40 Minuten, maximal zwölf; Moayed 5:15, Mahmoud 5:25. Abschluss wieder auf Folie 11. Der frühere Gamma-Eintrag ist als abgelöst markiert, die Git-Historie bleibt erhalten. Die externe Gamma-Präsentation wurde nicht gelöscht.

**Inhaltsprüfung:** Gesamten PDF-Text und alle Sprechernotizen gelesen. 79 Merkmale, Netzarchitektur, Q-Mittelung/Aktionsmaske und Double-DQN-Lernziel mit Agentenquellen abgeglichen. Alle sechs abgeschlossenen Basislauf-Manifeste bestätigen jeweils 3000 Spiele sowie die genannten Trainingsparameter. Benchmark-CSV erneut ausgezählt: 60/60 Siege gegen default, 28/60 gegen Solution_92, je 30 Karten auf beiden Seiten. Replay-Metadaten und Zwischenstände bei Frames 23/61/90 stimmen mit den Bildnachweisen überein. Einschränkungen zu mehrfach genutzten Testkarten, früheren ausgewählten Checkpoints und späterem Kandidaten m1_early bleiben ausdrücklich erhalten. Kein fachlicher Korrekturbedarf an den Folien festgestellt.

**Dateiprüfung:** Ursprüngliche PowerPoint/PDF stimmen bytegenau mit den in `source/PRUEFUNG.json` dokumentierten Prüfsummen überein. PowerPoint-Paketprüfung ohne Befund; 13 Sprechernotizen vorhanden, Reservefolien 12/13 ausgeblendet. Titel- und Ergebnisfolie erneut aus der PDF gerendert und angesehen; die vollständige Sichtprüfung der unveränderten 13 Seiten ist im ursprünglichen Erstellungsvermerk dokumentiert. Zeitbudget, relative Links und Diff geprüft. Keine Ausführung im nativen PowerPoint, kein Training und keine neuen Spieltests.

**Für Mahmoud:** `main` aktualisieren und den wiederhergestellten Vortragsplan lesen. In der PDF nach Seite 11 enden; Seiten 12/13 nur bei Rückfragen zeigen. Noch gemeinsam mit Uhr proben, Darstellung/Notizen auf dem Vortragsrechner prüfen, Slot bestätigen und PDF bis 16.10.2026, 08:00 Uhr auf Moodle hochladen.

**Unverändert:** Agent, Gewichte, Skripte, Tests, Kurs-Runner und Messdaten. Beide Abgabe-Gewichte weiterhin SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

## 14.10.2026 – Codex mit Moayed: Gamma-Entwurf (historisch, abgelöst)

Ein Gamma-Entwurf mit zehn Folien wurde in Commit `802ed46` erstellt. Moayed hat anschließend ausdrücklich das ursprüngliche Design gewählt. Die Gamma-Dateien und die zugehörige Bearbeitungsanleitung sind deshalb nicht mehr Bestandteil des aktuellen Repository-Stands. Der frühere Entwurf bleibt über die Git-Historie nachvollziehbar. Maßgeblich sind ausschließlich die ursprüngliche PowerPoint/PDF und der aktuelle Vortragsplan; die damalige Zehn-Folien-Aufteilung gilt nicht mehr.

## 14.10.2026 – Codex mit Moayed: neue Präsentation und gemeinsame Vortragsplanung

**Auftrag:** Es gibt laut Moayed keine verwendbare Präsentation. Für den ersten Review neu aufbauen, etwa zehn bis höchstens zwölf Minuten; Moayed erhält den leichter zugänglichen Teil. Aufteilung und Vorbereitung für Mahmoud/Claude Code dokumentieren. Agent und Gewichte bleiben unverändert. Ausgangspunkt `12e0c4d`, Arbeitszweig `docs/review-presentation`.

**Ergebnis:** [Bearbeitbare PowerPoint](presentation/Sherlock_Review_16-10-2026.pptx), [PDF](presentation/Sherlock_Review_16-10-2026.pdf) und [Vortragsplan mit Lernhilfe](presentation/VORTRAGSPLAN_1610.md). Elf Vortragsfolien plus zwei Reservefolien. Zielzeit **10:40**, Moayed **5:15** (Aufgabe, Überblick, Ergebnisse, Spielbeispiel, Abschluss), Mahmoud **5:25** (Merkmale, Netz, Double DQN, Training, nächste Schritte). Notizen auf jeder Folie, konkrete Übergaben, Kürzung auf zehn Minuten und Antworten auf typische Rückfragen. Zeitangaben sind Planwerte; eine menschliche Probe steht noch aus.

**Inhaltliche Abgrenzung:** Aktueller Agent bleibt `old3_sym3`. Architektur und Parameter mit Code und gespeicherter Konfiguration abgeglichen. 18.000 Trainingsspiele meint die sechs Basisläufe à 3000; gewählte Checkpoints können früher liegen. Siegquoten 60/60 und 28/60 aus den neuen Benchmarkdaten. Mehrfach verwendete Testkarten als Grenze benannt. Keine alten Konfidenzintervalle oder unzuverlässigen genauen Erkundungszeitvergleiche übernommen. `m1_early` bleibt späterer Kandidat. Zwei echte Viewer-Bilder desselben Spiels (Seed 900011, Frames 23 und 90) zeigen Zwischenstände 0:0 und 374:11; vollständige Zuschaueransicht, kein Agentenwissen. Eine Live-Demo ist nicht nötig.

**Tatsächliche Prüfung:**

- Alle 13 Folien erstellt und gerendert; sämtliche finalen PDF-Seiten einzeln auf Lesbarkeit, Umbrüche und Überlappungen angesehen. PowerPoint-Paket, Geometrie, Schriftzuweisung und Wiederimport geprüft; keine gemeldeten Befunde. Ergebnisdiagramm nativ mit eingebetteter Datentabelle, Tabellen und Texte bearbeitbar.
- PDF aus der finalisierten PowerPoint mit eingebetteter Helvetica Neue erzeugt; 13 Seiten. Reservefolien 12/13 in PowerPoint ausgeblendet; in der PDF nach Seite 11 enden. Notizen auf allen 13 Folien vorhanden. Kein Test im nativen Microsoft PowerPoint durchgeführt; vor Ort Darstellung und Notizenansicht prüfen.
- Zeitbudget rechnerisch geprüft: 315 + 325 = 640 Sekunden. Ergebnisse gegen CSV, Bildzwischenstände gegen Replay-Datei und Viewer, relative Dokumentlinks und Git-Diff geprüft. [Prüfvermerk mit Dateihashes](presentation/source/PRUEFUNG.json), [Quellen/Bildnachweise](presentation/source/QUELLEN.md) und [Notizen als JSON](presentation/source/slides.json) liegen bei.
- Keine neuen Spieltests und kein Training für diese reine Präsentationsarbeit. Agentenmodule, Skripte, Tests, Kurs-Runner und Experimentdaten unverändert. Beide Abgabe-Dateien behalten SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

**Übergabe an Mahmoud:** Nach Veröffentlichung `main` aktualisieren. Mit Claude Code zuerst den Vortragsplan und diese Notiz lesen. PowerPoint ist die bearbeitbare Folienquelle; bei Änderungen PDF, Notizen/JSON und Plan gemeinsam abgleichen. README, CLAUDE.md und Review-Checkliste verweisen auf den neuen Foliensatz; frühere Hinweise auf einen externen 19-Folien-Entwurf sind historisch.

**Noch durch das Team zu erledigen:** Inhalt und Aufteilung gemeinsam bestätigen, zwei Proben mit Uhr, Slot/Buchung bestätigen, Dateien auf dem Vortragsrechner öffnen und PDF bis **16.10.2026, 08:00 Uhr** auf Moodle hochladen. Codex hat keinen Moodle-Upload vorgenommen. Die bestehenden offenen Mess-/Trainingsfragen bleiben Aufgaben für nach dem Review.

## 14.10.2026 – Codex mit Moayed: Statistik nach Karte korrigiert

**Auftrag:** `compare_report.py` korrigieren, Gewichte unverändert lassen, für Mahmoud/Claude Code dokumentieren und die geprüfte Änderung in `main` veröffentlichen. Ausgangspunkt `839dacc`, Arbeitszweig `fix/paired-seed-bootstrap`.

**Änderung:** Der gepaarte Bootstrap zieht jetzt ganze Karten mit ihren beiden Spielseiten. Kandidat und Referenz werden nach Gegner/Seed/Seite gepaart; anschließend wird die Seitendifferenz je Karte gemittelt. 5000 Bootstrap-Wiederholungen, Zufallsseed 0, 95-%-Perzentilintervall für die mittlere Differenz. Zeilen- und Kandidatenreihenfolge beeinflussen die Berechnung nicht. Die Anzeige trennt Karten von Spielen und zeigt WR beider Agenten sowie ihre Differenz auf derselben gemeinsamen Kartenmenge.

**Eingaben und Grenzen:** Doppelte Spielschlüssel, unvollständige Karten, fehlende/ungültige Ergebnisse und Vergleiche ohne gemeinsame Karten werden abgewiesen. Nicht gemeinsame Karten werden ausdrücklich als ausgeschlossen ausgewiesen. Bei nur einer gemeinsamen Karte wird kein KI geschätzt. Alle Dateien werden vor der Berichtsausgabe validiert, um irreführende Teilberichte zu vermeiden. CLI-Aufruf bleibt `python -m scripts.compare_report --ref REFERENZ.csv KANDIDAT.csv`; bewusst passende Test-/Validierungsdateien auswählen. Alte CSVs ohne Punktezählungs-Version bleiben für den Siegvergleich verwendbar, denn das Skript nutzt ausschließlich `result`.

**Prüfung:** Ein neuer CLI-Regressionstest zeigte den alten Fehler zunächst mit einem Intervall von [−1; +1], obwohl die mittlere Seitendifferenz auf jeder Karte null war. Nach der Korrektur [0; 0]. Insgesamt **26 neue Tests**, einschließlich exakt nachvollziehbarer Zwei-Karten-Verteilung, Zeilenreihenfolge, Gegnertrennung, gemeinsamer Vergleichsmenge, ungültiger Eingaben und Einzelkartenfall. Vollständige Testsuite: **131 bestanden in 30,15 Sekunden**. Unabhängiger Review: 26 fokussierte Tests erneut bestanden, keine offenen Befunde. Keine neuen Benchmarkspiele und kein neues Modelltraining; nur bestehende Tests mit temporären Trainingsdateien.

**Neu berechnete Resultate:** Drei vorhandene Vergleichspaare, je zwei Gegner, ohne Änderungen an den historischen Rohdaten: [Statistikprüfung mit Tabelle und Aufrufen](STATISTIK_20261014.md), [Ergebnisse und Quellprüfsummen](../experiments/analysis/paired_bootstrap_20261014.json). Wichtig für die Folien: `m1_early` Runde 1 gegen Solution_92 hat jetzt KI [0,00; +18,33] pp, also keinen allein dadurch belegten klaren Vorteil. Runde 2 bleibt bei +7,92 pp mit KI [+2,50; +13,75] pp. Die übrigen historischen Intervalle wurden nicht pauschal neu berechnet. Das aktuelle Abgabe-Ensemble bleibt `old3_sym3`.

**Gewichte:** Beide Abgabe-Dateien weiterhin SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`. Sie passen zum aktuellen Agenten und wurden zuvor auf beiden Seiten in 120 Spielen geprüft. Dass beide Dateien identisch sind, ist beim seitenübergreifenden Ensemble beabsichtigt. Die Statistikänderung erfordert keine Anpassung oder neues Training. Über eine spätere bessere Version entscheidet ein separater Entwicklungs-/Validierungsschritt, nicht eine nachträgliche Änderung dieser Zahlen.

**Übergabe:** Nach dem Upload `main` aktualisieren und diese Notiz lesen. README, CLAUDE.md, Experimentprotokoll und Präsentationscheckliste sind angepasst. Keine Änderungen an Agent, Reward, Kurs-Runner, bisherigen Rohdaten oder Gewichten. Die konkrete Veröffentlichung wird durch die Git-Historie und den abgeglichenen Remote-Stand bestätigt.

**Weiterhin offen:** Zeitliche Ausrichtung der Erkundungsdiagnose, Reward-/Einheiten-Übergänge, neuer zurückgehaltener Testsatz für November sowie Folien und Vortragsvorbereitung. Mehrfachvergleiche und Modellauswahl auf bekannten Karten werden durch den Karten-Bootstrap nicht korrigiert. `scripts/report.py` bleibt die separate Zwei-Ebenen-Auswertung für Trainingsstarts.

## 14.10.2026 – Codex mit Moayed: vollständige Punktezählung

**Auftrag:** Punktezählung korrigieren, aktuelle Gewichte unverändert lassen und die Änderung für Mahmoud/Claude Code dokumentieren. Ausgangspunkt `9edac5f`, Umsetzung auf `fix/complete-point-counting`; geprüfte Änderung zur gemeinsamen Nutzung in `main` übernehmen.

**Ursache und Änderung:** LuxAI S3 zählt im letzten Matchschritt noch Punkte, setzt den sichtbaren Stand aber im selben Schritt auf null. Die bisherige Addition der sichtbaren Maxima unterschlug diesen Zuwachs. `scripts/scoring.py` rekonstruiert ihn aus dem nach der Aktion gespeicherten `info["final_state"]`: belegte aktive Punktefelder je Team, nur lebende Einheiten mit Energie ≥ 0, gestapelte Einheiten zählen einmal. `scripts/common.py` summiert vollständige Zuwächse; `analyze_losses.py` und `analyze_timing.py` melden ebenfalls vollständige Matchpunkte. Agentencode, Beobachtungen für den Agenten, Trainingsbelohnungen und Kurs-Runner bleiben unverändert.

**Datenformat und historische Ergebnisse:** Neue CSV-Zeilen tragen `point_counting_version=2`, auch in Training und Validierung. Ohne diese Spalte handelt es sich um historische Version 1; deren Punkte, Punktedifferenzen und Punkt-Siegquoten bleiben unvollständig. Alte Rohdateien nicht überschreiben oder mit Version 2 mischen. In neuen Diagnosen bedeutet −1 bei `first_score`, `opp_first_score` und `first_score_step` „nie gepunktet“; 101 bezeichnet den ersten Punkt im letzten Schritt. Die Kennzeichnung der Sichtbarkeitszeiten ändert sich nicht. Details und Migrationshinweise im [Experimentprotokoll](EXPERIMENT_PROTOKOLL.md#messkorrektur-vom-14102026-vollständige-punkte).

**Tatsächliche Prüfungen:**

- Sechs Regressionstests reproduzierten die Unterzählung auf beiden Seiten in gemeinsamer Spielauswertung und beiden Diagnoseskripten. Referenz: dieselbe echte Engine, derselbe Zustand, dieselben Aktionen und Zufallszahlen; nur der Reset wurde für den Referenzschritt verschoben, um die Endpunkte direkt zu lesen. Beispiel Seed 900011 gegen default als player_0: **1866:58 statt 1830:57**.
- Neue Prüfungen decken außerdem Stacking, Energie null/negativ, tote Einheiten, inaktive Relics, Nullpunkte, reine Schluss-Schritt-Punkte, Replay-Wrapper, fehlenden Endzustand und CSV-Versionskennzeichnung ab. Ein unabhängiger Review fand die Mehrdeutigkeit von 101 als „nie“ und als letzter Schritt; durch −1 und vier zusätzliche Diagnosefälle behoben und erneut geprüft.
- Abschließend **105 Tests bestanden in 28,71 Sekunden**, davon **17 neue Tests**. Der unabhängige Review meldet keine offenen Befunde.
- Alle **120 historischen Benchmarkspiele** des unveränderten Sechser-Ensembles neu gespielt (106,66 Sekunden). Jede bisherige Nicht-Punkte-Kennzahl je Spiel stimmt überein, Laufzeiten ausgenommen. Siege weiterhin **60/60 gegen default**, **28/60 gegen Solution_92**. Neue vollständige Daten: [CSV](../experiments/compare/TEST_old3_sym3_points_v2.csv), [Prüfsummen, Versionen und Wiederholungsanleitung](../experiments/compare/TEST_old3_sym3_points_v2.json). Mittlere Gesamtpunkte je Spiel: 1076,25:120,47 bzw. 741,52:883,25. Keine neuen Karten zur Modellauswahl verwendet.
- Beide Abgabe-Gewichte behalten SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`. Keine Änderungen unter `agents/` oder `lux/`, an `main.py`, `Paths.csv` oder historischen Experimentdateien. Kein neues Modelltraining außerhalb der bestehenden Tests mit temporären Dateien.

**Veröffentlichungsstand:** Nach Moayeds lokaler Entsperrung funktioniert SSH wieder. Erneuter Abruf bestätigte, dass auf GitHub keine zusätzlichen Änderungen seit `9edac5f` vorlagen. Die geprüfte Korrektur `03c5e3a` wurde erfolgreich ohne erzwungenes Überschreiben nach `origin/main` hochgeladen. Die frühere SSH-/GitHub-App-Blockade ist für diesen Upload damit erledigt; die lokale SSH-Konfiguration wurde nicht geändert.

**Für Mahmoud:** Jetzt die eigene Arbeitskopie von `main` aktualisieren und diesen Eintrag mit Claude Code lesen. Neue Läufe erhalten die korrekte Zählung automatisch. Für die Präsentation können die neuen Benchmarkdaten verwendet werden; alte Punktevergleiche anderer Modelle müssen mit den jeweiligen Originalgewichten in neue Dateien neu gemessen werden. README und Präsentationscheckliste sind angepasst.

**Weiterhin offen:** Bootstrap nach Karte in `compare_report`, zeitliche Ausrichtung der Erkundungsdiagnose, Reward-/Einheiten-Übergänge sowie Folien und Vortragsvorbereitung. Diese Korrektur verbessert die Messung, nicht die Spielstärke, und hebt die übrigen Einschränkungen nicht auf.

## 14.10.2026 – Codex mit Moayed: Überschreibschutz in main übernommen

**Auftrag:** Den geprüften Überschreibschutz in `main` übernehmen, damit Mahmoud ihn direkt nutzen kann; aktuelle Gewichte unverändert lassen.

**Übernahme:** Nach erfolgreichem Abruf von GitHub gab es keine zusätzlichen Änderungen auf `origin/main`. Commit `2038efd` wurde ohne Konflikte per Fast-forward in das lokale `main` übernommen. Dieser gemeinsame Stand ist für die Veröffentlichung auf GitHub vorgesehen; die folgende Git-Historie dokumentiert die Übernahme.

**Prüfung auf main:** Alle **88 Tests bestanden in 21,04 Sekunden**. Agentencode, Kurs-Runner, `main.py` und `Paths.csv` stimmen weiterhin mit dem Stand vor der Schutzänderung überein. Beide Abgabe-Gewichte behalten SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.

**Für Mahmoud:** Nach dem Upload genügt es, die eigene Arbeitskopie von `main` zu aktualisieren; ein Wechsel auf den Entwicklungsbranch ist nicht mehr nötig. Die Anleitung steht in [README: Sicher trainieren und fortsetzen](../README.md#sicher-trainieren-und-fortsetzen). Die übrigen fachlichen Korrekturen bleiben offen und sind weiterhin nicht beauftragt.

## 14.10.2026 – Codex mit Moayed: Abgabe-Gewichte beim Weiterarbeiten schützen

**Auftrag und Umfang:** Überschreiben der aktuellen Abgabe-Gewichte verhindern; Lernverfahren und trainierte Gewichte erhalten. Arbeit auf `fix/protect-submission-weights`, ausgehend von `c831ab3`.

**Änderungen:**

- `scripts.train` erzeugt pro Aufruf einen neuen Run-Ordner unter `experiments/runs/`; alternativ `--output-dir` mit einem noch nicht vorhandenen Ordner. Laufprotokoll, beide Gewichte, Bestmodell und Self-Play-Schnappschüsse liegen gemeinsam dort, auch beim Abbruch.
- `--resume` braucht jetzt einen expliziten Einzelnetz-Checkpoint. Seine gespeicherte Konfiguration wird übernommen; die Quelldatei wird nicht geändert. Der Replay Buffer wird nicht geladen. Ensembles werden abgewiesen, statt still nur deren erstes Mitglied weiterzutrainieren.
- Gemeinsame Prüfung der Ausgabeziele gegen den Abgabe-Gewichteordner, einschließlich symbolischer Links und Hardlinks.
- Beim Prüfen der Speicherwege fiel zusätzlich auf: `build_submission --from-run` ersetzte bisher die Abgabe-Dateien, bei fehlender zweiter Datei sogar teilweise. Es verpackt die ausgewählten Run-Gewichte jetzt direkt. Eingabe-Checkpoints dürfen nicht als ZIP-Ausgabe überschrieben werden.
- README und CLAUDE.md beschreiben die neuen Aufrufe und die Grenzen des Schutzes. Agentencode und Kurs-Runner bleiben unverändert; deren direkte Speicheraufrufe sowie andere Skripte sind keine allgemein gesperrten Dateioperationen. Für Vorführungen `main.py` weiterhin mit `train=False` nutzen.

**Prüfung:**

- 62 bestehende Tests vor der Änderung bestanden. Die erste Gruppe von 16 Regressionstests schlug mit dem alten Code fehl und bestand nach der Korrektur. Der unabhängige Review deckte zusätzlich verschachtelte Hardlinks, Groß-/Kleinschreibungs-Aliase auf macOS und inkompatible Resume-Checkpoints auf; auch diese Fehler wurden erst reproduziert und dann behoben.
- Abschließend **88 Tests bestanden in 21,90 Sekunden**, davon **26 neue Schutztests**. Darunter echte Trainings-/Evaluationsspiele mit kleinem Einzelnetz in temporären Ordnern, Self-Play-/Bestmodell-Speicherung, Abbruch-/Fehler-Speicherung, fehlende oder inkompatible Checkpoints, Ensemble-Ablehnung und Paketbau. Der Reviewer prüfte die Korrekturen nochmals unabhängig; keine offenen blockierenden Befunde.
- Das Standardpaket und ein Paket mit `--from-run` wurden separat gebaut, entpackt und auf beiden Seiten mit dem echten Sechser-Ensemble geladen und auf einer Beobachtung ausgeführt. ZIP-Inhalte, verwendete Quellgewichte und Abgabe-Gewichte per SHA-256 verglichen; unverändert.
- Beide Abgabe-Dateien behalten SHA-256 `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`. Keine Änderungen unter `agents/` oder `lux/`, an `main.py` oder `Paths.csv`. Diff-Prüfung ohne Befund.

**Für Mahmoud:** Ursprünglich auf dem separaten Branch `fix/protect-submission-weights` bereitgestellt; inzwischen auf ausdrücklichen Auftrag in `main` übernommen, siehe neuesten Eintrag oben. Neue CLI-Beispiele stehen in [README: Sicher trainieren und fortsetzen](../README.md#sicher-trainieren-und-fortsetzen). Ein alter Aufruf mit bloßem `--resume` muss einen Dateipfad zu einem passenden Sherlock-Einzelnetz-Checkpoint mit Config erhalten. Das aktuelle Sechser-Ensemble bleibt für die Präsentation unverändert. Die Messfehler und Reward-/Einheiten-Probleme aus der ursprünglichen Prüfung sind durch diesen Speicherschutz nicht behoben. Ein längerer Trainingslauf wurde nicht gestartet.

## 14.10.2026 – Codex mit Moayed: SSH-Zugriff und Veröffentlichung

**Auftrag:** Vorbereitete Dokumentationsänderungen auf GitHub hochladen, damit Mahmoud sie in seiner Arbeitskopie mit Claude Code verwenden kann. Agent, Trainingsskripte und Gewichte weiterhin nicht verändern.

**Zugriff eingerichtet und geprüft:** GitHub akzeptiert Moayeds bereits vorhandenen RSA-Schlüssel für den Account `ShaweshMoayed`. Die lokale Git-Konfiguration dieses Repositorys wählt diesen Schlüssel ausdrücklich aus; keine neuen Schlüssel und keine globalen SSH-Einstellungen angelegt. Die lokale Schlüsselkonfiguration wird nicht mit Git übertragen und ist auf Mahmouds Rechner nicht erforderlich.

**Synchronisierung:** `git fetch origin` erfolgreich. Vor der Veröffentlichung stimmen lokales `main` und `origin/main` auf Commit `40f236c7b418a3c9da407cd3129a760a7b5678cd` überein; keine fremden Änderungen zusammenzuführen. Der Veröffentlichungsumfang besteht aus genau fünf Dokumentationsdateien: AGENTS.md, CLAUDE.md, README.md, diesem Arbeitsstand und der Review-Checkliste. Der konkrete Commit und sein Upload werden über die Git-Historie nachvollziehbar.

**Übergabe:** Nach dem Upload kann Mahmoud sein `main` aktualisieren und Claude Code den neuesten Eintrag dieses Arbeitsstands lesen lassen. Die frühere SSH-Blockade und die damalige Einschränkung auf rein lokale Dokumentation sind damit überholt. Die offenen fachlichen Aufgaben unten bleiben unverändert; ihre Umsetzung ist noch nicht beauftragt.

## 14.10.2026 – Codex mit Moayed: gemeinsame Dokumentation

**Freigegebener Umfang:** Gemeinsame Dokumentation einrichten, README und Review-Checkliste aktualisieren. Agentencode, Trainingsskripte und Gewichte bleiben unverändert. Weitergehende Fehlerbehebungen und Experimente sind noch nicht beauftragt.

**Änderungen und Grund:**

- AGENTS.md verweist für Codex auf die gemeinsame CLAUDE.md und dieses Übergabeprotokoll. CLAUDE.md enthält dieselbe Dokumentationsregel für Claude Code.
- README beschreibt den aktuellen Abgabe-Agenten `old3_sym3` (sechs Netze), trennt seine Ergebnisse vom historischen Einzelnetz-Batch und benennt bekannte Grenzen der Auswertung.
- Review-Checkliste trennt belegte Projektinhalte von noch zu prüfenden Folien und Vortragsvorbereitung.
- Erste Präsentation am 16.10.: ungefähr zehn Minuten Vortrag laut Moodle-Aufgabe „Submission 1“, Upload bis 08:00 Uhr. Laut Moayed sind die Slots 20 Minuten lang. Die Aufteilung der restlichen Zeit für Fragen/Puffer ist eine Vermutung; auch die genaue Vortragsdauer späterer Termine ist noch zu bestätigen.

**Prüfgrundlage und Nachweise:**

- Lokaler Ausgangsstand: Commit `40f236c7b418a3c9da407cd3129a760a7b5678cd`. Alle 587 versionierten Dateien waren vor dieser Änderung identisch mit der bereits geprüften Projekt-ZIP.
- Frühere technische Prüfung vom 14.10. in separater Kopie: 62 Tests bestanden, 120 Spiele des Abgabe-Ensembles reproduziert, Paket auf beiden Seiten geladen und über den Kurs-Runner gespielt. Das sind keine im Rahmen dieser Dokumentationsänderung neu ausgeführten Tests.
- Ausführlicher Prüfbericht und Rohbelege liegen bei Moayed lokal im benachbarten Ordner `Pruefung_2026-10-14/`; sie sind nicht Bestandteil dieses Repositorys. Die wichtigsten offenen Befunde stehen unten, damit die Übergabe nicht von diesem Ordner abhängt.
- Prüfung dieser Dokumentationsänderung: `git diff --check` ohne Befund; alle relativen Dateilinks der fünf bearbeiteten/neuen Dokumente auf vorhandene Ziele geprüft. Aktuelle Ergebniszahlen direkt mit der CSV (60/60 und 28/60) und Trainingsumfang mit allen 34 Manifesten (99.000 Spiele) abgeglichen. Alle 584 übrigen Originaldateien sind bytegleich mit der geprüften ZIP, einschließlich Agent, Skripten, Gewichten und Experimentdaten. Keine neuen Trainingsläufe oder Spieltests für diese reine Dokumentationsänderung ausgeführt.

**Offene Punkte, keine bereits umgesetzten Korrekturen:**

1. Präsentationsdatei erstellen/exportieren, Inhalte gegen die Checkliste prüfen, Slot/Buchung bestätigen, Replays im Viewer ansehen und auf etwa zehn Minuten proben. Frühere Notizen erwähnen einen externen Folienentwurf; dessen aktueller Export liegt nicht im Repository.
2. Historischer Befund: `scripts/train.py` überschrieb die Abgabe-Gewichte und trainierte bei Ensembles nur ein Mitglied. Für dieses Skript durch neue Run-Ordner und Ablehnung von Ensemble-Resume behoben; siehe neuesten Eintrag. Ein gemeinsames Ensemble-Training bleibt unimplementiert.
3. Historischer Befund: Der letzte Punktezuwachs vor dem Match-Reset fehlte. Für neue Messungen mit `point_counting_version=2` behoben; siehe neuen Eintrag oben. Historische Dateien ohne Versionsspalte bleiben unvollständig. Siegquoten aus `team_wins` sind nicht betroffen.
4. Historischer Befund: `scripts/compare_report.py` resampelte einzelne Spiele; durch den gepaarten Karten-Bootstrap am 14.10. behoben, siehe neuen Eintrag oben. Alte Intervalle nur nach Neuberechnung weiterverwenden. Alte Testkarten wurden mehrfach ausgewertet; für November einen neuen, bis zur finalen Entscheidung unangetasteten Testsatz festlegen. Bestehende historische Rohdaten nicht überschreiben.
5. Vor weiterem Training gezielt prüfen/korrigieren: wiederverwendete Einheiten-IDs bei Tod und Respawn, Punktebelohnung bei negativer Energie und terminales Potential beim Reward Shaping. Passende Regressionstests ergänzen.
6. `scripts/analyze_timing.py` vergleicht eigene Beobachtung vor dem Schritt mit gegnerischer Sicht danach. Genaue Zeitvergleiche benötigen denselben Beobachtungszeitpunkt.
7. `scripts/report.py` deckt den ursprünglichen Varianten-Batch ab, nicht automatisch alle späteren Ensemble-/Self-Play-Vergleiche. Historische Gewichte fehlen teilweise; neue Läufe sollten Modell-Hashes und Softwareversionen mitführen.
8. `m1_early` bleibt der dokumentierte Kandidat für nach dem Review. Aktuelle Abgabe bleibt `old3_sym3`.
9. Historischer Stand dieser ersten Prüfung: SSH-Zugriff scheiterte mit `Permission denied (publickey)`; Commit und Push waren noch nicht beauftragt. Durch den anschließenden Auftrag und die Schlüsselkonfiguration überholt, siehe neuesten Eintrag oben.
