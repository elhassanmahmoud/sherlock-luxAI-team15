# Punktspeicher nachprüfen

Die beiden komprimierten Dateien je Stichprobe enthalten vollständige Originalbeobachtungen und die getrennt daraus berechneten Zertifikate. Eine Zeile entspricht einer echten Partie auf dem angegebenen Sitz. `public` enthält genau die fünf Eingaben des Beweisverfahrens. `policy` enthält V16s Einschätzungen und mögliche Bewegungsschritte. `referee` enthält die tatsächlichen Punktefelder vor jeder Aktion. Jede Liste in diesen drei Spuren hat 303 Einträge.

## Unabhängige Prüfung aus dem Repository

Vom Projektverzeichnis aus mit der Projektumgebung ausführen. Die Gegenrechnung benötigt NumPy und SciPy. Sie liest ausschließlich die archivierten Dateien und die Kartenliste. Die kleine vollständige Aufzählung benötigt nur Python.

```sh
studie=experiments/analysis/relictsuche_20261123/punktspeicher
python "$studie/pruefen.py"
python "$studie/gegenrechnung.py" archiv
python "$studie/gegenrechnung.py" frisch
```

Die Gegenrechnung prüft die Archivprüfsummen, die Zuordnung von Zug und Gutschrift sowie die Felder beider Seiten gegen die Wertungsmaske. Für jedes erstmals als positiv zertifizierte Spiegelpaar erzwingt sie versuchsweise den Wert null. Ein unabhängiges binäres Optimierungsmodell muss diese Annahme anhand aller zu diesem Zeitpunkt verfügbaren öffentlichen Belegungsgrenzen ausschließen. Die erreichbaren Ziele werden nochmals mit gewöhnlichen Koordinatenmengen berechnet.

## Wiederholung der Partien am Studienrechner

Der ursprüngliche Lauf nutzte das unveränderte Projektpaket V16 und die originale Solution. Die gemeinsame Spielbibliothek bindet ihre Identitäten, die lokalen Paketversionen und die Spielregeln an SHA-256-Prüfsummen. Der ursprüngliche Sammler ist auf den vereinbarten Endtermin am 23.11.2026 begrenzt. Die reine Archivnachrechnung hat keine Zeitbegrenzung.

```sh
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
studie=experiments/analysis/relictsuche_20261123/punktspeicher
python "$studie/karten.py"
python "$studie/spuren.py" archiv 0
python "$studie/spuren.py" frisch 0
python "$studie/auswertung.py" archiv
python "$studie/auswertung.py" frisch
```

Bereits abgeschlossene, quellengebundene Spiele werden wiederverwendet. Mehrere Sammler desselben Bereichs teilen sich die feste Kartenliste über dateiweise Sperren. Die vier bekannten Sitzverläufe müssen die ursprünglichen Befehlsprüfsummen und sämtliche Matchstände reproduzieren.

## Öffentliche Schnittstelle

Eine Instanz von `beweise.Evidence` gehört zu genau einem Sitz und einem gesamten Spiel. `observe(row)` erwartet jede Beobachtung einschließlich der Matchanfänge in zeitlicher Reihenfolge. `step` ist der absolute Zug, `ms` der Zug innerhalb des Matches, `points` der jetzt beobachtete eigene Punktestand und `occupied` die eindeutigen, von eigenen wertungsfähigen Einheiten besetzten Weltfelder. `epoch_seen` meldet, ob das aktuelle Reliktpaar schon in dieser Beobachtung sichtbar ist. Ein Feld `(x, y)` trägt die Nummer `24*x+y`. `worlds(evidence.positive)` enthält beide Weltfelder jedes bewiesenen Spiegelpaars. [Extraktion aus der Spielbeobachtung](spuren.py) · [Beweiskern](beweise.py) · [Unabhängige Nachrechnung](gegenrechnung.py)
