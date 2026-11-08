# Artillerievergleich abgeschlossen: V14 bleibt

08.11.2026. **ALIGNED38 verfehlt drei der zehn vorab festgelegten Bestätigungsbedingungen. Kein stärkerer Nachfolger ist nachgewiesen; beide V14-Gewichte und die bestehende ZIP bleiben unverändert.** Die Welle ist geschlossen: keine Zusatzkarten, kein Nachrücker und keine zweite Bestätigung. [Verbindliche Methode](../../../docs/superpowers/specs/2026-11-08-artillery-comparison.md)

CONTROL38 und ALIGNED38 ergänzen die unveränderten 36 V14-Netze jeweils um die beiden finalen Kontroll- beziehungsweise Artillerie-Endnetze der Starts 43/44. Alle Mitglieder werden gleich gewichtet; beide Kandidaten verwenden dieselbe ursprüngliche V14-Inferenzkonfiguration. Die Trainingsänderung betrifft ausschließlich die optionale Artillerie-Streuschadenregel.

**Auswahl: 440 Spiele, ALIGNED38 nominiert.** Drei Rollen gegen Solution92, sol92_sq und default, dazu beide Kandidaten direkt gegen V14 auf getrennten Karten. Je Liste 20 Karten mit beiden Seiten. W/D/L bezeichnet Siege/Remis/Niederlagen; Score = (Siege + 0,5 × Remis) / Spiele.

| Rolle | Zweierpanel W/D/L | Solution92 W/D/L | default W/D/L | Direkt gegen V14 W/D/L |
|---|---:|---:|---:|---:|
| V14 | 67/0/13 | 36/0/4 | 40/0/0 | — |
| CONTROL38 | 74/0/6 | 38/0/2 | 40/0/0 | 18/0/22 |
| ALIGNED38 | 70/0/10 | 38/0/2 | 40/0/0 | 24/0/16 |

Das Zweierpanel enthält Solution92 und sol92_sq; die Solution-Spalte ist darin bereits enthalten. CONTROL38 erreicht +8,75 Prozentpunkte Panelscore gegenüber V14, verfehlt aber mit 45 % Direktspielscore die Auswahlhürde. ALIGNED38 erreicht +3,75 pp und 60 % direkt und erfüllt alle fünf Auswahlbedingungen. Die Nominierung ist noch kein Stärkenachweis. ALIGNED minus CONTROL liegt im Auswahlpanel bei −5,00 pp [−11,25; 0,00], rein deskriptiv. [Auswahlergebnisse](selection/summary.json), [unabhängiger Auswahlaudit: PASS](operations/selection-independent-audit.json)

**Frische Bestätigung: 600 Spiele, keine Übernahme.** Nur ALIGNED38 und V14 gegen das lokale Sechserpanel plus default; zusätzlich 40 direkte Spiele auf eigener Kartenliste. Das Sechserpanel besteht aus Solution92, sol92_sq, V3, V7, V10 und V13.

| Gegner / Auswertung | V14 W/D/L | ALIGNED38 W/D/L |
|---|---:|---:|
| Solution92 | 38/0/2 | 38/0/2 |
| sol92_sq | 35/0/5 | 36/0/4 |
| V3 | 38/0/2 | 40/0/0 |
| V7 | 30/0/10 | 34/0/6 |
| V10 | 34/0/6 | 34/0/6 |
| V13 | 21/0/19 | 22/0/18 |
| **Sechserpanel gesamt** | **196/0/44** | **204/0/36** |
| default, separat | 40/0/0 | 40/0/0 |

ALIGNED38 erzielt 85,00 % Panelscore gegenüber 81,67 % bei V14. Im getrennten Direktduell lautet sein Ergebnis **16/0/24**, entsprechend 40 % Score. Sieben Bedingungen bestehen, diese drei scheitern:

| Verfehlte Bedingung | Beobachteter Wert mit 95%-Intervall | Erforderliche Untergrenze |
|---|---:|---:|
| Panelgewinn ausreichend abgesichert | +3,33 pp [−0,83; +7,92] | strikt über 0 pp |
| Solution92-Rückgang ausreichend begrenzt | 0,00 pp [−7,50; +7,50] | strikt über −2,50 pp |
| Direkter Vorteil gegenüber V14 abgesichert | 40,00 % [20,00; 60,00] | strikt über 50 % |

[Bestätigungsergebnisse und sämtliche zehn Bedingungen](confirmation/summary.json), [unabhängiger Bestätigungsaudit: PASS](operations/confirmation-independent-audit.json). Das Audit-PASS bestätigt Daten und Rechnung; der Leistungsentscheid bleibt **nicht bestanden**.

**Umfang, Prüfung und Grenzen.** Abgeschlossen sind **1.040 Leistungsspiele: 440 Auswahl + 600 Bestätigung**. Getrennt davon stehen die bereits abgenommenen **1.888 historischen Trainings-/Vorlauf-/Diagnoseausführungen**: 1.600 Lernspiele, 160 Vorlaufspiele und 128 Diagnosen, insgesamt 240.000 Updates. [Trainingsbericht](../artillery_alignment_20261108/TRAININGSERGEBNIS.md)

Alle Leistungsdaten wurden unter unveränderter Quelle `70669eb` erzeugt. Unabhängige Audits rekonstruierten beide Phasen; Root rechnete anschließend beide Originalanalysen auf derselben Quelle nach und prüfte die 512 Dateibindungen. Alle eigenen Prozesse sind beendet. Die [historische Abschlussabnahme](operations/historical_comparison_acceptance.json) hält `retain_V14` und `promotion_allowed=false` fest; SHA-256 `e3a7ec2b086f225a93287800b185f655b844c58f0a4a24d27eda2597fa7aa3e1`.

Die Intervalle verwenden 5.000 gepaarte Bootstrapziehungen ganzer Karten, PCG64-Seed 0 und 95%-Perzentile. Pro Kartenliste liegen nur **20 unabhängige Kartencluster** vor; Seiten und Panelgegner sind keine zusätzlichen unabhängigen Karten. Auswahl und Bestätigung werden nicht zusammengelegt. Die Intervalle sind nicht für Mehrfachvergleiche korrigiert, eine bestimmte Teststärke ist nicht garantiert. Zwei Trainingsstarts und diese Ensemblevergleiche belegen keine allgemeine kausale Wirkung der Regelangleichung. Auch 40 Siege in einem geprüften Block bedeuten keine garantierte künftige Siegquote.
