# Unabhängige Git-Archivprüfung — 03.11.2026

**PASS.** Der vorgemerkte Archivfix stellt die ursprünglichen CSV-Bytes wieder her; Zahlen und eingefrorene Studie bleiben unverändert.

- Alle13 vorgemerkten Auswahl-CSVs sind byteidentisch mit den Originaldateien des eingefrorenen Followup-Auswahllaufs und ihren Manifest-SHA256/Bytezahlen. Gegen Commit6c4f953 gilt für jede Datei exakt: neueBytes.replace(CRLF,LF)=alteBytes. Alte Blobs enthalten keinCR; neue Dateien haben die ursprünglichenCRLF. Insgesamt8800 Datenzeilen plus13 Kopfzeilen, keine andere Byteänderung.
- Die neue Attributdatei liegt ausschließlich unter experiments/analysis/final_battle_20261103/.gitattributes und setzt nur *.csv -text (plus Kommentar). Gitcheck-attr zeigt dort text:unset, außerhalb des Teilbaums weiterhinunspecified. core.autocrlf bleibt globalinput aus ~/.gitconfig; keine globale oder lokale Konfiguration wurde durch diesen Review geändert.
- Der aktuelle von Root genannte Abnahmeumfang ist **45 Dateien aus performance_selection/archive_manifest.json plus6 Dateien aus confirmation_start/manifest.json=51**. Alle51 vorgemerkten Gitblobs stimmen mit SHA256 und Bytezahl der jeweils vorgemerkten Manifeste überein. Die6 Bestätigungs-Startbelege wurden nur als archivierte historische Dateien gehasht; keine laufenden Bestätigungsergebnisse gelesen.
- Zusätzlich wurden die älteren7 Dateien aus selection_start/manifest.json geprüft: ebenfalls7/7 bytegleich. Die zuvor gemeldeten52 bezogen sich auf45+7 und damit einen anderen Umfang, nicht auf einen Fehler in Roots51er-Zählung.
- Einmalige attributgerechte Whitespaceprüfung mit git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --cached --check:exit0. CRLF wird bewusst als Originalbestand erhalten, nicht normalisiert.
- Laufende Studie unangetastet: FollowupHEAD7c906e16943ff7217afe1eae392834439cc76634, Freeze3b3bdbe8…19ae73c, alle246 gefrorenen Quell-/Protokolldateien und13 Modelldatei-Hashes unverändert. Keine Modelle geladen, Spiele/Tests ausgeführt, Quellen/Weights/Pläne verändert oder Commits erstellt.

Roots parallel ergänzte Dokumentation und zwei Diagnose-JSONs wurden als autorisierte zusätzliche Archivdokumentation behandelt. Keine Index-/Dateiänderung durch diesen Reviewer; nur dieser externe Bericht.
