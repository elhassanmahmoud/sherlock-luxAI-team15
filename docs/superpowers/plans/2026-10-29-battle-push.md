# Battle-Vorbereitung 29.10.–04.11.2026: Sherlock stärker und robuster machen

Auftrag Mahmoud (29.10.2026): „bis zum 4. Nov den Agent perfekt trainieren bis zum geht nicht mehr und vieles
ausprobieren“. Ausführung: Claude Code, autonom. Dieser Plan legt Testkarten und Hürden **vor** den
Messungen fest. Übernahme nur nach diesen Hürden (Freigabe vom 20.10. in `CLAUDE.md`), sonst bleibt V10.

## Ziel und Referenz

- Referenz **V10** = `experiments/releases/20261022_v10_baseline/agent_p0.pth`, SHA-256 `03cf8bdc…8c67`.
- Im Battle spielt Sherlock gegen Agents anderer Teams. Deshalb zählt die **Robustheit**, nicht nur Solution_92.
- Panel wie in der Liga-Studie (`scripts/league_gates.py`): Solution_92, `sol92_sq` (Sap im ganzen Quadrat),
  `sol92_weak` (zielt auf die schwächste Einheit), `old3_sym3` (unsere Abgabe vom 16.10.). Dazu default als
  Sicherheitsgegner. Robustheitsmittel R = mittlere Siegquote gegen die vier Panel-Gegner.

## Testkarten (absolute Env-Seeds, `par_eval --first` = Seed − 500000)

| Block | Seeds | Zweck |
|---|---|---|
| Dev A | 800000–800299 | Entwicklung, beliebig oft |
| Dev B | 801000–801299 | Gegenprobe für Dev-A-Sieger gegen Überanpassung, höchstens 6 Läufe |
| Auswahl 1 | 802000–802199 Panel + default, 802200–802399 direkt gegen V10 | einmal je Kandidatenbündel |
| Bestätigung 1 | 803000–803799 Panel + default, 804000–804399 direkt gegen V10 (800 Spiele) | einmal, höchstens ein Kandidat |
| Runde 2 | Auswahl 805000–805199 / direkt 805200–805399, Bestätigung 806000–806799 / direkt 807000–807399 | nur falls Runde 1 scheitert und Zeit bleibt |
| Reserve | 808000–809999 | unbenutzt bis auf Weiteres |

Trainingskarten bleiben unter 500000 (`protocol.train_seed`, `finetune.FT_SEED_BASE`).

## Hürden (unverändert aus `scripts/league_gates.py`)

- **Auswahl** (200 Karten, Punktschätzungen, höchstens ein Kandidat): R-Δ ≥ +1,5 pp, Solution_92-Δ ≥ −1,0 pp,
  default ≥ 99 %, direkt gegen V10 ≥ 50 %.
- **Bestätigung** (800 frische Karten, 400 frische Direktkarten = 800 Spiele): R-Δ ≥ +2 pp **und** untere
  95-%-Grenze > 0; Solution_92-Δ ≥ −0,5 pp **und** untere Grenze > −2,5 pp; default ≥ 99 % und Δ ≥ −1 pp;
  direkt gegen V10 untere 95-%-Grenze > 50 %.
- Gepaarter Karten-Bootstrap, 5000 Ziehungen, Seed 0. Bei unklarem Vorteil bleibt V10.

## Arbeitswege

1. **Fehlersuche (Hauptweg, so kam 78 → 90 %):** V10-Niederlagen auf Dev A gegen Solution_92 und `sol92_sq` mit
   dem wahren Spielzustand vergleichen (Mechanismen, Einzelbilder), Ursachen als neue Schalter (Standard aus)
   mit Tests beheben, auf Dev A messen, Bündel bilden.
2. **Nachtraining der 18 V3-Netze** (neu: bisher nie mit den V10-Regeln nachtrainiert):
   `scripts/finetune.py --variant full_rules_v10 --keep-final`, 1500 Spiele je Netz, Lernrate 1e-4,
   Gegner 35 % Solution_92, 25 % `sol92_sq`, 10 % `sol92_weak`, 20 % Pool (V10, `old3_sym3`), 5 % RushBot,
   5 % default; Seeds 10–27. Ensemble `ft18` (und Mischungen) mit V10-Config auf Dev A.
3. **Weitere Ideen** nach Befund, jeweils erst auf Dev A.

Jeder Weg schreibt nur in `experiments/runs/`, `experiments/ensembles/`, `experiments/compare/battle/`.
Die Abgabe-Dateien ändert nur eine Übernahme nach bestandener Bestätigung (`scripts/release_candidate.py`
bzw. gleiche Schritte: Sicherung mit Hash, Installation, Kurs-Runner, Bericht).

## Zeitplan

- Spätestens **04.11., 12:00** letzte Bestätigung starten; **04.11., 16:00** Entscheidung.
- Danach `python -m scripts.build_submission --battle`, Prüfung in der Original-Vorlage, Folie 11 der
  Präsentation aktualisieren, Mahmoud lädt am Abend hoch.

## Ressourcen

15 Kerne, 24 GB. Höchstens 6 Trainingsprozesse; Messungen mit 8 Workern, solange trainiert wird, sonst 12.

## Nachtrag 29.10.2026, 19:00 (vor den Messungen festgelegt)

- **Auswahl Runde 1** bekommt das Bündel `mix36` (V10 + ft18, 36 Netze), `ft2_18` (18 Netze nach Runde 2),
  `mix36b` (V10 + ft2_18) und `mix54` (V10 + ft18 + ft2_18), alle mit V10-Config. Jeder Kandidat läuft genau
  einmal auf 802000–802399; Wahl höchstens eines Kandidaten mit `scripts/league_gates.py` (größtes R-Δ unter
  den bestandenen). Nur der gewählte läuft danach auf dem Bestätigungsblock 803000–804399.
  Ablauf: `scripts/pipeline_battle_night.sh`, startet nach Ende von Runde 2 automatisch.
- **Runde 3 des Nachtrainings** (`scripts/pipeline_battle_ft3.sh`): +2000 Spiele je Netz ab dem Endstand von
  Runde 2, Kartenversatz 2000, gleicher Gegnermix; der Pool enthält zusätzlich `battle_mix36`.
  Ihre Kandidaten gehen frühestens in Runde 2 der Hürden (805000–807399).
- Wird in Runde 1 ein Kandidat übernommen, ist er in Runde 2 der Hürden die Referenz statt V10
  (`pipeline_battle_gate.sh` dann mit dieser Referenz und gleichem Direktduell gegen sie).
- Dateigröße: 36 Netze ≈ 24 MB (Zip ≈ 22 MB), 54 Netze ≈ 35 MB. Vor dem Upload die Moodle-Grenze prüfen.

## Nachtrag 29.10.2026, 21:00

- Befund vorher (Dev A, nur Entwicklung): Runde 2 machte dieselben 6 Netze nicht besser (`ft2_6` gegen `ft6`:
  `sol92_sq` −2,3 [−5,8; +1,0], Solution_92 −0,2). `mix36` gewinnt dagegen gegen die früheren RL-Abgaben V3/V7
  +3,5/+6,5 pp und direkt 58,0 % [52,7; 63,7] gegen V10.
- **Zweite Trainingslinie „RL-Liga“** (`scripts/pipeline_battle_ftrl.sh`): dieselben 18 V3-Quellnetze und
  Einstellungen wie Runde 1, 1500 Spiele je Netz, neue Trainingskarten (Kartenversatz 4000), Gegner Solution_92
  0,20, `sol92_sq` 0,20, `sol92_weak` 0,05, **Pool 0,50** (V10, `old3_sym3`, `battle_mix36`, V3- und V7-Abgabe),
  default 0,05. Ensemble `battle_ftrl18`. Kandidaten daraus (z. B. `mix36` + `ftrl18`) gehen frühestens in
  Runde 2 der Hürden.
- Runde 4 (`pipeline_battle_ftn.sh`, Pool 0,25) startet erst nach dem Ende von Runde 3, nicht schon nach Runde 2.

## Nachtrag 29.10.2026, 23:55 (vor den Messungen festgelegt)

- **Morgen-Screen** (`scripts/pipeline_battle_morning.sh`, je Kandidat `scripts/battle_screen.sh`), nur
  Entwicklung auf Dev A 800000–800299, keine Auswahl und keine Übernahme. Gegner: Solution_92, `sol92_sq`,
  V3- und V7-Abgabe, **zurückgehaltene RL-Gegner**, gegen die nie trainiert wurde (`league_nets6`: 6 Netze vom
  26.10. mit V10-Regeln; `threat6`: 6 Gefahr-Netze mit V3-Regeln), und direkt gegen V10. Gepaart gegen V10
  auf denselben Karten; Kennzahl ist das Mittel über die 6 Gegner ohne Direktduell.
