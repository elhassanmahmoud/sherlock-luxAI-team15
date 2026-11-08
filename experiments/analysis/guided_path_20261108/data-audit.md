# Unabhängiger Datenabschluss: PASS

**69683 Prüfungen bestanden**, eigenständiger 90-Zeilen-Stdlib-Audit, Exit 0. Grundlage sind `golden.jsonl`, `opportunities.jsonl`, `summary.json`, `bindings.json` und die genaue Root-Freigabe. Keine erneute Helferimplementierung, keine Modelle, pytest, Spiele oder Repoänderungen.

- Alle **22258 Goldenzeilen** haben identische historische/neuberechnete Rückgabe; **541** unterscheiden sich von ihrer Eingangsaktion. Identitäten und Reihenfolge sind eindeutig; Spiel-, Schritt-, UID- und Aktionsgrenzen stimmen.
- Alle **343 hypothetischen Änderungszeilen** sind eindeutig, verwenden verschiedene erlaubte Bewegungsklassen und weisen die berichtete BFS-Richtung auf. Zielklassen unabhängig aus diesen Zeilen nachgezählt: **144 Punktefeld**, **90 Kandidat**, **109 Erkundung**.
- Änderungen betreffen **303 verschiedene Partie-Schritte**, alle **12 archivierten Ausführungen**, **7 verschiedene Kartenseeds**. Nach ursprünglicher Auswahlgruppe: 142 auf bekannten Niederlagen, 201 auf den Kontroll-/Siegspuren; keine repräsentative Gruppenvergleichsaussage.
- Je Spiel und Match stimmen Zeilenzählung, Klassensummen und Änderungszähler exakt mit der Zusammenfassung überein. Berichtete Rahmenzahlen sind konsistent: **3636 Frames = 3600 Entscheidungen + 36 Resets**. Nennerpartitionen: **41937 = 41215 zugewiesen + 722 ohne Ziel**; **41215 = 22125 deterministische geführte Züge + 19090 ohne solchen Zug**.
- Eingangs-, komprimierte Archiv-, Script-, Approval- und Ergebnis-Hashes sowie aktueller Freeze-HEAD geprüft; alle Input-/Outputbindungen vor/nach Audit unverändert. Gemeldete Diagnosezeit 23,2769 Sekunden liegt unter der gebundenen 120-Sekunden-Grenze.

| Seed / Seite | Hypothetische Änderungen |
|---|---:|
| 831006 / player_1 | 30 |
| 831029 / player_0 | 24 |
| 831042 / player_0 | 5 |
| 831042 / player_1 | 6 |
| 831043 / player_0 | 19 |
| 831043 / player_1 | 58 |
| 831000 / player_0 | 90 |
| 831000 / player_1 | 35 |
| 831001 / player_0 | 27 |
| 831001 / player_1 | 36 |
| 831002 / player_0 | 5 |
| 831002 / player_1 | 8 |
| **Summe** | **343** |

**Grenzen:** Dieser enge Folgeaudit prüft die ausgegebenen Goldenwerte und zählt die Änderungs-JSONL neu. Er dekomprimiert die zwölf Archive nicht erneut und berechnet weder die Helfer noch sämtliche Unit-/Frame-Nenner unabhängig neu; deren Vollständigkeit stützt sich zusätzlich auf den vorher geprüften Runner und dessen vollständigen Lauf. Die Nenner wurden hier auf arithmetische Konsistenz geprüft. Die gespeicherte Zielklasse wird nachgezählt, nicht nochmals aus der ursprünglichen Karte abgeleitet.

`343 × 0,035 = 12,005` ist exakt bestätigte **theoretische Masse über zwölf alte Ausführungen**, kein beobachteter Trainingsanteil und keine Zahl geänderter finaler Aktionen. Die 343 Fälle entsprechen rund 1,55 % der berichteten deterministischen geführten Gelegenheiten in dieser ausgewählten Stichprobe. Zustandsverläufe, weitere Regeln und Zufallsfallbacks bleiben außerhalb der Aussage. Ein vorläufig niedrigerer Platz in der Priorisierung ist damit vertretbar; fehlende Lernwirkung oder Unwirksamkeit ist dadurch nicht bewiesen.

Maschinenlesbare Einzelzählungen und Hashinventar: `/tmp/guided-path-data-audit.json`. Reproduzierbarer Auditor: `/tmp/guided-path-data-audit.py`.
