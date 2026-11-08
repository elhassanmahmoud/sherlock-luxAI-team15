# Gepaarte Fog-Reward-Studie umsetzen

Spec: [Fog-Reward](../specs/2026-11-08-fog-reward.md). Autorisierter neuer Versuch nach abgeschlossenem HOLD-Kopf. V14-Rohgewichte/ZIP unverändert, kein pauschaler SAP0- oder neuer Ensemble-Suchlauf.

## Task 1: Herkunft und optionaler Reward

Schreibbereich: `agents/sherlock/config.py`, `agents/sherlock/main.py`, `agents/sherlock/reward.py`, neue `tests/test_fog_unknown_reward.py`.

TDD mit unverändertem Default, bekannt positiv/Null, unbekannt, Gewicht0, deaktiviertem Shaping, Tod/Terminal. Die vorhandene Fünf-Argument-Aufrufweise bei Flag False bewahren. Numerisches SAP-Tupel nicht ändern. Finale Herkunft über Tupelidentität nach allen Regeln nachweisen; Ersetzung einschließlich gleicher Koordinaten, Abbruch, Bewegung, nächster UID/Frame/Reset testen. Native Aktionen, vorherige Aktionen, Masken, numerische Trefferschätzungen und alte Statistiken bleiben bei beiden Flagwerten gleich. Nur die neue Provenienzmenge und der ausdrücklich gewählte Trainingsreward dürfen abweichen. Keine vollständigen Spiele während Implementierung. Kein Ändern anderer Trainer oder Gewichte.

## Task 2: fester Trainingslauf und Audit

Schreibbereich: neue `scripts/fog_reward_study.py`, bei sinnvoller Trennung `scripts/fog_reward_supervisor.py`, `tests/test_fog_reward_study.py`. Bestehende Studien nicht ändern; geprüfte Hilfsfunktionen aus ensemble_diversity_train/student_reward_train/final_training_supervisor wiederverwenden, alte Konstanten/Dateien nicht überschreiben. Vorhandenes `finetune` mit lokal begrenzten und finally-restaurierten Hooks nutzen, oder enges gleichwertiges Vorgehen begründen. Keine neue allgemeine Trainingsplattform.

1. Vorbereitung exklusiver neuer Verzeichnisse: V14-SHA prüfen, genau Komponente18 extrahieren, vier identische Q/Target-Starts und leeren Adam/Replay nachweisen. Feste Quellkonfiguration mit nur Flag-Unterschied pro Paar, vollständige Karten-/Seiten-/Gegnerpläne binden. RNG41/42, lr5e-5,40 Vorlauf/400 Lernen/initial+final je16 bekannte Diagnosespiele. Nur finalen Stand, kein bestes Modell wählen.
2. Provenienzbewusster Reward-Audit: beide Rewardformeln auf demselben Übergang vergleichen; tatsächliche finale `_sap_unknown` lesen, keine Schüsse anhand alter `hits==0`-Zähler erraten. Jede Abweichung fail closed. Alte numerische Hit-Zähler zusätzlich behalten. Pro Spiel Anzahl/Masse unbekannter Rewards, Lernen/Updates und exakte Inferenz-/Rolloutkennungen speichern.
3. Vorlaufbeleg mit unveränderten Parametern/Optimizer, explicit unknown>0, vollständigen Trajektorien- und Replay-ohne-Reward-Hashes. Wenn beide Paarbelege vorliegen, Supervisor vergleicht sie unabhängig vom späteren Ergebnis. Keine weiteren Starts bei unpassendem Vorlauf, laufende eigene Jobs kontrolliert stoppen. Teilstände behalten, keine Wiederaufnahme ohne neuen Plan.
4. Maximal zwei eigene Modellprozesse, beide Gegenstücke zuerst gemeinsam starten. Vor/zwischen Spielen Quelle/HEAD/Inputs/Abgabehashes/STOP/AC/frischen Usage<100/Fremdprozesse prüfen. Quellen bis Ende eingefroren; Signale stoppen kontrolliert an Grenzen, keine fremden Prozesse beenden. Eigene PID/PGID/Kommandos und Wachhalten speichern. Bestehende Eigentums-/Prozesshilfen wiederverwenden, keine blinden kill-Befehle.
5. Vollständige Endbelege:440 Rollouts+32 Diagnosespiele pro Arm,60000 Updates, endliche veränderte Q/Target/Adam, finaler Checkpoint+Konfiguration/Hash. Validierung darf Lernzustand/RNG nicht verändern und verwendet ursprüngliche V14-Inferenzkonfiguration (neues Flag False). Paarwirkung nur beschreibend, noch keine Promotion. Technische smoke-Option höchstens kurze neue Mechanikprobe, klar getrennt/nicht nominierbar.
6. Fokussierte synthetische Tests für Zeitplan/Flags/Arme, Vorlaufpaarprüfung/Fehler, Reward-Audit/Replays, Hash-/Quoten-/Prozessschutz und Vollständigkeit. Keine Modellspiele während Implementierung. Neue Dateien begrenzen; bestehende Prüfwerkzeuge verwenden.

## Task 3: Integration und wirkliche Ausführung

Root: A+B unabhängig prüfen und gezielt testen; alte Reward-/Agentprüfungen passend einbeziehen, keine volle unnötige Wiederholungsserie. Zwei bekannte vollständige V14-Spiele (beide Seiten) mit neuen Defaultquellen gegen archivierte unveränderte Referenzverläufe prüfen; optionale Flag-Inferenzgleichheit zusätzlich, getrennt zählen. Eingaben/Karten unabhängig prüfen und Werkzeuge committen, dann Quellen einfrieren. Erst danach den festen vierarmigen Lauf starten, max2 Prozesse. Subagents überwachen Remote/Quota und auditieren Daten ohne parallele Tests.

Nach vollständigem technischen Nachweis und allen Trainings: getrennten kleinen frischen Vergleich für zwei feste38-Netz-Kandidaten (V14+CONTROL41/42 bzw.V14+NEUTRAL41/42) vor Ergebnissen beschließen. Kein automatischer Gewichts-/Abgabetausch; zuerst tatsächliche Stärke, unabhängiger Audit, reproduzierbare Kursprüfung und Sicherung. Falls Reward-Mechanik nicht wie spezifiziert greift, Ursache klären und diesen Versuch nicht als bestanden ausgeben. User will autonome Weiterarbeit; alte negative Studien bleiben geschlossen.