- Ablauf: Sobald Runde 3 fertig ist, V10 und `mix36` gegen die zurückgehaltenen Gegner. Nach Ende der RL-Liga
  `mixrl36` (V10 + `ftrl18`) und `mixrl54` (V10 + `ft18` + `ftrl18`), beide mit V10-Config. 6 Worker neben
  Auswahl und Bestätigung.
- Was daraus folgt: Der beste Screen-Kandidat geht in Runde 2 der Hürden (805000–807399), falls er im Mittel
  über die 6 Gegner und direkt gegen V10 mindestens so gut ist wie `mix36`. Sonst gilt das Ergebnis der Runde 1.

## Nachtrag 30.10.2026, 01:50 (nach der Auswahl Runde 1, vor allen hier genannten Messungen festgelegt)

- Auswahl Runde 1 (802000–802399): gewählt `mix36b` (V10 + ft2_18), R +2,88 pp [+0,69; +5,06], Solution_92
  +4,0, direkt 55,5 %. `mix36` verfehlte R ≥ +1,5 um 0,06 pp. Die Bestätigung von `mix36b` (803000–804399) läuft.
- **Runde 4 der Hauptlinie entfällt**: Runde 2 machte dieselben Netze nicht besser, die Trainingskurven von
  Runde 3 sind flach. Ihr Kartenbereich (Kartenversatz 3000) geht an die v8-Linie.
- **Dritte Trainingslinie „v8-Linie“** (`scripts/pipeline_battle_ftv8.sh`): die 12 Netze `full_rules_v8` vom
  22.10. (Quellen von `v10nets12`, nie in einer Abgabe, keine zurückgehaltenen Gegner) unter allen V10-Regeln,
  1500 Spiele je Netz, Seeds 10–21, Kartenversatz 3000, Gegnermix der gestrichenen Runde 4 (Solution_92 0,30,
  `sol92_sq` 0,25, `sol92_weak` 0,10, Pool 0,25 mit V10, `old3_sym3`, `battle_mix36`, V3, V7; RushBot 0,05,
  default 0,05). Start nach Ende von Runde 3, 12 parallel. Grund: Die Gewinne kamen bisher aus der Mischung
  unterschiedlich trainierter Netze; die v8-Netze sind eine eigene Linie. Ungetunt brachten sie am 22.10.
  nichts (`v10mix30` ≈ V10).
- Kandidaten daraus, beide mit V10-Config: `mix30v8` (V10 + ftv8_12) und `mix48` (V10 + ft2_18 + ftv8_12).
  Screen wie im Nachtrag 23:55 (`battle_screen.sh`, Dev A). Zum Vergleich zusätzlich `mix36b`.
- **Vergleichsmaßstab ab jetzt `mix36b` statt `mix36`**: `mix36b` ist die Wahl der Auswahl Runde 1, `mix36`
  ist dort ausgeschieden. Festgelegt, bevor ein Screen von `mix36b`, `mixrl*`, `mix30v8` oder `mix48` vorliegt.
  Ein Screen-Kandidat kommt nur dann in Runde 2 der Hürden, wenn er im Mittel über die 6 Gegner und direkt
  gegen V10 mindestens so gut ist wie `mix36b`. Welche Kandidaten (höchstens 3) in die Auswahl Runde 2 gehen,
  wird in einem weiteren Nachtrag vor deren Start festgelegt.

## Nachtrag 30.10.2026, 03:23 (vor jeder Messung mit `ft3_18` festgelegt)

- Runde 3 ist um 03:15 fertig: `battle_ft3_18` (18 Netze, Endstand nach je +2000 Spielen, SHA-256
  c556cd6cb0161708). Die v8-Linie und der Morgen-Screen sind um 03:16 wie geplant gestartet.
- **Zusätzlicher Screen-Kandidat `mix36c`** = V10 + `ft3_18` mit V10-Config (36 Netze, SHA-256
  e8b0de223fee12f3). Screen wie im Nachtrag 23:55 (`battle_screen.sh`, Dev A, 6 Worker), über die
  Entwicklungs-Warteschlange erst nach dem Ende des Nachtablaufs, damit die Bestätigung nicht gebremst wird.
  Es gilt dieselbe Regel wie für die übrigen Screen-Kandidaten (Maßstab `mix36b`, höchstens 3 Kandidaten für
  die Auswahl Runde 2).
- Grund: In der Auswahl Runde 1 lag `mix36b` (V10 + Runde 2) vor `mix36` (V10 + Runde 1). Ob Runde 3 weiter
  hilft, zeigt der gepaarte Vergleich `mix36c` gegen `mix36b` auf denselben Dev-A-Karten. Keine Mischung aus
  `ft2_18` und `ft3_18`: Runde 3 setzt dieselben Netze fort, das bringt kaum neue Vielfalt.

## Nachtrag 30.10.2026, 04:09 (Regeln für Runde 2, bevor ein Screen von `mix36b`, `mix36c`, `mixrl*`, `mix30v8` oder `mix48` vorliegt)

- **Referenz in Runde 2:** `mix36b`, falls es die Bestätigung besteht und mit `scripts/release_candidate.py`
  übernommen ist; sonst weiter V10. Das Direktduell läuft immer gegen die Referenz (`pipeline_battle_gate.sh`
  bekommt dafür `REF`/`REFNAME`, `league_gates.py` die Option `--direct-opponent`; Änderung erst nach dem
  Ende der laufenden Bestätigung). Hürden unverändert (`scripts/league_gates.py`).
- `mix36b` selbst geht nicht in Runde 2. Scheitert es in der Bestätigung, wird es nicht auf neuen Karten
  wiederholt.
- **Zulassung zur Auswahl Runde 2** (Dev-A-Screen, `scripts/screen_table.py`): Mittel über die 6 Gegner und
  Direktduell gegen V10 jeweils mindestens so hoch wie bei `mix36b` (Punktschätzungen). Erfüllen mehr als 3
  Kandidaten das, gehen die 3 mit dem höchsten Mittel über die 6 Gegner. Erfüllt keiner das, startet Runde 2
  nicht mit diesen Kandidaten.
- Ablauf: Auswahl 805000–805399 für jeden zugelassenen Kandidaten genau einmal, Wahl höchstens eines Kandidaten
  (größtes R-Δ unter den bestandenen), Bestätigung 806000–807399 nur für ihn.

## Nachtrag 30.10.2026, 05:45 (vierte Trainingslinie, bevor ein Screen von `mix36c`, `mixrl54`, `mix30v8` oder `mix48` vorliegt)

- Die Bestätigung von `mix36b` ist nicht bestanden (R +1,77 pp [+0,64; +2,95], Hürde +2 pp). Referenz in Runde 2
  bleibt V10, wie im Nachtrag 04:09 vorgesehen.
- **Linie 4 „Altnetze“** (`scripts/pipeline_battle_ftold.sh`): 12 Quellnetze, die nie in einer Abgabe waren und
  keine zurückgehaltenen Gegner sind: `20261022_full_rules_v6_s{27,28,29,37,38,39}_sol70` (V6-Regeln, je 3.000
  Spiele) und `20261020_full_rules_fo_s{30..35}_sol70` (`far_opp`-Regeln, je 4.000 Spiele). Grund: Die Gewinne
  kamen bisher aus der Mischung unterschiedlich trainierter Netze; diese Netze haben eigene Initialisierungen
  und eigene Trainingsregeln.
- Einstellungen wie die v8-Linie (alle V10-Regeln, je 1.500 Spiele, derselbe Gegnermix und Pool). Seeds 0–5
  (v6) und 6–9, 28, 29 (fo), Kartenversatz 0. Start automatisch nach dem Ende der v8-Linie, 12 parallel.
- Danach `battle_ftold12` und `mix30old` (V10 + ftold12) mit V10-Config, Dev-A-Screen mit
  `scripts/battle_screen.sh`.
- Kandidaten für eine Runde 3 (Seeds 808000–809599, `pipeline_battle_gate.sh` Runde 3, dieselben Hürden)
  werden in einem eigenen Nachtrag festgelegt, bevor Runde 3 startet.

## Nachtrag 30.10.2026, 08:13 (Regel `art_splash` für Runde 2, vor jeder Messung auf 805000–807399 und vor den Ergebnissen der Gegenproben)

- Neue Regel `art_splash`: Ist der Sap-Streufaktor laut `param_est` sicher 1,0, sappt die Artillerie schon ab
  2 Treffern und auch in gegnerischer Reichweite. Dev B (801000–801299): +0,8 pp [+0,2; +1,3] gegen
  Solution_92/`sol92_sq`, bei Streufaktor 1,0 +3,1 [+1,0; +5,5], sonst unverändert (Arbeitsstand 30.10., 07:55).
  `art_low_off` brachte auf denselben Spielen nichts zusätzlich (±0,0) und entfällt.
