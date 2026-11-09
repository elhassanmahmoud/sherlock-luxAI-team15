# SAP-Vorhalten: begrenzter Vergleich

**Abgeschlossen am 09.11.:** vier Technikspiele und alle 120 Leistungsspiele. Direktgate verfehlt; keine Verlängerung/Übernahme. [Ergebnis](../../../experiments/analysis/sap_leading_screen_20261109/ERGEBNIS.md). Die folgenden Festlegungen wurden vor den Spielen getroffen; historische Messquelle `4b11f8a` bleibt in den Receipts gebunden.

**Ziel:** Prüfen, ob der separat vorbereitete SAP-Vorhalteprototyp einen weiteren Vergleich rechtfertigt. Kein Training, kein neuer Netzbestand und keine automatische Übernahme. V14 bleibt die Abgabe.

**Status vor dem ersten Spiel:** Plan und Karten festgelegt; echte Integration noch offen. Der technische Prototyp ist auf `2ddf64b` aufgenommen. Runner und Aufnahme werden getrennt geprüft. Frisches tatsächliches Kontingent, freie Rechenprozesse und eine vollständige Quellenbindung sind vor jedem Start erforderlich. Moayed hat am 09.11. ausdrücklich Akkubetrieb für diesen Vergleich erlaubt und übernimmt die Akkuüberwachung. Die gehashte Aufnahme darf dafür `allow_battery=true` festhalten; ohne diese ausdrückliche Ausnahme bleibt Netzstrom erforderlich. Spielumfang, Auswahlbedingungen und Gewichtsschutz ändern sich dadurch nicht.

## Rollen und Karten

Beide Rollen verwenden dieselben 36 V14-Netze, dieselbe Checkpointconfig und denselben expliziten Ladeweg: `frozen=False`, Eval, Epsilon 0, Autosave aus, keine Updates. OFF ist `SapLeadingAgent(lead_enabled=False)`, ON dieselbe Klasse mit `True`. Auch der direkte Gegner bekommt exakt diese Config; kein impliziter Self-Play-Ladeweg. Beide Abgabegewichte behalten SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.

| Block | Feste Karten einschließlich Grenzen | Rollen und Seiten | Spiele |
|---|---|---|---:|
| Solution_92 | 9940000–9940019 | OFF und ON, jeweils beide Seiten | 80 |
| Direkt | 9940100–9940119 | ON gegen OFF, beide Seiten | 40 |

Aufsteigende Kartenfolge, jeweils Spieler 0/1. Zwei Paneljobs dürfen gleichzeitig laufen, anschließend der Direktjob allein. Insgesamt genau 120 Leistungsspiele, keine Erweiterung, Nachrücker, Schwellenänderung oder Zwischencheckpointauswahl. Die lokale Frischeprüfung fand keine beobachtete Nutzung oder ältere Reservierung; seedlose, ausschließlich in Roh-JSONL dokumentierte und externe Historie bleibt unbekannt. Der konkrete Quellenwechsel während der Prüfung ist separat nachgeprüft, kein lückenloser damaliger Freeze behauptet.

## Vier bekannte technische Spiele zuerst

Einmal OFF auf `831006/player_1` und `831000/player_0`, danach ON auf genau denselben Schlüsseln. Höchstens vier Ausführungen, getrennt von den 120 Leistungsspielen. OFF muss jeweils alle 303 nativen eigenen Aktionsarrays, den gemeinsamen Aktionsstreamhash, Version-2-Punkte und vollständige Matchdaten gegen die historischen Targeting-Belege reproduzieren.

ON wird passiv vor und nach seinem Hook gemessen: genau ein originaler Core-Aufruf, höchstens ein SAP-Offsetwechsel, unveränderte andere Befehle und Aktionsklassen, öffentliche Auswahlbedingungen und Parameterschätzung, kleinste geeignete UID, native Spiegelung und korrekte Buchhaltung. Das originale `param_est.remember` muss die tatsächlich eingereichte Aktion enthalten. Keine zweite Entscheidung oder zusätzlicher Forward.

Mindestens ein tatsächlicher ON-Eingriff über diese zwei ON-Spiele ist erforderlich. Bei null Eingriffen bleibt die aktive Integration unbewiesen; kein Ersatzspiel. Jede technische Abweichung stoppt. Erst nach Root-Abnahme der vollständigen technischen Belege wird die getrennte Performanceaufnahme erstellt. Kein automatischer Phasenübergang oder Neustart.

## Messung und feste Entscheidung

Vorhandenes `common.play_game(..., train=False)` und die bestehende Punktezählung verwenden. Eigene Lead-Zähler nach jedem Spiel sichern, bevor `new_game` sie zurücksetzt. Pro Job genau 40 eindeutige Spielschlüssel, jeweils 303 Schritte, null abgefangene Agentfehler; Roh-W/D/L, Matchsiege, Punkte, Eingriffe und Ausschlusszähler erhalten. Quellen, Eingaben, ursprüngliche Gewichte und ZIP vor und nach der Ausführung prüfen. Ergebnisse nur in neuen exklusiven Experimentverzeichnissen.

Alle drei Bedingungen müssen gelten:

1. Tatsächliche Eingriffe auf mindestens fünf verschiedenen Panelkarten; eine Seite pro Karte reicht.
2. Solution-Score ON mindestens so hoch wie OFF auf denselben 40 Spielen.
3. Direkter ON-Score mindestens 60 Prozent: `2 * Siege + Unentschieden >= 48` bei 40 Spielen.

Score ist `(Siege + 0,5 * Unentschieden) / Spiele`; der Spielausgang folgt den Matchsiegen, nicht der Summe der Punkte. Ganze Karten mit beiden Seiten und gepaarten Panelrollen gemeinsam resamplen: 5.000 Bootstrapziehungen, PCG64-Seed 0, unadjustierte 95-Prozent-Intervalle. Nur 20 Kartencluster je Block; Intervalle sind deskriptiv und keine zusätzlichen nachträglichen Hürden.

Jeder Gatefehlschlag schließt diesen Screen ohne Nachschlag. Ein positives Ergebnis erlaubt nur einen separat geplanten nächsten Versuch, weder einen belegten allgemeinen Stärkegewinn noch den Ersatz von V14. Die ZIP bleibt SHA-256 `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.

## Durchführung

- [x] Technischen Prototyp unabhängig prüfen und aufnehmen.
- [x] Unveränderte Kartenbereiche lokal prüfen und begrenzt annehmen.
- [x] Runner und schmale Orchestrierung unabhängig prüfen und aufnehmen; Root37 synthetische Repo-Tests PASS, Launcher zusätzlich syntaktisch/statisch geprüft, noch nicht ausgeführt.
- [x] Frische Ressourcen-/Quellenaufnahme erstellen und vier technische Spiele ausführen.
- [x] Tatsächliche technische Daten prüfen; bei Erfolg getrennte Performanceaufnahme erstellen.
- [x] Genau 120 Spiele abschließen und unabhängig auswerten; Ergebnis und Grenzen für Mahmoud dokumentieren.

Ruling vom 09.11.: Der autonome Auftrag deckt diesen kleinen, von abgeschlossenen Studien getrennten Vergleich ab. Die frühere Prototypplanung allein wird nicht als Spielstartfreigabe verwendet. Nachweise und tatsächliche Starts stehen im Arbeitsstand; geplante Schritte sind keine erledigten Läufe.
