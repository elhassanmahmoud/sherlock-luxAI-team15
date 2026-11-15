# Aufnahme und Auswertung

Die Spielaufnahme nutzt dieselbe V14- und R3-Implementierung wie die ursprüngliche Bewegungsstudie. Der eingefrorene Sammler speichert zusätzlich die nativen Lehrerbewertungen über `--raw-teacher`. Sein Aufnahmeprotokoll mit R3 als spielendem Agenten hat den SHA-256-Wert `3476e80f57ff23f76fb4d8aa00269e647116ca9c468c0d2d0f6278af85567a03`. Das reine Aktionsprotokoll mit denselben Quellen und demselben R3 hätte den Wert `ae1d8f695ccef339cc7c6b6dd73cf190fe9fa76f3823f0f0a44a459950d34990`. Der Fit prüft den festgelegten Aufnahmehash und pro Archiv die vollständigen Spuren. Für seine 36 Kontextentscheidungen liest er weiterhin nur den endgültigen Lehrerzug. Beide gespielten Seiten, alle 303 Schritte, die Lehrerbefehle und die Befehls-Rückmeldung werden pro Archiv geprüft.

```bash
python -m scripts.selective_dagger collect --raw-teacher --parent "$R3" --out "$DATA" \
  --train-first 7287000 --train-count 48 --val-first 7287100 --val-count 24 --workers 1
python -m scripts.r3_context_study fit --data "$DATA" --out "$RESULTS"
python -m scripts.r3_context_study assess --data "$DATA" --out "$RESULTS"
```

`R3` ist der veröffentlichte `r3_soft.pth`-Checkpoint. `DATA` bezeichnet `experiments/imitation/final_20261115_r3_context`, `RESULTS` ein Ergebnisverzeichnis, beispielsweise `experiments/analysis/r3_context_selector_20261115/fit`. Beim Fit werden ausschließlich die 96 Lernarchive geöffnet. Die Validierung reproduziert zuerst das Trainingsergebnis, bevor sie die übrigen 48 Archive liest. `table.json` enthält 36 Wahrheitswerte in fester Reihenfolge. Die ID ergibt sich aus `((Halten × 2 + Punktfeld) × 3 + Zielnähe) × 2 + Gegner`. Halten ist 0 für V14, 1 für R3 und 2, wenn beide gehen. Zielnähe ist 0 für R3, 1 für Gleichstand/fehlende Zuweisung und 2 für V14.

Die ursprünglichen Bewegungsmasken müssen beide Befehle zulassen. Beim Fit steht der tatsächlich von R3 ausgeführte Zug in `played_act`. Die fünf Bewegungsklassen haben kanonische Richtung und Offset null. V14-Schüsse einschließlich ihrer Zieloffsets müssen vollständig im R3-Befehl erhalten sein. Beim Spielen arbeitet der Selector auf lebenden Einheiten. Er löst den Vergleich nach R3s 70-%-Auswahl und der Prüfung des vorgeschlagenen Weltbefehls aus. Für Spieler 1 werden beide Richtungen in den kanonischen Raum gespiegelt. Der Gewinner wird als ursprünglicher Weltbefehl übergeben. Die gemeinsame R3-Funktion schreibt anschließend einmal die wirklich ausgeführte Aktion und die zugehörigen Statistiken. Daten aus einem folgenden Schritt werden dafür nicht gebraucht.

`validation.json` enthält für jede Karte und Zelle die Zahl der zugelassenen Unterschiede und die beiden Lehrerübereinstimmungen. Ein anderes Lehrerkommando trägt null zu beiden Trefferzahlen bei. `gained` und `lost` zählen ausschließlich die vom Tabellenfilter wirklich auf V14 zurückgelegten Bewegungen. Das 95-%-Intervall beschreibt netto gewonnene Lehrerübereinstimmungen je ganzer Karte. Die Tabellenprüfung allein belegt keinen Spielgewinn.

Bei bestandener Diagnose im eingefrorenen Spielstand ausführen. Die Agenten- und Gegnerquellen stammen aus dem bereits verwendeten R3-Routenstand, dessen einzige Änderung an der ursprünglichen R3-Policy ein eigener Aufrufpunkt unmittelbar vor der letzten Befehlsverarbeitung ist. Ergänzt werden die vier `scripts/r3_context_*.py` sowie die gemeinsamen Vergleichs-/Auswertungswerkzeuge mit der aufrufbaren Funktion `final_battle_compare.run`.

```bash
A=(--study "$RESULTS" --r3 "$R3" --out "$GAMES")
for arm in context r3 v14; do
  python -m scripts.r3_context_games "${A[@]}" play screen "$arm" --workers 1 || exit 1
done
python -m scripts.r3_context_games "${A[@]}" assess screen
```

224 Ausführungen auf 16 Karten. Wenn alle Bedingungen im [Plan](PLAN.md) erfüllt sind, folgen 600 Ausführungen auf weiteren 60 externen und 60 direkten Karten. Die Prüfung liest die kompletten versiegelten Auswahlpartien erneut.

```bash
python -m scripts.r3_context_games "${A[@]}" play confirm v14 --workers 1 &&
python -m scripts.r3_context_games "${A[@]}" play confirm context --workers 1 &&
python -m scripts.r3_context_games "${A[@]}" play direct context --workers 1 &&
python -m scripts.r3_context_games "${A[@]}" assess confirm
```