- **Regelsatz R** = `art_splash=true`. `sap_still_splash=true` kommt dazu, wenn `art_splash` + `sap_still_splash`
  auf denselben 1.200 Dev-B-Spielen mindestens +0,5 pp über `art_splash` allein liegt (Punktschätzung) und bei
  Streufaktor 1,0 nicht darunter.
- **R geht in die Runde-2-Kandidaten**, wenn beide Gegenproben halten (Punktschätzungen, gepaart):
  1. V10 + R auf Dev B gegen `sol92_weak`, `old3_sym3` und default je höchstens 1 pp unter V10. Kommt
     `sap_still_splash` dazu, gilt das für den ganzen Regelsatz (eigener Lauf).
  2. `mix36` + `art_splash` auf Dev B gegen Solution_92/`sol92_sq` nicht unter `mix36` (`DB_mix36.csv`;
     Stellvertreter für die Mischungen, weil dort schon eine Dev-B-Basis existiert).
- Dann laufen in Runde 2 statt der zugelassenen Mischungen dieselben Mischungen mit eingebranntem R
  (`scripts.set_cfg`, Dateien `experiments/ensembles/battle_<name>_as.pth`, Netze und übrige Config bitgleich).
  Zulassung (aus den Screens ohne R), Auswahl, Wahl und Bestätigung wie im Nachtrag 04:09. Referenz bleibt V10
  ohne R, Hürden unverändert.
- Hält eine Gegenprobe nicht, läuft Runde 2 mit den zugelassenen Mischungen ohne R wie im Nachtrag 04:09.
- Grund: Ein Kandidat, der in einer Runde scheitert, wird nicht mit kleinen Änderungen auf neuen Karten
  wiederholt. Die Regel greift nur bei sicher geschätztem Streufaktor 1,0, deshalb geht die bessere Fassung
  gleich in Runde 2.
- Der Code mit den neuen Schaltern (Standard aus, V10 unverändert) kommt nach den laufenden Screens und vor
  Runde 2 in den Hauptstand. Der Gate-Log hält den Commit fest.

## Nachtrag 30.10.2026, 10:35 (Ausführung der Nachträge 04:09 und 08:13, vor jeder Messung auf 805000–807399)

- Alle Screens fertig (10:28, `python -m scripts.screen_table`). Zulassung nach 04:09 (`--admit`, mechanisch):
  **`mix36c`, `mix48`, `mixrl54`** (Mittel über 6 Gegner 77,8 / 77,1 / 76,3 %, direkt gegen V10 61,7 / 63,7 /
  62,3 %; Maßstab `mix36b` 76,2 / 59,5 %). Nicht zugelassen: `mixrl36` (76,1 / 59,3) und `mix30v8` (76,8 / 55,7).
- Beide Gegenproben aus 08:13 halten (Arbeitsstand 30.10., 09:45), R = `art_splash` + `sap_still_splash`.
  Code im Hauptstand seit Commit `f34f9c4` (Schalter Standard aus).
- **Kandidaten Runde 2** (Netze bitgleich mit den Screens, Config der Mischung + R, `scripts.set_cfg`):
  - `mix36c_as` = `experiments/ensembles/battle_mix36c_as.pth`, SHA-256 `2ab463e9034357a40cb721b34286ad1f9bad250629bf9f9f17b1d175157cd2e0`
  - `mix48_as` = `experiments/ensembles/battle_mix48_as.pth`, SHA-256 `088b0280aba348bdf30d6364fc67a0eb4a5d2d5ad506ed0f7f125c00c7d89324`
  - `mixrl54_as` = `experiments/ensembles/battle_mixrl54_as.pth`, SHA-256 `e0970b37b9a008509b715befd3af98e4ab5f8149f772a573c705d1f42cd0f712`
- Start mit `WORKERS=9 bash scripts/pipeline_battle_round.sh 2 mix36c_as mix48_as mixrl54_as`: Auswahl je Kandidat
  auf 805000–805399, Wahl höchstens eines Kandidaten (größtes R-Δ unter den bestandenen), Bestätigung auf
  806000–807399 nur für ihn. Referenz V10, Hürden unverändert (`scripts/league_gates.py`).

## Nachtrag 30.10.2026, 14:21 (Runde 4 der Hauptlinie und Regeln für Runde 3, vor jeder Messung mit `ft4_18`)

- Seit 13:36 ist V11 (`v11_mix36c_as`) die Abgabe. **Referenz für Runde 3 ist V11**: feste Kopie
  `experiments/releases/20261030_v11_baseline/agent_p0.pth` (bytegleich mit der Abgabe, SHA-256 `2ab463e9…cd2e0`).
  Das Direktduell läuft gegen V11.
- **Runde 4 der Hauptlinie** (`scripts/pipeline_battle_ft4.sh`): die 18 Netze von `ft3_18` je weitere 2.000 Spiele
  (Gewichte und Buffer aus Runde 3), Kartenversatz 3000, Gegnermix wie in den Runden 1–3, Pool V10 + old3 + V11.
  Danach `battle_ft4_18` und die Kandidaten `mix36d_as` (V10 + ft4_18) und `mix54d_as` (V10 + ft3_18 + ft4_18),
  beide mit eingebranntem R (`art_splash` + `sap_still_splash`).
- **Zulassung zu Runde 3** (Dev A 800000–800299, gepaart gegen V11 auf denselben Karten): Screen gegen die 6 Gegner
  wie `scripts/battle_screen.sh` und zusätzlich ein Direktduell gegen V11 auf Dev A. Zugelassen ist, wer im Mittel
  über die 6 Gegner mindestens +1,0 pp über V11 liegt und das Direktduell gegen V11 mit mindestens 52 % gewinnt
  (Punktschätzungen). Erfüllen das beide, geht der mit dem höheren Mittel. Erfüllt es keiner, gibt es keine Runde 3
  mit diesen Kandidaten.
- **Runde 3:** Auswahl 808000–808199 (direkt 808200–808399), Bestätigung 808400–809199 (direkt 809200–809599), nur
  für den zugelassenen Kandidaten. Hürden unverändert (`scripts/league_gates.py`), Referenz V11, Direktduell gegen
  V11 (`league_gates --direct-opponent`, `pipeline_battle_gate.sh` mit `REF`/`REFNAME`; Werkzeuge vor Runde 3 mit
  Tests).
- Ohne bestandene Bestätigung keine Übernahme. Bei unklarem Vorteil bleibt V11.

## Nachtrag 30.10.2026, 18:31 (nach der Zulassung zu Runde 3, vor jeder Messung mit `ft5_18` oder neuen Regeln auf V11)

- **Zulassung zu Runde 3 nach Nachtrag 14:21: keiner zugelassen** (`mix36d_as` Mittel über 6 Gegner +0,81 pp über
  V11, direkt gegen V11 48,3 %; `mix54d_as` −0,61 pp, direkt 57,7 %). Der Block 808000–809599 bleibt unbenutzt.
- **Runde 5 der Hauptlinie** (`scripts/pipeline_battle_ft5.sh`): die 18 Netze von `ft4_18` je weitere 2.000 Spiele
  (Gewichte und Buffer aus Runde 4), Kartenversatz 4000, Gegnermix und Pool wie in Runde 4, 6 parallel. Danach
  `battle_ft5_18` und die Kandidaten `mix36e_as` (V10 + ft5_18) und `mix54e_as` (V10 + ft3_18 + ft5_18), beide mit R.
- **Entwicklung auf V11** (nur Dev A 800000–800299; `REF=V11 bash scripts/battle_dev.sh`, gepaart gegen die
  V11-Spiele derselben Karten): frühere Schalter erneut auf V11 (seit 18:27 in der Warteschlange: `stage_attack`, `art_safe_cheb`, `dodge_auto`,
  `holder_guard`, `cand_rescue`, `window_infer`, `relic_scout=1`) und neue Schalter (zuerst ein Gegnermodell, das die
  Sap-Form des Gegners, Raute oder Quadrat, im Spiel erkennt). Neue Schalter Standard aus, mit Tests.
- **Zulassung zu Runde 3 unverändert wie 14:21** für jeden Kandidaten, auch Regelbündel auf den V11-Netzen:
  Dev-A-Screen über die 6 Gegner mindestens +1,0 pp über V11 und Direktduell gegen V11 auf Dev A mindestens 52 %
  (Punktschätzungen). Bei mehreren zugelassenen der mit dem höheren Mittel.
- **Neuer Block Runde 4** (falls Runde 3 benutzt ist und ein weiterer Kandidat die Zulassung schafft): Auswahl
  810000–810199 (direkt 810200–810399), Bestätigung 810400–811199 (direkt 811200–811599). Geprüft: Keine CSV unter
  `experiments/compare/` enthält Seeds 810000–819999; Trainingskarten liegen unter 500000. Hürden unverändert,
  Referenz V11.
