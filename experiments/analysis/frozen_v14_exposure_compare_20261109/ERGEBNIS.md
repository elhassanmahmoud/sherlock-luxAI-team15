# EXPOSURE38: kein bestätigter Nachfolger

## Ergebnis

Die zwei gezielt gegen den eingefrorenen V14 nachtrainierten Netze wurden zu den ursprünglichen 36 ergänzt. Alle 200 vorab festgelegten Vergleichsspiele sind vollständig abgeschlossen. **V14 und Gruppe15.zip bleiben unverändert.**

| Vergleich | Siege | Niederlagen | Remis |
|---|---:|---:|---:|
| V14 gegen Solution_92 | 37/40 | 3 | 0 |
| BEHAVIOR38 gegen Solution_92 | 39/40 | 1 | 0 |
| EXPOSURE38 gegen Solution_92 | 37/40 | 3 | 0 |
| EXPOSURE38 gegen V14 | 22/40 | 18 | 0 |
| EXPOSURE38 gegen BEHAVIOR38 | 20/40 | 20 | 0 |

Die Voraussetzung „mindestens so viele Solution-Siege wie V14“ ist erfüllt. Die drei weiteren Voraussetzungen sind verfehlt: mindestens so viele Solution-Siege wie BEHAVIOR38 sowie jeweils mindestens 24 echte Siege in beiden direkten Duellen. Keine Nominierung, Bestätigung oder Übernahme.

22/40 gegen V14 ist ein positiver Punktschätzer, aber kein belastbarer Stärkenachweis: Das deskriptive 95%-Ganzkartenintervall beträgt 35–75 %. Gegen BEHAVIOR38 beträgt es 30–70 %. Der gepaarte Solution-Unterschied zu V14 ist 0 Prozentpunkte [−15; +10], zu BEHAVIOR38 −5 Prozentpunkte [−15; 0]. 5.000 Bootstrapziehungen mit PCG64/Seed0; beide Spielseiten bleiben pro Karte zusammen. Viele Projektversuche und historische Kontrollen begrenzen die Interpretation; keine Korrektur für Mehrfachauswahl, kein isolierter Kausalnachweis zum Gegnertraining. Auch frühere 40/40-Ergebnisse garantieren keine allgemeine 100%-Siegquote.

## Tatsächlich durchgeführte Arbeit

Vor dem Vergleich: zwei neue Endnetze e48/e49, je40 Vorlauf- und400 Lernspiele, je60.000 Updates. Einschließlich vier Technikspielen884 tatsächliche Trainingsausführungen und120.000 Updates. Nur ursprüngliche Nicht-Solution-Positionen des festen Gegnerplans wurden durch den aktuellen eingefrorenen V14 ersetzt; Belohnungen, DDQN und Inferenzregeln blieben gleich. [Separater Trainingsbericht](../frozen_v14_exposure_20261109/TRAININGSERGEBNIS.md).

Vergleich: originale 36 Netze plus beide neuen Netze, gleiche ursprüngliche Inferenzkonfiguration; akzeptierte V14-/BEHAVIOR38-Kopien unverändert wiederverwendet. Drei Solution-Jobs auf10010000–10010019, direkt gegen V14 auf10010100–10010119, direkt gegen BEHAVIOR38 auf10010200–10010219, jeweils beide Seiten. Genau200 Spiele,303 Schritte und Punktezählungv2. Kein Nachschlag oder Austausch von Testkarten.

178 synthetische Werkzeugtests bestanden. Tatsächliche Montage unabhängig mit3.465 Prüfungen angenommen; vollständige200CSV-Ergebnisse und Ganzkartenintervalle unabhängig mit10.705 Prüfungen nachgerechnet. Root hat die ursprüngliche Analyse unter Quella9fc5b7 exakt reproduziert sowie Quellen, Eingaben, Gewichte und beendete Prozesse geprüft. Die Anzahl technischer Checks ist keine Anzahl unabhängiger Leistungsbeobachtungen.

Root-Abschluss: `1bccee286c4a00745f34c5dedd7998271a290249c76f43f1eb464454acf11f18`. Alle Originalworker und eigener Wachhalter beendet; erst danach Quellenfreeze aufgehoben. Sämtliche Rohdaten, Endmodelle und Auditbelege erhalten. Technische Aufruf-/Archivierungsfehler vor Beginn der Leistungsspiele stehen transparent im Arbeitsstand; sie erzeugten keine zusätzlichen Spiele.

## Übergabe und Budget

Neue Nutzergrenze: mindestens25% Kontingent behalten. Beim Abschluss tatsächlich30% übrig; keine weitere Trainings-, Bestätigungs- oder Residualstudie gestartet. Automatische Fortsetzung pausiert. Die ursprünglichen Abgabegewichte haben weiter SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`, ZIP `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.

Offen bleibt die grundsätzliche Verbesserung gegenüber V14. Eine mögliche spätere Untersuchung wäre ein Lernziel, das direkt den Ensemblewert optimiert; hierzu existiert nur eine ungetestete Machbarkeitsnotiz. Das ist keine implementierte Verbesserung und kein automatisch freigegebener neuer Lauf. Diese Studie nicht wiederholen oder nachträglich bis zum gewünschten Ergebnis verlängern.
