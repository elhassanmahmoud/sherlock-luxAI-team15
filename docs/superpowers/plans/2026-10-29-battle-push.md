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
