# Reproduktion der späten Suchentscheidung

Die Programme laufen im Projektstamm mit der Kurs-Python-Umgebung. Die Dateiablage für einzelne Spielprotokolle steht in `sammeln.py`. Die komprimierten Archive beim Studienbericht enthalten die tatsächlich verwendeten Präfixe und Fortsetzungen. Der gemeinsame Projekttag endet um 16 Uhr Berlin. Für historische Neuberechnungen aus fertigen Ergebnissen genügt die unabhängige Gegenrechnung.

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
d=experiments/analysis/relictsuche_20261123/spaetsuche
python "$d/karten.py"
python "$d/sammeln.py" train 0
python "$d/lernen.py" fit
python "$d/sammeln.py" test 0
python "$d/lernen.py" test
python "$d/technik.py"
python "$d/gegenrechnung.py"
```

Weitere Sammler können denselben Block mit einer anderen Arbeiternummer spielen. Dateisperren verhindern doppelte Austragungen. Beim Erreichen der vorbestimmten ersten qualifizierten Karten können wenige bereits laufende Sichtungen fertig werden. Sie werden separat archiviert und sind vom Lern- und Testergebnis ausgeschlossen.

Bei erfolgreicher unabhängiger Eröffnungsprüfung und bestandener Technikkontrolle erhält der Kandidat die 60 vorab ausgewählten Karten. Ein tatsächliches V16-Selbstspiel pro Karte liefert separate öffentliche Beobachtungen für beide Sitze.

```sh
python "$d/endspiel.py" play --worker 0
python "$d/endspiel.py" analyze
```

Die Werte der ursprünglichen Routenpolitik und des Zielschätzers stammen aus den eingefrorenen Quellen im benachbarten [Dreiervergleich](../vergleich/ERGEBNIS.md). Der späte Spieler benötigt dessen Paketdateien und das freigegebene Original-V16-Archiv. Seine Merkmale entstehen vor der eigenen Aktion in Zug 55. Die späteren Sichtungen, Gutschriften und Matchausgänge liefern die Trainingsziele und den unabhängigen Vergleich.
