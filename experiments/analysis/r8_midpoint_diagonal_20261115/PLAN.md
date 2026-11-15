# Das feste Gewichts-Mittel aus zwei Blickrichtungen

Geprüft wird dieselbe bereits vor der Spiegelstudie gespeicherte Netzdatei (SHA-256 `51a52f0453d5ac8e9a4ea70b3792572356761054cb2890520005160f77097cf2`). Die Parameter stammen je zur Hälfte aus den beiden unverändert registrierten R8-Nachtrainingsläufen. Der [ursprüngliche Versuch](../r8_midpoint_20261115/PLAN.md) prüfte diese einzelne Datei mit nur einer Kartenansicht. Das gesonderte [Nachtraining mit gespiegelten Beispielen](../r3_trained_reflection_20261115/ERGEBNIS.md) scheiterte auf beiden Kartensätzen.

**Eine Änderung bei der Ausführung.** Dasselbe feste Netz bewertet die Originalansicht und die an der Hauptdiagonalen gespiegelte Ansicht. Die sechs Rohwerte werden wieder in die Originalrichtungen übersetzt und gemittelt. Die gemeinsame Aktionsmaske, 70-%-Schwelle und V14s Schüsse bleiben wie beim bereits gemessenen Diagonal-R3. Kein Training, kein weiterer Mischanteil, keine neuen Parameter.

**Archivvergleich vor der ersten Inferenz registriert.** Alle drei Varianten sehen dieselben 96 Sitzarchive auf 24 älteren Diagnosekarten 7272200–7272223 und 24 R3-On-Policy-Diagnosekarten 7287100–7287123. Der eine Kontrollarm ist der ursprüngliche Diagonal-R3, der andere das Gewichts-Mittel mit Einzelansicht. Auf identischen, komprimierten Eingaben und für dieselben ursprünglichen V14-Befehle müssen ihre tatsächlich auszugebenden Aktionsklassen die bereits registrierten Kontrollzahlen je Sitz reproduzieren. Die primäre Zielgröße ist die endgültige Aktionsklasse des Lehrers nach Fallunterscheidung für Maske, Schüsse und Sicherheit. Pro Kartensatz und Kartensitz werden neu gewonnene oder verlorene Lehrerübereinstimmungen sowie verletzte vorher richtige V14-Befehle ausgewiesen. Der Kandidat muss auf beiden Sätzen mindestens den Diagonal-R3 erreichen, auf mindestens einem strikt darüber liegen und über beide Sätze in Summe wenigstens die korrekten Einzelansicht-Midpoint-Befehle erreichen. Alle Bedingungen gelten gemeinsam; kein Nachtraining oder weiteres Ausprobieren von Mischungen bei einem Fehlschlag. Aus Archiven folgen keine neuen Spielsiegquoten.

**Nur bei Bestehen des Archivs.** Bereits registrierter Entwicklungssatz 7170230–7170245, beide Sitze, externe Gegner Solution und Kaggle, direkter Gegner V14. Bereits absolvierte Sitzprüfungen des ursprünglichen Single-Midpoint-Panels für V14, Einzelansicht-R3 und Einzelansicht-Midpoint werden einmal verifiziert und wiederverwendet. Für einen noch laufenden Baseline-Versuch dessen fertiges Ergebnis abwarten. Für das neue Panel maximal 64 externe Spiele des Diagonal-R3 und 96 Spiele des Zwei-Ansichten-Midpoints (64 extern und 32 direkt). Für ein positives Screening muss der Zwei-Ansichten-Midpoint extern besser als beide unmittelbaren Referenzen (Einzelansicht-Midpoint und Diagonal-R3) sowie mindestens zwei Siege besser als V14 abschneiden. Gegen Solution muss er alle drei mindestens erreichen, direkt gegen V14 mehr als die Hälfte gewinnen. Einzelansicht-R3 wird zum Einordnen berichtet. Eine unabhängige Bestätigung wäre danach gesondert zu registrieren. Kursagent und Abgabe sind keine Ausgabepfade dieser Prüfung.

```bash
M=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15
"$M/.venv/bin/python" -B -u -m scripts.r8_midpoint_diagonal_audit \
  --r3 "$M/experiments/candidates/movement_dagger_20261115/r3_soft.pth" \
  --mid "$M/experiments/candidates/r8_warm_20261115/midpoint.pth" \
  --old "$M/experiments/imitation/final_20261115_movement_dagger" \
  --new "$M/experiments/imitation/final_20261115_r3_context" \
  --out "$M/experiments/analysis/r8_midpoint_diagonal_20261115/validation.json"
```
