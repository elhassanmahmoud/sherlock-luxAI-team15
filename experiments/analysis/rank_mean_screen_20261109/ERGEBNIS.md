# Legales Rangmittel: abgeschlossen, V14 bleibt

Vier bekannte Technikspiele und 120 feste Leistungsspiele sind vollständig abgeschlossen. Das Rangmittel liefert keinen qualifizierten Nachfolger. Gleiche 36 V14-Netze, keine Trainingsupdates, keine neue SAP-Regel. Eingefrorene Messquelle: `32772fd971c1e65338b476438deda9f4aac9969b`.

| Vergleich | Karten, jeweils beide Seiten | Siege / Remis / Niederlagen | Score |
|---|---|---:|---:|
| V14/OFF gegen Solution | 9944000–9944019 | 39 / 0 / 1 | 97,5 % |
| Rangmittel/ON gegen Solution | dieselben 20 | 39 / 0 / 1 | 97,5 % |
| ON direkt gegen V14/OFF | 9944100–9944119 | 19 / 0 / 21 | 47,5 % |

Solution-Kontrast 0 Prozentpunkte [0; 0]. Alle getesteten Ergebnispaare sind gleich; das degenerierte Bootstrapintervall ist kein Beweis allgemeiner Gleichwertigkeit. Direkt 47,5 % [25; 70], feste 60%-Hürde verfehlt. Ganze Karten mit beiden Seiten resampelt, 5.000 PCG64-Seed-0-Ziehungen, 20 Kartencluster je Block; unadjustierte deskriptive Unsicherheit. Wiederholte Projektversuche und lokaler Gegnerpool begrenzen die Aussage.

Auf allen 20 Panelkarten änderten sich legale Netzpräferenzen: 5.597 Schritte / 9.045 Einheitenvorschläge gegen Solution, direkt 5.018 / 7.723. Diese Exposition liegt vor nachgelagerten Regeln und ist kein gezählter kausaler Endaktionseffekt. Expositions- und Solution-Gate erfüllt, Direktgate verfehlt. Keine Bestätigung, kein Nachschlag oder Ersatz für V14.

## Technik und Daten

OFF auf 831006/player_1 und 831000/player_0 reproduziert jeweils alle 303 nativen Befehle, historischen gemeinsamen Aktionshash, Matchdaten und v2-Punkte exakt. ON: 47/131 Schritte mit anderer legaler Netzpräferenz, 199/226 native Frames verschieden zur jeweiligen alten Trajektorie. Nach dem ersten unterschiedlichen Befehl ist dies kein Vergleich identischer Zustände mehr.

Unabhängiger technischer Datencheck mit 93.245 Prüfbedingungen bestanden. Alle gespeicherten 36 Mitgliedsausgaben wurden in den Technikdaten unabhängig gerankt. Zusätzlich: über 6.472 OFF-Einheiten-Frames lagen die mittleren legalen Q-Spannen der 36 Mitglieder zwischen 2,158 und 3,037 (Median 2,469). Das belegt kein dominierendes Einzelnetz oder problematische Skalen.

Originalanalyse Exit 0; unabhängige Prüfung aller 120 Ergebniszeilen, 123 Rohdateihashes und der Statistik bestanden. [Zusammenfassung](performance_v1/summary.json), [unabhängiger Ergebnisbericht](operations/performance-data-review.md), [technischer Bericht mit Beobachtungsgrenzen](operations/technical-data-review.md), [Root-Abschluss](operations/closure.json). Performance speichert kompakte Präferenzdaten; die vollständigen 36 Q-Ausgaben wurden dort live geprüft, aber nur in der Technikphase archiviert.

Beide V14-Gewichte weiterhin SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; ZIP weiterhin `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Alle eigenen Worker, Owner und Wachhalter beendet. Quelle erst nach Root-Abnahme freigegeben.

## Weiterarbeit

Dieser Versuch ist geschlossen. Eine getrennte nächste Hypothese betrifft fehlende richtungsabhängige Kampfinformationen im 79er-Vektor: kontrollierter Warmstart eines vorhandenen Mitglieds mit den bereits implementierten 22 öffentlichen Gefahrmerkmalen. Die historische V3-Threat-Studie war negativ; ein heutiger V14-Warmstart ist damit weder belegt noch ausgeschlossen. Noch kein solcher Lernlauf aus diesem Bericht, keine automatische Promotion.
