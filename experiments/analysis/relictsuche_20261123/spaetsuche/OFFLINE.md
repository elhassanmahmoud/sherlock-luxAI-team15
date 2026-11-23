# Wenn Sherlock vor Zug 55 noch nichts gefunden hat

Auf 64 neuen, gezielt schwierigen Startplätzen brachte die gelernte Entscheidung den ersten sichtbaren Reliktfund durchschnittlich **4,09 Züge früher** als die ursprüngliche V16-Fortsetzung. Das 95-%-Kartenintervall reicht von +1,59 bis +6,83. Die erste eigene Gutschrift kam 4,14 Züge früher [+1,55; +7,03]. Beide Spieler gewannen 43 der 64 ersten Matches. Sechs davon gewann nur der späte Kandidat, sechs nur V16.

In jedem dieser Spiele waren bis zur Beobachtung vor Zug 55 weder ein eigenes Relikt noch eigene Punkte aufgetaucht. Alle Wege beginnen mit exakt denselben V16-Aktionen und öffentlichen Beobachtungen auf derselben Karte, derselben Seite und gegen denselben Gegner. Erst dann entscheidet der Kandidat zwischen der ursprünglichen V16-Fortsetzung, der früher eingefrorenen Routenpolitik und dem früher eingefrorenen Zielschätzer. Er kann höchstens ein Schiff umleiten. Die bekannt gewordene erste Sicht oder der erste eigene Punkt beendet weitere Eingriffe.

| Gegner | Qualifizierte neue Karten | V16 / gelernte Matchsiege | Mittlerer Fundgewinn in Zügen | Mittlerer Gutschriftgewinn in Zügen | Punktedifferenz nach Zug 70, Veränderung | Tatsächlich geändert |
|---|---:|---:|---:|---:|---:|---:|
| Solution | 32 | 25 / 26 | +3,19 | +2,75 | +2,00 | 23 Karten, 106 Befehle |
| V16 | 32 | 18 / 17 | +5,00 | +5,53 | +1,00 | 29 Karten, 137 Befehle |
| Zusammen | 64 | 43 / 43 | +4,09 | +4,14 | +1,50 | 52 Karten, 243 Befehle |

Alle drei möglichen Fortsetzungen wurden auf allen 64 Karten bis zum Ende des ersten Matches tatsächlich gespielt. Die Auswahl entschied 41-mal für den Zielschätzer, 13-mal für den Routenweg und zehnmal für V16. Auf zwei weiteren Sitzen erzeugte die gewählte Alternative dieselben Befehle wie V16. Immer den Zielschätzer auf diesen späten Starts zu verwenden ergab 39 Matchsiege, einen um 4,14 Züge früheren Fund und eine um 4,02 Züge frühere Gutschrift. Immer den Routenweg zu wählen ergab 44 Matchsiege, +1,59 Züge beim Fund und +1,83 bei der Gutschrift. Diese nach dem Fit beschriebenen Einzelarme werden auf dem gesperrten Test nicht nachgewählt.

## Herkunft, Lernziel und Kontrolle

Im Training waren die ersten 80 von 467 geprüften Sitz-Karten gegen Solution und die ersten 80 von 444 gegen V16 qualifiziert. Die 160 ausgewählten Karten lieferten 480 vollständige Eröffnungen für die drei Fortsetzungen. Auf 751 weiteren Startplätzen endete die Erhebung nach 55 Spielschritten. Das Modell verwendet 25 öffentliche Merkmale über den eigenen Sichtverlauf, die Flotte, ihre Energie, die aktuelle Sicht und den sichtbaren gegnerischen Fortschritt. Zwei feste Ridge-Regressionen schätzen die Vorteile der beiden Alternativen. Das Lernziel verwendet die tatsächlich gemessenen Zeitpunkte von Sicht und Gutschrift, die Punktedifferenz nach Zug 70 und den Sieg in Match 1.

Die endgültigen Gewichte wurden vor der neuen Testreihe gesperrt. Für 32 Testkarten pro Gegner wurden gegen Solution 148 und gegen V16 184 Sitz-Karten untersucht. Die 64 qualifizierten Karten ergaben 192 vollständige Eröffnungen, weitere 268 Präfixe endeten nach 55 Schritten. In Training und Test zusammen liefen zwölf schon begonnene zusätzliche Kontrollen fertig, darunter drei volle erste Matches. Sie sind separat archiviert und aus Fit und Testkennzahlen entfernt.

Die sechs vorher bestimmten Bedingungen für die anschließende Ganzspielprüfung sind erfüllt. Für den Methodentest wurden vier echte Eröffnungen einschließlich eines Sitzes mit Sensorreichweite vier unverändert gegen die Originalabgabe reproduziert, jeweils über alle 101 Züge beider Seiten. Vier weitere echte Wiederholungen reproduzierten den jeweils vom Modell gewählten zurückgehaltenen Arm einschließlich der vollständigen Befehlsfolge. Vor dem Sammeln bestätigten vier historische Eröffnungen zusätzlich die gemeinsame Vorgeschichte bis Zug 55. Eine unabhängige Rechnung aus den beiden Roharchiven lieferte dieselben Entscheidungen für alle 64 Testkarten. Die größte absolute Abweichung bei den neu berechneten Regressionsgewichten betrug 6,4 × 10⁻¹⁵.

[Vorabplan und Freigabeschwellen](PLAN.md) · [Training und Auswahl](train/material.json) · [Trainingsöffnungen](train/eroeffnungen.jsonl.gz) · [Alle unabhängigen Testöffnungen](test/eroeffnungen.jsonl.gz) · [Gelernte Entscheidungen](test/ergebnis.json) · [Tatsächliche Ergebnisse der festen Wege](test/feste_wege.json) · [Gegenrechnung](test/gegenrechnung.json) · [Aktionsprüfungen](technik.json)
