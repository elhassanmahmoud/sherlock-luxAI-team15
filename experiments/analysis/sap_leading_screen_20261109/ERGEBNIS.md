# SAP-Vorhalten: 40/40 gegen Solution, kein V14-Ersatz

Am 09.11.2026 wurden vier bekannte Technikspiele und alle 120 vorab festgelegten Vergleichsspiele ausgeführt. Die neue Variante erreichte auf diesem Kartensatz 40/40 gegen Solution_92 statt 39/40 bei V14. Direkt gegen V14 gewann sie jedoch nur 18/40. Damit wurde die vorher festgelegte direkte Hürde verfehlt. **V14 und ZIP bleiben unverändert; dieser Versuch ist ohne Verlängerung geschlossen.**

## Was wurde verändert?

Beide Rollen verwenden genau dieselben 36 trainierten V14-Netze. OFF ist die Kontrollrolle mit deaktiviertem Vorhalte-Hook, ON aktiviert ihn. Bei einem ohnehin gewählten SAP und geeigneter öffentlicher Bewegungshistorie wird höchstens ein Schuss pro Schritt auf die vermutete nächste Gegnerposition verschoben. Ein ausreichend sicher geschätzter Streufaktor unter 1 ist Voraussetzung. Es wurden keine Netze nachtrainiert und keine Lernupdates ausgeführt.

## Vollständige Ergebnisse

| Vergleich | Karten, jeweils beide Seiten | Siege / Remis / Niederlagen | Score |
|---|---|---:|---:|
| OFF gegen Solution_92 | 9940000–9940019 | 39 / 0 / 1 | 97,5 % |
| ON gegen Solution_92 | dieselben 20 Karten | 40 / 0 / 0 | 100 % |
| ON direkt gegen OFF | 9940100–9940119 | 18 / 0 / 22 | 45 % |

Der gepaarte Solution-Unterschied beträgt +2,5 Prozentpunkte; das deskriptive 95-Prozent-Kartenbootstrapintervall reicht von 0 bis +7,5 Prozentpunkten. Das direkte Intervall reicht von 30 bis 60 Prozent. Je Block liegen nur 20 Kartencluster vor, beide Seiten werden gemeinsam gezogen; 5.000 Ziehungen, PCG64-Seed 0.

Die 40 Siege sind ein tatsächliches positives Ergebnis dieser Stichprobe, **keine allgemeine 100-Prozent-Garantie**. Der empirische Bootstrap ergibt für die ausschließlich beobachteten ON-Siege rechnerisch [100 %, 100 %]; dieses degenerierte Intervall beschreibt keine Sicherheit über neue Karten. Auch ein allgemeiner Stärkegewinn oder eine allgemeine Verschlechterung ist aus diesem kleinen Versuch nicht nachgewiesen.

## Vorher festgelegte Entscheidung

- Eingriffe auf mindestens fünf Panelkarten: **bestanden, 14 Karten**.
- ON-Solution-Score mindestens OFF: **bestanden, 40 statt 39 Siege**.
- Direkt mindestens 60 Prozent: **verfehlt, 18/40 statt mindestens 24/40 ohne Remis**; `2W+D = 36 < 48`.

ON änderte gegen Solution 917 Schüsse und direkt gegen OFF 430. Diese Ereigniszahlen sind weder zusätzliche unabhängige Spiele noch ein Nachweis besserer einzelner Schüsse. Es gibt keinen Nachschlag, kein Nachrücken und keinen Ersatz der Abgabe durch diesen Kandidaten.

## Tatsächliche Prüfungen und Laufgrenzen

Vier bekannte technische Spiele: OFF und ON jeweils auf 831006/player_1 und 831000/player_0. Beide OFF-Spiele reproduzierten jeweils alle 303 nativen Aktionsarrays sowie historische Aktionshashes und Match-/Punktedaten exakt. ON änderte 36 beziehungsweise 0 Befehle. Der unabhängige Datencheck bestätigte öffentliche Auswahl, Spiegelung, höchstens einen geänderten SAP-Offset je Schritt und die Buchhaltungsänderungen. Remember und einzelner Core-Aufruf wurden während des Laufs geprüft, aber nicht separat erneut archiviert; diese Grenze bleibt im Review genannt.

Alle drei Performancejobs endeten mit Exit 0; alle 120 Spiele haben 303 Schritte und null abgefangene Agentfehler. Originalauswertung und unabhängige Nachrechnung stimmen überein. Messquelle war durchgehend `4b11f8a5ec61c63756bdab00748dd6779a2f2e61`. Nach Ende aller eigenen Prozesse hat Root Quelle, Eingaben, Originalgewichte und ZIP erneut geprüft und den Stand vor Freigabe der Quellen versiegelt.

Moayed hat Akkubetrieb ausdrücklich erlaubt und die Akkuüberwachung übernommen. Der erste Owner-Aufruf wurde wegen des macOS-Symlinks `/tmp` bereits vor Phase, Modell und Spiel abgewiesen; derselbe Quotenpfad wurde danach kanonisch über `/private/tmp` angegeben. Es wurden dadurch null Spiele doppelt ausgeführt. Die frühere Aufnahme ohne Akkuoption war ebenfalls nie gestartet.

## Belege

- [Originalauswertung](performance_v1/summary.json) und [vollständiger Laufzustand](performance_v1/state.json).
- [Unabhängiger Leistungscheck](operations/performance-data-review.md), [maschinenlesbar](operations/performance-data-review.json), SHA `68d308228e987efaf093af27344e0a63dd5e7307dadaa1d36f889d98f4f822a0`.
- [Unabhängiger Technikcheck](operations/technical-data-review.md), [technischer Lauf](technical_v1/state.json).
- [Root-Abschluss und Quellenbindung](operations/closure.json). Sämtliche Rohdateien und Receipts bleiben erhalten; keine fehlgeschlagenen Resultate entfernt.

V14-Gewichte beider Seiten: SHA `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`. ZIP: SHA `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.

## Folgerichtung

Unbedingtes Fortschreiben der letzten Bewegung reicht hier nicht für den festgelegten Vergleichserfolg. Als neue Hypothese kommt eine öffentliche, während des Spiels geschätzte Bewegungsverteilung infrage: erwartete Treffer beider Zielzentren vergleichen und bei Unsicherheit V14 beibehalten. Diese Idee ist noch unbewiesen und müsste getrennt geplant werden; sie ist kein Nachschlag für diesen geschlossenen Screen.
