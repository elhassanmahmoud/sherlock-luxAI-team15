# Trainingsdiagnose und begrenzter Kontrollpilot, 01.11.2026

Stand: Repository `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15`, HEAD `93a2ddd`, gelesen am 01.11. ca. 20:40–21:00 Berlin. Keine Änderungen am Repository, keine Modelljobs, keine Tests, keine neuen Spiele. Nur Dateiinventar, Code-/Log-Lektüre und Auswertung vorhandener CSV/Manifeste mit der Python-Standardbibliothek. Die Pilot-Spezifikation ist ein Vorschlag, noch keine Implementierung oder reservierter Seedblock.

## Empfehlung

**Ein kleiner gepaarter Pilot ist vertretbar: dasselbe deterministisch gewählte V14-Komponentennetz mit stärkerer Belohnung für bewiesene Punktefelder gegen eine unveränderte Belohnung trainieren.** Es ist ausdrücklich ein neuer Reward-Pilot mit frisch angelegtem Optimizer und Replay, keine Fortsetzung von Runde 6. Genau ein Faktor: `w_discovery=2.0` statt `0.5`. `w_explore=0.3` bleibt in beiden Armen gleich. Der Orakelbefund betrifft vor allem das Tempo beim Beweisen von Punktefeldern, nicht eine generelle Langsamkeit beim Finden des ersten Relics. Deshalb vermeidet dieser Ansatz einen zweiten, schlechter begründeten Faktor „mehr beliebige Kartenerkundung“.

Die geringe Größe (600 Trainingsspiele pro Arm, ein Modellprozess pro Arm) erfüllt den ausdrücklichen Trainingswunsch und begrenzt den Preis einer unbewiesenen Hypothese. Sie kann zeigen, ob der veränderte Lernanreiz überhaupt ein positives Signal liefert; sie rechtfertigt ohne separate Bestätigung weder eine stärkere Abgabe noch eine Aussage über 100 % Solution-Siege. Eine unveränderte Runde 7 ist durch die aktuelle Evidenz nicht begründet.

## Warum nicht einfach Runde 7?

Aus sämtlichen betreffenden `train.csv`, `val.csv` und `manifest.json` nachgerechnet:

| Runde | Netze | Tatsächlich protokollierte Trainingsspiele | Mittel kleine Solution-Val vor → nach | Befund für Ensemble |
|---|---:|---:|---:|---|
| 1, 29.10. | 18 | 27.000 | 71,53 → 76,74 % | Mischen half; einzelne Fortschritte sind keine Bestätigung |
| 2 | 18 | 36.000 | 76,74 → 77,78 % | `mix36b` frisch R +1,77 pp, Hürde +2 verfehlt |
| 3 | 18 | 36.000 | 77,78 → 81,25 % | Mit zusätzlichen Regeln wurde `mix36c_as` V11; Trainingseffekt und Regeleffekt sind vermischt |
| 4 | 18 | 36.000 | 81,25 → 82,99 % | `mix36d_as`: Dev-Mittel +0,81 pp, direkt 48,3 %; `mix54d_as`: −0,61 pp. Kein Kandidat zugelassen |
| 5 | 6 angefangene | 8.600 | 82,29 → 86,46 % bis letzter Val nach 1.000 | Abgebrochen, kein `status=done`, kein 18-Netz-Endensemble. Keine vollständige Runde |
| 6, 01.11. | 12 | 24.000 | **77,083 → 77,083 %** | `v17a` frisch nur +0,41 pp [−0,68; +1,52], direkt 53,75 % [49,0; 58,75], nicht bestanden |

Zusammen 167.600 protokollierte Spiele in diesen sechs Linien/Runden. Die Einzelnetz-Val besteht meist aus nur acht Karten je Gegner und beiden Seiten; sie ist eine bekannte Lernkurve, kein unberührter Test. `--keep-final` bedeutet Endgewichte trotz der Log-Zeile „bester Checkpoint“.

Runde 6 trainierte bereits unter `full_rules_v12`, einschließlich `est_censor`, `neb_cross`, Nebel-Sap und Halbstreuung, gegen einen gemischten Pool. Die frische Verbesserung von `v17a` lag auf Nebelabzug-25-Karten; auf den übrigen 685 Karten betrug sie −0,07 pp. V13 gewann mit denselben alten Tensoren durch die Nebelkorrektur. V14 ergänzt anschließend `cand_rescue`; das ist allein kein Beleg für erneutes breit angelegtes Nachtraining.

