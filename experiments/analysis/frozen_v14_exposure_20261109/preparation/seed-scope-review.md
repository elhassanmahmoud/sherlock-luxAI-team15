# Frozen-V14-Exposure Seedscan: geprüfter Scope und Treffer

Einmaliger gezielter Metadaten-/CSV-/Textscan, 2026-11-09 20:11:47.794081–20:12:14.655151 UTC (26.92 s). Kein weiterer Scan. Zielbereiche inklusiv:

- solution: 10010000–10010019
- direct_v14: 10010100–10010119
- direct_behavior: 10010200–10010219

Genau diese Spec- und Planpfade waren als aktuelle Reservierungsnennung allowlisted: `docs/superpowers/specs/2026-11-09-frozen-v14-exposure.md` und `docs/superpowers/plans/2026-11-09-frozen-v14-exposure.md`. Die einzige Texttrefferzeile war Spec, Zeile 27, mit genau diesen drei reservierten Kartenbereichen. Der Plan enthielt keine zusätzlichen Zielkarten-Erwähnungen.

**Rohverdikt:** `NO_OBSERVED_OTHER_CONSUMPTION_OR_RESERVATION_WITH_REPORTED_LIMITS`.

Weitere Treffer offen ausgewiesen: vier JSON-String-Substringmeldungen, alle als `non_seed_hash_substring` klassifiziert. Sie stammen aus demselben vollständigen 64-stelligen Digest `3951a5b6b9691d8b60db05576b10010109f66d97b5599dc12c2bd4ab60ff091b`, der im Feld `step_digests[87]` in drei Summary-Dateien vorkommt; in `summary.json` erscheint er zweimal (`runs[0]`/`runs[1]`). Das scheinbare Ziel `10010109` liegt innerhalb des Hashstrings. Der Treffer ist damit als Hash-Substring dokumentiert, nicht als Seedfeld/Seedverbrauch. Dateipfade stehen vollständig im `seed-audit.json`.

Keine CSV-Verbrauchsüberschneidung, JSON-Zahlennennung, JSON-Intervallüberschneidung oder nicht erlaubte Textnennung. Keine Parse-/Textfehler, Dekodierlücken, Dateimutationen oder HEAD-Änderung während des Scans. Acht registrierte Worktrees untersucht; deren vollständige HEADs vor/nach dem Scan sind im Rohbericht. Root- und Desktop-Hauptkopie standen auf `a87a2c14d2a3675fd567c22d43b9d328d5deb0f8`. Das ist nur die beobachtete Scanrevision, kein Freezeversprechen.

Geltungsgrenzen: 15.235 strukturierte CSV/JSON-Dateipfade (1.934.340.973 gespeicherte Bytes) und 9.937 Textdateipfade. 288 eindeutige CSVs ohne Seedspalte (5.061 Zeilen), 2.691 ungültige oder nichtnumerische Seedfeldwerte sowie rohe JSONL-Traces/Provenienz wurden nicht als Seedverbrauch verifiziert; keine Behauptung über unregistrierte Rechner, undokumentierte Läufe, opaque Formate oder berechnete Seeds. Bekannte Trainingskarten sind nicht Zielbereiche und erhalten keine Frischebehauptung.

**Berichtsvorlagenhinweis:** Das vom unverändert übernommenen Scanner automatisch erzeugte `seed-audit.md` enthält statischen Ensemble-Behavior-Titel-/Scope-/Allowlisttext aus der vorherigen Nutzung. Diese statische Prosa stimmt nicht mit dem neuen Scanprofil überein. Maßgeblich für diesen Lauf sind `ranges_inclusive`, `allowed_current_relative_paths`, `text_hits`, `heads_before/after` und die vollständigen Funde/Lücken in `seed-audit.json` sowie diese Scope-Prüfung. Das Rohartefakt bleibt unverändert erhalten.

## Herkunft und Prüfsummen

- Basis-Scanner: `/private/tmp/ensemble-behavior-seeds/seed-audit.py`, SHA-256 `a03e8d991eaaab2cd7790f02506e2e8f636545ce6d8f283705eb34fa0b48b634`.
- Ausgeführter Scanner: `seed-audit.py`, SHA-256 `149343081d4cfc9df8054672410dbe70c9f528301802f4065e680eb0338e470c`; Diff enthält ausschließlich Zielranges und aktuelle Allowlist.
- Spec SHA-256 `e3e04c493962626fb7c18143d3e08843cb0c1696153b96e90609423c6ba5c4a0`.
- Plan SHA-256 `35a7e12556d86a707ff460667824443ddb612a0dbfcadce58ec3465cf477f171`.
