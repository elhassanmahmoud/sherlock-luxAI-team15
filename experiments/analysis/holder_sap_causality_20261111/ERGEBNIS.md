# Halter-Schussverzicht: zwei gerettete Spiele, Stabilitätsbedingung verfehlt

11.11.2026. **Begrenzten Pilot geschlossen; V14 bleibt der produktive Agent.** Ein einzelner Schussverzicht kann helfen. Die geprüfte Ereignisklasse liefert jedoch keinen insgesamt tragfähigen Anlass für den geplanten Lerner: über die Alternativen zwei zusätzliche ganze Siege, ein zusätzlicher ganzer Verlust, aber zwei weniger gewonnene Matches. Kein Nachtraining, keine neue allgemeine Schutzregel, kein Gewichts- oder ZIP-Austausch.

## Was geprüft wurde

Acht bekannte Karten, beide Startseiten gegen Solution_92. Die Auswahl enthält bewusst bekannte Niederlagen und Siegkontrollen und ist kein neuer repräsentativer Leistungstest. Vor jedem Eingriff wird das Originalspiel von Anfang an neu gerechnet, einschließlich des unveränderten Gegners. Keine kopierten Gegnerzustände.

Pro Match die erste passende Einheit: alleiniger produktiver Halter auf einem bestätigten Punktefeld, legaler STAY, ursprünglicher maskierter Netzvorschlag STAY, aber nach den Regeln ein sichtbarer SAP. Bei mehreren Einheiten die kleinste UID. Nur diesen einen endgültigen SAP durch STAY ersetzen; anschließend normales V14 bis zum Ende aller drei Matches. Spätere Einheiten planen ohne den gestrichenen Schaden weiter. Alle 46 ausgewählten Schüsse stammten tatsächlich aus `pt_sap`.

Originalreferenz: vollständige vorab gesicherte Agentenquelle aus `021d13e`, ursprüngliche 36 Netze. Versuchscode eingefroren auf `3b1a456`. Der normale Agent bleibt ohne experimentelle Aktivierung unverändert. Ein historisch fehlender deaktivierter Konfigurationsschalter wurde vor dem ersten Spiel ausdrücklich abgeglichen; siehe [Vorabgleich](PREFLIGHT.md).

## Tatsächliche Ausführungen

- 32 vollständige Referenz-/Sammlerpartien, 46 vollständige Alternativpartien, acht vollständige Wiederholungen: **86 ganze Ausführungen, 26.058 Engine-Schritte, null Lernupdates**.
- Technik zuerst: zwölf Ausführungen, sechs Eingriffe, zwei Wiederholungen, 3.636 Schritte. Erst nach tatsächlicher Root- und unabhängiger Datenabnahme die übrigen 74 Ausführungen.
- Zwei gültige Nullfälle ohne Gelegenheit: erstes Match auf `2000029/player_1` und `2000055/player_0`. Keine Ersatzereignisse oder Zusatzläufe. Obergrenze 88/26.664 eingehalten; keine abgebrochenen Spielausführungen.
- 46 wirksame Paare auf acht Karten: **2 positive, 1 negativer und 43 unveränderte ganze Spielausgänge**. Drei Alternativen gewinnen mehr Matches, fünf weniger; Summe **−2 Matchsiege**. Summe der Änderungen der Punktedifferenz **−914**; zwölf positiv, zwanzig negativ, vierzehn null.

| Karte, beide Seiten | Paare | Ganze Spiele + / − | Summe Δ Matchsiege | Summe Δ Punktedifferenz |
|---|---:|---:|---:|---:|
| 9946007 | 6 | 0 / 0 | +0 | -276 |
| 2000000 | 6 | 0 / 0 | +0 | +2 |
| 2000001 | 6 | 0 / 0 | -1 | -430 |
| 2000009 | 6 | 0 / 0 | +0 | -126 |
| 2000029 | 5 | 0 / 0 | -1 | -334 |
| 2000035 | 6 | 0 / 0 | +1 | -87 |
| 2000045 | 6 | 1 / 1 | +0 | -19 |
| 2000055 | 5 | 1 / 0 | -1 | +356 |

Diese Summen vergleichen getrennte alternative Verläufe mit mehrfach verwendeten Originalspielen. **Sie sind keine Siegquote einer ausführbaren Policy und kein statistischer Nachweis eines stärkeren Agenten.**

## Konkrete Fälle

| Karte / Seite / Schritt / UID | Original → Alternative, eigene Matchsiege | Δ Punktedifferenz |
|---|---|---:|
| 2000045 / player_1 / 167 / 4 | 1:2 → 2:1 | +32 |
| 2000055 / player_0 / 127 / 0 | 1:2 → 2:1 | +741 |
| 2000045 / player_0 / 256 / 1 | 2:1 → 1:2 | −31 |

