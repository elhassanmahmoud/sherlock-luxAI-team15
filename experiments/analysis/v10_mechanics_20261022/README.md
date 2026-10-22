# V10: zwei Mechanikkorrekturen, 22.10.2026

Dieser Ordner enthält die technischen Belege und den getrennten Leistungsvergleich.
Das ursprüngliche Verfahren steht im [vorab festgelegten Plan](../../../docs/superpowers/plans/2026-10-22-v10-mechanics.md).
Moayed hat am 22.10. um 16:24 Berlin den Abschluss vor der Review beauftragt:
nur die laufende Bestätigung beenden, keine neuen Reihen und kein Versionswechsel.
Diese vor Sichtung der Kandidaten-Ergebnisse festgehaltene Begrenzung steht in
[closing_scope_20261022.json](closing_scope_20261022.json). Details und Ergebnisstand:
[Bericht für Mahmoud](RESULTS.md).

## Was wurde korrigiert?

- `sap_overkill_recovery=true`: Sap-Koordination berücksichtigt, dass ein Gegner
  nach Treffern durch Feldenergie überleben kann. Weil die beobachtete Feldenergie
  zeitlich veraltet sein kann, wird konservativ die öffentliche Obergrenze von
  normalerweise 20 angesetzt. Dadurch können auch zusätzliche, im konkreten Fall
  unnötige Schüsse entstehen. Ein korrekteres Überlebensmodell garantiert keinen
  besseren Gesamtscore.
- `nebula_infer_drift_safe=true`: Bei einer vom vorhandenen Detektor erkannten
  Terrain-Verschiebung wird die Nebel-Inferenz aus der alten Sichtmaske ausgelassen.
  Sichtbare neue Kartenzellen bleiben erhalten. Nicht erkannte Drift bleibt eine
  offene Grenze; der Detektor wurde nicht verändert.

Beide Schalter sind standardmäßig aus. Kein neues Training und keine veränderten
Netzparameter: weiterhin dieselben 18 Netze wie V10. V10 bleibt in diesem
Abschlussauftrag unabhängig vom Ergebnis aktiv. Direktduell, zusätzlicher
Robustheitsblock und eine Übernahme werden nicht mehr gestartet.

## Technische Belege

- `implementation-report.md`: Ursache, Änderungen, Einschränkungen, rote/grüne
  Regressionen und die zwei getrennten Fix-Commits.
- `code-review.md`: unabhängige Prüfung auf Anforderungserfüllung und Codequalität.
- `full-suite.log`: 527 Tests und 14 Untertests bestanden.
- `compatibility_*.json`: je vier Spiele mit originalem und erweitertem Code bei
  ausgeschalteten Schaltern. Beide Spieler haben identische vollständige
  Aktionsfolgen über 1.212 Schritte; alle Spielmetriken außer Laufzeit stimmen.
- `course_runner_combined.json`: acht technische Prüfspiele mit beiden Schaltern
  an, unveränderter Kurs-Runner und geschützte Dateien unverändert.
- `smoke_checkpoint.json`: temporärer Checkpoint nur für die technische Prüfung;
  alle 264 Tensoren und alle Nicht-Konfigurationsdaten identisch zu V10.
- `package_check.log`: Paket mit diesen aktivierten Korrekturen importiert/lädt.
- `seed-audit.json`: Frische der reservierten Karten, einschließlich Mahmouds
  neuem Ergebniscommit `bb7e84b`. Dessen zusätzliche Netze liefern laut seinen
  Entwicklungstests keinen qualifizierten Nachfolger; wir trainieren sie nicht erneut.

## Reproduktion für Mahmoud