Die eigenständige Liga vom 26.10. ist ebenfalls kein unerprobter Ansatz: sechs neue Netze × 4.000 Spiele, Kandidat L24 R +0,81 pp (Hürde +1,5), L6 −2,25 pp; kein Kandidat bestätigt. RL-Liga mit 50 % Pool, v8-Linie und Altnetze wurden am 29./30.10. ebenfalls untersucht. Nochmals denselben Mix aufzulegen wäre keine neue Hypothese.

Belege: `docs/ARBEITSSTAND.md` Einträge 30.10. 18:36, 31.10. abgebrochene Runde 5, 01.11. 06:45/08:00/10:55; `docs/superpowers/plans/2026-10-29-battle-push.md`; `experiments/pipeline_league.log`; `experiments/pipeline_battle_ft{,2,3,4,5,6}.log`.

## Artefaktlage und zwei gefährliche Fallstricke

Versioniert und lokal vorhanden sind V14 in `agents/sherlock/weights/agent_p0.pth`/`agent_p1.pth`, Sicherungen V13/V12/V11/V10/V7/V3/old3 sowie mehrere ältere Kandidaten. V14-SHA: `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.

**Nicht lokal vorhanden** sind die Einzelgewichte und Replay-Buffer von ft1–ft6; die jüngsten Run-Verzeichnisse enthalten nur `manifest.json`, `log.txt`, `train.csv`, `val.csv`. Das wurde zusätzlich mit `rg --files --hidden --no-ignore` und direkter Verzeichnisliste geprüft. Die fünf lokalen `experiments/ensembles/*.pth` sind nur ältere `all18_*`, `all24fo`, `rules6`; alle neueren `battle_*.pth` fehlen. Auch die zurückgehaltenen Gegner `league_nets6.pth` und `threat6.pth` fehlen einschließlich ihrer Quellnetze. Es gibt ältere lokale Codex-V3-Pilotnetze mit Buffern, aber sie sind keine jüngsten Mahmoud-Checkpoints.

1. `scripts.finetune` prüft kopierte Startgewichte nicht. Fehlt `INIT/weights/agent.pth`, übergibt `scripts.variants.make_learner` `path=None` und startet ein zufälliges Netz. Ein Aufruf auf das lokal vorhandene ft6-Manifest wäre **stilles Neutraining**, keine Fortsetzung.
2. Bei direktem Laden des V14-Ensembles aktualisiert DQN nur das primäre `q`; `extra_q` sind eingefroren. Das ist kein Weitertrainieren aller 36 Netze. Deshalb für diesen Pilot genau **ein** Netz sauber extrahieren und `ensemble=[]` speichern.

Für unveränderte echte ft6-Fortsetzung wären mindestens die passenden `weights/agent.pth` plus `weights/agent.buffer.npz` von Mahmoud nötig. Diese Übertragung ist für den vorgeschlagenen Extraktionspilot nicht erforderlich. Das bestehende vollständige Battle-Gate mit sechs Gegnern lässt sich lokal wegen der zwei fehlenden Gegner dagegen nicht für einen neuen Kandidaten wiederholen; die historischen CSVs ersetzen deren Gewichte nicht.

## Festes Pilotdesign

- **Ein Ausgangsnetz:** Index 0, also `q` des unveränderten V14-Checkpoints. Diese Auswahl erfolgt über die gespeicherte Reihenfolge, nicht über eine nachträgliche Rangliste der 36 Netze.
- Ein neues Init-Verzeichnis, z. B. `experiments/runs/20261101_nov_info_init_q0/`, enthält einen korrekten Manifest und `weights/agent.pth`. `q` und `target_q` sind beide Kopien von V14-`q`. `ensemble=[]`, keine CNN-Policy, kein `opt`-Feld; Adam wird frisch erzeugt. `learn_steps=0` ist expliziter Neustart des Optimizers/Target-Zählers. Die bisherigen `env_steps` erhalten, wenn damit Epsilon bereits 0,05 ist; andernfalls beide Arme explizit auf denselben Wert ≥60.000 setzen und das dokumentieren. Keine Wiederverwendung vermeintlicher Optimizerzustände für andere Ensemblekomponenten.
- Basiskonfiguration aus **genau dem aktiven V14-Checkpoint**, einschließlich `cand_rescue=true`, `rescue_after=30`, alle bestehenden Inferenzregeln. Zum Lernen `frozen=false`, `rules_in_training=true`, `rules_in_training_all=true`, `lr=1e-4`.
- Zwei Varianten, z. B. `full_rules_v14_nov01_ctl` und `full_rules_v14_nov01_disc`, identisch bis auf `w_discovery=.5` bzw. `2.0`. Bei beiden `w_explore=.3`. `full_rules_v12` allein reicht nicht, weil dort `cand_rescue` fehlt. `finetune` hat kein `--set`: zwei Variant-Einträge oder ein sauberer lokaler Wrapper sind vor dem Start nötig; nur Checkpoint-Config zu ändern reicht bei expliziter Variante nicht.
- Neue Replay-Buffer in beiden Armen; **120 Prefillspiele** mit eingefrorener Policy, ohne Lernen, danach exakt **600 Trainingsspiele** je Arm. Gegen dieselben Gegner auf denselben Karten. Keine Best-Checkpoint-Auswahl, nur vorab festgelegter Endstand.
- Die Prefillaktionen/-Zustände sollten zwischen den Armen identisch sein, weil nur Rewards geändert werden und nicht gelernt wird. Die gespeicherten Rewards unterscheiden sich absichtlich; kein altes Control-Replay in die Treatment-Variante kopieren.
- Gegnermix: `solution92=.35,sol92_sq=.25,sol92_weak=.10,pool=.20,rush=.05,default=.05`. Fester Pool aus V14, V10 und old3, alle lokal vorhanden. V3/V7 und die verfügbaren `sol92_sqweak` bleiben außerhalb dieses Trainingspools für die Entwicklungskontrolle. Keine neuen Selfplay-Snapshots in diesem kleinen Pilot.
- Ein Prozess pro Arm; `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`; Torch begrenzt `finetune` bereits auf einen Thread. Sonst keine anderen Modell-/Evaluationsprozesse parallel. Die alten Pipeline-Skripte mit PAR 6–18 nicht starten.

Konkrete CLI **nach** Herstellung und Prüfung der zwei Varianten und des gemeinsamen Init-Checkpoints, je ein Aufruf in einem der insgesamt höchstens zwei Workers:

```sh
.venv/bin/python -m scripts.finetune \
  --init experiments/runs/20261101_nov_info_init_q0 \
  --name 20261101_nov_info_control_s9 \
  --variant full_rules_v14_nov01_ctl \
  --games 600 --seed 9 --map-offset 4200 \
  --lr 0.0001 --prefill-games 120 --keep-final \
  --val-every 300 --n-val 8 --no-test \
  --mix 'solution92=0.35,sol92_sq=0.25,sol92_weak=0.10,pool=0.20,rush=0.05,default=0.05' \
  --pool agents/sherlock/weights/agent_p0.pth \
    experiments/releases/20261022_v10_baseline/agent_p0.pth \
    experiments/releases/20261020_old3_sym3/agent_p0.pth
```

Der zweite Aufruf hat ausschließlich `--name 20261101_nov_info_discovery_s9` und `--variant full_rules_v14_nov01_disc` geändert. Alle übrigen Argumente einschließlich Seed und Kartenversatz bleiben gleich. Unterschiedliche Namensräume verhindern Ausgabekollisionen, nicht unterschiedliche Seeds.

Vorabprüfung muss hart abbrechen bei fehlendem Init-Checkpoint, unerwarteter Netzanzahl/-dimension, ungleichen Anfangstensoren, weiter vorhandenem Optimizerfeld, falschem V14-Hash, ungleichen Gegnerplänen oder einem zweiten Konfigurationsunterschied. Nach dem Laden initiale Tensoren, Epsilon und leeren Optimizer tatsächlich prüfen. Manifest und Dateinamen allein reichen nicht.

## Seed-Audit und Auswahltrennung

Gelesen wurden **271 Manifeste**, einschließlich deklarierter Trainingsspannen und bei fehlendem geladenen Buffer der aus `run_seed` ableitbaren Prefillspannen, sowie **1.191 CSV/CSV.gz mit `seed`-Spalte, 1.555.218 Zeilen**. Das ist ein Audit der verfügbaren Dateien, kein Nachweis, dass auf Mahmouds Rechner keine unveröffentlichten Jobs existieren.

- Gemeinsamer Runseed 9, `map_offset=4200`: Training **294200–294499**, Prefill **295000–295059**. Für beide Blöcke keine Überschneidung mit verfügbaren Rohdaten/Manifestspannen. `finetune`-Grenzen passen: 4200+600/2 ≤5000 und alle Karten unter 500000.
- Die Alternative mit 200 Prefillspielen würde 295000–295099 verwenden; für diesen Entwurf **nicht geprüft**. Deshalb vorerst bei 120 bleiben.
- `finetune`-Lernkurven bleiben auf den bekannten acht Karten **500000–500007**. Sie dienen nur technischen/katastrophalen Warnsignalen, nicht Checkpoint- oder Hyperparameterauswahl.
- Optional zentral durch Root zu reservierende neue Blöcke (alle ohne Treffer in den 1.191 CSVs): **830000–830059** Entwicklung, **831000–831099** separate Gegenprobe, **832000–832799** spätere finale Bestätigung und **833000–833399** direkt. Noch keine Reservierung vorgenommen. Root muss Überschneidungen mit den anderen parallel arbeitenden Agents ausschließen und die Reservierung vor dem ersten Spiel schreiben.
- Ein Kandidat = die vorab festgelegten 600er-Endnetze. Primäre Methodenfrage ist Treatment gegen Control. Zusätzlich beide gegen den eingefrorenen Start auf denselben Entwicklungskarten prüfen, damit „weniger schlecht als Control“ keinen Fortschritt vortäuscht.
- Keine vier Rewardstärken, keine anschließende Best-Seed-Suche. Scheitert das Treatment, nicht mit 1.0/4.0 auf denselben Karten weiterprobieren. Ergebnisse der Gegenprobe getrennt zeigen; nicht mit Dev A zusammenpoolen.
- Eine neue Ensemble-Mischung wäre ein eigenes Transfer-Gate. Sie sollte vor den Pilot-Ergebnissen festgelegt werden (z. B. V14 + genau ein Treatmentnetz gegen V14 + Control und V14); ein besseres Einzelnetz bedeutet noch kein besseres 36-Netz-Ensemble. Nicht aus mehreren Mischgewichten das beste auf der späteren Bestätigung wählen.
- Das vorhandene `league_gates battle` verlangt weiterhin sechs definierte Gegner und darf nicht durch Weglassen der fehlenden Gegner als bestanden gemeldet werden. Ein vorab definierter kleinerer Entwicklungspanel mit lokalen Gegnern ist zulässig, trägt aber nur eine vorläufige Pilotentscheidung. Die vollständige Release-Bestätigung kann bei Bedarf nach Transfer der zwei Gegner später erfolgen.

## Gemessene Zeitbasis, Begrenzung und Stopregeln

**Tatsächliche Logs:** Auf diesem M3 brauchten die früheren 3.000-Spiel-Kontrollläufe s47/s48/s49 3338/3029/3048 Sekunden, etwa 1,01–1,11 s pro Trainingsspiel unter älteren V3-Regeln ohne den teureren V14-Pool. Diese Zahlen nicht direkt auf V14 übertragen. Auf Mahmouds Rechner dauerte ft6 je Netz 8.221–8.383 s für 2.000 Training +160 Valspiele; die ganze Welle mit zwölf parallelen Prozessen lief 04:23–06:43. Das sind etwa 3,8–3,9 s je tatsächlich gespieltem Training-/Valspiel bei dieser Parallelität. In `GF_v18r_conf.csv` beträgt das historische Prozessmittel 4,34 s/Spiel (Median 4,08, Maximum 9,09), auf anderer Hardware und zwölf Workern.

**Vorsichtige Planrechnung:** Pro Arm 120 Prefill +600 Training +3×32 Zwischenvalidierung =816 Spiele. Bei 4 s/Spiel etwa 54 Minuten pro Arm, plus Laden/Schreiben; zwei Arme parallel bleiben ungefähr eine Stunde Wandzeit. Mit 25 % Reserve grob **70–90 Minuten**. Das ist eine Extrapolation, keine Messung dieses Piloten. Die Hauptunsicherheit ist V14-Regel-/Poolkosten auf M3/8GB.

- Maximal **zwei Stunden Wandzeit für beide Arme zusammen ab gemeinsamem Start**. Vorab absolute Berliner Deadline festhalten; niemals die wissenschaftliche Horizontgrenze nach günstigem Zwischenstand verlängern.
- Ressourcen-Frühstop nur nach beobachteten Laufzeiten, Fehlern oder Nicht-Endlichkeit: aus den ersten festen 100 Prefillspielen (je Arm) konservativ abschätzen; passt der komplette restliche 600er-Plan plus Abschlussreserve nicht in zwei Stunden, beide Arme stoppen und als **unvollständig** kennzeichnen. Kein einzelner weiterlaufender Gewinnerarm.
- Fehler/NaN, falsche Startidentität, nicht trainierendes Modell, unerwarteter fremder Modelljob oder Speicherproblem: beide eigenen Jobs abbrechen; bestehende Abgabe nicht anfassen.
- Nach 300 Spielen keine Auswahl anhand der winzigen internen Val. Ein harter Zeitabbruch nach 300 ist ein abgebrochener 600er-Pilot, kein nachträglich umdefinierter erfolgreicher 300er-Versuch.
- Fester Endstand 600. Danach keine zusätzliche Runde aufgrund eines schönen Resultats. Für eine vordefinierte Futility-Auswahl genügt: Treatment muss auf unabhängiger Entwicklung gegen Control UND eingefrorenen Start mindestens nicht schlechter sein; für eine positive Methodenaussage verlangen wir einen vorab festgelegten tatsächlichen Vorteil auf der separaten Gegenprobe. Kleine Kartenintervalle messen keine Streuung über Trainingsinitialisierungen; ein Start bleibt ein Pilot.
- Neue schwere Phase nur starten, wenn Restlauf plus 30 Minuten Bericht/Prüfung vor 06:00 Berlin passt. Aktive Modellarbeit spätestens 05:30 beenden. Im Zweifel keine neue Bestätigung beginnen und V14 behalten.

Eine volle neue Battle-Bestätigung kostet 23.200 Spiele (je 11.200 pro Referenz/Kandidat plus800 direkt), zusätzlich zu Screening und Training. Bei 4,34 Prozesssekunden pro Spiel und zwei Workers wären das ungefähr **14 Stunden** reine Wandzeit; selbst die Übertragung dieser Rate zwischen Rechnern ist unsicher. Deshalb ist „600er-Pilot plus vollständiger historischer Release-Gate heute sicher bis 06:00“ keine seriöse Zusage. Root kann mit tatsächlichen heutigen Messungen die Zulassung für eine kleine unabhängige Gegenprobe entscheiden; eine historische Schwelle darf nicht allein aus Zeitdruck gelockert werden.

## Falls der Pilot technisch nicht sauber herstellbar ist

Ohne User-Aufhalten auf vorhandene V14-/V13-Rohdaten und einen begrenzten Mechanismustrace auf bereits bekannten Karten wechseln. Ein lauffähiger, lokaler Diagnoseaufruf (nur Root soll ihn bei Bedarf starten):

```sh
.venv/bin/python -m scripts.mechanism_probe \
  --weights agents/sherlock/weights/agent_p0.pth \
  --seeds 800000-800029 --workers 2 --opponent solution92 \
  --out experiments/analysis/nov01_v14_mechanism_known30.json
```

60 schon bekannte Spiele, keine frischen Bestätigungskarten. Ziel ist eine konkrete Entscheidung, ob Kandidaten zu spät bewiesen werden, Regeln die vorgeschlagenen Bewegungen überschreiben oder relevante Informationen in den bestehenden 79 Features fehlen. Der früher verworfene `cand_post`/`spawn_proof`-Ansatz darf nicht anhand derselben Dev-A-Spiele wiederbelebt werden: dort +1,81 pp, frisch −0,35 pp. Die Diagnose ist kein Stärkegewinn; sie begründet die nächste kleine Änderung oder einen ehrlichen Stop. V14 bleibt bis zu belastbarer neuer Evidenz die Abgabe.
