# Paketfilter: TDD und Diffreview

Arbeitskopie ausschließlich `/Users/moayedshawesh/Desktop/KI/sherlock-november-followup`, Branch `improvement/november-followup-20261101`, Ausgang und unveränderter HEAD `aa06601`. Kein Commit. Die laufende Auswahl in `sherlock-v10-mechanics` wurde nicht berührt.

## Änderung

Nur `scripts/build_submission.py` und die neue Datei `tests/test_submission_sources.py` geändert. Der Builder übernimmt bei `sources()` weiterhin sortierte `*.py`, schließt nun aber Stems aus, die keine Python-Identifier oder harte Pythonkeywords sind. `__init__.py` bleibt wie zuvor separat. Minimaler Produktivdiff: `import keyword` und eine erweiterte Filterbedingung.

Damit werden unter anderem `config 2.py`, `reward 2.py`, Namen mit Bindestrich/Punkt, führender Ziffer und `class.py`/`async.py` ausgeschlossen. Die Quelldateien selbst bleiben erhalten. Importierbare Unicode-Namen, Unterstriche/Ziffern, Softkeywords (`match`, `case`, `type`) und reguläre Module namens `license.py`/`provenance.py` bleiben enthalten. Keine Inhalts-, Lizenz- oder Provenienz-Blacklist.

Gewichteauswahl, Ausgabepfadschutz, ZIP-Writer, Einfrieren, Hinweise und Paketprüfung wurden nicht geändert. Die Tests bestätigen unveränderte Default-/Run-Gewichteauswahl, bytegleich erhaltene Dummygewichte und das separat behandelte `__init__.py`. Es wird nur `sources()` aufgerufen; keine ZIP gebaut und keine Gewichte geladen.

## RED / GREEN

Exakter fokussierter Aufruf aus der Followup-Arbeitskopie, jeweils mit deaktiviertem Plugin-Autoload und ohne Bytecode-Ausgabe:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python \
-m pytest -q --tb=short tests/test_submission_sources.py
```

- **RED vor Produktivänderung:** 11 erwartete Assertion-Fehler, 3 bestanden, **0,12 s**. Jeder Ausschlussfall wurde mit altem Builder fälschlich aufgenommen; kein Import-/Setupfehler. Vollständiger Beleg: `/tmp/sherlock-night-20261101/package-filter-red.log`.
- **GREEN nach minimaler Änderung:** **14 bestanden in 0,08 s**. Beleg: `/tmp/sherlock-night-20261101/package-filter-green.log`.
- Separat den realen Builder importiert und `sys.modules` geprüft: **keine torch-, lux- oder luxai_s3-Module geladen**. Die Tests verwenden ausschließlich Tempdateien/Dummybytes; keine Torch-/Lux-Imports oder Modelle.

## Diffreview / Grenzen

`git diff --check` ohne Befund; `git status --short` zeigt ausschließlich den Builder und die neue Testdatei. Produktivdiff auf den Namensfilter beschränkt, keine Agenten-, Gewichts-, Dokumentations- oder vorhandenen Lizenz-/Provenienzdateien geändert/entfernt. Die Assertions unterscheiden eigenständig erwartete erlaubte und ausgeschlossene Dateinamen; die erwartete Liste wird nicht mit dem Produktivfilter berechnet.

Keine Vollsuite, Spiele, Builds oder Modelljobs gestartet: Dies war ausdrücklich untersagt, während zwei Evaluationsworker laufen. Diese konkrete Ressourcenvorgabe geht der allgemeinen Vollsuite-Empfehlung des TDD-Skills vor. Ein späterer zentraler Gesamttest/Paketbau ist nicht als hier ausgeführt dargestellt. Integration erst an einer zulässigen Phasengrenze; der Fix verändert keine Agentenvariante und keine Spielentscheidungen.
