# Ensemble-Nachtraining: Abschluss am 08.11.2026

**V14 bleibt der aktuelle Agent. Die sechs neu trainierten Netze liefern in dieser Runde keinen nachweislich stärkeren Nachfolger.** Die frühe Verbesserung der Austauschvariante REPLACE36 hat sich auf frischen Karten nicht bestätigt. Keine Gewichte oder Abgabe-ZIP wurden ersetzt; die neuen Modelle bleiben als Experimente erhalten.

## Vollständiger frischer Vergleich

REPLACE36 enthält weiterhin 36 Netze: Die alten Mitglieder 0, 6, 12, 18, 24 und 30 wurden durch die sechs fertig nachtrainierten Netze ersetzt. Architektur, Agentenlogik, Regeln, Rewards und V14-Konfiguration waren während dieses Vergleichs unverändert. Dieser Versuch prüft genau diese Zusammenstellung; er isoliert keinen allgemeinen Effekt der Netzanzahl oder der Trainingsgegner.

| Gegner / Vergleich | V14 | REPLACE36 | Differenz REPLACE36 − V14 |
|---|---:|---:|---:|
| Solution_92 | 194/200 (97,0 %) | 193/200 (96,5 %) | −0,5 Prozentpunkte |
| sol92_sq | 171/200 | 169/200 | −1,0 Prozentpunkte |
| V3 | 190/200 | 166/200 | −12,0 Prozentpunkte |
| V7 | 156/200 | 168/200 | +6,0 Prozentpunkte |
| V10 | 150/200 | 154/200 | +2,0 Prozentpunkte |
| V13 | 101/200 | 80/200 | −10,5 Prozentpunkte |
| Sechserpanel, ohne default | 962/1200 (80,17 %) | 930/1200 (77,50 %) | −2,67 Prozentpunkte |
| default | 200/200 | 200/200 | gleich |

Direkt gegen V14 gewinnt REPLACE36 **206 von 400 Spielen (51,5 %)**. Das 95-%-Intervall reicht von **44,5 bis 58,5 %**; ein verlässlicher Vorsprung über 50 % ist damit nicht gezeigt. Panel-Differenz: **−2,67 pp [−6,25; +0,92]**. Gegen Solution: **−0,5 pp [−3,5; +3,0]**. Keine Remis. Sechs der zehn unveränderten Übernahmebedingungen verfehlt. Die Daten belegen keinen Gesamtgewinn; aus dem Panel-Intervall folgt auch keine gesicherte allgemeine Verschlechterung. Die schwächeren beobachteten Ergebnisse gegen V3/V13 sprechen gegen eine Übernahme dieses Kandidaten; die einzelnen Gegnerintervalle sind nicht für Mehrfachvergleiche korrigiert.

V14 selbst ist unverändert: Seine 97 % auf diesen Karten sind keine durch das neue Training verursachte Verbesserung gegenüber älteren Messreihen. 100 % gegen beliebige Karten/Gegner sind nicht erreicht oder garantiert.

## Umfang und Trennung der Daten

Auf Moayeds Wunsch wurde der Vergleich vor Betrachtung der ersten Ergebnisse gegenüber dem ursprünglichen Großplan stark verkleinert. Die konkrete Obergrenze wurde von Codex anhand früherer Studien gewählt, nicht als wörtliche Spielzahl vom Nutzer vorgegeben.

- Abgeschlossene Vorauswahl: 1560 Spiele auf 20 Panel- und 20 separaten Direktkarten, jeweils beide Seiten. A39, B39 und ALL42 qualifizierten sich nicht. ALL42 gewann zwar 40/40 gegen Solution, aber nur 18/40 direkt gegen V14. REPLACE36 war vorab ausschließlich diagnostisch und blieb nicht nominierbar; die Auswahl endet dauerhaft mit `nominee:null`.
- Daraufhin getrennt und vorab festgelegt: einmalige Prüfung genau des diagnostisch interessanten REPLACE36 auf neuen Karten. 100 Panelkarten **2000000–2000099**, zwei Agenten × sieben Gegner × beide Seiten = 2800 Spiele. 200 separate Direktkarten **2100000–2100199** × beide Seiten = 400. **15 vollständige Jobs / 3200 Spiele**, keine Ausschlüsse, Wiederholung oder nachträgliche Verlängerung.
- Damit **4760 vollständige Vergleichsspiele** in dieser verkleinerten Welle. Der davor gestoppte große Auswahlstart erzeugte keine vollständigen CSV; seine intern ausgeführte Spielzahl ist unbekannt und kommt gegebenenfalls zusätzlich hinzu. Sie wird nicht als null ausgegeben und nicht in Ergebnisse einbezogen.
- Die schon vorher abgeschlossenen sechs Trainingsarme bleiben getrennt: 18.000 Lernspiele, 720 Vorlauf- und 768 bekannte Validierungsausführungen, 2,7 Mio. Updates. Bekannte Trainingsvalidierung ist kein unabhängiger Stärkenachweis. Unterbrochenes Ersttraining und Smoke siehe [Trainingsbericht](ENSEMBLE_TRAINING_20261107.md).

