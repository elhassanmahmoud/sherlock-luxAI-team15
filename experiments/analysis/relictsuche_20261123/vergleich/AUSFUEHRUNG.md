# Reproduktion

Im Projektstamm die Python-Umgebung des Kursrunners aktivieren. Der folgende Ablauf schreibt pro Spiel eine Ergebnisdatei. Die Bezeichnungen der Kandidaten und ihre Dateiidentitäten stehen nach der Registrierung in `kandidaten.json` und im Herkunftsnachweis der jeweiligen Messung.

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
d=experiments/analysis/relictsuche_20261123/vergleich
python "$d/panel.py"
python "$d/pruefungen.py"
python "$d/spielen.py" technical
python "$d/technik.py"
python "$d/spielen.py" discovery
```

Jeder Kandidat hat eine eigene Kennung, einen absoluten Pfad zur Datei mit `create(side)` sowie die Dateien mit seinen Gewichten und zusätzlich geladenem Code. Diese werden mit `--dependency` einzeln gebunden. Die unveränderte V16-Abgabe und die Original-Solution kontrolliert das Vergleichsprogramm selbst. Beispiel für den Zielschätzer:

```sh
ziel="$(pwd)/experiments/analysis/relictsuche_20261123/zielschaetzer"
python "$d/spielen.py" discovery --id ziel --candidate "$ziel/kandidat.py" --dependency "$ziel/ort.json"
```

Weitere Prozesse können mit einer eigenen `--worker`-Nummer dieselbe Liste bearbeiten. Nach Absturz lassen sich identische Aufrufe fortsetzen. Eine exklusive Dateisperre schützt jeden offenen Sitz. Nur eine vollständig gespielte und geprüfte Partie erhält eine Ergebnisdatei. Die Auswertung prüft zusätzlich alle Herkunftsbelege und die Vollständigkeit des gesamten Plans, bevor sie einen Vergleich öffnet.

Mit `registrieren.py` vor der ersten Ergebniseinsicht die endgültigen Kennungen angeben. `auswerten.py discovery --ids …` verlangt exakt diesen Kreis und erstellt das Roharchiv und die Ergebnisdatei. Die Folgephasen verwenden nur einen nominierten Kandidaten. Die Bestätigung folgt ausschließlich nach bestandener Auswahl und die unselektierte Kartenreihe ausschließlich nach bestandener Bestätigung. Nach 16 Uhr ist eine historische Reproduktion in einer gesonderten Ablage mit `--work /pfad/zu/neuen/daten --reproduction` möglich. Technische Kontrollen in diesem Arbeitsverzeichnis zuerst ausführen.

`gegenrechnung.py discovery` liest das fertige Roharchiv direkt und rechnet die Messwerte, Kartenintervalle und Nominierung mit einer eigenständigen Implementierung nach. Entsprechend funktionieren `confirm` und `general`, sobald die jeweilige Stufe vollständig gespielt ist. Für dieses Programm genügt eine Python-Umgebung mit NumPy.
