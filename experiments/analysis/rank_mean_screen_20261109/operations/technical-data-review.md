# Unabhängiger Rank-Technikdatencheck

**PASS im geprüften Umfang.** Tatsächlich einmal ausgeführt: `python3 -B /tmp/rank-mean-technical-review/check.py`, Exit 0, 93.245 Prüfbedingungen. Ausschließlich Standardbibliothek und bestehende technische Daten; keine Projektimporte, Modelle, Forwards, Tests, Spiele oder Leistungsdaten. Quelle `32772fd971c1e65338b476438deda9f4aac9969b`.

| Modus | Karte / Seite | Frames | Geänderte Vorschlagsschritte / Einheiten | Native Frames abweichend zur Historie |
|---|---|---:|---:|---:|
| OFF | 831006 / player_1 | 303 | 0 / 0 | 0 |
| OFF | 831000 / player_0 | 303 | 0 / 0 | 0 |
| ON | 831006 / player_1 | 303 | 47 / 60 | 199 |
| ON | 831000 / player_0 | 303 | 131 / 186 | 226 |

Alle vier Schlüssel, 4 × 303 fortlaufende Frames und jeweils drei Resetframes bestätigt. In allen 1.200 aktiven Frames sind 36 endliche Mitglieder-Ausgaben, gültige Masken, eindeutige IDs und 79 Merkmale gespeichert. Ganzzahlige Rangzähler unabhängig über alle legalen Aktionen berechnet; gleiche Zähler wählen die kleinste Aktions-ID. Alle gespeicherten ON-Ränge, legalen Greedies sowie Schritt-/Einheiten-/Aufrufzähler stimmen überein. OFF enthält erwartungsgemäß keine Rangdiagnostik; die hypothetischen Ränge wurden nur innerhalb dieses Offlinechecks gerechnet.

OFF: beide 303 nativen Aktionsarrays vollständig identisch mit den alten Traces, gespeicherter gemeinsamer Aktionshash sowie alle Matchpunkte und Spielergebnisse exakt gleich. Match-Siege aller vier Zeilen zusätzlich aus den gespeicherten Punkten nachgerechnet. ON: 47/131 Vorschlagsänderungsschritte und 199/226 gegenüber der alten Trajektorie verschiedene native Frames bestätigt. Diese beiden Maße sind verschieden; spätere Trajektoriendifferenzen belegen keine isolierten gleichen-Zustand-Effekte.

Aufnahme, abgeschlossener Ownerzustand (Exit 0/active leer), Receipt, tatsächlicher Befehlsvektor und Quellenobjekt sind konsistent gebunden. Fünf Rohdateihashes, alle 21 Aufnahmeinputs, drei geschützte Dateien sowie drei relevante Rank-Quelldateien tatsächlich gehasht. Kein erneuter Vollscan des Quelleninventars. Geschlossene Aufnahme-/Receipt-/Rohdateien am Ende unverändert.

Zusatzbeschreibung im selben Datenpass: mittlere legale Q-Spanne pro Mitglied über **6472 OFF-Einheiten-Frames**, jedes gleich gewichtet, Singletonspanne 0. Unter den 36 Mittelwerten: Minimum **2.158375559**, Median **2.468694090**, Maximum **3.037127994**. Alle 36 Werte stehen im JSON. Nur Skalenbeschreibung, kein Dominanz-, Stärkenachweis oder neues Gate.

Grenzen: Q-Werte/Merkmale/Masken sind gespeicherte Laufzeitbeobachtungen, keine unabhängig wiederholten Netzberechnungen. Die gespeicherte ON-`rank_mean` ist die Rekonstruktion des Workers; die tatsächliche Aggregattensor-Gleichheit wurde live geprüft, der separate Tensor ist nicht archiviert. Genau ein Coreaufruf, ein Forward je Mitglied, aktuelle Member-Eingaben und Remember-Gleichheit sind Liveassertionen des erfolgreichen gebundenen Workers; einzelne Aufrufzähler/Eingabetensoren/Remember-Arrays wurden nicht gesondert gespeichert. Der Roh-Q-Mittelwert wird mit einer hochpräzisen Summe numerisch abgeglichen (rtol 1e-5, atol 1e-6); für rohe Beinahegleichstände gilt der gespeicherte tatsächliche Torch-Mittelwert. Der gemeinsame Aktionshash wird gegen die Historie verglichen, mangels roher Gegneraktionen nicht neu erzeugt. Keine Leistungsabnahme, Startfreigabe oder Promotions-/Stärkeaussage.

Prüfbare Belege:

- JSON: `/tmp/rank-mean-technical-review/result.json`, SHA256 `0fee9a1a6b3fd3cae21f1ace72385d56efc3e0df8e8ba2e8b7e9849248eca683`.
- Enger Auditor: `/tmp/rank-mean-technical-review/check.py`, SHA256 `5250d3cc2bff4899b16f648217527555fd80dfe1fca3025585e5cc161e445fa6`.
- Aufnahme: `d9a6fa03a4a75af52205f317c5ba79000c1efdc323ed2823316cfdd54f243ce9`.
- Ownerzustand: `97ef0c2d775b1ca2e1fb80af4df4779a068aa4a7b4b2befea660674e4d909bde`.
- Receipt: `254240aa40262b7bd2565926c1751ec3b2038ed9f94741d43f1f4bbab6d4a0d7`.
- Vollständige tatsächlich nachgehashte Eingabeliste im JSON.
