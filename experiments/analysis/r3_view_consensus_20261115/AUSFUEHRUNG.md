# Konsensprüfung reproduzieren

Die aktive Kursfassung bleibt getrennt. Für den Lauf die Quellen der ursprünglichen Diagonalbestätigung einschließlich Gegner und Abgabegewichten verwenden. Der Ordner des eingefrorenen Versuchs ist `/tmp/sherlock-r3-consensus.7719fz63`. `M` bezeichnet den Hauptcheckout, `W` die Studienkopie. Das erste Kommando berechnet ausschließlich auf vorhandenen Archiven.

```bash
cd /tmp/sherlock-r3-consensus.7719fz63
M=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15
W=/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15
RESULT="$M/experiments/analysis/r3_view_consensus_20261115"
REF="$W/experiments/analysis/r8_warm_20261115/validation.json"
MODEL="$M/experiments/candidates/movement_dagger_20261115/r3_soft.pth"
"$M/.venv/bin/python" -B -u -m scripts.r3_consensus_offline \
    --model "$MODEL" --data "$M/experiments/imitation/final_20261115_r3_context" \
    --reference "$REF" --out "$RESULT/audit.json"
```

Eine positive Offline-Auswahl eröffnet separat die fünf passiven Originalspiele. `trace` prüft dabei alte Quellstände, das Modell, die vollständige Veröffentlichung und jede reproduzierte Ergebniszeile. Erst wenn ein tatsächlich ausführbarer Eingriff bei einem Widerspruch vorlag, ist der getrennte Aufruf mit `candidate` möglich. Er spielt zehn vorab namentlich festgelegte Sitze. Die Einschätzung steht jeweils in `field/<Stufe>/assessment.json`. Einen frischen Test vor einer positiven gerichteten Auswahl registrieren wir nicht.

```bash
PHASE=trace
"$M/.venv/bin/python" -B -u -m scripts.r3_consensus_cases "$PHASE" \
    --offline "$RESULT/audit.json" --model "$MODEL" --reference "$REF" \
    --historical "$W/experiments/analysis/movement_reflection_20261115/confirm" \
    --archive "$W/experiments/analysis/movement_reflection_20261115/paired_validation.json" \
    --out "$RESULT/field"
```

Für einen neuen Rechner lässt sich der historische Quellbaum wie im [Wiederaufbau für den identischen Diagonalagenten](../movement_reflection_20261115/solution_quarter/REPRODUKTION.md) zusammensetzen. Die drei hier verwendeten Studienmodule sind `scripts/r3_view_consensus.py`, `scripts/r3_consensus_offline.py` und `scripts/r3_consensus_cases.py`. Diese zusätzlich in den Studienordner kopieren. Der ursprüngliche 144-Spiele-Datensatz enthält auch die Lehrerbewertungen auf den damals tatsächlich besuchten Zuständen. Die 48 Testdateien werden einzeln gegen ihre zuvor registrierten Prüfsummen geprüft.
