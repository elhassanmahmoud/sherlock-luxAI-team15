# Gauß-Admission abgeschlossen · 02.11.2026

**Technische Admission PASS; praktische Routinghürde FAIL.** Gauß geht nicht in einen Stärkevergleich und nicht in den Hauptzweig. Der standardmäßig ausgeschaltete Prototyp bleibt separat; V14 wird durch diese Studie nicht ersetzt.

Genau **168 vollständige Spiele** wurden abgeschlossen: C8 auf vier festen Schlüsseln je Quelle, danach S160 auf 840000–840039, beide Seiten und beide Quellen. Alle 84 Quellenpaare stimmen in nativen Aktionsbytes beider Teams, Ergebnissen und v2-Punkten überein; C reproduziert zusätzlich die historischen Benchmarkwerte. Jedes Spiel enthält 303 Rohframes mit 300 frischen Entscheidungen und drei Resets, insgesamt 50.904 Rohframes. Der S-Prototyp liefert 24.000 frische Shadowentscheidungen. Die handelnden Agenten hatten Overlap/Gauß ausgeschaltet; nur unabhängige Belief-Shadows verwendeten diese Verfahren.

Das [unabhängige Audit](independent/gauss_independent_audit.md) akzeptierte die Daten mit **1.318.342 Prüfungen und null Fehlern**. Root verifizierte außerdem **751 Tests und 14 Untertests**, siehe [Vollsuitenlog](implementation/fullsuite.log). Für diesen Abschluss wurden weder Audit noch Tests, Modelle oder Spiele erneut ausgeführt.

## Informationsgewinn und Entscheidung

**Vier strikte neue Fakten: zwei Punkt- und zwei Nullfelder.** Alle stammen aus 840011/P0, Match 0, Frame 80. Positive Weltfelder: `(2,14)`, `(9,21)`; Nullfelder: `(1,14)`, `(9,22)`. V und A kennen alle vier ab Frame 81: jeweils genau ein beobachteter Schritt Vorsprung, keine zensierten Fälle. Es gab keine falschen Zusatzfakten von G oder A, auch auf Resetframes.

Die vor Abschluss und vor dem Lesen der S-Ausgänge festgehaltene [Routingdefinition](independent/gauss-independent-audit-pin.json) wird unverändert angewendet. Positive physische Fakten werden als `(seed, world_x, world_y, point)` über Seiten und Erwerbsmatches entdoppelt. Vorteil-Feld-Schritte zählen je frischem Frame `G_point − (V_point ∪ A_point)`, einschließlich persistierender Vorteile.

| Praktische Mindesthürde | Tatsächlich | Ergebnis |
|---|---:|---|
| 20 strikte positive physische Fakten | 2 | FAIL |
| 5 erwerbende Spiele | 1 von 80 | FAIL |
| 3 erwerbende Karten | 1 von 40 | FAIL |
| 100 positive Vorteil-Feld-Schritte über V∪A | 2 | FAIL |

Die technische Mindesthürde von mindestens einem sicheren strikten Fakt wurde erfüllt. Der praktische Mehrwert reicht für die festgelegte Alternativroute nicht aus. Es wurden keine aktiven G-Agenten, A-/G-Siegquoten oder Stärkekandidaten geprüft und keine Hürde nachträglich gelockert.

G unternahm 161 Solverversuche in 240 Matchverläufen, maximal vier pro Match; beobachtete Abstände lagen bei 8–54 frischen Beobachtungen. G.observe CPU: P95 **0,092 ms**, Maximum **0,704 ms**; Wall: P95 **0,093375 ms**, Maximum **1,321250 ms**. Alle festen Kostenhürden wurden bestanden. Die feste V/A/G-Reihenfolge und der gemeinsame Warmzustand erlauben daraus keinen Schluss auf die Latenz eines aktivierten G-Agenten. S dauerte im inneren Phasentimer 625,1 s, unter dem Limit von 1.800 s.

Die separat beschriebenen **946 vorhandenen V-Falsch-Null-Fakt-Schritte** betreffen gespeichertes Nullwissen während regulärer Entscheidungen; alle lagen bereits im jeweiligen V-Vorherzustand. Das sind keine 946 unabhängigen neuen Ableitungen. Der [deskriptive Kontext](independent/gauss_baseline_fact_context.md) belegt weder Ursache noch Handlungsfolgen und ist kein neuer Bugbefund.

## Historische Bindung und Archiv

Diese Ausführungsidentitäten bleiben erhalten, auch nach Ende des Quellen-Freeze und späterem Sync:

| Quelle | Tatsächlich ausgeführter HEAD | Geprüfte Runtimebasis |
|---|---|---|
| Primäre Referenz | `384dad2b5a077f5ab026f63c5c8a2d944bc51776` | `3a7e7825b614a30bc85c7895a38e6b9fc62efdd5` |
| Separater Prototyp | `969cc319c76fbb5d01454bab1591f3411864f867` | `307b1ed2051cb9b1a339f849f4322630f5dca7b9` |

V14 blieb bei SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`: 36 identische geladene Netze, 79 Features, sechs Aktionen, Evaluation, Epsilon 0 und Autosave aus. Das [historische Manifest](evidence/manifest.json) und alle Phasenseals bleiben unverändert. Ein späterer Dokumentations-HEAD ist kein Ausführungs-HEAD; nach Ende des Freeze wurde kein gegen den aktuellen HEAD prüfendes Audit neu gestartet.

- [Rohdaten und ursprüngliche Werkzeugauswertung](evidence/): alle 168 Gzip-Traces, Ergebnis-/Timingdateien, Lade-/Importbelege und Phasenseals.
- [Unabhängiges Audit-JSON](independent/gauss_independent_audit.json), [unverändertes Auditskript](independent/gauss_independent_audit.py) und [Pin-/Routing-Sidecar](independent/gauss-independent-audit-pin.json).
- [C-Ausführungsbeleg](execution/gauss_C_execution.json), [S-Ausführungsbeleg](execution/gauss_S_execution.json), [Supervisor](execution/run_gauss_stage.py), [ausgeführter Plan](execution/admission_plan_executed.md) und bytegleiche historische C-Benchmark-CSV.
- [Implementierungsbericht](implementation/task-1-report.md), [Erstreview](implementation/task-1-review.md), [sauberes Re-Review](implementation/task-1-rereview-1.md), fokussierte Rot-/Grünlogs und Vollsuitenlog. Frühere Statusangaben darin sind historische Übergaben; dieser Abschluss beschreibt das endgültige Studienergebnis.
- [Archivprovenienz](ARCHIVE_PROVENANCE.json) und [Dateihashes](SHA256SUMS). Die Archivierung hat alle 527 bereits vorhandenen Evidenzdateien unverändert erhalten und kopierte Belege byteweise gegen ihre Originale geprüft.
