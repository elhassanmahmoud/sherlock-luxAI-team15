# DQN-Ensembles: vollständige Netze und geprüfte Eingabedimensionen

21.10.2026, Codex, isolierter Zweig `fix/ensemble-dimensions-20261021`, Ausgangsstand `baef7a8`.

Beim Erweitern eines gespeicherten homogenen Ensembles blieb bisher eine vorhandene
`ensemble_dims`-Liste unverändert. Zwei zusätzliche Netze konnten dadurch nur einen
Dimensionseintrag haben. Der Loader verarbeitete beide Listen mit `zip` und lud
unbemerkt weniger Netze, als der Builder gemeldet hatte.

Der Builder schreibt jetzt stets eine vollständige Liste in Netzreihenfolge.
Builder und Loader prüfen vor dem Schreiben beziehungsweise Laden gemeinsam:

- Nichtleere Dimensionslisten haben genau einen Eintrag pro Zusatznetz.
- Jeder Eintrag ist eine positive ganze Zahl, höchstens so groß wie `feature_dim`;
  Boolesche Werte, Strings und Fließkommazahlen werden nicht umgewandelt.
- Die tatsächliche Eingabebreite von `q` und jedem Zusatznetz stimmt mit der
  angegebenen Dimension überein.

Fehlende, `None`- und leere Dimensionslisten bleiben als historisches Format für
homogene Ensembles gültig, wenn sämtliche Tensorbreiten passen. Ein Einzelnetz
mit leerem Ensemble bleibt gültig. Gemischte Netze mit 101/79 Eingaben funktionieren
weiter; der Builder verlangt für das Hinzufügen kleinerer Eingaben weiterhin
`--mixed`. Fehlerhafte Quellen werden vor dem Schreiben der Ausgabe abgewiesen.

## Tatsächlich ausgeführte Prüfung

Nach Freigabe des gemeinsamen Rechenplatzes, vor jeder Produktionsänderung:
`tests/test_ensemble_dimensions.py` ergab **23 fehlgeschlagene und 5 bestandene
Tests** (3,82 s). Der Dreinetzfall reproduzierte die veraltete Liste `[79]` statt
`[79, 79]`; der separate Loaderfall meldete Erfolg mit nur zwei geladenen Netzen.

Nach der Korrektur bestanden **28/28 neue Tests** (3,95 s). Abschließender begrenzter
Lauf mit dem gemeinsamen Python aus `.venv`:

```text
python -m pytest -q tests/test_ensemble_dimensions.py tests/test_persistence.py tests/test_rules_2110.py::test_threat_agent_has_larger_input_and_roundtrips tests/test_rules_2110.py::test_mixed_ensemble_feeds_old_nets_their_first_features
32 passed in 6.42s
```

Geprüft werden echte Speicher-/Bau-/Ladezyklen, genaue Tensoridentität,
Aktionsinferenz nach erneutem Speichern/Erweitern, gemischte Ensembles,
Altformat-Kompatibilität und fehlerhafte Metadaten/Tensorbreiten. Der bestehende
Persistenztest enthält zwei kurze Engine-Testspiele mit Lernschritten.

Keine Änderung an Aktionsregeln, Konfiguration, Reward, Trainingscode oder
Abgabegewichten; kein neuer Stärkevergleich. Die vollständige Testsuite und der
unabhängige abschließende Review sind nach Integration durch Root noch offen.

## Nachtrag: bestehende Testverträge nach Integration angepasst

Roots erster Gesamtlauf deckte zwei ältere Testannahmen auf. Der Kandidatenrunner-
Test erwartete noch einen zufällig initialisierten Ersatz bei falscher
`feature_dim`; er verlangt jetzt die frühe Ausnahme. Die unabhängigen
Probe-Prüfungen gegen veränderte Tensoren, falsche Architektur und abweichende
Konfiguration bleiben ausdrücklich enthalten. Die inerten 21-Netz-Prüfdaten der
Curriculumstudie enthalten jetzt zusätzlich `body.0.weight` mit Eingabebreite 79.
Ihre bisherigen Identitätsmarker, Herkunfts-, Sperr- und Gate-Prüfungen bleiben
unverändert. Produktionsvalidator und Modellcode wurden nicht gelockert.

Vor den Testanpassungen reproduzierten die zwei gezielt ausgewählten Fälle
**2 Fehler in 4,34 s**. Danach bestanden beide vollständigen betroffenen Dateien:

```text
python -m pytest -q tests/test_candidate_runner.py tests/test_early_curriculum_study.py
98 passed in 44.30s
```

Dieser Nachtrag enthält nur Test- und Dokumentationsänderungen. Die erneute
vollständige Prüfung des zusammengeführten Stands bleibt bei Root.

### Gemeinsame Abschlussprüfung

Nach Integration in den V4-Arbeitszweig und der zusätzlichen Breitenangabe im dortigen Zielpilot-Mock bestand Root den vollständigen Lauf: 531 Tests plus 14 Untertests, 82,52 Sekunden. Unabhängiger statischer Follow-up-Review bestätigte unveränderte Identitäts-, Provenienz- und Gate-Assertions; [Review](ENSEMBLE_DIMENSIONEN_REVIEW_20261021.md). Dies ist die Suite des zusammengeführten Arbeitszweigs, kein behaupteter separater Volltest von main.
