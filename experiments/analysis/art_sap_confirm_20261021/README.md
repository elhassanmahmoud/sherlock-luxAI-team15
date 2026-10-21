# Artillerie-Kandidat: keine Freigabe nach frischer Bestätigung

**21.10.2026.** Der feste Vergleich ist vollständig: **2.208 neue Spiele**. Der Kandidat gewinnt auf 200 neuen Karten gegen Solution_92 **301/400**, V3 **292/400**. Der Unterschied beträgt **+2,25 Prozentpunkte**, das gepaarte 95%-Kartenintervall **[−0,25; +4,75] Prozentpunkte**. Die vorher festgelegten Bedingungen von mindestens +5 Prozentpunkten und einer strikt positiven unteren Intervallgrenze sind beide verfehlt. **V3 bleibt Abgabe.**

## Unveränderter Kandidat und Herkunft

Mahmouds bereits auf bekannten Karten ausgewählte Artillerie-Regel wird einmalig unabhängig geprüft. Der [Vorabplan](../../../docs/superpowers/plans/2026-10-21-art-sap-confirmation.md) wurde vor den eigenen Spielen veröffentlicht. Sieben frühere Regelvarianten machen deren Ergebnisse zu Auswahldaten; die günstige bekannte Siegquote ist kein Generalisierungsnachweis.

Der Kandidat [`v3_art3_20261021.pth`](../../candidates/v3_art3_20261021.pth) ist eine Kopie von V3 mit ausschließlich `art_sap=True` und `art_min_hits=3` in der gespeicherten Konfiguration. Effektiv gelten außerdem `art_reserve=0`, `art_safe=True`; `siege`, `threat_feats` und `joint_moves` sind aus. Alle 18 gelernten Netze, Target-/Optimizerdaten und sonstigen Checkpointfelder bleiben unverändert. Root prüfte die rekursive Gleichheit vor und nach Serialisierung und die tatsächliche Ladung aller 18 Netze. Ein unabhängiger Bytevergleich bestätigt 264 identische Tensor-Speicherblöcke; dieser Vergleich allein ist kein unabhängiger Modellladetest.

- Kandidat: `e392f20c60d51817591ee4c0061bc8150e7ec8aa312b42e704004538ead45497`.
- V3, beide Abgabedateien: `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`.
- Alte Sechser-Sicherung: `3788fb721d1873b74ec666df34da92eb6af311eed1d8fff6e03b71e59346d158`.
- Ausgeführter Quellstand: `9c1efc7fe4e09e1738ff489292786fa535670174` im Zweig `improvement/v4-joint-20261021`.
- Eingefrorene Inventare: 83 Quell-/Runtime-/Hilfsdateien, fünf Eingaben und acht getrennte geschützte Gewichtsdateien in Haupt- und Arbeitskopie. Alle Hashes bei Abschluss erneut geprüft.

Die Artillerie-Regel nutzt nur erlaubte Beobachtungen. Ihre Manhattan-Sicherheitsannahme bezieht sich auf Solution_92 und schützt nicht allgemein vor Splash-Schaden oder zukünftigen Bewegungen. Der historische Trefferzähler zählt auch sichtbare Gegner mit negativer Energie. Diese bekannte Einschränkung wurde für den reproduzierten Kandidaten nicht still geändert.

## Tatsächliche Spiele und Ergebnisse

| Stufe | Karten und Gegner | Neue Spiele | Ergebnis |
|---|---|---:|---|
| Reproduktion V3 | 500720–500779, beide Seiten, default + Solution | 240 | default 120/120; Solution 102/120 |
| Reproduktion Art3 | identische Karten/Seiten/Gegner | 240 | default 120/120; Solution 108/120 |
| Direkte Entwicklung | 500720–500779, beide Seiten gegen V3 | 120 | 80 Siege, 0 Remis, 40 Niederlagen |
| Kursprüfung Art3 | 500720/500721, beide Seiten, beide Gegner | 8 | alle technischen Pflichtprüfungen bestanden |
| Frische Referenz V3 | 523000–523199, beide Seiten, beide Gegner | 800 | default 399/400; Solution 292/400 |
| Frischer Kandidat Art3 | identische frische Karten/Seiten/Gegner | 800 | default 399/400; Solution 301/400 |
| **Summe** | sechs abgeschlossene Jobs | **2.208** | kein Training in dieser Studie |

In sämtlichen oben angegebenen Vergleichsspielen gibt es keine Remis. Die 480 Reproduktionsspiele stimmen in allen 23 Nichtzeitfeldern mit den historischen V3-/Art3-Referenzen überein. Entwicklung: Solution Δ +5 Prozentpunkte, Kartenintervall [+0,833; +10]; direktes mittleres Resultat 66,67 %, Intervall [58,33; 75] %. Diese Entwicklungsgates erlaubten die frische Prüfung, keine Gewichtsübernahme.

