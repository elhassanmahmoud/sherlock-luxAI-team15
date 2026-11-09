# SAP-Motion-Runner: gezielte Umsetzung

09.11.2026. Neue Dateien im Studiencheckout, keine Commits, Modellkonstruktionen, Tensorloads, Spiele oder Trainingsupdates. Root übernimmt Dokumentation und Aufnahme; reale technische Integration bleibt offen.

Feste Ausgangskopie: geprüfter `sap_leading_eval.py`/`sap_leading_owner.py`. Der Owner unterscheidet sich ausschließlich in den zwei Modulverweisen. Workeränderungen: Profil `sap_motion_screen_20261109`, `SapMotionAgent` mit gleichem `lead_enabled`-Interface, Panel9942000–9942019/Direkt9942100–9942119 und unabhängige öffentliche Bewegungs-/Entscheidungsrekonstruktion. Die vier bekannten technischen Schlüssel, 120er-Matrix, Ganzkartenbootstrap und drei Gates bleiben methodisch gleich. Schutzvertrag einschließlich expliziter Akkuoption unverändert; kein automatischer Start, keine Wiederholung oder neue Infrastruktur.

Die vorhandene passive Core-Umhüllung bleibt erhalten. Zusätzlich rekonstruiert sie pro ON-Partie eigene Fünfklassenhäufigkeiten aus drei unmittelbar aufeinanderfolgenden öffentlichen Frames, mit Match-/Spiegelungs-/Sicht-/Energiegrenzen. Diese Zähler werden in jedem Frame gegen Agent und Diagnosezähler geprüft. Eingriffe werden unabhängig aus Prior1, mindestens32Beobachtungen, sichtbarer Geometrie, konservativen Nebentreffern und `mean−2sd>0` rekonstruiert. Kleinste geeignete UID, native Endbefehle, ursprüngliches `remember` und produktive Buchhaltung werden weiterhin geprüft. Die protokollierten Modellgrößen des Agenten müssen mit der unabhängigen Rechnung übereinstimmen (Fließkommatoleranz1e−12). Keine zweite Agententscheidung und kein Zugriff auf künftige Beobachtungen.

## Tatsächlich ausgeführte gezielte Tests

Arbeitsverzeichnis: `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15`.

```sh
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_sap_motion_screen.py > /tmp/sap-motion-runner/GREEN.log 2>&1
```

- Erste Ausführung desselben Testsatzes gegen die unveränderte Ausgangskopie (damals24Fälle, Ausgabe `RED.log`): **24FAIL,0,28s,Exit1**. Erwartete fehlende neue Profile/Factory/Rekonstruktionsfunktionen/Ownerdatei.
- Danach neue gezielte Diagnoseprüfungen vor Implementierung des Checkers, gleicher Aufruf mit `-k live_motion_check`, Ausgabe `RED-hook.log`: **6FAIL,24deselected,0,05s,Exit1**; fehlender `check_motion`.
- Finale Ausführung oben, Ausgabe `GREEN.log`: **30PASS,0,24s,Exit0**. Matrix/Gates, gemockte Factory, fünf relative Klassen, ungültige Übergänge, Posterior/Unsicherheit, Off/geringe Unterstützung, kanonische Spiegelung, bekannte versus verborgene Hindernisse, verlorene Nebentreffer und absichtlich falsche Diagnosewerte.

Die Dateien sind tatsächliche umgeleitete Prozessausgaben, keine rekonstruierten Logs. Keine erneute50er-Batteriesuite und kein Gesamttestlauf. Factorymodule wurden gemockt; keine echten Modelle oder Spielumgebungen erzeugt. Eine echte Vier-Spiel-Integration ist damit ausdrücklich noch nicht belegt.

## SHA-256 der übergebenen Fassung

| Datei | SHA-256 |
|---|---|
| scripts/sap_motion_eval.py | 10485a00a24b571ec03eacfa0c9f6725771f25592267d6dc315be5f657fbcb59 |
| scripts/sap_motion_owner.py | ef7432694b1f8e2de8842a0c1b640af3c84e1ab1bc8355232981f6ea5ca80e53 |
| tests/test_sap_motion_screen.py | 97c414462fcee1f8f67b5f762cf2639b6cf396566f699f61e62f6b2a861da2de |
| RED.log | a6332a30b7d8e478e694ef462dbefff812fb8049e4ee90e138d8d910f047d810 |
| RED-hook.log | 3b283d090d402ea9926856818480c0c3e6602939e11637e844de9841cbd036c2 |
| GREEN.log | dd662b76eb38c0d930f3da911be9db6b3ab567f86b724a38c302e03008d82b7d |

Start weiterhin ausschließlich durch getrennte gehashte Root-Aufnahme. Laufaufruf strukturell unverändert, Owner jetzt `python -B -m scripts.sap_motion_owner technical|performance --admission ABSOLUTER_PFAD --admission-sha SHA256 --usage-file ABSOLUTER_USAGE_PFAD`; keine implizite Verbindung beider Phasen. Analyse später über `scripts.sap_motion_eval analyze` mit denselben Aufnahme-/Owner-State-Argumenten wie beim Leading-Runner.