Der ursprüngliche Verdachtsfall `9946007/player_0`, Schritt 138, UID 0 verbessert die Punktedifferenz um 65; der ganze Spielausgang und die Zahl eigener Matchsiege bleiben unverändert. Damit ist eine Wirkung dieses einzelnen ausgelassenen Schusses belegt, keine allgemeine Energieverlustursache oder passende dauerhafte Entscheidungsregel.

Zusätzliche Verschlechterungen betreffen auch Siegkontrollen: Auf `2000001/player_0` fällt ein 3:0 auf 2:1; auf `2000029/player_1` ebenso. Zwei getrennte Eingriffe auf `2000055/player_1` ändern jeweils 3:0 zu 2:1. Umgekehrt steigt `2000035/player_0` bei einem Eingriff von 2:1 auf 3:0. Ganze Siege allein würden diese Veränderungen verdecken.

## Vorab festgelegte Entscheidung

- Technische Integrität: bestanden.
- Mindestens zwölf wirksame Fälle auf vier Karten: bestanden (46 / 8).
- Mindestens zwei gerettete Spiele auf zwei Karten und mehr positive als negative ganze Spiel-Flips: bestanden (2 / 2 Karten, gegenüber 1 negativ).
- Nichtnegative Summe der Matchsiegänderungen: **verfehlt (−2)**.

Daher kein Übergang zum vorgesehenen öffentlichen Entscheider, kein 120-Spiel-Leistungsscreen und keine V14-Ablösung. Die Bedingung wird nicht nach Kenntnis der Ergebnisse gelockert. Die beiden positiven Fälle bleiben als überprüfbare Hinweise erhalten; sie begründen keine pauschale Schussunterdrückung oder aus diesen Karten nachträglich ausgewählte Energieschwelle.

## Prüfung und Grenzen

150 neue/betroffene synthetische Tests bestanden; nach dem engen historischen Schemaabgleich ein weiterer gezielter Lauf mit 37 bestandenen Tests, darunter der neue Regressionstest. Unabhängiger Quellreview ohne offenen blockierenden Befund. Root-Nachrechnung aller tatsächlichen Daten: 105.431 Prüfungen. Unabhängige kombinierte Nachrechnung: 107.071 Prüfungen bestanden; davor eigenständige technische Abnahme mit 19.233 Prüfungen.

Geprüft wurden alle Original-/Sammlerframes, tatsächliche Präfixe, acht vollständige Wiederholungen, native Aktionen beider Startseiten, öffentliche Haltervoraussetzungen und vetoabhängige Buchhaltung, Matchenden einschließlich Energie-/Zufallsauflösung, Quellen-/Eingabe-/Artefakt- und Gewichtshashes. Der historische Trace unterstützt 303 eigene native Aktionen und Ergebnisse; keine erfundene historische vollständige Enginezustands-Parität. Alle 14 historischen CSV-Schlüssel wurden nach Punkten und Matchsiegen reproduziert.

Die Engine liefert keine passiven Zwischenenergiephasen. Gegnerangriffe, SAPkosten, Nebel und andere Einflüsse werden deshalb nicht aus einer Energie-Differenz als bewiesene Einzelursachen herausgerechnet. Die gemessene Wirkung umfasst die vollständige Folge des Eingriffs einschließlich späterer eigener und gegnerischer Entscheidungen. Ungewählte ursprüngliche Netzvorschläge wurden nicht durchgehend archiviert; die erste Gelegenheit/UID-Auswahl stützt sich zusätzlich auf geprüften Code und synthetische Tests.

Belege: [Technikabnahme](technical_v1/accepted.json), [Gesamtergebnis mit Rohdateibindung](remaining_v1/manifest.json), [Root-Nachrechnung](remaining_v1/root_audit.json), [unabhängige Nachrechnung](remaining_v1/independent_audit.json), [Abschlussabnahme](remaining_v1/accepted.json). Der tatsächliche Source-Freeze endet erst mit der Abschlussabnahme. Beide V14-Dateien bleiben SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; `Gruppe15.zip` bleibt `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.

## Übergabe an Mahmoud

Alle Originalverläufe und Gegenfakten bleiben im Repo. Der experimentelle Adapter ist kein Abgabeagent und darf nicht als bereits validierter Verbesserungsmodus aktiviert werden. Aktuelle V14-Abgabe, Gewichte und bestehende Sicherungen bleiben erhalten. Diese begrenzte Studie ist beendet; keine laufenden Modellworker, keine neu gestartete Folgestudie. Remote-Abgleich bleibt pausiert. Die Nutzerreserve von mindestens 5 % wird eingehalten.
