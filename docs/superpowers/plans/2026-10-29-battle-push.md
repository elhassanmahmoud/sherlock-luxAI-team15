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
