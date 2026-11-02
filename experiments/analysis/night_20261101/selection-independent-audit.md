# Unabhängige Auswahlprüfung: vollständig und bestätigt

**Datenabnahme BESTANDEN. Einziger Nominee: `control`. Noch keine Bestätigung oder Übernahme.**

Der vorab außerhalb des Worktrees vorbereitete Prüfer wurde genau einmal nach der vollständigen Phase ausgeführt. Exit0, Laufzeit ca.0,31s. Ausschließlich CSV/JSON/NumPy und Git-HEAD-Lektüre; keine Spiele, Modelle, Tests, Subagents oder Quelländerungen.

Bestätigt wurden alle sieben Jobs und3100Spiele, jeweils vollständige erwartete Schlüssel auf50Karten831000–831049 mit beiden Seiten,303Steps/v2 und kohärente endliche Ergebnisse. Originalphase, Journal, Commands, Zulassungsbelege, Interpreter, Gewichte und Quellfreeze stimmen mit den vorab gepinnten SHA-Bindungen und HEADaa06601 überein. Kein Job, Gegner oder Kartenausschnitt fehlt.

Kennzahlen und Intervalle wurden unabhängig von den Repository-Statistikfunktionen berechnet: ganze Karten als Bootstrapeinheit, beide Seiten und beim Panel alle sechs Gegner gemeinsam;5000Ziehungen, RNG0,2,5/97,5Perzentile. Alle Kennzahlen, absoluten Siege/Remis/Niederlagen, Gates und Nominierung stimmen innerhalb1e-12 numerisch bzw. exakt boolesch mit dem offiziellen vollständigen Bericht überein.

| Kandidat | Paneldelta | Solutiondelta | default | direkt V14 | zugelassen |
|---|---:|---:|---:|---:|---|
| overlap | -0.33pp | +0.00pp | 100.0% | 50.0% | nein |
| control | +4.83pp | +1.00pp | 100.0% | 62.0% | ja |
| discovery | -0.33pp | +2.00pp | 100.0% | 45.0% | nein |

Der höchste zugelassene Panelwert nominiert `control`. Die festgelegte A/B/C-Reihenfolge wäre bei Gleichstand verwendet worden; kein Nachrücken nach einer später gescheiterten Bestätigung. Der stärkere Entdeckungsreward wird durch diese Auswahl nicht als Verbesserung bestätigt.

Maschinenlesbarer unabhängiger Bericht: `selection-independent-audit.json`; offizieller Vergleich darin mit `matched:true`. `promotion_qualified:false` ist korrekt, weil diese50Karten die Auswahl und keine unabhängige Bestätigung sind. Als nächster Schritt ausschließlich derselbe nominierte Kontrollkandidat auf den vorab geänderten200neuen Bestätigungskarten, nach Manifest-/Audit-Pin vor den ersten Spielen.