- Zeitplan unverändert: letzte Bestätigung spätestens 04.11., 12:00 starten. Ohne bestandene Bestätigung bleibt V11.

## Nachtrag 30.10.2026, 23:01 (Battle-Bestätigung, vor jeder Messung auf 810000–811599)

- **Zulassung `v11e`** (Dev A, gepaart gegen V11): Mittel über 6 Gegner +0,89 pp, direkt gegen V11 54,0 % → nicht
  zugelassen. Nach Streufaktor: Ausweichen bei 0,25 im Mittel ±0, direkt 47,4 %; Halbstreuung bei 0,5 +2,6, direkt 64,6 %.
- **`V11_halfsafe`** = V11 + `splash_min_drop=0.5` + `splash_safe_below=1.0` (R auch bei sicher geschätztem
  Streufaktor 0,5, Artillerie behält dort die Sicherheitsprüfung), Dev A gegen V11: Solution_92 +0,33, `sol92_sq` +2,17,
  V3 +0,67, V7 −0,67, `league_nets6` +4,00, `threat6` ±0; **Mittel 6 +1,08 pp [−0,08; +2,39]**, **direkt gegen V11
  55,5 % [52,8; 58,3]** → nach der Regel von 14:21/18:31 zugelassen. Ohne Sicherheitsprüfung (Messung vom Nachmittag)
  Mittel 6 +0,78, Solution_92 −0,50.
- **Kandidat `v11h`** = `experiments/ensembles/battle_v11h.pth`: Netze bytegleich mit V11, Config V11 + die beiden
  Schalter (SHA-256 `13c73cce…`), Code im Hauptstand seit `7c52545`.
- **Statt Runde 3 eine Battle-Bestätigung.** R misst nur die Solution_92-Familie und `old3_sym3`. Im Battle spielen aber
  RL-Agents anderer Teams, und der Gewinn von `v11h` entsteht vor allem gegen RL-Gegner (bei Streufaktor 0,5 gegen
  `league_nets6` +13). Gilt nur für diesen einen Kandidaten und nur einmal:
  - Karten: 810400–811199 gegen die 6 Gegner des Dev-A-Screens und default (V11 und `v11h`, je 800 Karten, beide
    Seiten), direkt gegen V11 auf 811200–811599 (800 Spiele). 810000–810399 und Runde 3 (808000–809599) bleiben unbenutzt.
  - Hürden (`scripts/league_gates.py battle`, gepaarter Karten-Bootstrap, 5000 Ziehungen, Seed 0): Mittel über die
    6 Gegner Δ ≥ +1 pp **und** untere 95-%-Grenze > 0; Solution_92 Δ ≥ −0,5 pp **und** untere Grenze > −2,5 pp;
    default ≥ 99 % und Δ ≥ −1 pp; direkt gegen V11 untere 95-%-Grenze > 50 %.
  - Ablauf `scripts/battle_confirm.sh v11h`. Runde 4 in `scripts/pipeline_battle_gate.sh` ist gesperrt.
- Bestanden → Übernahme als V12 mit `scripts/release_candidate.py` (Sicherung von V11, Kurs-Runner, Bericht), danach
  neues `Gruppe15.zip`. Nicht bestanden → V11 bleibt, kein weiterer Versuch auf diesem Block.
- **Runde 5 der Hauptlinie entfällt** (Runde 4 brachte im Ensemble nichts, Zeit bis 04.11.). Ebenso die Tests
  `V11_dropest` und `V11_rescue` (`cand_rescue` greift nur, wenn kein Punktefeld bekannt ist).

## Nachtrag 31.10.2026, 14:40 (Nebel-Sap `fog_v2` und letzte V12-Prüfung, vor jeder Messung mit `fog_v2` auf Dev A oder 808000–809599)

- **Befund** (Daten der verbrauchten Battle-Bestätigung, 810400–811199): V11 gewinnt bei Sensorreichweite 1 deutlich
  seltener, gegen Solution_92 87,9 % (Reichweite 3/4: 94,9/97,0 %), gegen V3 72,4 % (88,8/88,7 %), und sappt dort nur
  53 statt 89–100 Mal je Spiel. Funktionsprobe (V11 gegen Solution_92, 4 Karten mit Sicht 1 aus demselben verbrauchten
  Block): 97 % der gegnerischen Halter-Schritte sind für uns unsichtbar, je Spiel 28–343 Unit-Schritte mit
  unsichtbarem Halter in Sap-Reichweite (Energie ≥ Kosten + 30), dort nie ein Sap.
- **Ursache in der alten Regel `fog_sap`:** Mit `use_symmetry` gilt das Spiegelbild des Sensors in `belief.last_seen`
  als gesehen; die gegnerischen Punkte-Tiles sind das Spiegelbild unserer und fielen aus den Kandidaten. Neuer
  Schalter **`fog_v2`** (Standard aus, Tests `tests/test_fog_sap.py`, alle 594 Tests bestanden, 6 V11-Spiele
  identisch): echte Sicht, Kandidaten in beiden Hälften ohne eigene Unit, kein Nebel-Sap bei sichtbarem Ziel.
- **Screen:** `battle_v11fog` = V11 + `fog_sap` + `fog_v2` (sonst Standardwerte: nur Halter, Reserve 30, alle
  Sensorreichweiten) mit `scripts/battle_admit.sh` auf Dev A gegen V11 (6 Gegner, direkt 600 Spiele).
  **In V12 kommt `fog_v2`, wenn:** Mittel über 6 Gegner Δ ≥ +0,5 pp, direkt gegen V11 ≥ 50 %, Solution_92 Δ ≥ −1,0 pp
  (Punktschätzungen). Scheitert das nur an Karten mit Sicht ≥ 3, darf genau eine Variante mit
  `fog_sap_max_sensor=2` mit denselben Bedingungen geprüft werden.
- **V12** = `v11h` + die aufgenommene Nebel-Variante. Letzte Prüfung genau einmal, wie die Battle-Bestätigung vom
  30.10. (`league_gates battle`, Hürden unverändert): V11 und V12 auf 808000–808799 gegen die 6 Gegner und default,
  direkt gegen V11 auf 808800–809199 (800 Spiele). Spätester Start 03.11., 12:00. Bestanden → Übernahme mit
  `scripts/release_candidate.py` und neues `Gruppe15.zip`; nicht bestanden → V11 bleibt. Wird `fog_v2` nicht
  aufgenommen, entfällt die Prüfung (V11 bleibt; über `v11h` allein entscheidet nur das Team).

## Nachtrag 31.10.2026, 18:50 (Zielwahl des Nebel-Saps und V13-Prüfung, vor jeder Messung mit `fog_prior`/`fog_drop_est` auf Dev A oder 812000–813199)

- **Befund** (offline, nur vorhandene Gelegenheiten; `experiments/analysis/battle/v12_fog_hits.py` und `v12_fog_eval.py`):
  V12 auf Dev A gegen Solution_92, `sol92_sq` und `league_nets6` (1.800 Spiele, davon 1.728 mit Gelegenheiten,
  194.838 Gelegenheiten, 21.170 Nebel-Saps), bewertet mit den gegnerischen Positionen nach der Bewegung:
  - V12 (gleich gewichtet, Streufaktor fest 0,5): direkte Treffer 34,1 %, Schaden je Sap 40,0, netto +13 je Spiel.
  - Gewichte nach der letzten eigenen Beobachtung im laufenden Match (Gegner ×4, leer ×0,25, nie gesehen ×1):
    40,6 %, 44,9, netto +68.
  - Zusätzlich sicher geschätzter Streufaktor: 33,0 %, 46,5, netto +100 (Streufaktor 0,25: direkte Treffer 51,9 statt
    35,9 %; Streufaktor 1,0: 18,9 statt 12,3 Saps je Spiel).
  - Offline fehlen die Folgen im Spiel (Gegner weicht aus, Energie fehlt später). Deshalb entscheidet nur der Test.
- **Neue Schalter** (Standard aus): `fog_prior` (mit `fog_w_occ` 4,0 und `fog_w_empty` 0,25) und `fog_drop_est`. Der
  erste Entwurf setzte die Zeitstempel beim Matchwechsel nicht zurück (alte Beobachtungen wirkten frischer); behoben.
  3 neue Tests in `tests/test_fog_sap.py`, alle 601 Tests bestanden. V12 mit dem neuen Code: 16 Spiele auf
  808000–808003 (bereits verbraucht) in allen Kennzahlen identisch mit der Battle-Bestätigung.
- **Kandidaten** (Netze bytegleich mit V12, nur die Config weicht ab):
  - `v13p` = V12 + `fog_prior` (`experiments/ensembles/battle_v13p.pth`, SHA-256 `21087234…`);
  - `v13pd` = V12 + `fog_prior` + `fog_drop_est` (`battle_v13pd.pth`, SHA-256 `572f24b7…`).
