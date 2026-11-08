# Artillery Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Einen eng abgegrenzten Trainingsunterschied prüfen und nur bei belegtem Vorteil neue Gewichte übernehmen.
**Architecture:** Default-off Regeloption plus isolierter Beobachter und fester kontrollierter Lernlauf; vorhandene Trainer und Schutzfunktionen wiederverwenden.
**Tech Stack:** Python, NumPy, PyTorch, vorhandene Lux-Umgebung.
**Spec:** docs/superpowers/specs/2026-11-08-artillery-alignment.md

## Global Constraints

- V14 und ZIP unverändert bis unabhängig belegter besserer Kandidat; Backup und Kursprüfung vor Austausch.
- Maximal zwei Modellworker; keine Tests parallel zu Modellläufen, auch nicht in anderen Worktrees.
- Geschlossene Studien nicht wiederholen; keine neuen Karten nach negativem Ausgang.
- Quellen/HEAD/Startgewichte/Pläne während Läufen unverändert; einmalige exklusive Ausgaben.
- Keine Resets durch Agenten, keine fremden Änderungen verwerfen; Nutzer erlaubt selbstständige Commits/Push.

## Review Focus

- Alter Checkpoint ohne neuen Configschlüssel: DefaultFalse und unveränderte Inferenz.
- Trainingsoption ohne rules_in_training_all: Parameterschätzung muss trotzdem versorgt sein.
- Helper erlaubt SAP, spätere Regel verwirft: kein ausgeführter zusätzlicher Schuss zählen.
- Gespiegelte Spielerperspektive: native Aktion und kanonisches Replay korrekt zuordnen.
- Vorlauf ohne Effekt oder Lernmutation: keine Gradientenfreigabe oder automatische Wiederholung.

### Task 1: optionale Trainingsregel

**Files:** Modify agents/sherlock/config.py, agents/sherlock/main.py; create tests/test_art_splash_training.py.
**Interfaces:** AgentConfig.art_splash_in_training=False; _artillery_ok nutzt vorhandene Streuschadenabzweigung bei Inferenz oder aktiviertem Trainingsschalter, _act_est versorgt den Estimator für diesen Fall.

- [ ] Gezielte fehlschlagende Tests: fehlenderSchlüssel/False; TrainingTrue/False; art_splashFalse; Dropoff unbekannt/0,25/0,5/1,0; Sicherheits- und Energiegrenzen; Estimatorobserve/remember auch ohne rules_in_training_all; identische Inferenz bei beiden Flags; finale Aktion/_prev_actions und gespiegelte Seite.
- [ ] Minimalen Default-off Schalter und beide notwendigen Bedingungen umsetzen. Keine anderen Regeln, Rewards oder Gewichte ändern. Kein Produktionsdiagnostik-Framework.
- [ ] Neue Tests plus tests/test_art_splash.py ausführen, tatsächliche Ergebnisse melden. Keine vollständigen Spiele hier. Änderungen separat committen, Root vor Commit informieren; kein eigener Push.

### Task 2: kontrolliertes Training und Wirkungsbelege

**Files:** Create scripts/artillery_alignment_study.py, scripts/artillery_alignment_supervisor.py und tests/test_artillery_alignment_study.py. Alte Studien unverändert.
**Interfaces:** CLI prepare/run und Supervisor analog fog_reward_study, final_receipt.json mit klarer Quelle/Config/Zählern. Wiederverwenden: finetune-Rezept mit experiment.Learners/common.play_game und validate_v14, action_audit, prove_initial, _prove_prefill, _prove_end, source_identity, Ressourcen/Ownership/STOP-Prüfungen. Ein enger expliziter Spielplan-Loop ist gegenüber dem Patchen zahlreicher finetune-Globals erlaubt und bevorzugt, wenn die identische Konfiguration, Seeds, Lernbudgets und Validierungsisolation nachgewiesen werden. Keine neue allgemeine Trainingsplattform.

- [ ] Feste Werte aus der Spec übernehmen: vierArme43/44, Komponente18,40+400Spiele,32Diagnosen,240000Updates gesamt, Karten und Mischungen. Nur finalerCheckpoint. Quellkonfigurationsannahmen explizit ablehnen, wenn falsch.
- [ ] Temporären endlich-restaurierten Beobachter implementieren: actual/alternate Helperverdikt bei identischen Eingaben, Original-Rückgabe bewahren, keine RNG-/Estimator-/Kontextmutation; neueErlaubnis vsfinaleSAP-Ausführung/Abbruch getrennt. Finale native/kanonische/replayAktion prüfen. Artefakte mit tatsächlich messbaren Behauptungen.
- [ ] Vorlauf-Paarprüfung: gleicheInitialparameter/Schedules/einFlag-Unterschied; keineGleichheitderTrajektorien verlangen. Jealigned mindestens1ausgeführterzusätzlicherSAP, nullLernupdates undvollständigerVorlauf. VorGradienten blockieren,beiFehler stoppen.
- [ ] Supervisor maximal2eigeneWorker; Quelle/HEAD/Input/Abgabehashes, AC, echtefrischeQuota<100, STOP, Fremdprozesse, Eigentumsnachweise. Kanonischer STOP /private/tmp/sherlock-artillery-alignment-20261108/STOP. Usage experiments/analysis/artillery_alignment_20261108/operations/usage.json. Keine Wiederaufnahme/automatischen Wiederholungen.
- [ ] Fokussierte synthetische Tests für Schema/Plan/Config, Observerrestaurierung/Abbruch/Spiegelung/Replay, VorlaufannahmeundNullbefund, EndbelegundSchutzprüfungen. Keine Spiele während Umsetzung. Unabhängiger Review und Rootabnahme vor tatsächlichen Modellläufen.

### Task 3: prüfen, durchführen und entscheiden

**Files:** docs/ARBEITSSTAND.md, docs/EXPERIMENT_PROTOKOLL.md, experiments/analysis/artillery_alignment_20261108/.

- [ ] Offenen unabhängigen Datenabschluss der historischen Artillerie-Diagnose lesen, Quelle/Hashbindungen selbst prüfen; unabhängigen Kartenaudit und integrierten Werkzeugreview abschließen.
- [ ] Vier bekannte technische Ausführungen mit beidenFlagwerten gegen archivierte303Frames prüfen. Keine Lernupdates. Default/Inferenzgleichheit vor Trainingsfreigabe.
- [ ] Werkzeuge committen, Quelle einfrieren, tatsächlich vierarmigen Lauf durchführen. Zwischenresultate nur als solche melden. Rohdaten/Endgewichte unabhängig prüfen und versionieren, alteAbgabehashes kontrollieren.
- [ ] Separaten kleinen Vergleich vor Ergebnissen festlegen, durchführen und auswerten. Kein Nachrücken/Repeat-until-success. Nur bei belegtemVorteil Backup/Kursprüfung/Übernahme, andernfallsV14behalten undnächsteHypotheseausDaten ableiten.
- [ ] Dokumentation fürMahmoud, sinnvolleCommits/Pushund sichereAktualisierungderPrimärkopie. AktiveArbeitfortsetzen entsprechendNutzerauftrag; Quota-/Ressourcengrenzen einhalten.
