# Unabhängige Prüfung der vier tatsächlichen Technikspiele

**PASS, kein Datenblocker.** 09.11.2026. Einmalige gezielte Standardbibliotheksauswertung: Exit 0, 13.212 erfolgreiche Prüfungen. Keine Projekt-/Torchimporte, Modelle, Forwards, Tests oder neuen Spiele. Quelle `4b11f8a5ec61c63756bdab00748dd6779a2f2e61`.

| Modus | Karte/Seite | Frames | Tatsächliche Offsetwechsel | Befund |
|---|---|---:|---:|---|
| OFF | 831006/player_1 | 303 | 0 | Alle 303 nativen Arrays, gespeicherter gemeinsamer Aktionshash und vollständige historische Match-/Punktedaten identisch |
| OFF | 831000/player_0 | 303 | 0 | Derselbe vollständige historische Abgleich bestanden |
| ON | 831006/player_1 | 303 | 36 | Jeder Wechsel unabhängig aus öffentlicher Vorgeschichte, Geometrie und Posterior rekonstruiert |
| ON | 831000/player_0 | 303 | 0 | Null-Eingriffsschritte und unveränderte Buchhaltung bestätigt |

Alle 1.212 Frames in richtiger Reihenfolge, je drei Matchresetframes, maximal ein SAP-Offsetwechsel je Schritt und unveränderte übrige Zeilen/Aktionsklassen. Die ausgewählte UID ist jeweils die kleinste geeignete; native Spiegelung und Sicht-/Passierbarkeits-/Energie-/Reichweitenbedingungen passen. Posterior unabhängig aus gespeicherten Loggewichten berechnet; kleinste Konfidenz eines tatsächlichen Eingriffs 0,9762045807300296, somit oberhalb 0,9. Hitanzahl, `sap_hits_est`-Delta, Unknown-Entfernung sowie unveränderte Pending-/Feature-/Maskenfelder exakt geprüft. Die gespeicherten Änderungs-, SAP-, Eligibility- und Reset-Summen passen.

Vollständiger Owner-State mit Exit 0 und leerem `active`, tatsächlicher Workerbefehl, Aufnahme-/Receiptkette, identische Quelle/Config, alle fünf Rohdateihashes und vier Rohzeilen geprüft. Gebundene Quellen-, Input- und Schutzdateibytes ebenfalls abgeglichen. Technikaufnahme enthält ausdrücklich die erlaubte Akkunutzung. State-SHA vor und nach der Auswertung unverändert.

Maschinenlesbarer Bericht: `/tmp/sap-leading-technical-data-review.json`, SHA `a9a521f47ab09b355b6ccf4c4e77310c6fb987e25ddee174d6077825434a8bc5`. Eingangskette: Aufnahme `c6e9200884fde974a0e2224c0eb63bd51919fab3c1aae02c7f6603ef6af2189e`, State `bffb7b4b540d45677322ffb06061632e2dd76fd021030f2b567fc30d38136266`, Receipt `1ca7424208e4162074ec632066c24b04e143f59ecb1985d456417c4d13f4a8e8`. Enges Nachrechnungsprogramm: `/tmp/sap-leading-technical-data-check.py`.

Grenzen: Der gemeinsame Aktionshash wird gegen den historischen Beleg verglichen; gegnerische Rohaktionen liegen hier nicht separat vor, daher keine unabhängige Neuberechnung dieses kombinierten Hashes. Die Gleichheit von originalem Remember und eingereichtem Befehl sowie genau ein Core-Aufruf sind erfolgreiche Laufassertionen des gebundenen Workers. Erinnerte Arrays/Aufrufzahlen sind nicht gesondert archiviert und wurden hier deshalb nicht nachträglich unabhängig gemessen. Kein Engine-Replay oder neuer Forward. Bekannte technische Karten belegen keine allgemeine Stärke, Kausalwirkung oder Übernahme; die separaten Leistungsdaten sind nicht Gegenstand dieses Checks.
