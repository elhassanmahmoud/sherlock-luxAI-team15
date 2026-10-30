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
