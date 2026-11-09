# SAP-Bewegungsmodell: abgeschlossen, V14 bleibt

Vier bekannte Technikspiele und 120 feste Leistungsspiele sind vollständig abgeschlossen. Der neue Filter liefert keinen qualifizierten Nachfolger. Quelle während der gesamten Messung: `4ceff1943e274f476dab82c37b9a93e682a00c63`. Gleiche 36 V14-Netze, keine Trainingsupdates.

| Vergleich | Karten, jeweils beide Seiten | Siege / Remis / Niederlagen | Score |
|---|---|---:|---:|
| V14/OFF gegen Solution | 9942000–9942019 | 38 / 0 / 2 | 95 % |
| Bewegungsmodell/ON gegen Solution | dieselben 20 | 38 / 0 / 2 | 95 % |
| ON direkt gegen V14/OFF | 9942100–9942119 | 21 / 0 / 19 | 52,5 % |

Der gepaarte Solution-Kontrast beträgt 0 Prozentpunkte mit deskriptivem 95%-Kartenbootstrapintervall [0; 0]. Die Ergebnisse auf allen getesteten Schlüsseln sind gleich; das degenerierte Intervall belegt keine allgemeine Gleichwertigkeit. Direkt erreicht ON 52,5 % [50; 57,5], unter der vorab festen 60%-Hürde. Ganze Karten mit beiden Seiten resampelt, 5.000 Ziehungen mit PCG64-Seed 0, 20 Kartencluster je Block. Projektweite wiederholte Versuche und lokale Gegner begrenzen die Aussage.

Der Filter griff auf zehn Panelkarten ein: 478 geänderte SAPs gegen Solution, zwölf im direkten Vergleich. Expositions- und Solution-Gate erfüllt, Direktgate verfehlt. Keine Bestätigung, kein Nachschlag und kein V14-Ersatz. Die frühere pauschale Vorhaltevariante wurde auf anderen Karten geprüft; deren 18/40 sind kein gepaarter Vergleich mit diesen 21/40.

## Technische Evidenz

Die beiden OFF-Technikspiele 831006/player_1 und 831000/player_0 reproduzieren sämtliche 303 nativen Befehle, gespeicherten gemeinsamen Aktionshash, Matchdaten und v2-Punktesummen exakt. ON ändert 18 beziehungsweise null SAPs. Unabhängige technische Nachrechnung: 16.462 Prüfungen bestanden; öffentliche Zähler und alle Entscheidungsgrößen bestätigt. Grenzen zu UID-Wiederverwendung, gemeinsamem Aktionshash und nicht separat gespeichertem Core-Aufrufzähler/Remember stehen im Audit.

Alle 120 Leistungszeilen, 123 Rohdateihashes, drei Exit-0-Jobs und die Statistik unabhängig nachgerechnet: 2.833 Prüfungen bestanden. Originalanalyse ebenfalls Exit 0. [Zusammenfassung](performance_v1/summary.json), [unabhängiger Bericht](operations/performance-data-review.md), [Abschlussbindung](operations/closure.json). Rohdaten, Aufnahmen und Befehle sind versioniert.

Beide V14-Gewichte unverändert, SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; ZIP unverändert, SHA-256 `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Alle eigenen Worker, Owner und Wachhalter beendet. Quelle erst nach vollständiger Root-Abnahme freigegeben.

## Folgerichtung

Diese Methode ist geschlossen. Als neue Hypothese wird der unveränderte Netzverbund betrachtet: Rangmittel über legale Aktionen statt Mittel der rohen Q-Werte. Unterschiedliche Aktionsskalen könnten Netzpräferenzen ungleich beeinflussen; ein V14-Skalenproblem ist bisher nicht belegt. Kein neuer Lauf oder Stärkenachweis allein aus dieser Idee.
