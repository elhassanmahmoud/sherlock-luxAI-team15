# HOLD-Einflussprobe implementieren und ausführen

Spec: [Entscheidungslernen](../specs/2026-11-08-decision-learning.md). Autorisiert autonom einschließlich Umsetzung, Prüfung, kleiner Diagnose und evidenzabhängiger Fortsetzung. Bestehende Abgabe unverändert.

## Task 1: isolierte Probe mit gezielten Tests

Neue Dateien `scripts/holder_rollout.py`, `scripts/holder_rollout_probe.py`, `tests/test_holder_rollout.py`; keine Produktionsagenten-/Gewichtsänderung.

1. TDD: synthetische Eligibility-/Grenztests, gemeinsame Objektgraphkopie/Referenzrestauration, Zufallszustände und Exceptions. Bestehende Umgebung und helpers verwenden, keine neue allgemeine Frameworkschicht.
2. DiagnosticAgent-Unterklasse fängt `_rule_override` ab. Passiver Modus sammelt Kandidaten; Intervention ist unveränderlicher (Schritt, UID)-Auftrag am geklonten Agenten. Eligibility wie Spec; Q/öffentlichen Kontext für spätere Interpretation speichern, keine Lehrermodelle trainieren.
3. Vor beiden act-Aufrufen Snapshot; Liveaktionen einmal ausführen. Bei Auswahl Baseline/HOLD von pre-act-Kopie starten und anschließend den post-act Livezustand exakt restaurieren. Umweltbranch zwölf Schritte, nur erste Intervention. Originalspiel mit zuvor berechneten Liveaktionen fortführen. Baselinebranch gegen Livezukunft vergleichen.
4. Exakte game-/frame-/state-/action-/point-Digests und NDJSON-Paarbelege streamen, Vollständigkeit/Passivität fail closed. Referenzlauf ohne Snapshot/Hook muss bytegleiches Spiel ergeben. Erste geeignete Situation je Spiel zusätzlich Reverse-/Repeatcheck, technische Zusatzschritte separat zählen.
5. CLI: `--weights`, `--keys`, `--out` (neu/exklusiv), `--expected-head`, `--usage-file`, `--stop-file`. Alle zwölf bekannten Keys explizit planbindend; `--technical-smoke` für die beiden bekannten Schlüssel831006/player_1 und831043/player_0 (beide Seiten, bekannte Abzugssituationen), je Referenz- und Sammelspiel mit höchstens einem Paar je Spiel, getrennte Ausgaben. Es gibt keinen Resume/Overwrite. Laufstatus, source/inputs/protected hashes, Zeit/Prozess-ID, Fertigzähler; Guard vor Spiel und regelmäßig zwischen Paarschritten: STOP, fresh usage<100, AC, unveränderte Quellen/HEAD/Gewichte. Bestehende helpers wiederverwenden. Kein automatisches Training/Promotion.
6. Selbstprüfung, gezielte Unit-Tests und Reviewpaket. Keine ganzen Spiele während Implementierung. Root lässt unabhängig prüfen und führt erst danach echte technische Smoke-/Passivitätsläufe aus. Fehler vor Diagnoselauf beheben, alte Teilbelege erhalten.

## Task 2: unabhängige Abnahme und feste Diagnose

Root prüft Diff und einschlägige Tests, Reviewer kontrolliert Klon/RNG/Global-Grenzen, Labels und exakte Spec. Protokoll und Werkzeug sinnvoll committen/pushen, Remote abgleichen. Höchstens zwei bekannte technische Smokeschlüssel, danach genau zwölf bekannte Paare wie Spec. Keine parallelen Tests, Quelle eingefroren. Tatsächliche Fertigstellungen und Teil-/Zusatzschritte protokollieren.

## Task 3: Datenprüfung und Weiterarbeit

Unabhängig Zahl/Identitäten/Passivität und Labelarithmetik prüfen. Ergebnis und Unsicherheit in Arbeitsstand/Experimentprotokoll für Mahmoud dokumentieren. Machbarkeitsfilter aus Spec unverändert anwenden. Bei Bestehen separaten kleinen Lernplan erstellen und ausführen; andernfalls nächste konkrete SAP-/Energiediagnose planen. Keine alte Studienwiederholung, keine unbestätigte Abgabeänderung. User will fortlaufende Arbeit, nicht Ende beim Prototyp.
