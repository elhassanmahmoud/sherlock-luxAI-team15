# Belege: A2 mit Lehreranker am 04.11.2026

Abgeschlossen: Alle vier Trainingsarme und 920 frischen Diagnosepartien sind unabhängig geprüft. Der Anker verbessert die jeweiligen Kontrollen, qualifiziert aber keinen neuen Agenten. V14 bleibt die Abgabe. Solution: V14 40/40, A2 39/40, beide Anker 36/40; direkt gegen V14 Anker 14/40 und 12/40.

## Aufbau

- `retention_before/`: gleiche 68.687 ausgeschlossene Zeilen für A2 und vier historische RL-Endstände.
- `traces/`: zwölf bekannte Entwicklungssituationen, je normaler und beobachteter Durchlauf; Original-JSONL verlustfrei mit gzip komprimiert.
- `preflight/`: Quellen-/Gewichtspins, Fallanalyse, unabhängige Prüfungen, Seedinventur und vorbereitete Werkzeuge.
- `training/`: vier vollständige Trainingsarme. Große Replay-Puffer bleiben lokal; finale Modelle sind unter `../../candidates/a2_anchor_20261104/` gespeichert.
- `retention_after/` und `completion/`: tatsächliche Lernabnahme, unabhängige Nachrechnung, Laufzeitfreigaben, Test- und Vergleichsnachweise.
- `diagnostic/`: fester neuer Vergleich mit sechs Rollen; 720 Panel- und 200 Direktpartien. Original-CSV-Bytes bleiben unverändert.
- `review/`: Implementierungs-/Reviewberichte und transparent erhaltene technische Testvorfälle.

## Modell und Lernunterschied

Alle neuen Modelle sind einzelne Dueling-Netze mit 79 Eingängen, zwei 512er Schichten und sechs Aktionswerten. Jeder Arm startet bei A2; CONTROL nutzt gewöhnliches TD-Lernen, ANCHOR denselben Schritt plus 0,1 × maskierten Lehrer-Aktionsverlust. Pro Arm 40 Vorlauf-, 160 Lern- und 32 bekannte Validierungsspiele sowie 24.000 Updates. Je ANCHOR 6.144.000 Lehrerziehungen aus ausschließlich 356.415 Lernzeilen. Keine neue Spielregel, kein anderer Reward und kein Ensemble.

Die vier Modellkopien sind die Endstände, auch wenn die bekannte Zwischenvalidierung einen früheren Stand bevorzugte. `manifest.json` neben den Modellkopien dokumentiert ihre Herkunft. Die alten Gewichte werden durch diese Dateien nicht ersetzt.

## Daten prüfen und wiederverwenden

Die manifesteigenen SHA-256-Werte beziehen sich auf die ursprünglichen Bytes. Für komprimierte Dateien benennt das Archivmanifest sowohl den komprimierten als auch den entpackten Hash. `.gitattributes` verhindert automatische Zeilenumwandlung.

Der unabhängige Auswerter in `completion/audit_results.py` akzeptiert `--data-ready --directory PATH_ZU/diagnostic --out-prefix NEUER_AUSGABEPFAD` und liest nur die elf fertigen CSVs. Er prüft Schlüssel, Vollständigkeit, Ergebnisse und gepaarte Kartenintervalle; er startet kein Spiel. `--self-test` verwendet ausschließlich erfundene Testdaten.

Die portablen Projektwerkzeuge `python -m scripts.student_retention --help`, `python -m scripts.student_failure_trace --help` und `python -m scripts.student_anchor_train --help` beschreiben ihre Eingaben und neue Ausgabeordner. Historische Manifeste und Betriebshelfer behalten bewusst die absoluten Quellpfade des ursprünglichen Macs. Sie sind Provenienznachweise; nicht als verschobene oder erneut auszuführende Originalstudie ausgeben. Für neue Läufe neue Manifeste und Verzeichnisse erzeugen, bestehende Ergebnisse nicht überschreiben. Eine Wiederholung der gespeicherten Testkarten ist keine frische Bestätigung.

## Grenzen

20 neue Panelkarten und 20 getrennte Direktkarten, zwei getrennt berichtete Trainingsstarts. Ganze Karten mit beiden Seiten (im Panel allen Gegnern) gemeinsam resampeln; 5.000 Bootstrapziehungen, Seed 0. Intervalle sind explorativ und nicht für Mehrfachvergleiche korrigiert. Lehrerübereinstimmung ist keine Siegquote; auch ein perfekter Schüler könnte Fehler des Lehrers übernehmen. Die kleine Diagnose allein qualifiziert keine Abgabe.

[Vollständiger Bericht für Mahmoud](../../../docs/A2_LEHRERANKER_20261104.md).
