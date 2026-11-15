# V14 gegen Solution auf dem M3 mit 8 GB

Vier parallele Evaluationsprozesse erreichten nach dem Aufwärmen **51,73 Partien pro Minute**. Das sind 69 % mehr als mit zwei und 39 % mehr als mit drei Prozessen. Die für fünf Prozesse vorgesehene Stufe brach während des Aufwärmens ab.

| Vorgesehene Prozesse | Gewertete Partien | Erste / zweite Messrunde (Partien/min) | Gemeinsamer Durchsatz (Partien/min) | Änderung belegter Swap (MiB) |
|---:|---:|---:|---:|---:|
| 2 | 8 | 30,98 / 30,17 | 30,57 | −8,0 |
| 3 | 12 | 36,94 / 37,73 | 37,33 | 0,0 |
| 4 | 16 | 60,29 / 45,29 | 51,73 | 0,0 |
| 5 | 0 | – | – | +191,5 |

Die Messung verwendete V14 und den Kursgegner Solution auf Karte 7170230, auf beiden Sitzen mit je 303 Zügen. Jeder Prozess spielte zuerst allein sein Aufwärmpaar, während bereits aufgewärmte Prozesse warteten. Danach spielten alle gleichzeitig zwei weitere Paare. Der Durchsatz ist die Gesamtzahl gewerteter Partien geteilt durch die Summe der beiden Rundenzeiten; je Runde zählt die Zeit bis zum letzten fertigen Prozess. Aufwärmen, Start und Beenden der Prozesse liegen außerhalb dieser Messzeit. Jedes Spiel musste die archivierten Endstände wiederholen: V14 gewann auf beiden Sitzen 3:0, auf Spieler 0 mit 1989:1540 Punkten insgesamt, auf Spieler 1 mit 1929:1530. [Referenzpartien](../r8_midpoint_20261115/games/screen/v14/games.jsonl)

**Speichergrenze.** Beim Versuch mit fünf Prozessen hatten erst drei ihr Aufwärmpaar beendet. Während der vierte aufwärmte, lag der systemweite macOS-Speicherdruck rund 19 Sekunden durchgehend auf Warnstufe 2. Binnen rund 23 Sekunden meldete das System 199,5 MiB neue Auslagerungen; der belegte Swap stieg um 191,5 MiB. Die Abbruchbedingung griff vor dem Start des fünften Prozesses. Es gibt deshalb keinen Durchsatzwert für fünf Prozesse. Auch bei zwei, drei und vier Prozessen gab es zeitweise Warnstufe 2, aber während dieser drei Stufen keine neuen Auslagerungen. [Unveränderte Rohmessung mit Zeit- und Speicherstichproben](messung.json)

Die Messung lief auf Mac15,12 mit macOS 27.0.1, Python 3.13.13, Torch 2.14.1, NumPy 2.5.4, JAX 0.12.0 und Lux 0.2.1. Jeder Prozess verwendete einen Torch-Rechenthread und einen Torch-Interop-Thread; die BLAS-Threadvariablen standen auf eins. Eine Karte, zwei zeitlich gemessene Runden je Stufe und systemweite Speichersensoren begrenzen die Aussage. Vier Prozesse waren der schnellste **abgeschlossene** Wert für diesen warmen V14-Vergleich. Dauerlast, Training und größere Agenten wurden hier nicht gemessen.

## Laufende Spielvergleiche

Anschließend liefen vier unabhängige Vergleiche gleichzeitig. In 200,2 Sekunden kamen **81 vollständige Spiele** hinzu, entsprechend **24,3 Partien pro Minute**. Davon entfielen 20 auf den ursprünglichen R3 im 400-Karten-Vergleich, 21 auf die V14-Kontrolle des nachtrainierten Netzes, 19 auf den Richtungsberater und 21 auf dessen V14-Kontrolle. Die Reihen enthielten neben Solution auch den aufwendigeren Kaggle-Gegner und unterschiedliche Karten. Ein zweiter Durchlauf derselben vier Reihen mit zwei Prozessen wurde nicht gemessen. Alle neun Speicherstichproben lagen im normalen Bereich, der systemweite Auslagerungszähler blieb konstant. [Zählerstände der fünf Ergebnisdateien über 200 Sekunden](spielbetrieb.jsonl).

## Reproduktion

Im vollständigen Projekt mit den V14-Gewichten, der historischen Kaggle-Quellkopie und der Projektumgebung ausführen. Der Benchmark prüft vor dem Start die Gewichte, 47 Quelldateien, drei Lux-Engine-Dateien und beide Referenzdateien. Der Kaggle-Code gehört zum historischen Quellenmanifest. Als Gegner spielt ausschließlich Solution. Die mitgelieferte Datei verlangt die beiden Pfade explizit; die Messlogik entspricht dem im Rohprotokoll gehashten Skript. Ergebnisse werden in eine neue JSON-Datei geschrieben. [Benchmark](benchmark.py)

```sh
PROJECT=$(pwd -P)
SNAP=$(mktemp -d)
git archive 0105658188b2ec5eaf5c3a4b0ef477be9a1412f8 agents scripts lux | tar -xf - -C "$SNAP"
mkdir -p "$SNAP/agents/sherlock/weights" "$SNAP/experiments/opponents"
cp "$PROJECT/agents/sherlock/weights/agent_p0.pth" "$SNAP/agents/sherlock/weights/"
cp -RL "$PROJECT/experiments/opponents/kaggle3_lux3_048fn" "$SNAP/experiments/opponents/"
caffeinate -i "$PROJECT/.venv/bin/python" -B -u \
  experiments/analysis/macos_durchsatz_20261115/benchmark.py \
  --project "$PROJECT" --frozen "$SNAP" --pairs 2 --max-workers 8 \
  --out "$SNAP/durchsatz.json"
```

Die Stufen 2, 3 und 4 laufen, solange die Speicherprüfung sie zulässt. Weitere Stufen (5, 6, 8) kommen jeweils nur hinzu, wenn die letzte abgeschlossene Stufe insgesamt mindestens 5 % schneller als die zuvor beste ist und in der Mehrheit der Messrunden vorne liegt. Kritischer Speicherdruck bricht sofort ab. Auf Warnstufe gilt nach mindestens zwölf Sekunden eine zusätzliche Schwelle im jüngsten Fenster von bis zu 24 Sekunden: über 100 MiB neue Auslagerungen oder über 150 MiB mehr belegter Swap.
