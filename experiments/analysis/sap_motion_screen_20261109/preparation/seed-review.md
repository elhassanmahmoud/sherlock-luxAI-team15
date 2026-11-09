# Enger Kartencheck für das SAP-Bewegungsmodell

**Keine beobachtete frühere Nutzung oder Reservierung im geprüften Umfang.** Keine absolute Frischebehauptung und keine Spielstartfreigabe. Panel **9942000–9942019**, Direkt **9942100–9942119**, insgesamt 40 verschiedene Karten.

Das vorhandene Werkzeug `experiments/analysis/sap_leading_screen_20261109/preparation/seed-audit.py.txt` wurde ausschließlich außerhalb des Repositories kopiert. **Einzige Änderung: `RANGES`.** Bytevergleich nach Rücktausch bestätigt. Daher bleiben der historische `profile`-Text und die Überschrift „SAP-leading“ im automatisch erzeugten Rohbericht unverändert; maßgeblich sind dessen korrekt geänderte `ranges_inclusive` und diese auf das Bewegungsmodell bezogene Einordnung. Keine neue Prüfinfrastruktur.

Tatsächlich einmal ausgeführt: `python3 -B /tmp/sap-motion-seeds/seed-audit.py --targeted-readonly-scan`, Exit 0, **20,56 Sekunden**; 09.11.2026, 11:30:30–11:30:50 UTC. Acht registrierte Arbeitskopien, 14.585 strukturierte JSON-/CSV-Pfade einschließlich gzip und 9.210 Textpfade. Nach exakter Byte-Deduplizierung 1.540 JSON-, 1.695 CSV- und 1.856 Textinhalte; 1.647.885 CSV-Zeilen, 1.643.224 numerische CSV-Seedwerte, 117.942 JSON-Seedwerte und 720 konservative Intervallkandidaten.

**Null** CSV-Nutzungsüberschneidungen, JSON-Zahlen-/Intervall-/Stringtreffer und Textnennungen; keine SHA-Zahlenstrings als vermeintliche Kartennutzung. Auch aktuelle eigene Plan-/Runnernennungen wurden in dieser erfassten Stichprobe nicht gefunden. Solche zukünftigen neuen Planungsnennungen würden gesondert als aktuelle Planung eingeordnet, nicht als historische Nutzung. **Null** strukturierte/Textfehler, Textdekodierlücken und beobachtete Mutationen. Rohverdikt: `NO_OBSERVED_OTHER_CONSUMPTION_OR_RESERVATION_WITH_REPORTED_LIMITS`.

Studien- und primäre Arbeitskopie standen zu Anfang und Ende auf `97d04c20caf6cbc3374329b0c84393e81734a9ab`; sämtliche acht HEADs blieben gleich und stehen vollständig in `seed-audit.json`. Das Werkzeug behauptet trotzdem keinen lückenlosen Freeze: die Textpfadliste wird am Ende nicht komplett neu inventarisiert, sodass erst danach angelegte Dateien nicht ausgeschlossen sind.

Grenzen: 286 eindeutige CSVs ohne Seedspalte (4.661 Zeilen), 1.605 heuristisch ungültige Seedfelder ausschließlich in JSON, null ungültige CSV-Seedwerte. **1.480 Roh-JSONL-Pfade wurden bewusst nicht gelesen**; ebenso keine Tensorarchive. Externe/unregistrierte Arbeitskopien, undokumentierte oder seedlose Spiele, ausschließlich in JSONL belegte Historie, berechnete Zahlenformeln und nicht unterstützte Formate bleiben unbekannt. Keine Projektimporte, Tests, Modelle oder Spiele; keine Repoänderung.

| Beleg | SHA-256 |
|---|---|
| Unverändertes Ausgangswerkzeug | `fbff0c9963d71f2e09c4002d6fc5579b16eb3a03a6c9fb8d6950a9bbc5da96e1` |
| `/tmp/sap-motion-seeds/seed-audit.py` | `d01a8c27451e09dffcf6d15b766a4ef94416589497914aa140f118138b139329` |
| `/tmp/sap-motion-seeds/seed-audit.json` (17.509.112 Bytes) | `de914ac891136886f83ded7a3e41ee4f90ee5ba5eb0735566cdf23261d1f052b` |

Die vorgeschlagenen Bereiche müssen aufgrund dieser lokalen Evidenz nicht geändert werden. Die Entscheidung über ihre konkrete Aufnahme bleibt bei Root.
