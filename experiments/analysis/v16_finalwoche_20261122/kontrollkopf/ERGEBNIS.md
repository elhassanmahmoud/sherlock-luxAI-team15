# Der ungewichtete Kontrollkopf gegen V16

**Der Kontrollkopf hat die vier Kriterien für eine unabhängige Bestätigung erreicht.** Im direkten Duell gewinnt er auf elf der zwanzig frischen Karten von beiden Startseiten. Das entspricht **22 von 40 Spielen**. Gegen Solution und Kaggle ist die Zahl gewonnener ganzer Spiele jeweils gleich wie bei V16. Für eine Ablösung der Abgabe reicht der kleine Vergleich nicht. [Vorabplan](PLAN.md) · [Auswertung](ergebnis.json) · [alle 200 Spielausgänge](partien.jsonl)

| Gegner | V16, Spielsieg | Kontrollkopf, Spielsieg | V16, Matchsieg | Kontrollkopf, Matchsieg |
| --- | ---: | ---: | ---: | ---: |
| Solution_92 | 40/40 | 40/40 | 119/120 | 118/120 |
| Kaggle-Dritter | 2/40 | 2/40 | 10/120 | 14/120 |
| Direkt gegeneinander | 18/40 | **22/40** | 62/120 | 58/120 |

Der Kontrollkopf holt gegen Kaggle zwei Spiele auf Karte 19377011, während V16 auf Karte 19377010 zwei Spiele gewinnt. Auf den übrigen 18 Karten verlieren beide Stände von beiden Seiten. Der rechnerische Matchgewinn beträgt +0,10 Matches je Spiel. Das 95-%-Intervall aus 20.000 Bootstrap-Ziehungen ganzer Karten umfasst −0,15 bis +0,40. Auch die direkte Siegquote von 55 % bleibt bei einem Kartenintervall von 35–75 % unsicher. V16 hat im direkten Vergleich sogar vier einzelne Matches mehr gewonnen. Für einen ganzen Sieg zählen zwei der drei Matches derselben Partie. Das gelang dem Kontrollkopf häufiger.

Für Kaggle und im direkten Duell sind Spielausgang, Matchsiege und Punktsummen auf jeder einzelnen Karte auf beiden Startseiten identisch. 40 Spiele je Vergleich entsprechen hier zwanzig Karten mit beobachtbarer Variation. Gegen Solution bestehen Seitenunterschiede bei den Punktsummen. Die perfekten 40/40 beider Stände belegen lediglich diesen Kartensatz. Das beim Wiederziehen der zwanzig Karten konstante Sieggefälle von null sagt nichts über die verbleibende Unsicherheit auf ganz neuen Karten aus.

## Herkunft und Prüfungen

Der Kandidat war der ungewichtete Kontrollarm des [separaten Lernversuchs](../lernversuch/ERGEBNIS.md). Er wurde nach dessen Offlineergebnis ausgewählt. Seine Gewichte und sämtliche Bedingungen dieser Spielauswahl lagen vor dem ersten Spiel fest. Keine zusätzlichen Lernschritte, Gewichtswechsel, Ersetzungen von Karten oder vorzeitige Auswahl nach Zwischenergebnissen. Die dreifache Gewichtung von Feldbeispielen hatte ihre eigene Vorbedingung verfehlt und wurde hier nicht eingesetzt.

Vor und nach der Messung stimmten Quell- und Modellprüfsummen. Der Quellcode aller Spieler war das veröffentlichte V16-Kurspaket beziehungsweise die vorab gebundenen Referenzgegner. Die zwei Ensembles unterschieden sich nur in Gewicht und Bias des v9-Aktionskopfs (1.542 Zahlen). Startwerte aller weiteren Module, beide Zielköpfe, v8L und Konfiguration wurden direkt verglichen. Vollständigkeit, Zuordnung und Ergebnisrechnung wurden für alle **200** eindeutigen Karten-/Sitz-/Gegner-/Varianten-Kombinationen geprüft: je 303 Schritte, drei entschiedene Matches, Punktezählung Version 2. Keine gefangenen Agentenausnahmen. [Prüfsummen und Laufauftrag](auftrag.json)

## Reproduktion

Die Auswertung der archivierten Rohspiele benötigt nur Python und NumPy. Für einen vollständigen Neulauf braucht es die lokale Projektumgebung und die installierten Kaggle-Lehrergewichte. Der Kontrollkopf liegt hier als [6-KB-Datei](kontrollkopf.npz). Die Rekonstruktion aus dieser Datei und der ursprünglichen V16-ZIP lieferte byteidentisch den tatsächlich gemessenen Checkpoint (SHA-256 `5b200d5a7fadfffb86ccb6c3e74324e49fe4c1e27510581ae810e6a452b2a67b`).

```sh
python="$HOME/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python"
dir=experiments/analysis/v16_finalwoche_20261122/kontrollkopf
"$python" "$dir/auswertung.py" "$dir/partien.jsonl"
lauf=$(mktemp -d)
"$python" "$dir/kopf.py" "$lauf/modell"
PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  "$python" "$dir/vergleich.py" "$lauf/modell/kontrolle.pth" "$lauf/spiele"
```
