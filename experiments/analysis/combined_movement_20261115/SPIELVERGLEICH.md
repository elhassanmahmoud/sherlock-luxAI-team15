# Spielvergleich für R7

Voraussetzung ist der bestandene Archivvergleich für genau den ausgeführten R7-Checkpoint. Das Werkzeug prüft die 64 Archivzeilen, die resultierenden Kontrollwerte und die Prüfsummen von R3, R5, R7 sowie dem Trainingscode. Die Prozentschwellen und Karten stammen aus dem [vorher festgelegten Vergleich](PLAN.md).

| Phase | Karten und Gegner je Agent, immer beide Sitze | Ganze Spiele |
|---|---|---:|
| Auswahl | 7284000–7284015. R7 spielt gegen Kaggle, Solution und V14, danach V14, R3 und R5 je gegen Kaggle und Solution. | 288 |
| Unabhängige Bestätigung | 7284100–7284159 gegen Kaggle und Solution, je mit V14 und R7. Zusätzlich 7284200–7284259 im direkten Duell R7 gegen V14. | 600 |

R3 und R5 sind im Plan Kontrollen für die 16 Auswahlkarten. Nur dort sind beide zusätzlich zu messen. Die unabhängige Bestätigung vergleicht R7 mit der freigegebenen V14-Version. Eine spätere mögliche Ablösung eines inzwischen anderen Abgabeagenten erfordert ihren eigenen Vergleich.

Der Spielcode ist der zuvor tatsächlich für R5 geprüfte Stand. Derselbe Lader verarbeitet R3 mit 79 und R5/R7 mit 85 Merkmalen. Ein Versuch verwendet einen Spielprozess je Aufruf. Für einen unterbrochenen Arm denselben Befehl mit identischen Quellen, Eingabedateien und Zielordner verwenden. Der Runner schützt jeden Arm mit einer Sperre. Er prüft Modell, Code und Laufzeit vor und nach dem Spielen. Fertige Arme werden anhand ihres Spielprotokolls eingelesen.

## Durchführung

Im eingefrorenen R5-Spielstand starten, der im [R5-Spielbericht](../own_command_20261115/SPIELE.md) beschrieben ist. Für die Auswertung zusätzlich `scripts/final_battle_assess.py` aus Git-Stand `c703c8a093e946f8ded705f2134ae8659eff54e8` und dieses Werkzeug `scripts/combined_movement_games.py` kopieren. Die drei vorher registrierten Laufzeit-Prüfsummen für die Spielquellen müssen vor dem ersten Spiel stimmen. Das Trainingssnapshot enthält andere Messquellen und ist ein eigener Stand. Ein erneuter Lauf archiviert seine Ergebnisse in einem eigenen Ordner.

```sh
M=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15
P="$M/.venv/bin/python"
A="$M/experiments/analysis/combined_movement_20261115"
O="$M/experiments/imitation/final_20261115_r7_combined/student.pth"
C="$M/experiments/candidates/movement_dagger_20261115"
H=$(shasum -a 256 "$A/paired_validation.json" | awk '{ print $1 }')
r7_games() {
  "$P" -B -u -m scripts.combined_movement_games "$@" --model "$O" --controls "$C" \
    --audit "$A/paired_validation.json" --audit-sha256 "$H" --out "$A"
}
r7_games play screen
r7_games assess screen
```

Nach echter Nominierung die Bestätigung als separaten Schritt beginnen. Die Eingangsprüfung rechnet die vollständige Auswahl aus den Rohzeilen erneut und vergleicht sie mit `screen/assessment.json`. `r7_games play confirm` und anschließend `r7_games assess confirm` führen den unabhängigen Vergleich durch. Die Auswertung nennt die Ergebnisse und gepaarten Intervalle je Gegner und für das direkte Duell. Gewichtsdateien und Abgabepaket können durch diese Befehle nicht ersetzt werden.