Die Sicherung liegt unter `experiments/releases/20261022_v10_baseline/` und trägt
für beide Dateien SHA-256 `03cf8bdc20bef58a99e7d00ca743add92ed4fc21b7e8c4452f1bb7feea6d8c67`.
Ausgangsversion für eine genaue Reproduktion ist Commit `de2e95d` in einem
getrennten Checkout; spätere Verhaltensänderungen können andere Ergebnisse liefern.
Ein portabler Einzelaufruf vom Repo-Verzeichnis für die kombinierte Variante:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m scripts.par_eval \
  --weights experiments/releases/20261022_v10_baseline/agent_p0.pth \
  --first 110100 --n 200 --workers 2 --opponents solution92 \
  --set sap_overkill_recovery=true --set nebula_infer_drift_safe=true \
  --out experiments/compare/my_v10_mechanics_combined.csv
```

Für V10 beide Schalter auf `false`, für Einzelkorrekturen nur einen auf `true`
setzen und jeweils neue Dateinamen verwenden. Auf Kurskonfiguration mit drei
Matches achten. Das Wiederholen dieser Karten ist eine Reproduktion, kein
weiterer unabhängiger Stärkenachweis. Neue Versuche benötigen eine neue Reservierung.

`run_jobs.py`, `selection_jobs.json`, `source_freeze.json` und die Phasenjournale
halten die tatsächlich ausgeführten Aufrufe, Quellen-/Engine-Prüfsummen und
Dateipfade auf Moayeds Mac fest. Historische Belege nicht überschreiben oder
einen alten Freeze für einen anderen Rechner umdeuten. Für eine Reproduktion
den portablen Aufruf oben und neue Ausgaben verwenden. Der kleine Runner
entscheidet weder über Kandidaten noch über eine Übernahme.

## Bewertung

Spielzeilen zunächst auf exakt erwartete Gegner, Karten, beide Seiten und
vollständige Spiele prüfen. Statistiken nutzen gepaarte ganze Karten, 5.000
Bootstrap-Stichproben und 95-%-Intervalle. Ein Sieg zählt 1, Remis 0,5; echte
Siege/Remis/Niederlagen werden zusätzlich ausgewiesen. Auswahl und unabhängige
Bestätigung getrennt lesen. Auch 100 % in einem endlichen Test wären keine
Garantie für alle Karten oder Gegner.

Die frühe `protocol-review.md` enthält noch Entwurfsformulierungen. Verbindlich
ist der danach festgelegte Plan: Auch bei der Default-Auswahl gilt neben mindestens
99 % bereits die Grenze von höchstens −1 pp. Beide Bedingungen wurden geprüft.

## Archivierte Auswertung

- `confirmation-data-review.md` und `.json`: unabhängige vollständige Prüfung der
  Bestätigung, abgeschlossen vor der anschließenden Git-Integration.
- `audit_pair.py`: tatsächlich verwendeter Daten-/Statistikprüfer für
  `selection_default` und `confirmation`. Erwartet den Studienordner als erstes
  und den Phasennamen als zweites Argument. Er legt die Zusammenfassung exklusiv
  neu an; zum Nachrechnen die Rohdaten und Phasenjournale in einen neuen Ordner
  kopieren und dort ohne vorhandene Zusammenfassung ausführen. Er ersetzt nicht
  die getrennte Prüfung von Quellenstand, Gewichten und Zulassung.
- `selection_data_audit.py` und `confirmation_data_audit.py`: unveränderte Skripte
  der unabhängigen Prüfung. Die historischen absoluten Mac-Pfade und der geprüfte
  HEAD sind absichtlich erhalten. Ein erneuter Aufruf gegen den inzwischen
  integrierten Checkout ist keine Reproduktion der damaligen Quellenprüfung;
  historische Ergebnisse nicht überschreiben.
- `decision.json`: abgeschlossene Entscheidung, kein Austausch von V10.

Die Prüferskripte wurden erst nach dem Ende des Quellen-Freeze archiviert. Sie
sind deshalb keine zusätzlichen Eingaben der bereits beendeten Spielmessungen.
Die lokale `.gitattributes` erhält die originalen CSV-Zeilenenden, damit Git die
protokollierten Datei-Prüfsummen beim Übertragen nicht verändert.
