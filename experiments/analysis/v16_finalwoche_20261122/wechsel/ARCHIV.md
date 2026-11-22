# Weshalb den Halterwechsel noch einmal überprüfen?

Im Dev-H-Vergleich am 17. November konnten nur mit dem Halterwechsel sieben Kaggle-Karten auf beiden Sitzen gewonnen werden. Auf einer anderen Karte gingen beide Sitze verloren. Die oft zitierte Verbesserung um zwölf ganze Spiele entspricht genau diesem Unterschied auf acht Karten. Ein exakter zweiseitiger Vorzeichentest für die acht Karten mit verändertem Gewinner ergibt 0,0703; die nachträgliche Auswahl unter 17 Varianten vergrößert die Unsicherheit zusätzlich. Der damalige vorab gewählte Kaggle-Punkteanteil verbesserte sich nur um 0,17 Prozentpunkte. Die fünfte Bestätigung galt der Option SAPBIAS. Eine unabhängige Ganzspielprüfung allein für WECHSEL auf V16 ließ sich im Projektarchiv nicht finden. [Historische Untersuchung mit damaliger Entscheidung](../../devh_20261117/ERGEBNIS.md) · [gepaarte Rohdaten und veränderte Sitze](archiv.json)

| Archiv, 400 Sitze je Agent und Gegner | Beide gewinnen | Nur WECHSEL gewinnt | Nur V16 gewinnt | Beide verlieren | Einzelmatches WECHSEL / V16 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Solution | 392 | 3 | 0 | 5 | 1.154 / 1.155 |
| Kaggle | 22 | 14 | 2 | 362 | 144 / 134 |

Die Archivdateien enthalten keinen Zähler für den Halterwechsel. Auf 286 der 400 Solution-Sitze und 314 der 400 Kaggle-Sitze weichen die Punktesummen eines oder beider Teams zwischen den Spielverläufen ab. Das zeigt häufige Veränderungen des Spielverlaufs. Die tatsächliche Eingriffshäufigkeit wird im neuen Vergleich direkt an der Taktikschicht erfasst.

Für die technische Wiederholung verwenden wir die Python-Dateien aus dem im damaligen Laufprotokoll genannten Commit `0cd2ce37bf5c9dec21ac976c549c9c7f616ac614`. Das veröffentlichte V16-Paket wurde bereits vor Dev H gebaut und enthält diese spätere Taktikschicht nicht. Der Kandidat verwendet daher die damalige evaluierte Taktikschicht mit den Lerngewichten aus dem V16-Release und allen drei V16-Basisschaltern. Der Gegenagent lädt die unveränderte Kurs-ZIP. [Historischer Startbefehl](../../devh_20261117/run_devh.sh) · [neue Vorfestlegung](PLAN.md)

## Technischer Abgleich vor dem ersten neuen Spiel

Alle acht festgelegten Ausführungen auf 7266000 entsprachen den archivierten eigenen und gegnerischen Punktesummen, Matches und ganzen Spielen auf beiden Seiten gegen beide Gegner. In den vier technischen WECHSEL-Spielen registrierte die Taktik sechs Paarwechsel und acht tatsächlich geänderte Einheitsbefehle. Ein Ersatzschiff kann schon den gewünschten Zug vorgeschlagen haben; ein Paarwechsel erzeugt deshalb nicht zwingend zwei verschiedene Befehle. [Acht ursprüngliche Wiederholungen](technik.json) · [Quellen- und Modellbeleg](auftrag.json)

Für eine getrennte Reproduktion aus dem Repo-Stamm:

```sh
haupt="$HOME/Desktop/KI/sherlock-luxAI-team15"
python="$haupt/.venv/bin/python"
d=experiments/analysis/v16_finalwoche_20261122/wechsel
out=$(mktemp -d)
"$python" "$d/freeze.py" "$out/quelle"
export PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
"$python" "$out/quelle/$d/spielen.py" "$out/messung" technik
"$python" "$out/quelle/$d/spielen.py" "$out/messung" check
"$python" "$d/leitung.py" "$out" "$out/quelle/$d/spielen.py" "$d/auswertung.py"
```

Die einmalig gestartete lokale Aufsicht prüft vor beiden Messreihen die technische Parität. Sie startet zwei getrennte Sitzlisten und enthält einen technisch begrenzten Wiederanlauf pro Worker. Vollständige Kombinationen werden beim Wiederanlauf geprüft und übersprungen. Eine frische Endauswertung ist erst ab genau 1.200 vollständig gespeicherten Kombinationen möglich.
