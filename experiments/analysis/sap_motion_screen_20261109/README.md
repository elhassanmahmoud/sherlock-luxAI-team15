# Separater SAP-Bewegungsvergleich, 09.11.2026

Ein öffentliches fünfklassiges Bewegungsmodell ergänzt V14 ausschließlich in der experimentellen Eval-Unterklasse. Es zählt abgeschlossene Bewegungen im aktuellen Spiel, berücksichtigt mögliche verlorene Nebentreffer und verändert höchstens einen SAP-Offset pro Schritt. Die 36 Netze werden nicht nachtrainiert. V14 und ZIP bleiben unverändert.

[Vorab festgelegte Methode und Grenzen](../../../docs/superpowers/plans/2026-11-09-sap-motion-model.md). Vier bekannte Technikspiele müssen OFF exakt reproduzieren und mindestens einen realen ON-Eingriff zeigen. Anschließend separat aufgenommene120Spiele: je40OFF/ONgegenSolution auf9942000–9942019 und40direkt auf9942100–9942119. Keine Nachschläge oder automatische Übernahme.

Implementiererprüfungen:70Agent-/Hooktests PASS in2,37s und30engeRunnertests PASS in0,24s. OriginaleLogs unter preparation. Unabhängiger enger Review und Root-Code-/Hashprüfung PASS; Belege in preparation. Diese Vorbereitung enthält noch keine Leistungsspiele. Der Kartencheck fand keine beobachteten Konflikte; seine Datenlücken bleiben im seed-review.md ausdrücklich erhalten. Nutzer erlaubt Akkubetrieb, alle übrigen Laufkontrollen bleiben aktiv.