- **Screen** (`bash scripts/battle_v13.sh admit v13p v13pd`): Dev A gegen die 6 Gegner, gepaart gegen V12 auf denselben
  Karten (V12-Basis einmalig), dazu direkt gegen V12 auf Dev A (600 Spiele). **Zugelassen** wird, wer im Mittel über
  die 6 Gegner Δ ≥ +0,5 pp, direkt gegen V12 ≥ 50 % und gegen Solution_92 Δ ≥ −1,0 pp erreicht (Punktschätzungen wie
  Nachtrag 14:40). Bei zwei zugelassenen der mit dem höheren Mittel.
- **Battle-Bestätigung** genau einmal und nur für den zugelassenen Kandidaten (`bash scripts/battle_v13.sh confirm
  NAME`): V12 und Kandidat auf **812000–812799** gegen die 6 Gegner und default (je Gegner 1.600 Spiele), direkt gegen
  V12 auf **812800–813199** (800 Spiele). Hürden unverändert `scripts/league_gates.py battle`: Mittel 6 Δ ≥ +1,0 pp
  und untere Grenze > 0, Solution_92 Δ ≥ −0,5 pp und untere Grenze > −2,5 pp, default ≥ 99 % und Δ ≥ −1 pp, direkt
  untere Grenze > 50 %. Geprüft: Keine CSV unter `experiments/` enthält Seeds 812000–813199; Trainingskarten liegen
  unter 500000.
- Bestanden → Übernahme als V13 mit `scripts/release_candidate.py` (V12 bytegleich gesichert), neues `Gruppe15.zip`,
  Kurs-Runner, Tests, Nachspielen unter Python 3.10. Kein Kandidat zugelassen oder Bestätigung nicht bestanden →
  **V12 bleibt**. Spätester Start der Bestätigung 03.11., 12:00.
- **Ergebnis (31.10., 19:59): kein Kandidat zugelassen.** `v13p` Mittel 6 Δ +0,08 pp [−0,53; +0,69], direkt 50,7 %;
  `v13pd` Δ +0,08 pp [−0,72; +0,89], direkt 50,2 %. Die Battle-Bestätigung entfällt, **812000–813199 bleiben
  unbenutzt**, V12 bleibt (Arbeitsstand 31.10., 20:05).

## Nachtrag 31.10.2026, 20:10 (Wie oft der Nebel-Sap schießt, vor jeder Messung mit `fog_reserve`/`fog_any` abweichend von V12)

- **Befund:** Die Zielwahl (`fog_prior`) brachte offline +6,5 pp direkte Treffer, im Spiel aber nur +0,08 pp (Nachtrag
  18:50, Ergebnis). Auch V12 selbst bringt offline netto nur +13 Energie je Spiel, im Spiel aber +5,9 pp gegenüber V11.
  Die Offline-Kennzahl sagt also wenig. **Hypothese:** Es zählt, dass und wie oft im Nebel geschossen wird. Offline
  (`v12_fog_eval_devA.txt`, auf R3) feuert der Nebel-Sap mit Reserve 0 45 statt 13 Mal je Spiel, mit `fog_any`
  17,7 Mal. Risiko: Halter mit wenig Energie sterben leichter durch gegnerische Saps, Kollisionen oder Nebel.
- **Kandidaten** (Netze bytegleich mit V12, nur ein Schalter weicht ab):
  - `v13r0` = V12 + `fog_reserve` 0 statt 30 (`experiments/ensembles/battle_v13r0.pth`, SHA-256 `98b9ba5c…`);
  - `v13r15` = V12 + `fog_reserve` 15 (`battle_v13r15.pth`, `a69a3056…`);
  - `v13any` = V12 + `fog_any` (Nebel-Sap für jede stehende Unit, nicht nur auf Punkte-Tiles; `battle_v13any.pth`,
    `d08a4936…`).
- **Screen und Zulassung** unverändert wie Nachtrag 18:50 (`bash scripts/battle_v13.sh admit v13r0 v13r15 v13any`):
  Dev A gegen die 6 Gegner, gepaart gegen die V12-Basis vom 31.10. (dieselben Dateien `D_v12*.csv`, der Code ist für
  nicht eingefrorene Gewichte unverändert), direkt gegen V12 600 Spiele. Zugelassen: Mittel 6 Δ ≥ +0,5 pp, direkt
  ≥ 50 %, Solution_92 Δ ≥ −1,0 pp; bei mehreren der mit dem höchsten Mittel.
- **Battle-Bestätigung** genau einmal für den zugelassenen Kandidaten auf dem im Nachtrag 18:50 reservierten, dort
  unbenutzten Block **812000–812799**, direkt **812800–813199** (`bash scripts/battle_v13.sh confirm NAME`), Hürden
  unverändert `scripts/league_gates.py battle`. Spätester Start 03.11., 12:00.
- Bestanden → Übernahme als V13 wie im Nachtrag 18:50 beschrieben (Sicherung von V12, neue Zip, Kurs-Runner, Tests,
  Nachspielen unter Python 3.10). Kein Kandidat zugelassen oder nicht bestanden → **V12 bleibt**, und an der
  Nebel-Sap-Menge wird vor dem Battle nicht weiter gedreht.
- **Ergebnis Screen (31.10., 21:40):** `v13r0` zugelassen (Mittel 6 Δ +0,94 pp [−0,08; +1,97], direkt 58,5 %
  [55,0; 61,8], Solution_92 +0,17); `v13r15` (+0,08, direkt 53,5 %) und `v13any` (+0,39, direkt 49,2 %) nicht.
  Battle-Bestätigung `v13r0` auf 812000–813199 gestartet 21:42.
- **Ergebnis Battle-Bestätigung (31.10., 23:46): nicht bestanden, V12 bleibt.** Mittel 6 Δ +0,45 pp [−0,24; +1,10]
  (Hürde +1,0 und untere Grenze > 0 verfehlt), Solution_92 Δ −0,75 [−1,69; +0,19] (Hürde −0,5 verfehlt), default
  ±0, direkt gegen V12 59,4 % [56,5; 62,3] aus 800 Spielen (bestanden).

## Nachtrag 31.10.2026, 22:05 (Restenergie am Matchende, vor jeder Messung mit `end_sap` auf Dev A oder 813200–814399)

- **Befund** (nur Zuschauen, `experiments/analysis/battle/v12_end_probe.py`, V12 auf Dev A 800000–800029, beide
  Seiten, gegen `league_nets6` und Solution_92, 120 Spiele): Die Engine entfernt am Matchende alle Units, Restenergie
  zählt nur bei Punktgleichstand. Bei Schritt 99 haben unsere Units im Mittel etwa 1.100 Energie je Match. In den
  letzten 10 Schritten gibt es je Match 14–20 Unit-Schritte mit Energie und sichtbarem Gegner in Reichweite ohne Sap.
  Verlorene Matches sind oft knapp (gegen `league_nets6` 14–21 % mit höchstens 5 Punkten), und 1.123 der 1.240
  Niederlagen der V12-Bestätigung endeten 1:2.
- **Neue Regel `end_sap`** (Standard aus): In den letzten `end_sap` Schritten eines Matches schießen Units auf
  sichtbare Gegner in Reichweite: zuerst auf Gegner auf bekannten Punkte-Tiles, dann auf im letzten Schritt
  unbewegte, dann auf alle übrigen, jeweils den mit der geringsten Restenergie nach den schon geplanten Saps (so
  verteilen mehrere Units ihr Feuer). Eigene Halter behalten eine Sap-Kosten Energie, außer im letzten Schritt. Units,
  die ein Punkte- oder Kandidaten-Tile noch rechtzeitig erreichen, laufen weiter. Tests `tests/test_end_sap.py`.
- **Basis** ist die Abgabe nach der laufenden Battle-Bestätigung: `v13r0`, wenn sie besteht, sonst V12. Für beide
  liegen die Dev-A-Dateien schon vor (`D_v13r0*.csv` bzw. `D_v12*.csv`, gleicher Code für nicht eingefrorene Gewichte).
- **Kandidaten** (Netze und Config der Basis, nur `end_sap` gesetzt): `v14e10` (`end_sap` 10) und `v14e20` (20).
  Vor der Messung: ganze Testsuite im Projektordner, und die Basis spielt mit dem neuen Code (Schalter aus) in
  16 vorhandenen Spielen identisch.
- **Screen** `REF=<Basis> bash scripts/battle_v14.sh admit v14e10 v14e20`, Zulassung unverändert wie Nachtrag 18:50
  (Mittel 6 Δ ≥ +0,5 pp, direkt gegen die Basis ≥ 50 %, Solution_92 Δ ≥ −1,0 pp; bei zwei das höhere Mittel).
