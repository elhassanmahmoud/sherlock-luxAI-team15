# Fester P/PT-Vergleich

Werkzeuge für den vorab geplanten Vergleich, **keine neue Abgabe**.
Verbindliche Karten, Kandidaten und Gates stehen im
[Leistungsprotokoll](../../../../docs/superpowers/plans/2026-11-02-targeting-performance.md).
Den tatsächlichen Laufstatus im jüngsten [Arbeitsstand](../../../../docs/ARBEITSSTAND.md) lesen.

`targeting_eval_driver.py` ruft den vorhandenen `scripts.par_eval` mit zwei
Workern auf. Je Rolle laufen sechs Panelgegner und Default gemeinsam; die
Statistik behandelt Default separat. Vollauswahl: fünf Jobs /4.600Spiele;
vorab festgelegter P-only-Fallback: drei Jobs /3000Spiele. Bestätigung in
beiden Fällen unverändert drei Jobs /9000Spiele, höchstens ein Nominee.

`build_targeting_candidates.py` baut ausschließlich Experimentdateien. Der
Vollmodus erfordert vollständige unabhängige Abnahme aller vier Trainingsarme.
Der explizite Modus `--p-only` verwendet keine Trainingsgewichte und beansprucht
keinen Trainingsaudit; er darf nicht mit `--audit` kombiniert werden. P behält alle
36 Netze, PT ersetzt im Vollmodus exakt Komponenten18/19 durch die adaptierten Endstände.
Beide erhalten nur die zwei P-Inferenzflags. Aktive Gewichte werden nie beschrieben.

`targeting_stats.py` akzeptiert ausschließlich vollständige, unveränderte
Phasen mit echten Schlüsseln, Punktzählungv2, Quell-/Modellbindung und denselben
Auswahl-/Bestätigungsquellen. Sie verwendet die festgelegten Gates,
Karten-Bootstraps und den Gleichstandsentscheid für P. Kein nachträgliches Nachrücken.

## Prüfung und Bedienung

Aus dem Projektordner, mit der eingerichteten Python-Umgebung:

```sh
TARGETING_SOURCE_ROOT="$PWD" python -B -m unittest discover \
  -s experiments/analysis/continuation_20261102/performance -p 'test_*.py' -q
python -B experiments/analysis/continuation_20261102/performance/targeting_eval_driver.py --help
```

49 fokussierte synthetische Tests, einschließlich vollständiger künstlicher
3000-/4600-/9000-Dateipipelines und unveränderlicher2/3-Modelllisten. Das sind keine gespielten Lux-Spiele oder Trainings.
Reviewnachweise stehen unter `review/`; der Laufzeitcode ist zur finalen Abnahme
bytegleich. Ein Übertragungsfehler betraf nur zwei Testfixtures, die einen
Tempordner unter `/tmp` voraussetzten; diese sind nach dem Ortswechsel ebenfalls geprüft.

Die Reihenfolge im Vollmodus ist: vier Trainingsarme abschließen und abnehmen → P/PT bauen →
Source/HEAD/Modelle/Protokolle gemeinsam einfrieren (`freeze`) → feste Auswahl
vorbereiten (`prepare --phase selection`) und starten (`run --start`) → vollständig
unabhängig prüfen und zusammenfassen → höchstens den Nominee bestätigen.
`freeze`, `prepare` und ein Import starten selbst keine Spiele.
Die jeweiligen `--help`-Ausgaben dokumentieren die erforderlichen Pfade.
Im datenblind vorab festgelegten Fallback wird nurP ausV14 gebaut und `freeze`
ohne `--pt` erzeugt. Derselbe Freeze gilt für Auswahl/Bestätigung; PT lässt sich
später weder als Kandidat ergänzen noch bestätigen. Die9000Bestätigungsspiele
und Übernahmegates werden durch den Fallback nicht reduziert.

Während eines Freeze keine Quellen oder HEAD ändern. Neue Remote-Commits nur
abrufen und getrennt prüfen. Der Runner erhält ein gemeinsames Manifest für
beide Phasen, stoppt ausschließlich eigene Prozessgruppen und überschreibt
keine fremde Receipt. Zwei Laufzeitklassen berücksichtigen sämtliche vorherigen
Messzeiten, globale Verlangsamung,20% Zeitreserve und60min Schlussreserve.
Kein neuer langer Job unter35%Akku; bei25%Stop, außer bei AC.

Der aktuelle feste Endtermin dieses Werkzeugs ist **03.11.2026,05:30Berlin**,
einschließlich einer Stunde Schlussreserve. Tatsächliche Spiele enden somit
spätestens04:30Berlin. Nach diesem Studientermin nicht unverändert neu starten;
eine weitere Studie braucht einen neuen vorab fixierten Plan.
