# Task 1 — optionale Trainingsregel

Status: Umsetzung fertig; Root hat parallel bereits als `18a81c7` committet. Kein eigener Commit/Push.
Review-Basis laut Root: `b7332c8`.

## Änderung

- `agents/sherlock/config.py`: `AgentConfig.art_splash_in_training: bool = False`; alte fehlende Config-Schlüssel bleiben standardmäßig ausgeschaltet, explizites True wird serialisiert.
- `agents/sherlock/main.py`: `_artillery_ok` verwendet den unveränderten Streuschaden-Zweig zusätzlich bei aktiviertem Trainingsschalter. `_act_est` beobachtet und merkt den vorhandenen Estimator dafür auch ohne `rules_in_training_all`, ausschließlich mit `art_splash`.
- `tests/test_art_splash_training.py`: 40 synthetische Fälle für Default/Config-Roundtrip, Training False/True, deaktiviertes `art_splash`, unbekannten/0,25/0,5/1,0-Streufaktor, Mindesttreffer, Sicherheits-/Energiegrenzen, Punktehalter, reale Estimator-Beobachtungen, finale native Aktionen und `_prev_actions` auf beiden Seiten sowie unveränderte Inferenzaktionen, Merkmale, Masken, Statistik und RNG.

Produktionsdiff: 7 hinzugefügte und 2 ersetzte Zeilen. Keine Schwelle, `art_still`, andere Regel, Reward, Gewichte oder ZIP bearbeitet. Keine Produktionsdiagnostik hinzugefügt.

## Tatsächliche Prüfungen

Interpreter: `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python`.

1. RED vor jeder Produktionsänderung: `-m pytest -q tests/test_art_splash_training.py`. Erster Lauf: 21 Fehler / 19 bestanden in 4,63 s. Acht Fehler waren ein eigener Fixturefehler: unabhängig zufällig initialisierte RNG-Zustände wurden miteinander verglichen. Fixture auf gleichen Seed gesetzt; keine Produktionsänderung dafür.
2. Bereinigter RED: `-m pytest -q tests/test_art_splash_training.py --tb=no`: 13 erwartete Fehler / 27 bestanden in 2,38 s. Fehler ausschließlich fehlendes Config-Feld/Roundtrip, fehlende zusätzliche finale Trainings-SAPs und fehlende Estimator-Beobachtung.
3. GREEN nach minimaler Umsetzung: `-m pytest -q tests/test_art_splash_training.py tests/test_art_splash.py`: **45 bestanden in 3,06 s**, Exit 0, keine Warnungen.
4. `git diff --check`: Exit 0.

Keine vollständigen Spiele, kein Training, keine Gradienten und keine Vollsuite gestartet; der Auftrag beschränkt diese Teilaufgabe ausdrücklich auf synthetische Tests ohne Spiele. Keine laufenden eigenen Prozesse.

## Offene Punkte / Grenzen

- Kein bekannter Umsetzungsblocker. Root verantwortet unabhängige Prüfung und Integration; bei Abschluss dieses Berichts ist Root-Commit `18a81c7` sichtbar.
- Die synthetische Inferenzgleichheit ist kein vollständiger V14-Trace-Nachweis. Die vier separat vorgesehenen bekannten technischen Ausführungen bleiben Aufgabe des Gesamtplans.
- Keine Spielstärkeaussage. Reale Versuchsausführung und Estimator-/Aktionsexposition im Vorlauf bleiben separat abzunehmen.
- Arbeitsstand/Projektübergabe bleiben gemäß Dateizuständigkeit beim Root.
