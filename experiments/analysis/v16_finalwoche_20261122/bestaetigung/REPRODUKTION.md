# Lauf fortsetzen und nachrechnen

Der Bestätigungslauf verwendet eine eigene Kopie der Quellen aus dem Zeitpunkt der Aufnahme. Die Pakete im Kurs-Repository werden für diese Messung ausschließlich gelesen. Der laufende lokale Datenordner ist `experiments/imitation/finalwoche_20261122/bestaetigung` im Hauptcheckout. Dort liegt die Messung unter `messung/` und die isolierte Laufquelle unter `quelle/`.

Der gespeicherte [Quellenbeleg](quellen.json) erfasst das V16-Paket, die Spielumgebung, Projektmodule und Gegner. Jede fertige Kombination aus Seed, Sitz, Gegner und Variante wird atomar unter dem zugehörigen Namen gespeichert. Für erneutes Starten vergleicht der Worker die aktuelle Umgebung, alle gebundenen Quellen und vorhandene Zeilen mit dem Ausgangsbeleg. Treffen zwei Worker auf denselben Sitz, kann nur der Inhaber der Dateisperre ihn ausführen.

Im Repo-Stamm und mit der bestehenden virtuellen Projektumgebung:

```sh
haupt="$HOME/Desktop/KI/sherlock-luxAI-team15"
python="$haupt/.venv/bin/python"
rel=experiments/analysis/v16_finalwoche_20261122/bestaetigung
d="$haupt/experiments/imitation/finalwoche_20261122/bestaetigung"
export PYTHONHASHSEED=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1

# Originale V16-Referenz fortsetzen
"$python" "$d/quelle/$rel/festlauf.py" referenz "$d/messung"

# Nach verbindlicher Auswahl den dokumentierten Kandidaten fortsetzen.
# Bei einem Netz-Kandidaten ist der feste Checkpoint erforderlich.
"$python" "$d/quelle/$rel/festlauf.py" kandidat "$d/messung" \
  --weight "$haupt/experiments/imitation/finalwoche_20261122/modelle/kontrolle.pth"

# Gesamtauswertung nach vollständigen 1.700 Partien
"$python" "$rel/auswerten.py" "$d/messung" "$rel"
```

Für einen getrennten vollständigen Wiederholungslauf einen leeren Datenordner und `einfrieren.py` zum Anlegen einer eigenen Quellkopie verwenden. Ein Zustandswechsel im gemeinsamen Repository beeinflusst die bereits angelegte Kopie nicht. Die Python-Umgebung muss mit dem gespeicherten Beleg übereinstimmen. Die `auswahl.json` mit dem ausgewählten Kandidaten gehört vor Start seiner Spiele in den neuen Messordner. Dateien im Originalrelease bleiben die Quelle für die formale Abgabe.

## Automatischer Abschluss dieses konkreten Laufs

Die einmalig gestartete lokale [Abschlussaufsicht](abschluss.py) läuft in einer eigenen Sitzung. Alle 15 Sekunden prüft sie ausschließlich die Anzahl gesicherter Dateien und die technischen Workerzustände. Verletzte Eingangsprüfungen oder wiederholte Workerfehler erzeugen einen Fehlerstatus mit Logpfad. Nach Ende eines Arms kann sie dem verbleibenden Arm einen zweiten Worker zuteilen. Die Sperren des unveränderten Evaluators sichern dabei jede Partie einzeln. Nach vollständiger Prüfung erscheinen im selben Messordner `partien.jsonl.gz`, `ergebnis.json` und `ende.json` mit den Prüfsummen. Der aktuelle Betriebsstatus steht in `abschlussstatus.json`. Eine Chatunterbrechung lässt diese lokale Sitzung weiterlaufen. Bei einem tatsächlichen Neustart des Rechners muss die Aufsicht mit derselben Konfiguration erneut aufgerufen werden.
