# Sherlock: begrenzte Planungs-/Artillerieprototypen

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Aufgaben einzeln prüfen.

**Goal:** Die zwei tatsächlich beobachteten Mechanismen abschaltbar umsetzen,
ohne V14 zu ersetzen oder neue Leistungsdaten vorab anzusehen.
**Architecture:** Ein früher Artillerie-Guard und ein reiner einzelner
Eigentümertausch vor der Merkmalsbildung; beide Default aus.
**Tech Stack:** vorhandenes Python/NumPy/PyTorch, keine neuen Abhängigkeiten.
**Spec:** `docs/superpowers/specs/2026-11-02-targeting-prototypes-design.md`.

## Global Constraints

- Keine Gewichts-, Reward-, Kursrunner- oder Gegneränderung.
- Flags `art_move_guard=False`, `point_pair_swap=False`; keine neuen79 Features.
- Nur öffentliches Wissen; höchstens ein Eigentümertausch/Step und120 Paarprüfungen.
- Maximal zwei schwere Worker; kein Volltest parallel zu Modelljobs.
- Akku freigegeben, unter35% keine neue lange Phase, bei25% schwere Jobs beenden.
- Mindestens30% Kontingent behalten; kein Reset. Ende03.11.,06:00 Berlin.

## Review Focus

- SAP ursprünglich vom Netz gewählt darf nicht zum Bewegungsfallback werden.
- Erhaltener Zug durchläuft vorhandene spätere Nebel-/Gefahrenprüfungen.
- Dead Legacyholder darf lebenden produktiven Halter nicht freigeben.
- Tausch ändert weder Zielset noch Gegner-/Kandidatenprioritäten und nie zwei Paare.
- Merkmale/Q müssen das neue Ziel sehen, Masken/Cache dürfen nicht veralten.

## Task 1: gemeinsame kleine Implementierung

- [ ] Rote Verhaltenstests für die in der Spec genannten Fälle schreiben.
- [ ] Reinen Helper `agents/sherlock/assignment.py`, zwei Configflags und minimale
  Pipelineeinbindung in `main.py` implementieren. Tests in
  `tests/test_targeting_prototypes.py`; keine anderen Schreibbereiche.
- [ ] Fokussierte Tests, unabhängiges Review, dann zentral koordinierter Volltest
  ohne gleichzeitigen Modelllauf. Keine realen Spiele durch den Implementer.
- [ ] Nur die vier eigenen Dateien committen und Prüfungen/Limits berichten.

## Task 2: technische Spiele und Entscheidung

- [ ] Quelle/Configs pinnen, Default-off-Aktionen auf12 bekannten Schlüsseln gegen
  die alten Rohmanifesthashes vergleichen; aktivierte Smoke-Schlüssel vorher fixieren.
- [ ] Nur nach bestandener Technik Leistungs-/eventuellen Trainingsnachtrag fixieren.
  Neue Gewichte ausschließlich Experimente; Gates aus Fortsetzungsplan unverändert.
