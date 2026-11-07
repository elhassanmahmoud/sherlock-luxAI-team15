# Neue Ensemble-Mitglieder – Trainingsabschluss 07.11.2026

**Sechs neue Netze vollständig trainiert und unabhängig technisch geprüft. Noch kein Leistungsvergleich und kein Nachweis, dass Sherlock stärker geworden ist. V14 bleibt unverändert.**

Der neue Versuch `20261107_diversity_r1` lief vom 07.11. um 15:32 bis 23:48 Uhr Berlin auf dem unveränderten Quellstand `6ad34527673e29f0e50e2dacc917e5ded59f0343`. Alle sechs Prozesse endeten erfolgreich; eigene Trainings- und Wachhalteprozesse sind beendet.

## Was tatsächlich gerechnet wurde

| Arme | V14-Elternnetz | Je Arm Vorlauf / Lernen / Validierung | Lernupdates je Arm |
|---|---:|---:|---:|
| A0, B0 | 18 | 120 / 3000 / 128 | 450.000 |
| A1, B1 | 24 | 120 / 3000 / 128 | 450.000 |
| A2, B2 | 30 | 120 / 3000 / 128 | 450.000 |

Insgesamt **19.488 Spielausführungen und 2.700.000 Lernupdates** in r1. 18.000 Lernspiele verwenden 9000 Karten mit beiden Seiten; zusätzlich 720 Vorlaufspiele auf 360 separaten Karten. Die 768 bekannten Validierungsausführungen wiederholen acht feste Karten gegen zwei Gegner an vier Meilensteinen pro Arm. Sie sind kein frischer Ensemblevergleich.

A trainiert gegen Solution_92 / sol92_sq / default im Verhältnis 70/20/10; B gegen Solution_92 / sol92_weak / rush / default im Verhältnis 40/20/20/20. Die festen Zufallspläne bestimmen die tatsächlichen Häufigkeiten. A und B haben verschiedene Karten und Zufallsstarts, deshalb kein isolierter kausaler Vergleich der Gegnermischung. Alle Netze behalten die Architektur 79 → 256 → 256 mit Dueling-Ausgabe für sechs Aktionsklassen. Reward unverändert; Lernrate 0,00005. Trainingsregeln einschließlich Rettungslogik sind aktiviert; `art_splash` bleibt trotz dieser Flags eine reine Inferenzregel.

Der frühere, von Codex durch parallele Werkzeugtests unterbrochene Versuch bleibt separat: 4484 Ausführungen, 612.600 Updates, zwei nicht nominierbare Teilstände. Hinzu kommen 24 technische Smoke-Ausführungen mit 600 Updates. Gesamtaufwand dieser Studie bisher 23.996 Ausführungen; die Unterbrechung wird nicht als zusätzlicher unabhängiger Versuch oder Stärkegewinn gezählt. Der Neuanlauf reproduzierte die festgelegten Initialzustände, Pläne und geprüften frühen Lernstände.

## Prüfung und Artefakte

Der unabhängige [Lernaudit](../experiments/analysis/ensemble_diversity_20261107/operations/final_training_audit.md) regenerierte die chronologischen Karten-/Seiten-/Gegnerpläne und prüfte Rohzeilen, Zähler, Gewichte, Optimierer, Dimensionen, Quellen und Konfiguration. Alle sechs neuen Q-Zustände sind endlich, gegenüber ihren Eltern verändert und untereinander verschieden. Alle 24 protokollierten Validierungsgrenzen bewahren den Lernzustand. Historische Aktions-/RNG-Transkripte wurden nicht vollständig gespeichert; die Grenzen dieses Nachweises stehen ausdrücklich im Audit.

Die festen Kandidaten wurden gebaut und nach dem Speichern wieder geladen:

- **A39:** V14 plus A0/A1/A2.
- **B39:** V14 plus B0/B1/B2.
- **ALL42:** V14 plus alle sechs neuen Netze.
- **REPLACE36:** sechs vorab bestimmte alte Mitglieder ersetzt; ausschließlich Diagnose, nicht nominierbar.

Alle verwenden exakt die V14-Inferenzkonfiguration. [Kandidaten und Manifest](../experiments/candidates/ensemble_diversity_20261107/) sind experimentell. Unter `trained/` liegen zusätzlich bytegleiche Kopien der sechs vollständigen Endcheckpoints samt Herkunft/Prüfsummen für Mahmoud. Die großen Replay-Puffer und historischen Zwischencheckpoints bleiben lokal. Zur erneuten Zulassungsprüfung einer frischen Arbeitskopie können die sechs `trained/<Arm>.pth` anhand dieses Manifests in ihre ursprünglichen Run-Pfade `weights/agent.pth` kopiert werden; keine Abgabe-Datei überschreiben. Rohprotokolle und finale Receipts sind versioniert.

## Nächster Schritt und Ressourcen

**Noch null Auswahl- oder Bestätigungsspiele gestartet.** Der unveränderte [Vergleichsplan](superpowers/plans/2026-11-07-ensemble-comparison.md) verlangt 7800 vollständige Auswahlspiele. Höchstens ein qualifizierter Kandidat erhält anschließend 23.200 unabhängige Bestätigungsspiele. Die 100-%-Zielquote bleibt ein Ziel, keine zugesicherte Eigenschaft.

Beim Abschluss wurden 64 % Kontingentverbrauch gemessen. Die bisherige Nutzergrenze reserviert mindestens 30 %; ab 65 % soll keine neue Arbeit beginnen. Daher wird der mehrstündige Vergleich mit diesem knappen Spielraum nicht mehr neu gestartet. Die Rückfrage zur Fortgeltung der Reserve ist unbeantwortet; kein Reset und keine stillschweigende Aufhebung. Der wiederkehrende Remote-Abgleich ist für diesen gesicherten Zwischenstand pausiert. Vor Wiederaufnahme Kontingent, Netzstrom, Prozesse, Remote-Stand, Artefakthashes und neue Source-Freeze prüfen; keine Trainingswelle wiederholen. Auswahl und Bestätigung müssen denselben eingefrorenen Quellstand verwenden.

V14-Dateien unverändert: `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. Abgegebene ZIP unverändert: `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Beide lokalen Arbeitskopien wurden geprüft; keine neue Moodle-Abgabe.
