# HOLD-Lernversuch – Implementierung

Die vorherige Einflussprobe ist vollständig und unabhängig geprüft. Rohdaten: `decision_learning_20261108`. Der neue verbindliche Plan steht unter `docs/superpowers/plans/2026-11-08-holder-learning.md`.

Geplant sind 24 Trainingskarten und acht Validierungskarten, jeweils beide Seiten. `plan.json` bindet die genauen Schlüssel. Noch keine neuen Spiele, Labels oder Modelle; kein aktiver Source-Freeze. Zwei Subagents implementieren getrennt Lernarithmetik und Spielanbindung. Danach folgen unabhängiger Review und neutrale Spielprüfung, bevor Daten gesammelt werden. V14 und ZIP bleiben unverändert.

Aktive Arbeitskopie: `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15`, Branch `improvement/decision-learning-20261108`. Root koordiniert die Starts; keine zweite Instanz starten. Keine Tests parallel zu Modellspielen. Quellen und Inputs bleiben während der Messung eingefroren, der Kopf zusätzlich während der Validierung. Das restliche Kontingent ist freigegeben; Resets übernimmt ausschließlich Moayed.
