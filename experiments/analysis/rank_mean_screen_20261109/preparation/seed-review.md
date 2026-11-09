# Begrenzter Kartencheck: legales Rangmittel

**Keine beobachtete frühere Nutzung oder fremde Reservierung der 40 vorgesehenen Karten.** Zwei Texttreffer sind die eigene aktuelle Reservierung des vorab festgelegten Plans; keine historische Spielnutzung. Keine absolute Frischebehauptung oder Spielstartfreigabe.

Panel **9944000–9944019**, Direkt **9944100–9944119**. Vorhandenes `/tmp/sap-motion-seeds/seed-audit.py` ausschließlich extern kopiert und **nur `RANGES` geändert**; exakter Rücktausch reproduziert die Ausgangsbytes. Automatischer historischer Profilname/Überschrift „SAP-leading“ bleiben deshalb absichtlich unverändert; die neuen `ranges_inclusive` sind korrekt. Kein neuer Scanner.

Einmaliger tatsächlicher Aufruf: `python3 -B /tmp/rank-mean-seeds/seed-audit.py --targeted-readonly-scan`, Exit 0, **21,13 Sekunden**, 09.11.2026 11:56:05–11:56:26 UTC. Acht registrierte Arbeitskopien; **14.631 JSON-/CSV-Pfade** inklusive gzip, **9.261 Textpfade**. Nach Byte-Deduplizierung 1.563 JSON-, 1.695 CSV- und 1.880 Textinhalte. 1.647.885 CSV-Zeilen, 1.643.224 numerische CSV-Seedwerte, 118.084 JSON-Seedwerte und 722 konservative Intervallkandidaten.

Null CSV-Nutzungsüberschneidungen, JSON-Zahlen-/Intervall-/Stringtreffer; null Lesefehler, Dekodierlücken oder beobachtete Mutationen. **Zwei Texttreffer**, daher bleibt das rohe Werkzeugverdikt unverändert `REVIEW_REQUIRED`. Die gezielte Einordnung löst diese beiden Treffer:

| Treffer | Einordnung |
|---|---|
| `docs/ARBEITSSTAND.md:15` | Eigener neuer Planungs-/Übergabeeintrag: Bereiche vor Start prüfen, ausdrücklich noch keine Spiele/Leistungsresultate. Zeile aus Commit `a917af1`. |
| `docs/superpowers/plans/2026-11-09-rank-aggregation.md:46` | Eigene beabsichtigte Kartenreservierung für den exakt begrenzten neuen Vergleich; keine frühere Nutzung. Zeile aus Commit `a917af1`. |

Die Treffer stammen nach exakter Text-Deduplizierung aus der primären Arbeitskopie. Ihre Dateien sind bytegleich zu den entsprechenden Studienkopien: Arbeitsstand SHA `afe0e28eed0e6b283b088a3611a2893d51a8f4e8ed8b663055c85525ad1619dc`, Plan SHA `681e46b5277fc9b4b73cbb70546e88c2d88e046bff5ac911b53f6dc2a1d1f1e0`. Beide Hauptcheckouts standen vor/nach dem Scan auf **`a917af127f0532336305b7b6d6e892d21df16dec`**; alle acht HEADs unverändert, vollständig im Rohbericht. Kein erneuter Scan nach dieser konkreten Trefferprüfung.

Grenzen unverändert: 286 eindeutige CSVs ohne Seedspalte/4.661 Zeilen; 1.735 heuristisch ungültige Seedfelder ausschließlich in JSON, null ungültige CSV-Seedwerte. **1.736 Roh-JSONL-Pfade bewusst ausgeschlossen**, keine Tensorarchive gelesen. Externe/unregistrierte Arbeitskopien, undokumentierte/seedlose oder ausschließlich in JSONL belegte Historie und berechnete Seedformeln bleiben unbekannt. Die Textpfadliste wird am Ende nicht neu inventarisiert; später neu entstandene Dateien sind nicht ausgeschlossen. Kein lückenloser Freeze behauptet. Keine Projektimporte, Tests, Modelle, Spiele oder Repoänderungen.

| Beleg | SHA-256 |
|---|---|
| Ausgangs-Seedskript | `d01a8c27451e09dffcf6d15b766a4ef94416589497914aa140f118138b139329` |
| `/tmp/rank-mean-seeds/seed-audit.py` | `9374cd84578c9c9704e6415a98b5c9cf794a28740297cc1d83319df57eababfe` |
| `/tmp/rank-mean-seeds/seed-audit.json`, 17.666.328 Bytes | `946047803b31c74b6dd52f7264039cf56483be724fe822294b0bb1f6b4e086ed` |

Die lokale Evidenz erfordert keine Änderung der vorgesehenen Bereiche. Das unveränderte Rohverdikt und diese begrenzte manuelle Einordnung gemeinsam archivieren.