- **Battle-Bestätigung** genau einmal für den zugelassenen Kandidaten: `REF=<Basis> bash scripts/battle_v14.sh confirm
  NAME`, Basis und Kandidat auf **813200–813999** gegen die 6 Gegner und default, direkt gegen die Basis auf
  **814000–814399** (800 Spiele). Hürden unverändert `scripts/league_gates.py battle`. Vor dem Start prüfen, dass keine
  CSV diese Seeds enthält. Spätester Start 03.11., 12:00.
- Bestanden → Übernahme wie Nachtrag 18:50 (Sicherung der Basis, neue Zip, Kurs-Runner, Tests, Nachspielen unter
  Python 3.10). Nicht zugelassen oder nicht bestanden → die Basis bleibt. Danach keine weiteren Regeltests vor dem
  Battle (Absprache mit Mahmoud, 31.10. abends).
- **Ausführung (31.10., 23:54):** Basis **V12**, da `v13r0` nicht bestanden hat. Vorher ganze Testsuite (609
  bestanden) und V12 mit dem neuen Code in 16 Spielen auf 812000–812003 identisch mit der Battle-Bestätigung.
  Kandidaten `battle_v14e10.pth` (SHA-256 `57d50b21…`) und `battle_v14e20.pth` (`16600f07…`), sonst bytegleich mit
  V12. Screen `REF=v12 bash scripts/battle_v14.sh admit v14e10 v14e20` gestartet.
- **Ergebnis Screen (01.11., 00:44): kein Kandidat zugelassen, V12 bleibt.** `v14e10` Mittel 6 Δ +1,11 pp [+0,22;
  +2,00], Solution_92 −0,33, aber direkt gegen V12 nur 45,7 % [40,8; 50,5] (Hürde ≥ 50 %); `v14e20` Mittel 6
  +0,14 [−1,03; +1,31], Solution_92 −0,33, direkt 54,0 %. Keine Battle-Bestätigung; 813200–814399 bleiben unbenutzt.
  Wie vereinbart keine weiteren Regeltests vor dem Battle.

## Nachtrag 01.11.2026, 02:20 (Nebel-Korrekturen, vor jeder Messung mit `est_censor`/`neb_cross` auf Dev A oder 813200–814399)

- **Auftrag Mahmoud (01.11., gegen 1 Uhr):** neue Regeln bauen und testen, „alles was geht“, Ziel Platz 1 gegen alle
  Agenten im Kurs. Die Absprache „keine weiteren Regeltests vor dem Battle“ (Nachtrag 22:05) ist damit aufgehoben.
- **Befund** (nur Zuschauen auf verbrauchten Karten): V12 verliert gegen Solution_92 auf 812584 beide Seiten
  (272:1112, 259:1074). Karte mit Nebelabzug 25 und Bewegungskosten 5.
  - Die Schätzung des Nebelabzugs (`param_est`) kippt in Match 1 bei Schritt 33 von 25 auf 0, die Nebel-Meidung ist
    danach für das ganze Spiel aus.
  - Ursache: Die Engine kappt die Energie nach Feld und Nebel bei 0 (`luxai_s3/env.py`, `clip(..., min_unit_energy=0, ...)`).
    Eine Unit mit 0 Energie auf einem Nebel-Tile mit Feldenergie 0 zeigt „Verlust 0“. Das zählt als Beleg für
    Abzug 0, und jeder weitere Schritt verstärkt es.
  - In Match 2 stehen 3 von 4 verfolgten Units mit 0 Energie im Nebel fest (16:629 Punkte). Schon vorher gingen Units
    mit pauschal 2 × Abzug Energie in breite Nebel und blieben darin stecken.
- **Neue Schalter** (Standard aus, Tests `tests/test_nebula_fix.py`):
  - `est_censor`: Beobachtungen mit Energie 0 wertet die Parameterschätzung nicht aus, auch beim Streufaktor.
  - `neb_cross`: Nebel nur mit Energie für die ganze Durchquerung betreten, also k Nebel-Tiles auf dem kürzesten Weg
    × (Zugkosten + Abzug) + ein Zug hinaus. Ist das Ziel ein Punkte-Tile im Nebel, genügt es, das Ziel zu erreichen.
    Sonst Energie sammeln; im Nebel den nächsten Ausgang nehmen.
- **Rauchtest** (812584, kein Gate, Karte verbraucht): Mit beiden Schaltern gewinnt V12 beide Seiten (994:342,
  825:337).
- **Kandidaten** (Netze und Config von V12, nur die Schalter gesetzt): `v15c` (`est_censor`) und `v15cx`
  (`est_censor` + `neb_cross`).
- **Vor der Messung:** ganze Testsuite; V12 spielt mit dem neuen Code (Schalter aus) 16 vorhandene Spiele identisch.
- **Screen:** `REF=v12 bash scripts/battle_v14.sh admit v15c v15cx`. Zulassung unverändert: Mittel 6 Δ ≥ +0,5 pp,
  direkt gegen V12 ≥ 50 %, Solution_92 Δ ≥ −1,0 pp; bei zwei der mit dem höheren Mittel.
- **Battle-Bestätigung** genau einmal für den zugelassenen Kandidaten: `REF=v12 bash scripts/battle_v14.sh confirm
  NAME` auf **813200–813999**, direkt **814000–814399** (um 23:58 und 01.11., 00:46 unbenutzt), Hürden unverändert
  `scripts/league_gates.py battle`. Spätester Start 03.11., 12:00.
- **Bestanden** → Übernahme wie Nachtrag 18:50 (Sicherung von V12, neue Zip, Kurs-Runner, Tests, Nachspielen unter
  Python 3.10). **Nicht zugelassen oder nicht bestanden** → V12 bleibt.
- Weitere Kandidaten nur mit eigenem Nachtrag vor ihrer Messung. Höchstens eine weitere Battle-Bestätigung, auf
  814400–815199 und direkt 815200–815599.
- **Ergebnis Screen (01.11., 03:21): kein Kandidat zugelassen.** `v15c` Mittel 6 Δ +0,08 pp [−0,36; +0,53], direkt
  49,8 %. `v15cx` Mittel 6 Δ +0,42 [−0,36; +1,28], Solution_92 +0,33, direkt 51,5 %; die Hürde +0,5 ist knapp
  verfehlt. Die Wirkung liegt fast ganz auf Karten mit Nebelabzug 25: dort `v15cx` 88,39 statt 85,71 % (+2,68 pp,
  672 Spiele, 84 von 87 veränderten Ergebnissen); auf allen anderen Karten ist es praktisch gleich.

## Nachtrag 01.11.2026, 03:25 (Regel `no_strand`, vor jeder Messung mit `no_strand` auf Dev A oder 813200–814399)

- **Befund** (verbrauchte Karte 812256, Bewegungskosten 4, Sicht 1, V12 gegen Solution_92 0:3, Match 2 1:297):
  - Die Relics liegen in der Ecke unten links, 20 Felder vom eigenen Start; unser Gedächtnis findet sie nie.
  - Units, die dorthin erkunden sollen (Ziele (0, 21), (0, 19), (4, 23)), bleiben 3–5 Felder davor mit 0 Energie auf
    Feldern ohne Energiegewinn liegen, bis zum Matchende. Die Engine kappt die Energie bei 0.
  - Zeitweise haben 11 von 15 Units kein Ziel mehr, weil die übrigen Erkundungsziele vergeben sind.
- **Neue Regel `no_strand`** (Standard aus, Tests `tests/test_no_strand.py`): kein Zug mit der letzten Zugenergie
  (Energie danach < Zugkosten) auf ein Feld ohne Energiegewinn (Feld minus geschätzter Nebelabzug ≤ 0). Ausnahmen
  sind Punkte- und Kandidaten-Tiles. Stattdessen sammelt die Unit Energie: stehen bleiben, oder auf das beste
  Nachbarfeld mit Gewinn.
- **Rauchtest** (verbrauchte, gezielt ausgewählte Niederlagen 812256, 812584, 812036, 812229, beide Seiten gegen
  Solution_92, kein Gate): V12 2/8 Siege, mit `no_strand` 3/8, mit `est_censor` + `neb_cross` + `no_strand` 6/8.
- **Kandidaten** (Netze und Config von V12, nur die Schalter gesetzt): `v16s` (`no_strand`) und `v16all`
  (`est_censor` + `neb_cross` + `no_strand`).
- **Vor der Messung:** ganze Testsuite; V12 spielt mit dem neuen Code (Schalter aus) 16 vorhandene Spiele identisch.
- **Screen:** `REF=v12 bash scripts/battle_v14.sh admit v16s v16all`. Zulassung unverändert: Mittel 6 Δ ≥ +0,5 pp,
  direkt gegen V12 ≥ 50 %, Solution_92 Δ ≥ −1,0 pp; bei zwei der mit dem höheren Mittel.
- **Battle-Bestätigung** genau einmal für den zugelassenen Kandidaten auf **813200–813999**, direkt
  **814000–814399** (`REF=v12 bash scripts/battle_v14.sh confirm NAME`). Hürden unverändert `league_gates battle`;
  vorher prüfen, dass keine CSV diese Seeds enthält. Bestanden → Übernahme wie Nachtrag 18:50, sonst V12.
