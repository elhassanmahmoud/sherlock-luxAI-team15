# Unabhängiger Task4-Entwurfsreview

**PASS_STATIC_DRAFT – keine konkreten Blocker in der gelesenen Fassung. Alle Tests: UNRUN.**

08.11.2026, während des von Root gemeldeten Trainingsfreeze945e193. Nur externe Entwurfsdateien, feste Spec/Plan/Übergabe und unmittelbar verwendete Repo-Helfer gelesen. Keine Imports, Syntaxprüfung, Tests, Modell-/Checkpointladungen, Forwards, Spiele oder Repoänderungen. Dieser Bericht erteilt keine Startfreigabe und bestätigt keine tatsächlich abgeschlossene Trainingsabnahme.

## Exakte geprüfte Fassungen

Die vier externen Dateien wurden vollständig gelesen; ihre SHA-256 waren bei wiederholter Kontrolle unverändert:

| Datei unter `/tmp/sampled-target-performance-staging/` | SHA-256 |
|---|---|
| `scripts/sampled_target_compare.py` | `ea5b853ed7981ebe87d684210c98f7ee1bac8ea383e9f30fd2a744496703a9ea` |
| `scripts/sampled_target_eval.py` | `96e72e72652f9f9b4644480f468ba812705b9b812bcd2963f46ce98ef1fbe1f5` |
| `tests/test_sampled_target_performance.py` | `7a1748eef0d8c08ceb4b8b80919c7bccddadcdea69d0010fa95b0bcc8cbc20ce` |
| `README.md` | `f79b19ffcc3ccbe07953546e386e2724305a2d3f047592cc51ee645970786265` |

Methodenanker:

- `/tmp/sampled-target-task4-handoff.md`: `46b12887f407713771d048767697438a3ddd2feb742e470d8a1153dd9522fb52`.
- Committe Spec `docs/superpowers/specs/2026-11-08-sampled-target.md`: `0b3e86ca7e1ca2559f9001343f8c8073127d5d46c363ec761500964e8ae91a2d`.
- Committer Plan `docs/superpowers/plans/2026-11-08-sampled-target.md`: `2649209104db363c8b5fb0efcfdf6cb5ccaf8a4de27957abe86159f351b44d34`.

## Prüfergebnis

1. **Genau400 Spiele:** `performance_plan`/`validate_plan` (compare221–242) erzwingen vier finale Rollen, acht Paneljobs à40 auf9930000–9930019 und zwei Sampled-gegen-passenden-Control-Direktjobs à40 auf9930100–9930119. Beide Seiten sind über die vollständigen Schlüssel vorgeschrieben. Planvergleich verwirft zusätzliche Jobs, Overrides, falsche Pfade, Karten oder Zählwerte. Keine V14-Rolle, Zwischenstände oder zusätzliche Leistungsphase.
2. **Identische Inferenzconfig:** `validate_copy`/`build_inference_copies`/`validate_admission` (compare149–216) erhalten sämtliche Nicht-Config-Daten über den typisierten Identitätshash, verlangen Einzelnetze und finale Zähler und setzen ausschließlich die gebundene V14-Quellconfig mit `frozen=False`. Die ursprünglichen Trainingsdateien werden nur gelesen. Direkte `self:`-Pfade sind fest auf die separaten Control-Inferenzkopien gelegt; der ausgeführte Befehl erlaubt keine einseitigen `--set`-Overrides. Der vorbereitete synthetische Test prüft die tatsächlichen Wege über `par_eval.build_cfg`/produktiven `Agent_x` und `common.make_opponent('self',...)`. Die gelesenen produktiven Ladewege passen hierzu; der Test wurde nicht ausgeführt.
3. **Historische Trainingsabnahme:** `historical_acceptance` (compare43–147) bindet Root-PIN, alte Quelle/HEAD, vier finale Receipts,800 Ausführungen/96.000 Updates, vollständige Artefaktinventur, beide Vorlaufgates, Originalvalidator- und unabhängige Abnahme sowie beendete Worker/Wachhalter. Die ursprünglichen Validatoren werden unter dem späteren HEAD nicht erneut als zeitgenössischer Trainingsbeleg ausgegeben. Sechs feste Seedlisten und nichtleere Auditgrenzen bleiben erhalten. `ACCEPTANCE_SHA256=None` sperrt bewusst die noch nicht mögliche Aufnahme; das ist kein Defekt und kein erfundener zukünftiger PASS.
4. **Feste Statistik:** Vollständige Matrizen werden vor Berechnung geprüft. Beide Panelgewinne müssen positiv, ihre Summe mindestens16 Halb-Siege sein; Direktwerte je mindestens40 und zusammen strikt über80. Remis zählen einen Halb-Sieg, strikte Siege separat. Die wiederverwendeten Helfer ziehen5000 ganze Kartencluster mit PCG64/Seed0 und95%-Perzentilen. Das Mittel über Starts mittelt zuerst dieselben Karten über beide Starts und Panelgegner, bevor es Karten zieht. Die Interpretation nennt20 Kartencluster, zwei feste Starts, keine Trainingspopulations- oder Promotionsaussage. Die Texttests umfassen die exakten16/15- und81/80-Grenzen sowie unvollständige/falsche Matrizen.
5. **Originaldaten und Betrieb:** Der lokale CSV-Adapter nutzt den bestehenden strikten Reader einschließlich Ergebnis-/Punktkonsistenz. `analyze` verlangt alle zehn Original-CSVs und Receipts, vollständige Schlüssel, Quell-/Input-/Modell-/Befehlsbindungen und geschlossenen400-Spiel-Endstand, bevor es aggregiert. Der bestehende Owned-Queue-/Cleanup-Pfad wird mit zwei im `finally` zurückgesetzten Controllercallbacks verwendet. Quellenfreeze, frisches Kontingent, AC, Fremdprozessprüfung, zwei Worker, Threads1 und exklusive Startreservierung bleiben angebunden. Kein Resume, automatischer Retry oder Folgeversuch.

**Noch ausstehend, kein Befund gegen den Entwurf:** tatsächliche gezielte Tests am sicheren Phasenübergang, abgeschlossene und unabhängig akzeptierte Trainingsdaten, daraus gebildeter echter Root-Hashanker sowie spätere Leistungsaufnahme. Insbesondere werden weder die geplanten Loader-Tests noch die zukünftigen400 Spiele hier als ausgeführt oder bestanden bezeichnet. Keine zusätzlichen Änderungen oder Erweiterungen aus diesem Review empfohlen.
