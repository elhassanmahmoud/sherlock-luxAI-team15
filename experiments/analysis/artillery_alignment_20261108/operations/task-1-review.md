# Task 1 — unabhängiger Spec- und Qualitätsreview

Reviewbasis: `b7332c8..18a81c7`, Task-Brief/-Bericht, tatsächliche Produktionsdateien und Testquellen. Root-Entscheidung berücksichtigt: Der neue Schalter funktioniert auch ohne `rules_in_training_all`; dafür ist die zusätzliche Estimatorversorgung ausdrücklich erforderlich. Die geplanten Studienarme verwenden beide `rules_in_training_all=True`.

## Spec: PASS

- `AgentConfig.art_splash_in_training=False` bleibt bei fehlendem Altschlüssel ausgeschaltet; `from_dict`/`to_dict` erhalten explizites True. Ohne `art_splash` ist der Schalter wirkungslos.
- `_artillery_ok` erweitert ausschließlich die Freigabebedingung des vorhandenen Streuschadenzweigs. Treffer-, Konfidenz-, Sicherheits-, Energie-/Reservegrenzen und Halterausschluss bleiben erhalten. `art_still` und nachfolgende Regeln werden nicht verändert.
- `_act_est` führt `observe` vor der Entscheidung mit aktueller unveränderter Beobachtung/Team-ID und `remember` danach mit den endgültigen nativen Aktionen aus. Die zusätzliche Bedingung versorgt den Estimator auch ohne den breiten Trainingsschalter. `new_game` setzt ihn weiterhin zurück.
- Bei Inferenz sind beide neuen Bedingungen logisch unabhängig vom neuen Flag. Andere Estimatorverbraucher behalten ihre bisherigen Trainingsbedingungen; mit `rules_in_training_all=False` werden dadurch keine weiteren Regeln freigeschaltet. Im festgelegten Studienfall war die Versorgung bereits für beide Arme aktiv.
- Der Commit betrifft genau Config, Aktionsdatei und neue Tests. Keine Änderungen an Reward, Merkmalen, Masken, Replayformat, Gewichten oder ZIP.

## Qualität: PASS

Keine blockierenden Befunde. Der Produktionsdiff ist klein und verwendet die vorhandene Implementierung, statt Regeln oder Schätzlogik zu duplizieren.

Die 40 neuen synthetischen Fälle decken fehlenden/False-Schlüssel, True-Roundtrip, beide Trainingswerte, deaktiviertes `art_splash`, unbekannten/0,25/0,5/1,0-Streufaktor, Schwellen 0,5/1,0, Trefferzahl, bewaffneten Gegner an der Energiegrenze, Reservegrenze, Punktehalter, reale Estimatorupdates auf beiden Seiten und native Endaktion plus `_prev_actions` ab. Inferenzvergleiche prüfen zusätzlich Merkmale, Masken, Statistik und RNG. Die vorhandenen fünf Streuschadentests bleiben unverändert.

Tatsächlich in diesem Review: Quellen-/Diffprüfung einschließlich Aufrufkette und Estimatorverbrauchern; `git diff b7332c8 18a81c7 --check` erfolgreich. Die im Implementierungsbericht gemeldeten **45 bestandenen Tests** wurden entsprechend Auftrag nicht erneut ausgeführt. Keine Modelle geladen, Spiele, Lernupdates oder Tests gestartet. Vollständige V14-Tracegleichheit und reale zusätzliche SAP-Exposition bleiben separate Abnahmen.

## Ergänzender Technikvermerk: PASS für die geplante Ausführung

`operations/technical_trace.py` gegen den früheren Fog-Prüfer gelesen. Änderungen beschränken sich auf Studienpfade/STOP/PID-Metadaten, den neuen Flag und die zusätzliche Prüfung `not self.training`/korrekter Flag bei jedem Agentenzug. Dieselben zwei bekannten Schlüssel laufen je False/True: vier Ausführungen. Jeweils werden alle 303 Frames einschließlich der gespeicherten Zustands-/Beobachtungs-/Aktionsbelege und das vollständige Spielergebnis mit den historischen V14-Referenzen exakt verglichen.

Der bestehende Ressourcen-Lock und Guard prüfen Quellen/HEAD/Pläne, Referenzen, V14-/ZIP-Hashes, AC, Kontingent, STOP und fremde Prozesse; `finally` stellt beide temporär ersetzten Methoden wieder her und schreibt den Abschlussstatus. Die verwendete `probe.play`-Route ist uninstrumentierte Inferenz ohne Lernen. Keine Blocker im eng geprüften Adapterdiff. **Noch kein Ausführungs-PASS**: Root führt die vier technischen Reproduktionen erst nach dem Code-Freeze aus.