| Frisches Gate | Messwert | Bestanden? |
|---|---|---|
| Solution: mindestens +5 Prozentpunkte | +2,25 Prozentpunkte | nein |
| Solution: untere 95%-Grenze strikt > 0 | −0,25 Prozentpunkte | nein |
| default: mindestens 99 % | 99,75 % | ja |
| default: höchstens 1 Prozentpunkt schlechter als V3 | 0 Prozentpunkte | ja |
| Direkte frische Überlegenheit | gemäß Vorabplan nicht mehr ausgeführt | nicht geprüft |

Die Statistik resampelt 5.000-mal ganze Karten einschließlich beider Seiten, mit NumPy `default_rng(0)` und den 2,5-/97,5-Perzentilen. Siegquoten gegen feste Gegner zählen nur tatsächliche Siege; ein direktes Remis wäre ein halbes Resultat. Keine Zusammenlegung mit früheren Ergebnissen auf anderen Karten. Der Befund schließt einen kleinen Nutzen nicht aus, liefert aber keinen ausreichenden Nachweis für die geforderte Übernahme.

## Technische Prüfung und Grenzen

Alle Vergleichsdateien besitzen vollständige eindeutige Gegner/Karte/Seite-Schlüssel, 303 Schritte, Punktezählversion 2 und `invalid_frac == 0`. Diese vorhandene Metrik ist keine vollständige Garantie jeder semantischen Spielregel. Der Kursprüfer bestätigt insbesondere tatsächliche Checkpoint-/Configladung, frischen Spielzustand sowie endliche ganzzahlige Aktionen mit korrekter Form. Größte p95-Aktionszeit eines Kursprüfspiels: **2,326 ms**, absolutes Maximum **10,946 ms**; Grenzen waren 50 bzw. 250 ms.

Der Root-Integrationslauf vor dem Einfrieren bestand mit **531 Tests plus 14 Untertests** in 82,52 Sekunden. Elf synthetische Protokolltests bestanden zusätzlich. Während der Spiele wurde kein Quellstand gewechselt, maximal zwei Evaluationsworker liefen zugleich; alle sechs Jobs endeten mit Rückgabecode 0 und leerer eigener Prozessgruppe.

Vor der frischen Stufe wurden 2.109 zugängliche CSV-Dateien mit Seedspalte und 1.485.640 Zeilen auf Überschneidungen geprüft. Die Karten 523000–523199 sind jetzt verbraucht. **523200–523399 wurden nicht gespielt**, ebenso wenig der optionale 100%-Audit. Mahmouds reservierter Bereich 503220–503819 wurde von dieser Studie nicht benutzt. Kein Auffüllen, keine Parameteränderung und kein weiterer Kandidat auf dem frischen Testsatz.

## Nachweise und Wiederholung

- [Ausführungszustand, Befehle, Hashes und Zeiten](execution_state.json)
- [Kandidatenidentität](candidate_identity.json), [separater Identitätsreview](candidate_review.md), [Inventarreview](freeze_review.md)
- [Entwicklungsdatenreview](development_data_review.md), [abschließender unabhängiger Datenreview](final_data_review.md)
- [Entwicklungsauswertung](development_results.json), [Voraussetzungen der frischen Prüfung](pre_fresh_results.json), [frisches Ergebnis](fresh_results.json)
- [Unabhängige Rechnung](independent_results.json), [Root-Nachrechnung](root_reproduction.json), [reproduzierbarer Audit](independent_final_audit.py)
- Rohdaten: `development_v3.csv`, `development_candidate.csv`, `direct_development.csv`, `fresh_v3.csv`, `fresh_candidate.csv`, `course.json`; zugehörige Logs liegen daneben.

Die archivierten Hilfsquellen `*.py.txt` und die absoluten Pfade im Zustandsprotokoll dokumentieren die ursprüngliche Ausführung. Für eine technische Reproduktion den angegebenen Quellcommit und die gebundene Kurs-Runtime verwenden; die späteren Dokumentationscommits sind nicht der eingefrorene Spielstand. Ein erneuter Lauf auf diesen Karten wäre eine Reproduktion auf bekannten Daten, keine neue Bestätigung.

Der Kandidat bleibt ausschließlich ein Experiment. Es wurde keine Abgabedatei ersetzt und kein neues Releasepaket freigegeben.

Der Zustand wurde nach dem unabhängigen Audit und dessen erfolgreicher Root-Wiederholung als `completed_negative` geschlossen. [Originalzustand zum Auditzeitpunkt](execution_state_at_audit.json) erhält dessen dokumentierten Hash; die späteren Abschlussfelder ändern keine eingefrorene Quelle und keine Rohdaten.
