# Entscheidungslernen 08.11. – Vorbereitung

Neuer ausdrücklicher autonomer Auftrag nach abgeschlossener Ensemble-Studie. Aktiver Worktree `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15`, Branch `improvement/decision-learning-20261108`. Kein Modelllauf gestartet. Implementierung/gezielte Tests laufen; vor Spielen separate unabhängige Prüfung und Freeze.

Plan: `docs/superpowers/plans/2026-11-08-holder-rollout-probe.md`; Spec daneben unter specs. Zunächst genau zwölf bekannte Spiele zweimal, maximal96 gepaarte12-Schritt-Fortsetzungen, getrennte technische Smokeprüfung. Bestehendes V14/ZIP unverändert. Source-Freeze erst mit dokumentiertem Laufstart; keine zweite Instanz oder parallelen Modelltests.

Historische Diagnose unter origin: Auffällige Halterabzüge fast immer mit Energie/Kampfdruck. Kein kausaler Fehlernachweis; kein Grund für blanket hold. Tatsächliche alternative Folgen messen, erst danach eventuell kleinen Korrekturkopf trainieren. Bei negativem Machbarkeitsfilter getrennte Energie-/SAP-Diagnose; alte Studien bleiben geschlossen.
