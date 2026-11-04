# Aktionsbezogener Schüler, 04.11.2026

**Abgeschlossen: A2 verbessert das Ausgangsnetz S30; V14 bleibt die Abgabe.** Alle 2.452 neuen Spielausführungen sind dokumentiert, darunter 1.400 vollständige Diagnosepartien. A2 und V14 gewinnen auf den neuen Solution-Karten jeweils 38/40, S30 16/40. A2 liegt im Panel bei 94/120 gegenüber V14 mit 98/120 und direkt gegen V14 bei 14/40. Kein qualifizierter Ersatz, keine Bestätigung und keine nachträgliche Modellauswahl.

[Vollständiger deutscher Bericht](../../../docs/AKTIONSSCHUELER_20261104.md) · [Datenreview](diagnostic/diagnostic_review.md) · [Statistik-JSON](diagnostic/diagnostic_review.json) · [Root-Gegenprüfung](diagnostic/root_crosscheck.json) · [Modelle](../../candidates/action_student_20261104/README.md).

- `collection/r1,r2`: Originaldatensätze, Manifeste, Spiele und Status. 425.102 Zeilen mit echten Merkmalen/Masken und Lehrerbewertungen; portable relative Datasetdateien für das Lernwerkzeug.
- `fitting/r1,r2`: vollständige Lernmanifeste und Metriken; 30 Aktions- plus fünf Wertkopf-Epochen je Runde.
- `rl/seed27,seed28`: Originalmanifeste, 232 Spiele je Arm, Protokolle/Receipts und unabhängige Prüfung; je Verzeichnis ein Manifest sämtlicher Kopien. `rl/independent_summary.json` fasst vier Arme, 928 Ausführungen und 96.000 Updates zusammen.
- `diagnostic`: alle 17 Original-CSVs, Lauf-/Start-/Deadline-Nachweise, unabhängige Auswertung und 288 numerische Gegenprüfungen.
- `preflight`: vorab feste Vergleichsliste, Seeds, Inventar, technische Beobachterprüfung, 136 Tests, Quellreviews und unveränderte Auditprogramme. `prepare_diagnostic_draft.py` ist ein erhaltener, nicht ausgeführter früher Entwurf; tatsächlich verwendet wurde `prepare_diagnostic.py`.

Originalmanifeste behalten ihre tatsächlichen absoluten Entstehungspfade. Archivzuordnungen und Prüfsummen zeigen die kopierten Dateien; nicht jeder historische lokale Pfad existiert auf einem anderen Rechner. Die .gitattributes bewahrt die ursprünglichen Bytes. Große originale Replay-Puffer bleiben lokal im Studienworktree; keine vollständige Wiederherstellung ihrer früheren Inhalte behauptet. Frühere Studien und ihre Resultate unverändert erhalten. Veröffentlichung und Betriebsabschluss im gemeinsamen Arbeitsstand.
