# Finaler unabhängiger Code- und Grenzreview

Geprüft: vollständiges Reviewpaket `final-code-review.diff` und tatsächlicher Git-Diff `aa06601→c905c63`, aktueller Builderkontext, neue Paketquelltests, Arbeitsbaumgrenzen, aktive Gewichts-SHAs und Byteidentität der drei nach Studienabschluss archivierten Analyseprogramme. Keine Auswahldaten erneut ausgewertet, keine Modelle, Spiele, Testwiederholungen oder Quelländerungen.

**Ergebnis: keine actionable Codebefunde. Spec-konform für den abschließenden Paketfilter.** Kein unbeabsichtigter Agenten-/Gewichts-/Gauß-Eingriff über `aa06601` hinaus gefunden. Kein heute erfolgter Push und kein fertiger Paket-/Runnernachweis werden aus diesem Lesereview abgeleitet; diese Prüfungen führt Root separat aus.

## Änderung und Qualität

Der committete Source-Diff enthält exakt zwei Dateien: `scripts/build_submission.py` und die neue `tests/test_submission_sources.py`. Einziger Produktivunterschied ist der zusätzliche Standardbibliotheksimport `keyword` und der Dateinamensfilter in `build_submission.py:62–63`.

Der Filter behält Python-Identifier als Modulstämme bei und verwirft harte Schlüsselwörter. Damit verschwinden lokale Kopien wie `config 2.py`, `reward 2.py`, Namen mit Bindestrich/Punkt oder führender Ziffer. Gültige Namen mit Unterstrich, späteren Ziffern und Unicode bleiben erhalten. Soft Keywords `case`, `match`, `type` werden korrekt nicht versehentlich verworfen. Es gibt keine fragile Whitelist, die ein späteres gültiges Laufzeitmodul verlieren würde, und keine zusätzliche Abhängigkeit.

`__init__.py` bleibt wie zuvor separat als Paketinitializer erzeugt. Die bestehenden Entscheidungen zu P0/P1, geteilten Rungewichten, Ausgabezielschutz und Battle-Freeze bleiben unverändert. Der Filter löscht oder verändert keine lokale Quelldatei. `sources()` wird von beiden Paketbauarten verwendet, sodass der Schutz konsistent greift.

Die neuen Tests verwenden temporäre Quellen und Dummy-Gewichte. Sie prüfen tatsächliche Dateiauswahl, Bewahrung lokaler Ausschlussdateien, Erhalt gültiger/Unicode-/Soft-Keywordmodule und unveränderte Gewichts-/Initializer-/Ausgabezielbehandlung. Keine Modell-/Enginearbeit ist hierfür nötig. Der von Root gelieferte vollständige Testlog endet mit **694 bestanden und14Subtests in119,95s**. Dieser Lauf wurde gelesen und nicht wiederholt.

## Abgrenzung zu Agent und Abgabe

- Der tatsächliche vollständige Diff unter `agents/` zwischen `aa06601` und `c905c63` ist leer; auch im aktuellen Arbeitsbaum gibt es darüber hinaus keine Agentenänderung.
- Unter `agents/`, `scripts/` und `lux/` ist über `aa06601` hinaus allein der beauftragte Builder verändert. Keine neue Aktions-, Belief-, Reward-, Netz- oder Evaluationslogik.
- Kein Gauß-Merge: der getrennte technische Prototyp bleibt außerhalb dieser Abgabequelle.
- Beide aktuellen Dateien `agents/sherlock/weights/agent_p0.pth` und `agent_p1.pth` wurden als Bytes gehasht und sind weiterhin exakt V14:
  `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.
- Der Builder sammelt ausschließlich direkte gültige `*.py` aus `agents/sherlock`; Gewichte und Paket-Hinweise/Importkonfiguration werden gezielt ergänzt. Er durchsucht kein `docs/` oder `experiments/` rekursiv. Interne Forschungs-/Arbeitsstanddokumente und nachträgliche Auswerter gelangen über diesen Pfad nicht in die ZIP.

## Archivierte Auswerter nach Freeze

Die drei neuen Pythondateien unter `experiments/analysis/night_20261101` wurden byteweise per SHA mit den bereits vor ihrer Anwendung überprüften externen Originalen und dem Archivmanifest verglichen:

- `selection-independent-audit.py`: `aa19d5790c4fe311e0de6f9a1cd1c520e4e2c195edcce3eebf844af06dbc8683`
- `confirmation200-summary.py`: `83430c9f2b8aadede9da807d88026c2416b07b89a5d2eccbac28ce8829216c4d`
- `confirmation200-independent-audit.py`: `b14f91a9b321f5f33eaf3bc8870ae819ed85738b8a5bcda8678b1392a037f0b9`

Alle drei sind unveränderte Archivkopien nach der abgeschlossenen unabhängigen Studienabnahme. Sie sind keine nachträgliche Änderung der damals eingefrorenen Ausführung. Ihre Erstellung im Archiv darf die alte Freeze-Identität erwartungsgemäß verändern; historische Messungen wurden davor vollständig geprüft. Kein erneuter Datenlauf wurde hierfür gestartet.

## Abschlussgrenze

Die Studie ist bereits unabhängig mit vollständigen Daten abgenommen und hat den Kandidaten **nicht** qualifiziert. Dieser Review bestätigt ausschließlich den abschließenden Code-/Paketquellumfang und unveränderte V14-Gewichte. Root muss den noch laufenden konkreten ZIP-Bau und die acht Kursprüfspiele mit ihrem tatsächlichen Ergebnis separat dokumentieren. Keine offenen Codeblocker aus diesem Review.
