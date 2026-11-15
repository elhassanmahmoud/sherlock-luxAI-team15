# Spielprüfung für R8 und die Warmkontrolle

Für die Ausführung werden die beim [Nachtraining](PLAN.md) verwendeten Pfade und der tatsächlich positiv geprüfte Offlinebericht benötigt. `FIT` ist der eingefrorene Quellordner, aus dem Training und Archivvergleich liefen. `ZIEL` enthält `control.pth`, `r8.pth` und `validation.json`. `AUDIT_SHA` ist die nach Prüfung festgehaltene SHA-256 dieser Datei. Die Spielauswertung prüft alle 96 Diagnose-Sitzberichte, ihre Karten- und Panel-Summen, die vorab festgelegten Hürden, beide trainierten Dateien und die Quellen des Fits. Alle Netzstände nutzen im Spiel den ursprünglichen selektiven R3-Einstieg mit demselben V14.

Der eingefrorene Spielstand lässt sich aus Commit `0105658188b2ec5eaf5c3a4b0ef477be9a1412f8` nachbauen. Aus diesem Stand die Verzeichnisse `agents`, `lux` und `scripts` exportieren. Ausschließlich die vier Hilfsdateien `scripts/final_battle_compare.py`, `scripts/final_battle_assess.py`, `scripts/final_battle_select.py` und `scripts/residual_ensemble_compare.py` aus `c60074a0ef0afc32434b0355317df49885b33822` einsetzen. Hinzu kommen `scripts/r8_warm_games.py` aus diesem Versuch und die bereits installierte native Gegnerkopie unter `experiments/opponents/kaggle3_lux3_048fn`. Alle betreffenden Quell-, Modell- und Engineprüfsummen werden vor den Spielen geprüft. Die Kontrollen werden anhand ihrer tatsächlichen Modellprüfsummen und der registrierten Armnamen unterschieden.

Im Spielstand ausführen (Zsh/Bash):

```sh
args=(--fit-root "$FIT" --models "$ZIEL" --r3 "$R3" --audit "$ZIEL/validation.json"
      --audit-sha256 "$AUDIT_SHA" --out "$SPIELE")
python -B -u -m scripts.r8_warm_games play screen "${args[@]}"
python -B -u -m scripts.r8_warm_games assess screen "${args[@]}"
```

Jeder Arm arbeitet mit einem Worker. `--arm r8`, `--arm control`, `--arm r3` oder `--arm v14` wählt genau einen Arm aus, beispielsweise für die Wiederaufnahme. Das ergibt 96 + 64 + 64 + 64 Spiele. Nur bei positiver Auswahl können mit `play confirm` die weiteren 600 Spiele freigeschaltet und mit `assess confirm` ausgewertet werden. Dazu reproduziert das Programm die vollständige Auswahl aus den einzelnen Partien und vergleicht sie mit der abgelegten Auswertung. Die Unsicherheit beruht immer auf ganzen Karten mit beiden Sitzen. Ein bestätigtes Spielergebnis ist separat gegenüber dem aktuellen Turnierstand zu bewerten.