- **Ergebnis Screen (01.11., 04:19): kein Kandidat zugelassen.** `v16s` Mittel 6 Δ −0,28 pp [−1,50; +0,92], direkt
  50,8 %; `v16all` −0,06 [−1,33; +1,22], direkt 51,0 %. Gegen `league_nets6` −3,0 bzw. −3,7, gegen V3/V7/Solution_92
  +0,7 bis +1,7. 280 von 3.600 Ergebnissen verändert, ohne klares Muster (Bewegungskosten 4: +1,0, 1–3: −0,6 bis
  −1,2). `no_strand` wird nicht weiter verfolgt.

## Nachtrag 01.11.2026, 04:25 (Nachtraining unter den V12-Regeln, vor jeder Messung mit den neuen Netzen)

- **Grund:** Die 36 Netze von V12 haben die Regeln von V11/V12 (Halbstreuung, Nebel-Sap) und die Nebel-Korrekturen nie
  im Training gesehen. V11 entstand aus genau so einem Nachtraining unter den damaligen Regeln (R +4,66 pp). Die
  Regeltests dieser Nacht brachten höchstens +0,42 pp (`v15cx`).
- **Lauf** `scripts/pipeline_battle_ft6.sh`:
  - 12 der V12-Netze (Runde 3, Seeds s16–s27; Gewichte und Buffer) spielen je 2.000 Spiele, 12 parallel.
  - Neue Variante `full_rules_v12`: V12-Config + `est_censor` + `neb_cross`, alle Regeln im Training.
  - Kartenversatz 4000, für s16–s27 noch unbenutzt.
  - Gegner: solution92 0,30, sol92_sq 0,20, sol92_weak 0,10, Pool 0,30 (V10, old3, V11, V12), rush 0,05, default 0,05.
    Die zurückgehaltenen Ensembles `league_nets6`/`threat6` und die Abgaben V3/V7 sind nicht im Pool.
- **Kandidaten** (beide Config V12 + `est_censor` + `neb_cross`):
  - `v17a`: die 36 V12-Netze + 12 neue = 48 Netze.
  - `v17b`: V10-Netze + Runde-3-Netze s10–s15 + 12 neue = 36 Netze; die 12 neuen ersetzen ihre Vorgänger.
- **Screen:** `REF=v12 bash scripts/battle_v14.sh admit v17a v17b`, Zulassung unverändert (Mittel 6 Δ ≥ +0,5 pp,
  direkt ≥ 50 %, Solution_92 Δ ≥ −1,0 pp; bei zwei der mit dem höheren Mittel).
- **Battle-Bestätigung** genau einmal für den zugelassenen Kandidaten auf **813200–813999**, direkt **814000–814399**
  (`REF=v12 bash scripts/battle_v14.sh confirm NAME`). Hürden unverändert `league_gates battle`; vorher prüfen, dass
  keine CSV diese Seeds enthält. Spätester Start 03.11., 12:00. Bestanden → Übernahme wie Nachtrag 18:50, sonst V12.
- **Ergebnis Screen (01.11., 07:56): `v17a` zugelassen.** Mittel 6 Δ +1,22 pp [−0,64; +3,17], Solution_92 ±0,
  direkt gegen V12 60,3 % [55,0; 66,0] (je Gegner: V7 +8,0, `league_nets6` +2,0, V3 −1,3, `sol92_sq` −1,3, `threat6`
  und Solution_92 ±0). `v17b` ebenfalls zugelassen (Δ +0,69 [−1,33; +2,75], Solution_92 −0,83, direkt 56,0 %), aber
  mit dem niedrigeren Mittel. Battle-Bestätigung von `v17a` gestartet 07:56; 813200–814399 vorher in keiner der 1.157
  CSVs mit Seed-Spalte (die einzigen Treffer der Suche waren Trainingskarten 313000–314749).
- **Ergebnis Battle-Bestätigung (01.11., 10:40): `v17a` nicht bestanden.** Mittel 6 87,75 statt 87,34 % (Δ +0,41 pp
  [−0,68; +1,52]), Solution_92 +1,31 [+0,19; +2,50], default 99,88 %, direkt gegen V12 53,75 % [49,0; 58,75] aus
  800 Spielen. Verfehlt: Mittel 6 ≥ +1 pp, untere Grenze > 0, direkt untere Grenze > 50 %. Nachträglich getrennt (nur
  Beschreibung): Karten mit Nebelabzug 25 +3,26 pp, übrige 685 Karten −0,07 pp. Weiter mit Nachtrag 04:45.

## Nachtrag 01.11.2026, 04:45 (gezielte Bestätigung der Nebel-Korrektur, vor jeder Messung auf 816000–819999)

- **Grund:** `v15cx` (`est_censor` + `neb_cross`) wirkt nur auf Karten mit Nebelabzug 25.
  - Dev A: 84 der 87 veränderten Ergebnisse liegen dort, +2,68 pp, jeder der 6 Gegner +1,8 bis +5,4 pp, direkt 57,1 %
    gegen V12. Die übrigen Karten spielt `v15cx` praktisch gleich (direkt 50,2 %).
  - Eine Hürde von +1 pp im Mittel über alle Karten kann eine solche Korrektur kaum erreichen (erwartet etwa +0,45 pp),
    obwohl sie nirgends schadet. Deshalb ein Test genau dort, wo sie wirkt, und ein Gleichheitstest für den Rest.
- **Karten** (nur nach Kartenparametern aus `env.reset` gewählt, vor jedem Spiel festgelegt; 815600–819999 um 04:40 in
  keiner CSV, `experiments/analysis/neb25_20261101/`):
  - **N25:** die ersten 300 Karten mit Abzug 25 aus 816000–819999, `seeds_n25.json` (816000–817792).
  - **Rest:** die ersten 60 übrigen Karten, `seeds_rest.json`.
- **Lauf** `WORKERS=12 bash scripts/battle_neb25.sh v15cx`:
  - V12 und `v15cx` auf N25 gegen die 6 Gegner und default, je Gegner 600 Spiele.
  - Direkt `v15cx` gegen V12 auf N25, 600 Spiele.
  - V12 und `v15cx` auf Rest gegen die 6 Gegner, je 120 Spiele.
- **Hürden** (alle müssen halten):
  - N25: Mittel 6 Δ ≥ +1 pp und untere 95%-Grenze > 0; Solution_92 Δ ≥ −0,5 pp; default ≥ 99 %; direkt gegen V12 ≥ 50 %.
  - Rest: ≥ 98 % gleiche Ergebnisse und Mittel 6 Δ ≥ −0,5 pp.
- **Reihenfolge:** erst Runde 6 (Nachtrag 04:25). Besteht `v17a`/`v17b` die Battle-Bestätigung, enthält die Abgabe die
  Korrektur schon, und dieser Test entfällt. Sonst läuft er.
  - Bestanden → Übernahme als V13 `v13_neb` (V12-Netze, Config V12 + `est_censor` + `neb_cross`) wie Nachtrag 18:50.
  - Nicht bestanden → V12 bleibt.
  - `scripts/release_candidate.py` erkennt dafür auch „GATE Nebel-25-Bestaetigung: BESTANDEN“ (Test in
    `tests/test_release_gate.py`).
- **Ergebnis (01.11., 09:04): bestanden, alle 7 Hürden.** N25: Mittel 6 87,17 statt 84,78 % (Δ +2,39 pp [+0,31;
  +4,36], 300 Karten), Solution_92 95,0 statt 94,2 % (Δ +0,83 [−1,17; +2,83]), default 100 %, direkt gegen V12 56,0 %
  [50,8; 61,3] aus 600 Spielen. Je Gegner: `league_nets6` +10,3 [+4,0; +16,3], V7 +3,2, V3 +1,8, `sol92_sq` −0,7,
  `threat6` −1,2. Rest: 720 von 720 Ergebnissen gleich. Lief parallel zu Runde 6; nach der Reihenfolge oben zählt es
  nur, falls `v17a` die Battle-Bestätigung nicht besteht (dann V13 `v13_neb`).
- **Übernahme (01.11., 10:46):** `v17a` fiel durch, also **V13 `v13_neb`** mit `scripts/release_candidate.py`
  (V12 gesichert in `experiments/releases/20261101_v12_fog/`). Vorher wurde `gate_passed` korrigiert (Commit
  `a5d6dd6`): Durch die parallelen Läufe stehen die Zeilen gemischt im Gate-Log; das alte Skript erkannte `v15cx` nicht
  und hätte `v17a` fälschlich als bestanden gewertet. [Übernahmebericht](../../../experiments/analysis/release_20261101_v13/RELEASE.md).

