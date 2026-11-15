# Technik und Reproduktion

Ein geeignetes Python-Environment ist die lokale Spielumgebung aus der durch 606 Aktionsmatrizen geprüften Kursparität. Der Aufruf `check` lädt keine Netze. Die Monate später eventuell neueren Python-, Torch- oder Lux-Versionen würden eine andere Umgebung ergeben und an der Prüfung scheitern. Die beiden Referenz-CSV stehen unter `experiments/analysis/umbau_20261115/confirm`. Die lokal erzeugte Diagonal-Kurs-ZIP, das R3-Gewicht und der native Kaggle-Gegner müssen vorhanden sein. Der Kaggle-Gegner ist Teil des überprüften historischen Quellenmanifests; er spielt im neuen Vergleich keine Partie.

Folgendes Beispiel baut den Quellenstand aus Git in einem leeren, temporären Verzeichnis nach. Am Anfang im vollständigen Projekt mit den lokal erzeugten Studienartefakten arbeiten. Der bestehende Checkout und laufende Spiele bleiben erhalten.

```bash
repo=$(pwd -P)
frozen=$(mktemp -d)
git archive 0105658188b2ec5eaf5c3a4b0ef477be9a1412f8 agents scripts lux | tar -x -C "$frozen"
git show aa5cd60:scripts/r3_diagonal.py > "$frozen/scripts/r3_diagonal.py"
git show d635551:scripts/r3_diagonal_games.py > "$frozen/scripts/r3_diagonal_games.py"
git show 3f3fd45:scripts/r3_shared_confirmation.py > "$frozen/scripts/r3_shared_confirmation.py"
cp scripts/r3_diagonal_quarter.py "$frozen/scripts/"
mkdir -p "$frozen/experiments/opponents" "$frozen/references" "$frozen/agents/sherlock/weights"
cp -R experiments/opponents/kaggle3_lux3_048fn "$frozen/experiments/opponents/"
cp agents/sherlock/weights/agent_p0.pth "$frozen/agents/sherlock/weights/"
cp experiments/candidates/movement_dagger_20261115/r3_soft.pth "$frozen/references/"
reflection=experiments/analysis/movement_reflection_20261115
shared=experiments/analysis/movement_soft_20261115/shared_400/measured
cp "$reflection/confirm/diagonal/manifest.json" "$frozen/references/original.json"
cp "$reflection/confirm/assessment.json" "$frozen/references/previous.json"
cp "$reflection/course/kursvergleich.json" "$frozen/references/parity.json"
cp "$reflection/course/r3-diagonal-course-candidate.zip" "$frozen/references/diagonal.zip"
cp "$shared/reproduction.json" "$frozen/references/reference_reproduction.json"
cp "$shared/r3/manifest.json" "$frozen/references/original_r3_400.json"
out="$repo/$reflection/solution_quarter/diagonal"
cd "$frozen"
unset CUDA_VISIBLE_DEVICES JAX_PLATFORMS PYTHONHASHSEED XLA_FLAGS
"$repo/.venv/bin/python" -B -m scripts.r3_diagonal_quarter check --repo "$repo" --out "$out"
```

Im selben Verzeichnis führt `play` anstelle von `check` die genau 200 vorgesehenen Spiele aus und setzt einen vorhandenen, vollständig lesbaren Präfix mit gleichem Manifest fort. Bei bereits versiegeltem Lauf prüft es die vorhandenen Ergebnisse. `assess` liest die beiden CSV und die ersten 400 vollständigen, geordneten Zeilen der schon laufenden Original-R3-Reihe. Je zwei Zeilen pro Karte enthalten den Vergleich gegen Solution. Abweichende Reihenfolge, Prüfsummen oder unvollständige Daten beenden die Auswertung.
