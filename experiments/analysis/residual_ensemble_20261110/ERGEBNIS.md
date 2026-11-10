# Residual-Pilot abgeschlossen: V14 bleibt

**Kein stärkerer Nachfolger nachgewiesen. Beide neuen Kandidaten verfehlen
beide festen Auswahlbedingungen.** Keine Bestätigungsrunde, keine Verlängerung,
kein Austausch der Abgabe oder ZIP.

| Agent | Siege gegen Solution | Siege direkt gegen V14 | 95%-Intervall direkt |
|---|---:|---:|---:|
| V14 | 40/40 | Referenz | – |
| R61 | 35/40 | 14/40 | 15–55 % |
| R62 | 38/40 | 10/40 | 9,875–45 % |

Keine Remis. Voraussetzung waren für **beide** Kandidaten mindestens 24/40
direkte Siege und mindestens die Solution-Siegzahl der frischen V14-Referenz.
Die unabhängige Nachrechnung stimmt exakt mit der Originalanalyse überein.

## Was tatsächlich gemacht wurde

- Additive Korrektur `M+R` umgesetzt, während die originalen 36 Netze eingefroren
  bleiben. Einheitliche Summenfunktion in Verhalten und DDQN; volle
  Auswertungsregeln, unveränderte Rewards/Merkmale und separater Sammler.
- Acht technische Ausführungen auf zwei bekannten Schlüsseln: Originalquelle
  und Nullkorrektur mit Sammler erzeugen dieselben finalen Aktionen und
  öffentlichen Verläufe, Scores und Punkte. Keine Gradienten.
- Zwei unabhängige Starts 61/62, jeweils 40 Vorlauf- und 80 Lernspiele,
  je 12.000 Updates. Beide vollständigen Endstände behalten. [Trainingsbericht](TRAININGSERGEBNIS.md).
- Genau 200 Auswahlspiele auf 40 getrennten frischen Karten: 20 gegen Solution
  mit beiden Kandidaten und V14, 20 für direkte V14-Duelle mit beiden Kandidaten;
  immer beide Seiten. Unveränderte Kandidatenbytes, keine Zwischenwahl.

**Gesamt 448 vollständige Ausführungen:**8 Technik + 240 Training/Vorlauf + 200
Auswahl. Davon 160 Lernspiele, 24.000 Updates. Keine zusätzlichen Pilot-,
Ersatz- oder Bestätigungsspiele. Die reservierten 180 Bestätigungskarten wurden
nicht verwendet. Quellenstand der Auswahl: `c1fdff2b`.

## Einordnung und Unsicherheit

Der neue Zusatz lernt und verändert rohe Aktionsvorschläge, führt unter dieser
Rezeptur aber zu schlechteren beobachteten Ergebnissen. Auf den direkten
Testkarten gewinnt R61 nur 35 %, R62 nur 25 %. Die Lösung wird deshalb nicht
übernommen. Das widerlegt nicht jede residuale Methode oder jedes längere
Training; es gibt jedoch keinen Beleg, diese zwei Endstände weiter einzusetzen.

Gepaarte Solution-Differenz gegenüber V14: R61 −12,5 Prozentpunkte
[−25;−2,5], R62 −5 Punkte [−12,5;0]. Intervalle stammen aus 5.000
PCG64/Seed0-Bootstrapziehungen ganzer Karten; beide Seiten bleiben gemeinsam,
bei Solution zusätzlich Kandidat und V14 gepaart. Trainings- und Auswahlkarten
werden nicht vermischt. Mit 20 Karten bleiben die Intervalle breit.

**40/40 für V14 ist nur das Ergebnis dieses Kartensatzes.** Der empirische
Bootstrap ergibt hier [1;1], weil alle beobachteten Karten vollständig gewonnen
wurden. Dieses degenerierte Intervall bedeutet keine Gewissheit über neue
Karten und keine allgemeine 100 %-Siegquote.

Die rohe M+R-Auswahl im DDQN-Target bildet weiterhin nicht jede nachgelagerte
Regel ab. Die gemessenen Vorschlags-/Regelzähler sind keine kausale Messung
finaler Residualwirkung. Diese Grenzen waren vorab festgehalten.

## Prüfung, Artefakte und Abschluss

18 gezielte neue und 63 vorhandene relevante Tests bestanden. Ein unabhängiger
Kern-/Startreview führte vor den Spielen zu konkreten Korrekturen. Der finale
[unabhängige Datenreview](INDEPENDENT_AUDIT.md) umfasst 11.161 kombinierte Checks
an tatsächlichen Artefakten; Root hat Datenbindung, Modelle und die originale
Auswertung ebenfalls nachgerechnet. Die Rohprotokolle enthalten Verlaufs-/
Aktionshashes, keine vollständigen Simulator-Replays für eine neue Nachzählung.
[Root-Abschluss](selection/accepted.json), [Originalanalyse](selection/completion.json).

Beide experimentellen End-/Vorlaufcheckpoints und alle Spielprotokolle sind
versioniert. Große Replay-NPZs sind lokal in Studien- und Hauptkopie erhalten,
mit Hashes im Trainingsabschluss. Nicht im GitHub-Download enthalten.
V14-Gewichte SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`,
ZIP `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`
in beiden Arbeitskopien unverändert. Kein neuer Abgabestand, alte Sicherungen
erhalten. Eigene Modell- und Wachhalteprozesse beendet, Remote-Automation
weiterhin pausiert. Kontingent beim Abschluss 25 % übrig, geforderte Reserve 5 %.

Diese feste Rezeptur ist geschlossen. Eine weitere Studie braucht eine neue
begründete Entscheidung; aus diesem Ergebnis folgt keine automatische
Verlängerung, weitere Ensemblemischung oder Änderung der Gewichte.
