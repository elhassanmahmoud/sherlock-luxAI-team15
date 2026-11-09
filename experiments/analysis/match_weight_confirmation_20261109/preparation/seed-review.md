# Begrenzter Seed-Konfliktcheck: Matchgewicht-Bestätigung

**Rohverdikt: `REVIEW_REQUIRED`.** Einmaliger Scan der exakt 80 vorgesehenen Karten-IDs: Panel `9980000–9980019` (20) und Direkt `9980100–9980159` (60). Scanfenster 2026-11-09T17:42:15.248711+00:00 bis 2026-11-09T17:42:40.415980+00:00 UTC (25.22 Sekunden); Exit 0.

## Methode und Abdeckung

Vorlage: vorhandener `seed-audit.py.txt` unter `experiments/analysis/match_weight_20261109/preparation`, SHA-256 `ecfaf1e859394b0e2e6ee84edb4cdc91c680c9f6470d01ecbc1ec36d727e2c12`. Es wurde eine externe Kopie verwendet; Suchlogik unverändert. Nur die zwei Zielbereiche, die einzelne exakte Allowlist für `docs/superpowers/plans/2026-11-09-match-weight-confirmation.md` sowie Profil-/Zusammenfassungstexte wurden angepasst. Kein breiter Ausnahmefilter. Alle acht registrierten lokalen Worktrees wurden geprüft; HEADs vor und nach Scan sind im Rohbericht identisch. Plan- und Spec-Hashes im Scan und beim anschließenden Leseabgleich blieben identisch.

Der Scan umfasste 15,085 strukturierte Artefaktpfade und 9,717 Textpfade. Er las CSV/JSON sowie `.gz`-Varianten mit Dateihash-Deduplizierung, plus die begrenzte Textsuche des vorhandenen Werkzeugs. Keine Repoimporte, Modelle, Spiele, Tests oder Repoänderungen; nur Ausgabedateien unter diesem `/private/tmp`-Ordner.

## Befund und offener Reviewpunkt

- CSV seed consumption hits: **0**. JSON-Zahlen-/Intervall-/Stringüberschneidungen: **0 / 0 / 0**.
- Zwei Texttreffer: die erlaubte exakte Planreservierung sowie ein nicht allowlistierter Treffer in untracked `scripts/match_weight_confirmation.py:21`: `COHORTS = {'panel':list(range(9980000,9980020)), 'direct':list(range(9980100,9980160))}`. Er bleibt im Rohbericht `requires_review`; ich habe ihn nicht nachträglich allowlistet. Der generische Textbereichs-Parser notiert Endpunkte inklusiv und zeigt daher im Rohbericht 9980000–9980020 sowie 9980100–9980160. Der Quelltext nutzt Python `range(start, stop)` mit exklusivem `stop`, also genau 20 und 60 IDs. Dieser Texttreffer allein belegt keine Spielausführung. Root soll diesen konkreten Implementierungspfad separat adjudizieren.
- Scannerbegrenzer: 288 CSV-Dateien (5,061 Zeilen) ohne Seedspalte; 2,405 heuristisch seedähnliche, nicht numerische JSON-Feldwerte; 2,020 Roh-JSONL-Pfade wurden nicht geparst. Externe/unregistrierte Worktrees, undokumentierte oder ausschließlich JSONL-belegte Nutzung, berechnete Seedformeln, unbekannte Schemas und opaque Binärarchive bleiben außerhalb des Nachweises.
- Scanfehler, Textdekodierfehler und beobachtete Mutationen: **0**. Die fehlende Abdeckung und der eine nicht freigegebene Quelltexttreffer verhindern eine uneingeschränkte Aussage über Konfliktfreiheit.

## Hashes

| Beleg | SHA-256 |
|---|---|
| Ursprüngliche Scanner-Vorlage | `ecfaf1e859394b0e2e6ee84edb4cdc91c680c9f6470d01ecbc1ec36d727e2c12` |
| Adaptierte externe Scan-Kopie | `0a05c8c68d5d1b3092760d77b513d413958333959e7f7f36d4a69e8670d3f8dc` |
| Anpassungsdiff | `e580b261159ec0c5902d8897cbd0d63ce040f585d290af91dc262ef1d85cbb27` |
| Rohbericht `seed-audit.json` | `5aa36aa0cb3ebd0db5679e1fe0c3fac2e4497112af2f11b31b434157dd1df689` |
| Vorheriger Seed-Audit-Archivinput (unverändert) | `d7cd3b599394ddee754e641572ca77a873516aa41e4ce6ca5ba720aa738231f2` |
| Neuer Plan | `3e639507319e0b92acd410645c52f6e95f52a4f1475409aa17b139cbcb32f6d3` |
| Neue Spec | `f44fc48d0c73f5307559d1ec217364f51038e810f9e31504a42c05f5e66ee545` |
| Nicht allowlistierter Code-Treffer bei Scan | `956d26e376b6aa2a1919940f833433c62a537e43d9da4515ffcefac6ccc30694` |

Vollständige Dateiinventare, Hashes, Konflikttreffer, Worktree-HEADs, Schema-Lücken und JSONL-Auslassungsliste sind in `seed-audit.json`; Methoden-/Hashbindungen zusätzlich in `method.json`. Der vorherige komprimierte Rohbericht wurde nicht verändert. Es gab keinen zweiten Scan.
