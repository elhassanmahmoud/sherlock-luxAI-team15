# Trainings-Vorlaufabnahme, 01.11.2026

Prüfzeit UTC: 2026-11-01T20:34:43.484148+00:00. Ausschließlich Standardbibliothek (JSON, CSV-Lektüre, SHA-256), keine Torch-Imports, Modelle, Tests oder Spiele. Keine Dateien im Repository verändert. Die beiden Modellworker laufen weiter; dies ist keine Abschlussabnahme und keine Stärkenauswahl.

**Befund: Start-/Parameterkonfiguration konsistent mit dem vorregistrierten Pilot. Kein Vorlaufblocker gefunden.**

- Beide tatsächlichen Run-Manifeste nennen den sauberen Quellstand `390de378c06dbde8bde0e11c68b2ba35b77bda48`, denselben Init-Ordner, Seed 9, Kartenversatz über die verzeichnete Trainingsspanne 294200–294500 (oberes Ende exklusiv), 600 geplante Trainingsspiele, lr=0,0001, 120 Prefillspiele, keinen geladenen alten Buffer, keinen Pool und keine Snapshots.
- In beiden tatsächlichen Manifesten ist der Mix Solution .6 / Quadrat-Solution .2 / default .1 / rush .1. Das historische ungenutzte Feld `sol92_frac=.5` ist bei explizitem `mix` kein tatsächlicher Gegneranteil.
- Validierung: dieselben acht bekannten Karten 500000–500007, alle 300 Spiele, default/Solution, epsilon=0; keine Testkarten; Endstand per `--keep-final`.
- Vollständiger Configvergleich der tatsächlichen Manifeste: **genau ein Unterschied**, `w_discovery=.5` versus `2.0`. `w_explore=.3` in beiden Armen. Beide Configs stimmen exakt mit ihrer jeweiligen Arm-Provenienz und mit der Init-Config plus diesem einen Rewardwert überein. V14-Rescue bleibt gesetzt, die unveränderte Agentenlogik sperrt es weiterhin im Training; `overlap_infer=false`, `frozen=false`, V12-Trainingsregeln aktiv.
- Beide Arm-Provenienzen nennen Komponentenindex 18, frischen Adam (kein Resume), denselben Starttensorhash `3c79c58371bc67badf7962e84276d474bad3bff690d1ad465cb3977a45ddb309` und denselben geschriebenen Init-Checkpoint-Hash `39a1feb9892027cee4240121e4ad5bcf3987005a843973b372c24153e05ed2c4`.
- Aktuell erneut mit SHA-256 geprüft: V14-Quellbytes unverändert `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; Init-Checkpointbytes unverändert `39a1feb9892027cee4240121e4ad5bcf3987005a843973b372c24153e05ed2c4`. Die Vorab-Tensorprüfung in `real-warm-start-check.json` dokumentiert 12 Tensoren, q/target identisch zum genannten Tensorhash, null Ensemble-Extras, null Optimizerzustände, Training aktiv, epsilon≈0,05. Diese Datei wurde jetzt nur gelesen; keine neue Tensorladung während der beiden laufenden Worker.
- Die Logs beider Arme bestätigen abgeschlossenen Prefill mit 120 Spielen und 300000 Transitions. Die Anfangsmanifestangabe `buffer_loaded=0` bezeichnet das Fehlen eines geladenen alten Replay, nicht das Fehlen des neuen Prefills.
- Beim ersten einmaligen CSV-Lesesnapshot lagen in beiden Armen je 150 gespeicherte Trainingszeilen vor. Es wurde kein Zwischenergebnis zur Auswahl oder Änderung benutzt. Die vollständige Zeilen-/Loss-/Val-/Checkpointprüfung erfolgt erst nach dem Supervisorende.

Supervisor/Arm-Provenienzen stehen erwartungsgemäß noch auf `running`. **B/C bleiben bis zur unabhängigen Abschlussprüfung unzugelassen.** Root meldet das Ende; kein aktives Polling durch diesen Reviewer.
