# Gefahrmerkmale im Ensemble: V14 bleibt

**Kein nominierter Nachfolger.** Alle vier bekannten Technikspiele und alle 200 vorab festgelegten Vergleichsspiele sind vollständig. Beide Direktbedingungen wurden verfehlt; keine Verlängerung oder automatische Übernahme. Messquelle `ffc8b451fd0bd69a5b7e364776d8575e43ee01d2`.

| Vergleich | Siege | Remis | Niederlagen |
|---|---:|---:|---:|
| V14 gegen Solution | 35 | 0 | 5 |
| Nachtrainierte Kontrolle gegen Solution | 36 | 0 | 4 |
| Gefahrmerkmalsvariante gegen Solution | 36 | 0 | 4 |
| Gefahrmerkmalsvariante direkt gegen V14 | 16 | 0 | 24 |
| Gefahrmerkmalsvariante direkt gegen Kontrolle | 14 | 0 | 26 |

Solution-Karten 9946000–9946019, direkt V14 9946100–9946119, direkt Kontrolle 9946200–9946219; jeweils beide Seiten. Die Solution-Blöcke sind gepaart auf denselben Karten. Andere historische Studien benutzten andere Karten; die heutigen 35/40 sind keine gemessene Verschlechterung unveränderter V14-Gewichte gegenüber früheren Prozentangaben.

## Interpretation und Unsicherheit

Gegen Solution beträgt der gepaarte Unterschied zur V14-Referenz +2,5 Prozentpunkte mit deskriptivem 95%-Kartenbootstrapintervall [−5; +10]. Zur nachtrainierten Kontrolle beträgt er 0 Punkte [−7,5; +7,5]. Direkt gegen V14 sind es 40 % [20; 60], gegen die Kontrolle 35 % [15; 55]. Je 5000 Ziehungen ganzer Karten einschließlich beider Seiten mit NumPy PCG64-Seed 0. Gates zählen echte Siege, Intervalle den Halbpunkt-Score bei Remis; tatsächlich keine Remis. Beide direkten Hürden von mindestens 24 Siegen sind verfehlt.

Die neuen Zusatzmerkmale wurden im vorherigen Training nachweislich gelernt. Ihr Nutzen im untersuchten 36er-Ensemble ist damit **nicht nachgewiesen**. Ein einziger Sieg mehr gegen Solution belegt keinen stärkeren Agenten, zumal die Kontrolle dasselbe Ergebnis erzielt. Eine einzelne Initialisierung und viele frühere Projektversuche begrenzen die Aussage; keine Korrektur für Mehrfachauswahl. Dieses negative Ein-Mitglied-Ergebnis widerlegt nicht sämtliche möglichen Gefahrmerkmalsverfahren. Kein weiterer Kandidat wird aus dieser Studie nachgeschoben.

## Durchführung und Nachweise

Die zwei finalen 101er-Netze ersetzen jeweils genau das nullbasierte V14-Mitglied 18. Alle übrigen 35 Netze und ihre Reihenfolge sind in beiden Varianten gleich. V14-Inferenzkonfiguration, nur benötigte Zusatzmerkmale und Fehlertransparenz; keine Trainingskonfiguration übernommen. Kontrolle mit Standardloader wurde vorher auf realen 101er-Batches und vier bekannten Stock-/Nulladapter-Ausführungen geprüft: identische Ausgaben, legale Auswahl, native Aktionen, Verläufe, Matchpunkte und Ergebnisse. Genau 36 Netze geladen, kein stiller Loader-Fallback.

[20 gezielte synthetische Tests](preparation/implementation-final-tests.log), [unabhängiger Codereview](preparation/code-review.md), [technische Root-Abnahme](operations/technical-acceptance.json). Alle fünf Leistungsjobs Exit 0. [Roh-CSVs und ursprüngliche Auswertung](performance_v1/summary.json), [unabhängiger Ergebnisaudit](operations/result-audit-REPORT.md) und [Root-Abschluss](operations/closure.json). Die unabhängige Nachrechnung bestätigte alle 200 tatsächlichen Zeilen, W/D/L, Gates und Intervalle. Quellen und Eingaben wurden vor Freigabe geprüft; alle eigenen Prozesse einschließlich Wachhalter beendet. CSVs erlauben keine vollständige nachträgliche Rekonstruktion der Engineaktionen; Technikgleichheit ist aus gespeicherten Laufzeitbelegen dokumentiert.

Training ist getrennt unter [Trainingsbericht](../threat_warmstart_20261109/TRAININGSERGEBNIS.md) abgeschlossen: 80 Vorlauf-, 800 Lernspiele und 120.000 Updates, zusätzlich vier technische Spiele. Dieser Vergleich erzeugte keine weiteren Gradienten. Modelle bleiben Versuchskandidaten unter `technical_v1/`; die produktiven Gewichte und ZIP bleiben bytegleich.

## Beobachtung für die weitere Diagnose

Vier der fünf V14-Solution-Niederlagen haben mehr Gesamtpunkte als der Gegner, aber weniger gewonnene Teilmatches. Alle fünf betreffen hier player_0; aus dieser kleinen Auswahl folgt noch kein allgemeiner Seitenfehler. Die CSVs zeigen keinen zeitlichen Entscheidungsverlauf. Deshalb folgt zunächst eine getrennte, kleine Niederlagendiagnose; keine neue Trainingswelle oder pauschale Halteregel aus diesen Summen ableiten.

V14-SHA-256 beider Dateien: `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. ZIP: `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.
