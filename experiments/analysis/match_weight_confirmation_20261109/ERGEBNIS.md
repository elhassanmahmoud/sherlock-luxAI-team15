# MATCH38: Bestätigung nicht bestanden, V14 bleibt

Der erste 200-Spiel-Screen hatte MATCH38 nominiert. Der einzige vorab festgelegte frische Vergleich mit **440 Spielen** bestätigt jedoch keinen direkten Vorteil gegenüber V14. Beide Direktbedingungen werden verfehlt; die sechs Panelbedingungen bestehen. **V14 und Gruppe15.zip bleiben unverändert.** Kein Nachschlag, keine geänderten Schwellen und keine weitere Mischung aus dieser Reihe.

## Vollständige Ergebnisse

| Gegner | MATCH38 Siege / Remis / Niederlagen | V14 Siege / Remis / Niederlagen | Gepaarter Scoreunterschied, 95%-Kartenintervall |
|---|---:|---:|---:|
| Solution | 38 / 0 / 2 | 38 / 0 / 2 | 0 pp [−7,5; +7,5] |
| default | 40 / 0 / 0 | 40 / 0 / 0 | 0 pp [0; 0], degeneriert |
| Square-Solution | 37 / 0 / 3 | 34 / 0 / 6 | +7,5 pp [−2,5; +17,5] |
| rush | 40 / 0 / 0 | 40 / 0 / 0 | 0 pp [0; 0], degeneriert |

Panel: **155/160 statt 152/160**, mittlere Differenz +1,875 Prozentpunkte [−1,25; +5,625]. Das Panel umfasst 20 Karten mit beiden Startseiten und vier Gegnern je Variante, also 320 Ausführungen. Direkter Vergleich auf 60 anderen Karten mit beiden Seiten: **58 Siege, 0 Remis, 62 Niederlagen**, Score 48,33 % [35; 61,67 %], insgesamt 120 Spiele. Keine Zeilen ausgeschlossen.

Die vorab geforderten mindestens 72 direkten Siege und die untere Scoregrenze über 50 % sind verfehlt. Das breite Intervall belegt auch keine allgemeine Unterlegenheit. Der Square-Vorsprung ist ein unsicherer Einzelbefund; Solution wurde in dieser Bestätigung nicht verbessert. Die nominierenden 26/40 aus der Auswahl werden nicht mit der Bestätigung zu einer nachträglichen Bestehensregel zusammengefasst.

## Methode und tatsächliche Prüfung

Gleiche akzeptierte Evalkopien: V14 mit 36 ursprünglichen Netzen, MATCH38 mit diesen 36 plus den beiden vollständigen Matchreward-Endnetzen. Originale Inferenzkonfiguration und bisherige Runtime unverändert, kein weiteres Training oder Modellumbau. Panelkarten 9980000–9980019, Direktkarten 9980100–9980159. Alle acht Bedingungen und Grenzen vor den Daten im [Plan](../../../docs/superpowers/plans/2026-11-09-match-weight-confirmation.md) fixiert.

Je Statistik 5000 PCG64-Seed-0-Bootstrapziehungen ganzer Karten. Im Panel werden alle Gegner und Seiten derselben Karte gemeinsam behandelt. Remis zählen im Score halb, tatsächliche Siegbedingungen nur echte Siege. Panelbedingungen sind empirische Stabilitätswachen, kein formaler Populations-Nichtunterlegenheitsbeweis. Degenerierte [0;0]-Intervalle bei default/rush schließen unbekannte Kartenrisiken nicht aus. Keine Korrektur für viele historische Projektversuche, isolierte Rewardkausalität oder allgemeine 100-Prozent-Garantie.

Unabhängiger Audit mit 24.837 Prüfungen und 512 Hashbindungen bestanden: alle 440 CSV-Zeilen, eindeutige Keys, 303 Schritte, Punktzählung v2, Ergebnisarithmetik, Gates, Intervalle, Sourceinventar, Eingaben und Prozessende. Root hat die Originalanalyse unter eingefrorener Quelle **98f2b02** exakt reproduziert und erst nach versiegelter [Gesamtabnahme](operations/confirmation-closure.json) den Freeze gelöst. [Originalsummary](confirmation_v1/summary.json), [unabhängiger Bericht](operations/confirmation-audit-review.md), [Maschinenbeleg](operations/confirmation-audit-results.json).

Lokaler Kartencheck ohne beobachtete gespielte Überschneidung; ein eigener COHORTS-Definitionsfund wurde ausdrücklich als ungespielte Reservierung eingeordnet. Das rohe REVIEW_REQUIRED bleibt archiviert, ebenso Grenzen bei seedlosen/externen oder ausschließlich JSONL-belegten Historien. Keine globale Frischebehauptung.

## Konsequenz und erhaltene Arbeit

Alle eigenen Prozesse und der Wachhalter beendet, keine automatische Folgephase. Geschlossene Matchgewichtsreihe insgesamt **2.638 Ausführungen und 262.500 Updates**, einschließlich des offen dokumentierten unterbrochenen ersten Trainingsversuchs. Endmodelle und sämtliche Originalbelege bleiben erhalten; das ist geleistete Rechenarbeit, kein nachgewiesener Stärkezuwachs.

Die technisch geprüfte Möglichkeit einer späteren 38er-Abgabe wird hier nicht ausgeführt. Neuer Ansatz separat festzulegen: während des Trainings die Aktionsauswahl mit dem bestehenden Ensemble mitteln, während das einzelne Netz weiterhin mit seinem eigenen DDQN lernt. Keine Fortsetzung oder erneute Auswahl des gescheiterten MATCH38-Kandidaten.
