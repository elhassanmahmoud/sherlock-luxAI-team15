# Spielvergleich des R8-Mittelwerts

Beide ursprünglichen Diagnoseberichte, alle 96 archivierten Sitzdateien, die beiden Datensatzprotokolle, die vier Netzdateien sowie die Quellen des Fits sind vor Spielbeginn an ihre SHA-256 gebunden. Die Sitzzähler beider Berichte werden erneut summiert. Der Mittelwert trifft auf den alten Karten 99.107 von 156.243 Lehrerbefehlen, R3 98.938. Auf den neuen Karten lauten die Zähler 109.947 und 109.585 von 160.863. Die Differenzen beziehen sich auf die archivierte Rekonstruktion des R3-Befehls. Der vorliegende Einlass prüft die gespeicherten Zähler und Dateien. Die Netzvorhersagen stammen aus dem zuvor durchgeführten Fit-Audit.

Der R3- und der Mittelwertarm verwenden den gleichen ursprünglichen Forschungsagenten mit ausschließlich Bewegungseingriffen und unveränderter Schwelle 0,70. Für die V14-Basis und den direkten Gegner gelten der originale Produktionsagent, seine Gewichte und seine im Checkpoint gespeicherten Einstellungen aus der R3-Bestätigung. Alle drei ursprünglichen Laufmanifeste, einschließlich der Spiel- und Gegnerquellen, sind an ihre veröffentlichten Prüfsummen gebunden. Die importierten Hilfsquellen, die installierte Spielengine, Softwareversionen und Laufzeitvariablen werden vor dem ersten Spiel festgehalten. Die spätere Kursprüfung bleibt separat.

## Bedienung

Vom eingefrorenen Spielverzeichnis aus mit dem ursprünglichen Projektinterpreter starten. `PROJECT` ist der absolute Pfad des Projektverzeichnisses mit der Umgebung, den Gewichten und den gespeicherten Trainingsdaten. `OUT` ist ausschließlich der Ergebnisordner dieses Versuchs. Die erste Zeile prüft die Eingaben ohne ein Spiel. Die zweite startet die 224 Auswahlspiele mit einem Worker und schreibt die Auswertung. Der letzte Befehl steht für die getrennt anzusetzende Bestätigung. Er prüft vor dem ersten Spiel die tatsächlich gespeicherten 224 Spielschlüssel und die vollständig neu berechnete Auswahlentscheidung.

```sh
"$PROJECT/.venv/bin/python" -B -m scripts.r8_midpoint_games check screen --repo "$PROJECT" --out "$OUT"
"$PROJECT/.venv/bin/python" -B -u -m scripts.r8_midpoint_games run screen --repo "$PROJECT" --out "$OUT"
"$PROJECT/.venv/bin/python" -B -u -m scripts.r8_midpoint_games run confirm --repo "$PROJECT" --out "$OUT"
```

Für einen einzeln reservierten Arm gibt es `run screen --arm midpoint|v14|r3|direct`. `assess screen` prüft die beendeten Arme und schreibt die Auswahlentscheidung. Bei Unterbrechung kann derselbe Aufruf im selben Ergebnisverzeichnis fortgesetzt werden. `screen/assessment.json` und gegebenenfalls `confirm/assessment.json` enthalten Vollspielsiege, gewonnene Matches, gepaarte Wechsel und die Intervalle von 10.000 Ziehungen kompletter Karten (NumPy PCG64, Startwert 2711). In der Bestätigung spielen nur V14 und Mittelwert auf 60 gemeinsamen externen Karten und der Mittelwert auf 60 separaten Karten direkt gegen V14.

## Wiederaufbau der Spielkopie

Ein leeres Verzeichnis als `SNAP` anlegen. `SOURCE` bezeichnet das Checkout mit diesem Werkzeug und den historischen Git-Objekten. Die gebundenen Fitquellen liegen separat unter `fit_sources`, damit Importe des ursprünglichen R3-Agenten unverändert bleiben.

```sh
git -C "$SOURCE" archive 0105658188b2ec5eaf5c3a4b0ef477be9a1412f8 agents scripts lux | tar -xf - -C "$SNAP"
for f in final_battle_assess.py final_battle_select.py residual_ensemble_compare.py; do
    git -C "$SOURCE" show "9cf38ec6c9ee6c9d5946af42054fea83d4a6ce4c:scripts/$f" > "$SNAP/scripts/$f"
done
mkdir -p "$SNAP/fit_sources" "$SNAP/experiments/opponents"
git -C "$SOURCE" archive 3fd87a64 agents/sherlock/cnn_model.py agents/sherlock/imitation_net.py scripts/collect_combat_advice.py scripts/imitate.py scripts/r3_diagonal.py scripts/r8_warm.py scripts/r8_warm_assess.py scripts/selective_advice_agent.py scripts/selective_dagger.py scripts/train_combat_advice.py scripts/r8_midpoint.py | tar -xf - -C "$SNAP/fit_sources"
git -C "$SOURCE" archive 3fd87a64 experiments/analysis/r8_midpoint_20261115/PLAN.md 'experiments/analysis/movement_soft_20261115/confirmation/*/manifest.json' | tar -xf - -C "$SNAP"
cp -RL "$PROJECT/experiments/opponents/kaggle3_lux3_048fn" "$SNAP/experiments/opponents/"
cp "$SOURCE/scripts/r8_midpoint_games.py" "$SNAP/scripts/"
```