Die neue Validierung entstand aus den alten Diagnoseergebnissen. Sie ist deshalb eine separate, durch Ergebnisse motivierte Folgeprüfung und keine nachträgliche Umdeutung der alten Nomination. Alte und neue Leistungsergebnisse wurden nicht zusammengelegt. Ganze Karten wurden gepaart über Rollen, Seiten und Gegner resampelt: 5000 PCG64-Ziehungen mit Seed 0, unadjustierte 95-%-Intervalle. Projektweite wiederholte Studien und der feste lokale Gegnerpool begrenzen die Aussage. Kein Nachschlag bis zur Signifikanz und kein automatischer nächster Kandidat.

## Tatsächliche Prüfungen und Reproduktion

- Root: **228 Tests plus 43 Untertests bestanden**; unabhängiger Werkzeugreview PASS. Synthetische Testzeilen sind keine gespielten Partien.
- Lauf auf eingefrorenem Quellstand **f9e1195bb65b6587206685971b3ce11e604666db**. Alle 15 Prozesse erfolgreich, maximale Parallelität zwei, Netzstrom vorhanden. Alle eigenen Rechen- und Wachhalteprozesse nach Ende nachweislich beendet.
- Unabhängiger Rohdaten-/Statistikaudit PASS: 3200 Zeilen, 317 Quellhashes, 129 gebundene Eingaben, 85 unveränderte frühere Nachweisdateien. **262 Auswertungswerte bis 1e-12 reproduziert**, ohne die produktiven Statistikfunktionen aufzurufen. Keine neuen Spiele für diesen Audit; Ergebnisse nicht unabhängig in der Engine nachgespielt.
- Abgabe-Gewichte auf beiden Seiten weiterhin SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; ZIP `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Bestehende Sicherungen bleiben erhalten. Mangels qualifizierten Kandidaten keine neue Paket-/Übernahmeprüfung oder zusätzliche Spielrunde.

[Vorabplan](superpowers/plans/2026-11-08-replacement-validation.md), [kompakte Vorauswahl](ENSEMBLE_AUSWAHL_20261108.md), [Rohdaten und Prüfberichte](../experiments/analysis/replacement_validation_20261108/), [unabhängiger Audit](../experiments/analysis/replacement_validation_20261108/validation/independent_audit.md).

Die CSV-Statistik ist unabhängig reproduzierbar. Vollständige Prozess-/Quellenbelege enthalten die absoluten Pfade und Python-Datei des ursprünglichen Macs; diese historischen Belege nicht für einen anderen Rechner umschreiben. Der unveränderte unabhängige Auditcode ist als `independent_audit_script.py` archiviert, einschließlich seines ursprünglichen, inzwischen abgeschlossenen Host-Kontexts. Er schreibt seinen Ergebnisbeleg exklusiv und soll nicht über das bestehende Audit erneut ausgeführt werden. Für erneute Analysen separate Ausgaben verwenden und keine neuen Spiele starten.

## Konsequenz für die weitere Arbeit

Diese begrenzte Welle ist abgeschlossen; Remote-Abgleich-Automation pausiert. V14 bleibt, alle neuen Netze und negativen Ergebnisse sind für Mahmoud erhalten. Mehr Mitglieder oder der Austausch dieser sechs Netze allein haben in den untersuchten Varianten keinen bestätigten Nachfolger geliefert. Als nächste Forschungsfrage wäre zu klären, welches Verhalten gegen V3/V13 verloren geht und ob die neuen Mitglieder bestimmte Aktionen systematisch anders bewerten. Das ist eine mögliche getrennte Diagnose, noch kein gestarteter Versuch und kein nachträgliches Auswählen anhand der frischen Validierungskarten.