## Nachtrag 01.11.2026, 07:15 (`cand_rescue` auf der Nebel-Korrektur, vor jeder Messung von `v18r`)

- **Grund** (nur verbrauchte Karten 812000–812149, V12 gegen Solution_92, 900 Matches mit Endstand je Match):
  - Gleichstand nach Punkten entscheidet nur 0,9 % der Matches (alle gewonnen). Die Regel `tie_save` (Energie sparen
    bei drohendem Gleichstand) wird deshalb nicht verfolgt.
  - V12 verliert Match 2 und 3 dreimal so oft wie Match 1 (16,7/15,7 statt 5,7 %), 102 von 114 verlorenen Matches mit
    mehr als 10 Punkten Rückstand. 14 Matches mit weniger als 20 % der Gegnerpunkte stecken in 13 der 21 verlorenen
    Spiele.
  - Ursachen: der Nebel-Fehler (812049, 812081) und 812121: Relics seit Match 1 bekannt, in Match 2 über 140 Schritte
    kein Punkte-Tile; die Units pendeln auf Energiefeldern im Nebel, ihr Ziel-Kandidat wechselt jeden Schritt (0:202).
- **Schalter `cand_rescue`** (seit 22.10. im Code): Ist ein Relic seit `rescue_after` Schritten bekannt und noch kein
  Punkte-Tile, gehen die Units gezielt auf Kandidaten (`obey_target`, `neb_cand`, `idle_approach`). Auf V10 bester
  Einzelschalter (+0,7 pp, Entwicklung), auf V11/V12 aus Zeitgründen nie gemessen.
- **Diagnose** (9 verbrauchte, gezielt gewählte Karten, 18 Spiele, kein Gate): V12 10/18, `v15cx` 12/18,
  `v15cx` + `cand_rescue` (`rescue_after=30`) 14/18.
- **Kandidat** `v18r` = `v15cx` (V12-Netze, Config V12 + `est_censor` + `neb_cross`) + `cand_rescue=true` +
  `rescue_after=30`.
- **Screen:** `REF=v15cx bash scripts/battle_v14.sh admit v18r` (Dev A, gepaart gegen die vorhandenen
  `D_v15cx*.csv`, misst nur `cand_rescue`). Zulassung unverändert: Mittel 6 Δ ≥ +0,5 pp, direkt gegen `v15cx` ≥ 50 %,
  Solution_92 Δ ≥ −1,0 pp.
- **Battle-Bestätigung** (nur nach Zulassung, genau einmal): `cand_rescue` + `rescue_after=30` auf der dann aktuellen
  Abgabe gegen genau diese Abgabe, Hürden unverändert `league_gates battle`.
  - Karten: 813200–813999, direkt 814000–814399, falls Runde 6 sie nicht braucht; sonst **820000–820799**, direkt
    **821000–821399**. Vorher prüfen, dass keine CSV diese Seeds enthält.
  - Bestanden → Übernahme wie Nachtrag 18:50, sonst bleibt die Abgabe.
- **Ergebnis Screen (01.11., 09:05): nach der Regel zugelassen, das Skript meldete wegen eines Rundungsfehlers „nicht
  zugelassen“.** Mittel 6 86,47 statt 85,97 % (Δ +0,50 pp [+0,14; +0,94], 300 Karten), Solution_92 +0,17, direkt gegen
  `v15cx` 52,3 % [51,0; 53,7] aus 600 Spielen.
  - Exakt: 18 Siege mehr in 3.600 Spielen, Δ = 1/200 = +0,50 pp; die Regel verlangt Δ ≥ +0,5 pp. `battle_v14.sh`
    rechnete in Gleitkomma 0,004999999999999999 und verglich mit `>= 0.005`.
  - Je Gegner (Siege von 600): Solution_92 567 statt 566, `sol92_sq` 546/545, V3 534/530, V7 470/460, `league_nets6`
    440/440 (4 gewonnen, 4 verloren), `threat6` 556/554. 26 von 3.600 Ergebnissen verändert, 22 davon zu Siegen.
  - Die Battle-Bestätigung läuft wie oben festgelegt erst nach der Entscheidung über `v17a` (dann aktuelle Abgabe als
    Referenz) auf 820000–820799, direkt 821000–821399.
- **Battle-Bestätigung gestartet (01.11., 11:33):** `v18r` gegen die aktuelle Abgabe V13 (= `v15cx`) auf 820000–820799,
  direkt 821000–821399 (`REF=v15cx WORKERS=12 bash scripts/battle_v15.sh confirm v18r`, Dateien `GF_*`, Code
  `961a93a`). Vorher geprüft: Keine der 1.166 CSVs mit Seed-Spalte unter `experiments/` enthält diese Seeds. Hürden
  unverändert `league_gates battle`, seit Commit `e6d4624` mit Toleranz 1e-9 bei den Vergleichen (die vier früheren
  Battle-Entscheidungen bleiben gleich).

## Nachtrag 01.11.2026, 12:17 (Kandidaten-Reihenfolge und Spawn-Beweis, vor jeder Messung von `v19c`/`v19cr` auf Dev A oder 822000–823399)

- **Grund** (Diagnose nur auf Dev A und verbrauchten Karten, kein Gate):
  - Mit den wahren Punkte-Tiles um bekannte Relics gewinnt V13 bei Sichtweite 1 gegen Solution_92 94,4 statt 85,4 %
    (Orakel `points`).
  - Bis alle Punkte-Tiles einer neuen Zone bewiesen sind, vergehen 30–40 Schritte; die Units testen etwa ein Kandidaten-Feld
    pro Schritt.
  - Ein Tile in k Relic-Zonen ist zu 20 / 34 / 49 / 57 % ein Punkte-Tile (k = 1 / 2 / 3 / 4+, 1.500 Karten). Spätere Paare
    liegen meist neben früheren, Überlappungen sind deshalb häufig.
  - Im 2./3. Match ist die Inferenz im Mittel 41–47 Schritte gesperrt (Spawnfenster), auch wenn ein Punkt schon beweist,
    dass das neue Paar gespawnt ist.
- **Schalter** (Standard aus, Commit vor dieser Messung, Tests in `tests/test_relic_prior.py`):
  - `cand_post` (Gewicht 15): Kandidaten mit höherer Punkte-Wahrscheinlichkeit werden zuerst getestet. Die Wahrscheinlichkeit
    kommt aus der Zonen-Überlappung und aus offenen Gleichungen des Gedächtnisses.
  - `spawn_proof`: Kann im Match j ≥ 1 kein bekanntes Relic einen Punkt erklären (alle früheren Paare bekannt), ist Paar j
    gespawnt, und die Inferenz darf vor match_step 50 schließen.
- **Entwicklungsprobe** (V13 + beide Schalter, Dev A, nur zur Auswahl der Kandidaten):
  - gegen Solution_92 auf 221 der 300 Dev-A-Karten 95,7 statt 92,8 % (Sichtweite 1: 91,7 statt 85,4 %);
  - gegen V7 bei Sichtweite 1 unverändert (76,4 %, je 12 Spiele gewonnen und verloren).
  - Der Screen wiederholt diese Spiele. Sein Solution_92-Teil ist daher nicht unabhängig; unabhängig ist erst die
    Battle-Bestätigung.
- **Kandidaten** (Netze und Config von V13 = `v15cx`, Netze bytegleich):
  - `v19c` = V13 + `cand_post=15` + `spawn_proof=true`;
  - `v19cr` = `v19c` + `cand_rescue=true` + `rescue_after=30`.
- **Screen:** `REF=<aktuelle Abgabe> bash scripts/battle_v15.sh admit v19c v19cr`.
  - Referenz ist `v15cx` (V13); besteht `v18r` seine laufende Bestätigung, ist es `v18r`.
  - Zulassung unverändert: Mittel 6 Δ ≥ +0,5 pp, direkt gegen die Referenz ≥ 50 %, Solution_92 Δ ≥ −1,0 pp. Bei zwei
    zugelassenen der mit dem höheren Mittel.
  - Ist `v18r` die Referenz, ist `v19cr` = `v18r` + die beiden neuen Schalter, und `v19c` (ohne `cand_rescue`) entfällt.
- **Battle-Bestätigung** genau einmal für den gewählten Kandidaten gegen die Referenz auf **822000–822799**, direkt
  **823000–823399** (`REF=<Referenz> CONF_FIRST=322000 DIR_FIRST=323000 PFX=GG bash scripts/battle_v15.sh confirm NAME`).
  - Um 12:17 in keiner der 1.166 CSVs mit Seed-Spalte.
  - Hürden unverändert `league_gates battle`.
  - Bestanden → Übernahme als V14 wie Nachtrag 18:50 (Sicherung der Abgabe, neue Zip, Kurs-Runner, Tests, Nachspielen
    unter Python 3.10); sonst bleibt die Abgabe.
  - Start nach dem Ende der laufenden `v18r`-Bestätigung.
