# Entscheidung zur Verbesserungsnacht 01./02.11.2026

**V14 bleibt die Abgabe. CONTROL hat die unabhängige Bestätigung nicht bestanden. Es gibt keine Übernahme und keinen nachrückenden Kandidaten.**

Die 6.000 Spiele der Phase `confirmation200` sind vollständig und unabhängig abgenommen. Die Daten sind gültig; die vorab festgelegten Übernahmebedingungen sind nicht erfüllt. V14 mit 36 Netzen bleibt unverändert, beide Gewichtsdateien mit SHA-256:

```text
98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8
```

## Ergebnis und Bedingungen

200 frische Karten, beide Seiten, je sechs Panelgegner und default für V14 und CONTROL; dazu 200 getrennte Direktkarten. Das ergibt 2.800 + 2.800 + 400 = 6.000 vollständige Spiele. Die Intervalle stammen aus 5.000 Bootstrap-Ziehungen ganzer Karten mit beiden Seiten; im Panel werden alle sechs Gegner einer Karte gemeinsam gezogen.

| Kriterium | Unabhängiges Ergebnis | Vorab festgelegte Bedingung | Erfüllt? |
|---|---|---|---|
| Lokales Sechserpanel | CONTROL 81,375 %, V14 81,542 %; Δ **−0,167 pp**, 95%-KI **[−2,375; +2,000] pp** | Δ ≥ +1 pp und untere Grenze > 0 | Nein |
| Solution_92 | **384/400 statt 382/400** Siege; Δ +0,50 pp, KI **[−1,25; +2,50] pp** | Δ ≥ 0 und untere Grenze ≥ −1 pp | Nein: untere Grenze |
| Direkt gegen V14 | **201/400**, also 50,25 %; KI **[43,50; 57,00] %** | Untere Grenze > 50 % | Nein |
| default | Beide **400/400** | ≥ 99 % und Δ ≥ −1 pp | Ja |

Der einzige Nominee CONTROL hatte in der Auswahl auf 50 Karten **+4,83 pp** erreicht. Dieser Vorteil hat sich auf den unabhängigen Bestätigungskarten **nicht wiederholt**. Der Punktwert von +0,50 pp gegen Solution allein reicht nicht zur Übernahme. Die Bestätigung zeigt auch keinen gesicherten Schaden von CONTROL; sie liefert den verlangten Verbesserungsnachweis nicht.

## Transparenter Zeitnachtrag

Der ursprüngliche Plan sah 300 Bestätigungskarten vor. Am **01.11., 22:33:45 Berlin**, vor Ergebnislektüre und bevor ein Auswahljob abgeschlossen war, wurde wegen der gemessenen Laufzeit eine eigene vollständige Phase mit **200 Karten** festgelegt. Es wurde keine nach Ergebnis ausgewählte Teilmenge eines bereits laufenden Bestätigungslaufs ausgewertet. Auswahl, maximal ein Nominee, alle Gates und das Verbot des Nachrückens blieben unverändert.

Beleg: [confirmation_time_addendum.json](confirmation_time_addendum.json), gebunden an [confirmation200_jobs.json](confirmation200_jobs.json). Die kleinere Stichprobe liefert geringere Präzision als 300 Karten; sie ist kein stärkerer Nachweis. Es werden weder Auswahl- und Bestätigungskarten nachträglich gepoolt noch weitere Karten oder Kandidaten nachgeschoben.

## Grenzen der Aussage und nächste Schritte

- Das lokale Panel umfasst Solution, Quadrat-Solution, V3, V7, V10 und V13. Es ist ein anderes Panel als Mahmouds historischer Vergleich mit `league_nets6` und `threat6`; seine Mittelwerte sind nicht direkt vergleichbar.
- Der Trainingspilot untersucht einen gepaarten Start aus einem V14-Einzelnetz. Er beweist weder eine allgemeine Wirkungslosigkeit von Nachtraining noch einen allgemeinen Vor- oder Nachteil des höheren Entdeckungsrewards. Das zusätzliche Netz verändert außerdem die Ensemblegewichtung; eine einzelne Verhaltensursache ist nicht isoliert.
- OVERLAP und DISCOVERY waren nicht für die Bestätigung nominiert und rücken nicht nach. Der getrennte Gauß-Prototyp gehört nicht zu dieser Stärkenstudie und erhält aus ihrem Ausgang keine neue Messfreigabe.
- Abschließende Tests, Paketprüfung, Archivierung und Übertragung werden getrennt dokumentiert. Dieses Entscheidungsdokument behauptet deren Abschluss nicht. Eine optionale Verlustdiagnose bleibt bis zum Ende der Kernprüfungen und einer eigenen Rootfreigabe zurückgestellt.

Maßgebliche Ergebnisbelege: [confirmation200_summary.json](confirmation200_summary.json), [confirmation200_state.json](confirmation200_state.json) und [selection_summary.json](selection_summary.json). Der unabhängige Prüfer bestätigt alle Zahlen, Intervalle und Gates; sein Bericht ist unter [confirmation200-independent-audit.md](confirmation200-independent-audit.md) bytegleich archiviert. Laufzeitquellen, HEAD `aa06601` und Gewichte blieben während der gesamten Messphase eingefroren.
