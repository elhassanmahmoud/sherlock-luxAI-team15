# Beobachtung von Zielvergabe und Sap-Geometrie

V3, 20 bekannte Entwicklungskarten 500720–500739, beide Seiten gegen
Solution_92: 40 Spiele mit drei Matches. Messcode `63cb26c`, unveränderte
V3-Gewichte (`aac1c910…d935`). Die zusätzlichen Berechnungen erreichten weder
Aktionsauswahl noch Belief. Sämtliche nichtzeitlichen Spielkennzahlen stimmen
mit den entsprechenden Zeilen von `dev_reference.csv` überein.

| Beobachtung | Anzahl | Spiele betroffen |
|---|---:|---:|
| Unbesetztes eigenes Punktefeld durch negative Einheit reserviert und in Schattenzuweisung an lebende Einheit übergeben | 425 | 38/40 |
| Dabei lebende Einheit höchstens zwei Felder entfernt und mit Bewegungsenergie | 139 | — |
| Schritte mit anderer Zielzuweisung lebender Einheiten | 699 | 40/40 |
| Ausgeführte Sap-Angriffe | 4.807 | — |
| Davon für Geometrievergleich geeignet | 4.168 | — |
| Freies Zentrum mit strikt höherem bestehenden Energiescore | 218 | 32/40 |

Die übrigen 639 Sap-Angriffe wurden wegen sichtbarer Gegner mit negativer
Energie ausgeschlossen. Keine beobachtete `pt_sap`-Stehenbleiben-Gelegenheit
wurde durch einen negativen ersten Besitzer blockiert. Dieser separate
Mechanismus wird daher jetzt nicht geändert.

Beide untersuchten Mechanismen treten wiederholt auf; getrennte Varianten
sind begründet. Die Zählungen belegen weder tatsächlichen Zusatzschaden noch
verlorene Punkte oder mehr Siege. Es handelt sich um wiederholte
Einheiten-/Schrittbeobachtungen, keine unabhängigen Stichproben. Distanz ist
kein garantierter legaler Weg; Sap nutzt sichtbare Energien und die bisherige
angenommene Streuwirkung 0,5. Gegner können sich noch bewegen.

Die Schalter `active_targets` und `sap_geometry` werden einzeln auf denselben
bekannten Entwicklungskarten geprüft; keine ungeprüfte Kombination oder
Änderung der Abgabe. Der Reward-Trainingspilot verwendet beide ausgeschaltet.

Quellen: `target_diagnosis_720_739.json` (Rohdaten), `diagnosis_summary.json`
(reproduzierte Kennzahlen und SHA-256). `tools/README.md` beschreibt die
portablen Beobachtungswerkzeuge. Deren `manifest.json` enthält die Hashes der
damaligen Quelldateien; sie wurden gegen Messcommit `63cb26c` geprüft.
`tools/summarize_diagnosis.py` erzeugt die Zusammenfassung aus Rohdaten und
Referenz erneut, sofern der Ausgabepfad noch nicht existiert.
