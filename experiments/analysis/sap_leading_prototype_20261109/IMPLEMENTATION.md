# Technischer SAP-Vorhalteprototyp, ausschließlich extern

Bindender Plan: `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/docs/superpowers/plans/2026-11-08-sap-leading-prototype.md`.

`scripts/sap_leading_agent.py` enthält die 156-zeilige experimentlokale `SapLeadingAgent`-Unterklasse. Gleiche Konstruktorparameter wie der Core, `train=False` als Vorgabe und zusätzlich ausschließlich keyword `lead_enabled=False`. Explizites Training, `set_to_train_mode` und `update` werden abgelehnt; Autosave und Lernfreigabe sind aus. Keine produktive Quelldatei wurde verändert.

Ein einziger originaler `_act` erzeugt zunächst alle Befehle. Die Erweiterung prüft dann öffentliche Historie, Energie, Zielzuordnung, Geometrie und den vorhandenen Parameterposterior. Nur beim kleinsten geeigneten Schützen werden die beiden nativen SAP-Offsetkomponenten ersetzt. Originales `_act_est` beobachtet vorher und erinnert den geänderten Befehl danach. SAP-Klasse, andere Befehle, Features/Masken/Cache und Pendinglisten bleiben erhalten; gespeicherter alter `_sap_hits`-Wert dient der Delta-Korrektur von `sap_hits_est`. Der neue Wert zählt die aktuell sichtbaren Gegner im neuen 3×3-Bereich und behauptet keinen zukünftigen Treffer.

Routineentscheidungen: Bei einer von V14 abweichenden Config ohne aktiven originalen Eval-Estimatorpfad bleibt die Aktion unverändert; es gibt kein zusätzliches `observe`. Deaktivierter Modus sammelt keine eigene Historie. Aktivierte Historie speichert nur kopierte Tupel/Skalare, einschließlich Schritt/Match/Spiegelungsmodus. Ein Reset, fehlender oder veralteter Corecache unterbricht sie. Kumulative `leading_stats` gelten pro Spiel und werden mit dem originalen Episodenreset zurückgesetzt; sie beeinflussen keine Entscheidung. `leading_last` ist ausschließlich der letzte tatsächlich geänderte Befehl samt öffentlichem Ziel-/Zeitbeleg, sonst `None`.

## Tatsächlich ausgeführte synthetische Prüfung

```sh
env PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15 \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B \
  -m pytest -q -p no:cacheprovider \
  /tmp/sap-leading-prototype/tests/test_sap_leading_agent.py
```

- Tests zuerst geschrieben. RED-Aufruf zusätzlich `-k known_public_lead`: **2 fehlgeschlagen, 40 abgewählt**, Exit1, 2,45s. Beide scheiterten am noch unveränderten SAP-Offset. Rohbeleg `RED.log`.
- Erste vollständige Prüfung: **40 bestanden, 2 fehlgeschlagen**, Exit1, 2,32s (`FIRST_FULL.log`). Ursache war die Testannahme, dass log/exp-Normalisierung eines vorgegebenen Werts0,9 exakt0,9 zurückliefert. Tatsächlich lag der berechnete Wert knapp darunter. Keine Änderung am produktiven Schätzer oder Schwellenwert: reale Logposteriorfälle liegen jetzt ausdrücklich ober-/unterhalb; zwei zusätzliche Tests prüfen den exakten Posteriorwert0,9 und dessen direkten Gleitkommanachbarn.
- Finale vollständige lokale Testdatei: **44 bestanden**, Exit0, 1,55s; `GREEN.log`. Die ursprünglichen beiden RED-Fälle sind enthalten.

Die Tests ersetzen nur Basiskonstruktor und Core-`_act` durch synthetische Ein-/Ausgaben, um den Hook isoliert zu prüfen. Echte originale `_act_est`, Episodenreset, `new_game`, Parameterentscheidung und `remember` werden verwendet. `QNet`-Konstruktion und `torch.load` sind durch fehlschlagende Testwächter gesperrt. NumPy/Torch werden durch Quellenimporte geladen, aber es werden keine Netze konstruiert, Gewichte/Tensorarchive geladen oder Vorwärtsläufe/Spiele ausgeführt. Kein Gesamtprojekt-Testlauf, da dieser die ausdrücklich untersagte Modell-/Spielgrenze überschreiten könnte. Reale Integration bleibt offen und separat freizugeben.

## Prüffassung und Schutzdateien

| Datei | SHA256 |
|---|---|
| `scripts/sap_leading_agent.py` | `3b4b779f25f32af9f523b69b169a68eea78b862ce89ede77a3138ef2db26c2eb` |
| `tests/test_sap_leading_agent.py` | `1e3c5835af3bc8f823a7383de2bcec5a11bf188377f699a3a5b3d03b6b50ea22` |
| `RED.log` | `095341aec48bca1fc1083f478ff3b3de9afd79da93d9cf1f46f89485defd4292` |
| `GREEN.log` | `98785bd0cb049358efc5dd3df77560b7b63bb629b1e53d1f3781985abe84a3ad` |
| Beide produktiven V14-Gewichte | `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` |
| `Gruppe15.zip` | `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6` |

Schutzdateien abschließend nur gehasht: entsprechen den historischen V14-Pins. `git diff --stat -- agents/sherlock` war leer. Keine Repositoryaufnahme, Gewichtsänderung, Kartenreservierung oder automatische Spiel-/Studienfreigabe. Unabhängiger enger Code-Review für diese Fassung ist angefragt.
