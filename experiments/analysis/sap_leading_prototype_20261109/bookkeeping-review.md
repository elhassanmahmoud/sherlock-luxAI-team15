# SAP→SAP-Offsetwechsel: ursprüngliche Buchhaltung

**Lesender Befund: Der geplante enge Hook ist geeignet.** Überschreiben von `_act`, genau einmal `super()._act(step, obs)`, danach höchstens eine SAP-Zeile ändern und zurückgeben. Das unveränderte `_act_est` führt bereits `param_est.observe → self._act → param_est.remember` aus ([main.py:303](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/main.py:303)). Damit sieht die Auswahl die aktualisierte Parameterschätzung und `remember` den tatsächlich ausgegebenen nativen Befehl. Kein zusätzlicher Observe-/Remember-/Entscheidungsaufruf. Die gebundene V14-Config aktiviert diesen Pfad bereits über `art_splash`, `sap_still_splash` und `nebula_avoid`.

## Genau erforderliche Änderungen

| Feld | Änderung für den einen gewählten UID |
|---|---|
| Zurückgegebene native `actions[uid]` | Klasse bleibt5; nur beide Offsetkomponenten ersetzen. Alle anderen Zeilen unverändert. |
| `_sap_hits[uid]` | Trefferindikator für das neue **kanonische** Zentrum anhand aktueller sichtbarer `enemy_coords` neu zählen: Anzahl mit Chebyshev-Abstand≤1. Das entspricht der Core-Grundkonvention in `_best_sap_target` (main.py1491ff.): keine Dropoffgewichtung und keine zusätzliche Energie-/Survivalfilterung. Keine prognostizierten zukünftigen Treffer als beobachtet eintragen. |
| `ep_stats['sap_hits_est']` | Nur `int(new_hits > 0) − int(old_hits > 0)` addieren. `old_hits` ist der bereits gespeicherte Originalwert **vor** dem Ersetzen, nicht eine nachträglich neu berechnete alte Geometrie. Der Zähler misst SAP-Versuche mit positivem Trefferindikator, nicht die Zahl getroffener Gegner. |
| `_sap_unknown` | Nur `discard(uid)`: Das neue Zentrum wurde ausdrücklich als aktuell sichtbar gewählt; seine Herkunft ist kein finaler Fog-SAP mehr. Markierungen anderer Schützen erhalten. |

Originalschreibstellen: [main.py:596](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/main.py:596). `_sap_hits` und `_sap_unknown` sind außerdem Eingaben des Trainingsrewards (main.py1555ff.; reward.py149ff.); der Prototyp darf deshalb Training weiterhin ablehnen, ohne diese Werte im Evalbetrieb irreführend zu belassen.

## Was beim reinen Offsetwechsel unverändert bleibt

- **`sap_attempts`:** Der SAP wurde vom Core bereits einmal gezählt; keine zweite Zählung.
- **`_prev_actions[uid]`:** enthält nur die kanonische Aktionsklasse, keinen Zieloffset. SAP bleibtSAP. Merkmale, Masken, `_prev_ctx` und die übrigen Unit-Einträge bleiben unverändert.
- **`_pred_pending`:** Tupel `(eigener_uid, eigene_x, eigene_y, eigene_Energie, sapped)`. Es betrifft vorhergesagte gegnerische Treffer auf eigene stehende Units und die Subtraktion eigener SAP-Kosten, nicht das eigene SAP-Ziel ([main.py:554](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/main.py:554), `_check_predictions`783ff.). Eigenposition, eigene Kosten und SAP-Klasse ändern sich nicht: nichts umschreiben.
- **`_shape_pending`:** dasselbe Prinzip mit zusätzlichem `form`; eigene Position/Energie und SAP-Kostenflag für die Diagnose gegnerischer SAP-Formen ([main.py:803](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/main.py:803)). Kein eigenes Zielzentrum gespeichert: unverändert lassen; `_record_shapes` nicht erneut rufen.
- **`param_est._prev`:** nicht manuell anfassen. Originales `remember` kopiert danach die vollständigen nativen Aktionen einschließlich des neuen Offsets ([param_est.py:134](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/param_est.py:134)).
- **Lokale Teamplanung (`planned`, `planned_dmg`, `planned_fog`) und `_cache`/`sap_targets`:** keine nachträgliche Neuplanung. Die Arrays sind lokale Entscheidungshilfen des abgeschlossenen Core-Aufrufs; andere Endaktionen bleiben absichtlich fixiert. Der Helpervorschlag im Cache ist kein finaler Zielbeleg. Folgeinteraktionen mit der ursprünglichen Teamplanung sind eine Wirkungsgrenze dieses Eingriffs, kein Anlass, weitere Units umzuschreiben.

## Koordinaten und Historie

Corekontext und eigene Positionen sind kanonisch. Den alten nativen SAP-Offset bei `belief.mirrored` mit `mirror_delta(dx,dy)=(-dy,-dx)` genau einmal in diesen Raum bringen; das neue Zentrum dort prüfen und den neuen Offset vor Rückgabe mit derselben involutiven Abbildung zurückwandeln. Die Bedingung ist **`belief.mirrored`**, nicht pauschal `player_1`; keine zweite Spiegelung bereits kanonischer Positionen ([geometry.py:60](/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15/agents/sherlock/geometry.py:60)).

Nach dem Originalaufruf enthält `_enemy_prev` schon die aktuelle Beobachtung (`_enemy_stationary`, main.py1130ff.). Für Vorhalten ist daher die geplante separate kopierte öffentliche Historie erforderlich; Originalcache nicht zurücksetzen. Bei Matchstart hat der Core `_prev_ctx=None` und leere Pendinglisten hergestellt; diesen No-op/Reset erhalten, keinen alten Cache als aktuelle Entscheidung verwenden.

**Prüfumfang:** ausschließlich Plan und originale Quellen gelesen, Dateihashes bestimmt; keine Implementierung, Imports, Tests, Modelle oder Spiele. Noch keine Abnahme eines fertigen Prototyps und keine Spielstartfreigabe. Quellen-SHA256: main.py `108ea9cb072bbdba0987d91873a7001cedda420b965da96cd9e9090e7c1d33bc`; geometry.py `081ffbbfa6b50b8d01b1a2875250ec7c66aa8275a56bb44bc478808df099c9fa`; param_est.py `c98eae7b8afba125bc7df3b2e8371b3c00a89ead149d3058a1dbc448affd8419`; reward.py `9953671c54315132ee28cdcbfe3968e23e0bbdce9e67298d794cd02633639bc8`; technischer Plan `89d0e81f895d85c375e33e45726741348f7af78aadd6b898a1153cc1467c706f`.
