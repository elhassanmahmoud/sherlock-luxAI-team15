# Abgeschlossenes gepaartes Rettungstraining

03.11.2026, tatsächlich beendet und unabhängig akzeptiert. **Noch kein Stärkenvergleich oder Abgabeersatz.** [Enddatenreview](training_final_review.md), [maschinelle Prüfung](training_final_audit.json), [Vorabplan](../../../../docs/superpowers/plans/2026-11-03-final-battle.md).

`training_evidence_and_final_weights.tar.gz` enthält 34 unveränderte Dateien unter ihren ursprünglichen relativen Repository-Pfaden: beide festen Endgewichte, CSV-/JSONL-Rohdaten, vollständige Lern-/Aktions-/Validierungsnachweise, vorbereitete Startgewichte und Manifeste, Supervisorzustand/Logs sowie das Kandidatenmanifest. Größe 10.968.693 Bytes; SHA-256 `e583a413f330999909dc02ee028af9b3e38c4e0b09333ff3eaa05624ad010ad8`. Die [Dateiliste](archive_manifest.json) enthält Größe und SHA jeder Datei; Root hat sämtliche Inhalte im fertigen Archiv erneut gegen diese Werte geprüft.

In ein **neues, leeres Verzeichnis** entpacken, um keine bestehenden Läufe zu überschreiben. Provenienzdateien unverändert lassen: absolute Pfade und Interpreter-/Quellenpins beschreiben die tatsächliche Ausführungsmaschine und den eingefrorenen Commit `7c906e16943ff7217afe1eae392834439cc76634`. Eine fremde Maschine oder ein späterer HEAD erfüllt diese Pins nicht automatisch. Die ursprüngliche Arbeitskopie bleibt für diese Abnahme erhalten.

Ausgelassen sind die großen Replay-Puffer und die nicht ausgewählten besten Zwischencheckpoints; beide bleiben in den originalen lokalen Runverzeichnissen erhalten. Die sechs fertig gebauten Kandidatendateien liegen lokal unter `experiments/ensembles/final_battle_20261103/`; ihre Herkunft und Hashes stehen im enthaltenen Manifest. Das Archiv enthält die zwei neu trainierten Einzelnetze, **keine freigegebene neue Abgabe**. Der Trainingskontrollkandidat C36 ist nicht nominierbar.

Alle 2.832 Trainings-/Validierungsausführungen sind vollständig; die bekannten Zwischenvalidierungen sind keine frischen Leistungsnachweise. Die zwei technischen Vorabspiele liegen separat in `../training_start/`. Nächster Schritt ist die vorab festgelegte Leistungsauswahl auf unbenutzten Karten.
