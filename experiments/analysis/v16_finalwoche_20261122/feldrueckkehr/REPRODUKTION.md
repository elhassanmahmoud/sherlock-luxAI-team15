# Den Versuch nachrechnen

Die gespeicherten Verläufe reichen zur Auswertung. Die Befehle laufen im Stamm des Projekt-Repositories mit der eingerichteten Lux-Kursumgebung. Falls die virtuelle Umgebung im Hauptcheckout liegt, deren Python verwenden. Die geprüften Versionsnummern stehen in [herkunft.json](herkunft.json).

```sh
d=experiments/analysis/v16_finalwoche_20261122/feldrueckkehr
py=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

# Verlustursachen und Wirkung des einzelnen Befehls aus vorhandenen Daten
"$py" "$d/auswerten.py" "$d/diagnose"

# Nach vollständigem Spielvergleich: alle 200 Datensätze und Auswahlbedingungen aus dem Archiv
"$py" "$d/spiele_auswerten.py" auswahl "$d/auswahl_partien.jsonl.gz"
```

Für eine tatsächliche Wiederholung der vier Diagnosekarten erst das V16-Release und den Kaggle-Dritten bereitstellen. Der Code verwendet den SHA-geprüften V16-Loadereinstieg. Das folgende Beispiel schreibt in ein neues Verzeichnis und lässt genau zwei CPU-Prozesse laufen. Jede Ursprungs- und Vergleichsdatei enthält den Seed und die Startseite.

```sh
probe=$(mktemp -d)
for sitz in 0 1; do
    "$py" "$d/batch.py" original "$probe" 160347000 160347003 "$sitz" &
done
wait
for sitz in 0 1; do
    "$py" "$d/batch.py" fork "$probe" 160347000 160347003 "$sitz" &
done
wait
"$py" "$d/auswerten.py" "$probe"
```

Bei den Gegenproben wird das Spiel vom selben Start aus wiederholt. Identische Kommando-Präfixe und der SHA-256 des vollständigen Enginezustands verhindern den Vergleich verschiedener Lagen. Stimmen diese, die reproduzierten Punktestände, die Einheits-ID oder das Zielfeld nicht überein, bricht die Messung mit einer Fehlermeldung ab. Die erneut gespielte Rückkehr nutzt nur die eigene Sicht. Das Gegnerwissen der Schiedsrichterauswertung bleibt außerhalb der Policy.

Für eine vollständige Wiederholung des Auswahlpanels das Skript `spielvergleich.py` mit Phase `auswahl`, einem eigenen Ausgabeordner und den beiden Spuren `0` und `1` aufrufen, je eine Spur pro Prozess. Die Auswertung übernimmt ausschließlich vollständige Datensätze mit den erwarteten Quellen- und Modellbindungen. Sitze ohne tatsächlichen Eingriff müssen bei beiden Agenten dieselben Spiel- und Matchausgänge sowie beide Punktesummen haben.
