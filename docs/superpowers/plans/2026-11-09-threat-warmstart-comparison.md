# Vergleich der finalen Gefahrmerkmalsnetze

Stand 09.11.2026. Fortsetzung des autorisierten autonomen Verbesserungsauftrags. Beide Lernarme sind vollständig abgenommen; maßgeblich ist `experiments/analysis/threat_warmstart_20261109/operations/closure.json`. Kein Training wiederholen. Akku ist ausdrücklich erlaubt. Eine höhere Spielstärke ist noch nicht belegt.

## Feste Kandidaten

Nur die beiden Endmodelle verwenden: Kontrolle SHA-256 `bcb00242b1b73429c72deb556e5a74fb3386aab288bea02f21f538398af34994`, Gefahrmerkmale `2acf88f8dedbb1eb060ff4ebc3a4b365dc022ef2d0bb8ecf41dfe60883819c93`. Neues 101er-Hauptnetz ersetzt genau V14-Mitglied 18 (nullbasierter Gesamtindex; bisher Ensemble-Eintrag 17). Danach ursprüngliche Mitglieder 0–17 und 19–35 in gleicher Reihenfolge beider Varianten. Genau 36 Mitglieder, keine 37 und keine Auswahl anderer Endstände.

Inferenzkonfiguration aus V14, nur `threat_feats=True` und `frozen=False` zur Fehlertransparenz. Keine Lernkonfiguration übernehmen. V14-Evalkopie nur `frozen=False`; beide Rollen direkter Duelle verwenden ihre gebundene Konfiguration. Strenge Tensor-, Dimensions-, Konfigurations- und Loaderprüfung. Reihenfolge und 101er-GEMM können Rundungsunterschiede gegenüber V14 verursachen; die gleich aufgebaute Kontrolle dient der Abgrenzung.

## Technische Prüfung vor Leistungsspielen

Die Kontrolle wurde mit Nullsuffix trainiert. Der vorhandene Standardloader darf für ihre Auswertung nur nach tatsächlichem Gleichheitsnachweis verwendet werden: sämtliche neuen Kontrollspalten exakt null; auf den ersten 16 exponierten, endlichen Folgezuständen des gebundenen Threat-Vorlaufreplays einschließlich zugehöriger Folgemasken identische Outputs aller 36 Netze, Mittelwerte und legale Argmaxe mit echten versus genullten Zusatzmerkmalen. Gleiche 101er-Formen und Batchgrößen 1, 8 und 16. Dieser begrenzte Rechentest ist keine allgemeine Leistungsaussage.

Zusätzlich genau vier bekannte technische Ausführungen: finale Kontrolle mit Standardloader und mit bestehendem `ThreatAgent(role=control)`, jeweils 831006/player_1 und 831000/player_0 gegen Solution. Native Aktionen, öffentliche Verläufe, sämtliche Matchpunkte nach v2 und Resultate müssen exakt übereinstimmen. Eine Umgebung pro Worker wiederverwenden und schließen. Keine Gradienten. Bei Widerspruch anhalten, keine automatische Wiederholung oder Ersatzmethode. Der Standardloader ersetzt den ursprünglich geplanten Nulladapter erst nach bestandener tatsächlicher Prüfung.

## Einmaliger Screen: 200 Spiele

Drei feste, disjunkte Bereiche vor Start auf beobachtete frühere Nutzung prüfen; Grenzen des lokalen Audits offenlegen. Keine Karten vorab simulieren. Jeweils 20 Karten, beide Seiten:

| Block | Karten | Spiele |
|---|---|---:|
| V14 gegen Solution | 9946000–9946019 | 40 |
| Kontrolle gegen Solution | dieselben | 40 |
| Gefahrmerkmale gegen Solution | dieselben | 40 |
| Gefahrmerkmale direkt gegen V14 | 9946100–9946119 | 40 |
| Gefahrmerkmale direkt gegen Kontrolle | 9946200–9946219 | 40 |

Vorab festgelegte Nominierung: tatsächliche Siege gegen Solution mindestens so viele wie beide Referenzen; in **beiden** Direktblöcken mindestens 24 tatsächliche Siege von 40. Remis zählen dabei nicht als Sieg. Zusätzlich W/D/L und deskriptive 95%-Bootstrapintervalle mit 5000 Ziehungen ganzer Karten einschließlich beider Seiten, NumPy PCG64-Seed 0. Für diese Intervalle gilt der übliche Halbpunkt-Score bei Remis; vom Sieg-Gate unterscheiden. Wiederholte Projektversuche und eine einzelne Trainingsinitialisierung begrenzen die Aussage; keine Korrektur für Mehrfachauswahl behaupten.

Ein positiver Screen nominiert nur für eine separat vor neuen Daten festgelegte frische Bestätigung einschließlich Robustheit und Kursprüfung. Keine Übernahme aus diesem Screen. Bei negativem oder unklarem Ergebnis keine Zusatzspiele bis zum gewünschten Resultat, kein Nachrücken. Ein erfolgloser Austausch eines von 36 Mitgliedern widerlegt nicht pauschal alle Gefahrmerkmale.

## Umsetzung und Ausführung

Drei eng begrenzte Dateien: `scripts/threat_warmstart_compare.py`, `scripts/threat_warmstart_compare_owner.py`, `tests/test_threat_warmstart_compare.py`. Vorhandene Spielschleife, `par_eval`, Quellen-/Prozess-/Quota-Hilfen und Statistik verwenden. Synthetische Tests und unabhängiger Review vor echten Modellen. Root prüft finale Bytes und Belege; danach eigene Quellenaufnahme.

Trainingabschluss wird als historische, gehashte Datenbasis geprüft; das alte `admission()` darf nicht gegen den neuen HEAD ausgeführt werden. Neue Vergleichsquelle separat binden. Technikaufnahme und spätere Performanceaufnahme sind getrennt; kein automatischer Phasenwechsel. Technische Root-Abnahme bindet PASS, Profil, neue Quelle und Receipt-Hash. Performanceaufnahme bindet diese Abnahme, alle drei Modelle, feste Kohorten und Kartenprüfung.

Fünf vorhandene `par_eval --workers 1`-Jobs in Wellen 2/2/1; maximal zwei tatsächliche Modellworker, keine parallelen Tests. Quelle/HEAD/Gewichte bis Abschluss unverändert. Echte frische Quota, bei tatsächlichen 100 % kontrolliert stoppen; kein Reset. Kein automatischer Neustart oder Ersatzspiel. Unterbrochene Spielzahlen nur soweit tatsächlich nachvollziehbar berichten; CSVs erscheinen erst nach einem ganzen Job.

Abschluss: alle fünf CSVs auf 40 eindeutige Spiele, beide Seiten, 303 Schritte, v2-Punkte und konsistente Resultate prüfen; originale Analyse und unabhängige Ergebnisnachrechnung. V14-Dateien und ZIP gehasht erhalten. Erst nach abgeschlossener Abnahme Quellen freigeben, Ergebnis dokumentieren und sinnvoll committen/pushen; primäre Arbeitskopie verlustfrei aktualisieren. Neue Mahmoud-Commits nur am sicheren Übergang integrieren.
