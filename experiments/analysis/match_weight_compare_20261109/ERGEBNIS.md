# Matchreward-Vergleich: MATCH38 nominiert, V14 bleibt vorerst

**MATCH38 erfüllt alle vier vorab festgelegten Auswahlbedingungen.** Das ist ein positiver Kandidatenbefund und erlaubt eine getrennte Bestätigung auf neuen Karten. Es ist noch kein belastbarer allgemeiner Stärkegewinn, kein V14-Ersatz und keine 100-Prozent-Quote gegen Solution.

| Vollständige Reihe | Siege | Remis | Niederlagen |
|---|---:|---:|---:|
| V14 gegen Solution | 36 | 0 | 4 |
| CONTROL38 gegen Solution | 36 | 0 | 4 |
| MATCH38 gegen Solution | 37 | 0 | 3 |
| MATCH38 direkt gegen V14 | 26 | 0 | 14 |
| MATCH38 direkt gegen CONTROL38 | 24 | 0 | 16 |

**200 feste Leistungsspiele vollständig**, jeweils beide Seiten auf 20 Karten pro Reihe. Die drei Solution-Reihen nutzen dieselben 20 Karten; direkte Duelle zwei getrennte 20er-Kartensätze. Keine Wiederholung, Verlängerung oder Zwischencheckpointwahl. Karten und Grenzen des lokalen Frischechecks stehen in preparation.

## Was verändert wurde

Beide neuen Ensembles enthalten die ursprünglichen 36 V14-Netze in gleicher Reihenfolge plus genau die beiden passenden vollständigen Nachtrainingsnetze (Starts 48/49). CONTROL38 nutzt das bisherige Matchreward-Gewicht 2, MATCH38 Gewicht 20. Architektur und übrige Lernkonfiguration sind innerhalb der Trainingspaare gleich. Alle drei Auswertungsvarianten verwenden die ursprüngliche normalisierte V14-Inferenzkonfiguration, lediglich frozen=False für sichtbare Fehler. Neue Regeln oder die Trainingskonfiguration wurden nicht in die Inferenz übernommen.

Die tatsächliche Zusammensetzung, unveränderte Originaltensoren/Target und der normale Agentenloader wurden vor den Spielen geprüft; unabhängige Artefaktprüfung bestanden. Diese separate Technikphase spielte null Spiele. Die Abgabegewichte und Gruppe15.zip bleiben bytegleich.

## Auswahl und Unsicherheit

Die vier vorher festgelegten Gates waren: MATCH38 mindestens so viele echte Solution-Siege wie beide Referenzen sowie mindestens 24 echte Siege in jedem direkten 40er-Duell. Alle vier bestanden. Remis hätten nicht als Siege gezählt.

| Vergleich | Messwert | Deskriptives 95%-Ganzkartenintervall |
|---|---:|---:|
| Solution: MATCH38 minus V14 | +2,5 Prozentpunkte | −7,5 bis +15,0 |
| Solution: MATCH38 minus CONTROL38 | +2,5 Prozentpunkte | −12,5 bis +17,5 |
| Direkt gegen V14 | 65 % | 45 bis 85 % |
| Direkt gegen CONTROL38 | 60 % | 40 bis 80 % |

Es wurden 5.000 PCG64-Seed-0-Bootstrapziehungen verwendet, beide Seiten einer Karte gemeinsam. Die Intervalle umfassen weiterhin Gleichstand beziehungsweise keinen Vorteil. Ein zusätzlicher Solution-Sieg und zwei Trainingsstarts reichen nicht, um den isolierten Rewardeffekt oder eine allgemeine Verbesserung zu beweisen. Viele vorherige Projektversuche und Auswahloptimismus bleiben berücksichtigt; keine Korrektur über alle historischen Versuche. Unterschiedliche Q-Skalen sind Teil der gemessenen Ensemblevariante, nicht separat kausal untersucht.

## Tatsächliche Prüfung und nächste Grenze

93 synthetische Werkzeugtests, unabhängiger Code-/Methodenreview, reale Zero-game-Loaderprobe, unabhängige Tensorprüfung und vollständige unabhängige Nachrechnung aller 200 CSV-Zeilen bestanden. Der letzte Audit prüfte 10.489 Bedingungen ohne Abweichung. Root hat die originale Auswertung unter eingefrorener Quelle `e5b13d1ace7ae100fa73bd53bcfe4820495e0317` exakt reproduziert, Quellen/Eingaben/Prozessende geprüft und den Abschluss vor Freigabe der Quelle versiegelt. Eigene Rechen- und Wachhalteprozesse sind beendet.

[Originalergebnis](performance_v1/summary.json), [unabhängiger Audit](operations/performance-review.md), [Root-Abschluss](operations/performance-closure.json), [vorab festgelegter Plan](../../../docs/superpowers/plans/2026-11-09-match-weight-training.md), [Training einschließlich Unterbrechung](../match_weight_20261109/TRAININGSERGEBNIS.md).

Gesamte Rechenarbeit dieser Hypothese einschließlich unterbrochenem Training: **2.198 Spielausführungen und 262.500 Updates**. Davon stammen die 200 hier berichteten Leistungsspiele ausschließlich aus dem festen Screen.

Nächster Schritt ist eine einmalige, vor neuen Daten festgelegte Bestätigung mit unveränderten Modellkopien. Noch keine Bestätigungsspiele oder Freigabe zur Abgabe. Bei unklarer Bestätigung bleibt V14; kein Nachschlag bis zum Wunschergebnis.
