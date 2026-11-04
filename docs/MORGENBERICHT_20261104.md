# Abschlussbericht Sherlock – 04.11.2026

**V14 bleibt die Abgabe. Dieser Durchlauf hat keinen nachweislich stärkeren Nachfolger geliefert; 100 % gegen Solution wurden nicht erreicht.** Die einzige unabhängige Bestätigung endete am 04.11. um 06:29:21 Uhr Berlin vollständig. Alle Ergebnisse wurden aus den Rohdaten unabhängig nachgerechnet. Gewichte und bestehende Abgabe-ZIP bleiben unverändert.

## Ergebnis für Moe und Mahmoud

Die kompakte Variante **FT18** verwendet nur die bereits nachtrainierten 18 Netze aus V14, statt aller 36. Sie war in der kleinen Auswahl vorne, bestätigte den Gesamtvorteil auf neuen Karten aber nicht. Gegen Solution gewann FT18 **755 von 800 Spielen (94,375 %)**, das unveränderte V14 **761 von 800 (95,125 %)**. Diese neue Messung betrifft andere Karten als Mahmouds historische 95,4 % und bedeutet keine Veränderung der V14-Gewichte.

FT18 gewann das direkte Duell gegen V14 mit **453/800 (56,625 %)**. Trotzdem lag es im Mittel gegen die sechs festgelegten Gegner etwas hinter V14. Ein Vorteil im direkten Duell genügt damit nicht als Beleg für eine insgesamt bessere Abgabe. Vier der sieben vorher festgelegten Bedingungen wurden verfehlt. Die Unsicherheitsintervalle beweisen auch keine allgemeine Verschlechterung.

Zusätzlich wurden **zwei echte Nachtrainingsläufe** vollständig durchgeführt. Ihre neuen Endgewichte wurden in C36 und R36 geprüft und sind nicht Bestandteil von FT18. Das Rettungsnachtraining lieferte in dieser Untersuchung keinen qualifizierten Kandidaten. Die technisch geprüften Trainingswerkzeuge und Endgewichte bleiben für spätere Forschung erhalten.

## Tatsächlich ausgeführter Umfang

| Teil | Karten und Gegner | Spielausführungen |
|---|---|---:|
| Replay-Vorlauf, zwei Arme | Je 60 Karten 495000–495059, beide Seiten | 240 |
| Lernen, zwei Arme | Je 600 Karten 493000–493599, beide Seiten; gemeinsamer gemischter Gegnerplan | 2.400 |
| Bekannte Validierung, zwei Arme | 500000–500007, default/Solution, beide Seiten, drei Zeitpunkte | 192 |
| Auswahl | 80 Karten 851000–851079; V14 und sechs Varianten gegen sieben Gegner, zusätzlich sechs Direktblöcke | 8.800 |
| Unabhängige Bestätigung | 400 Panelkarten 852000–852399, beide Seiten, V14/FT18 gegen sieben Gegner | 11.200 |
| Direkte Bestätigung | 400 getrennte Karten 853000–853399, beide Seiten, FT18 gegen V14 | 800 |
| Technische Kontrollspiele vor dem Training | Bereits bekannte Karte 500720, beide Seiten | 2 |
| **Gesamt** | **20.800 Leistungsspiele, 2.832 Trainings-/Validierungsausführungen, zwei Technikspiele** | **23.634** |

Das sind Ausführungen, nicht 23.634 unabhängige Karten. Die Leistungsmessung verwendet insgesamt **880 unterschiedliche Karten** in drei getrennten Blöcken; Auswahl- und Bestätigungsdaten werden nicht zusammengefasst. Vier Vorlaufkarten waren bereits für historisches Training verwendet worden und sind ausdrücklich keine frischen Tests. Die unabhängigen Leistungsblöcke waren laut Prüfung aller lokalen Arbeitskopien vorher unverbraucht. Undokumentierte Versuche auf einem anderen Rechner lassen sich damit nicht ausschließen.

Das lokale Sechserpanel umfasst **Solution_92, sol92_sq, V3, V7, V10 und V13**. `default` wird getrennt bewertet. Dieses Panel ist nicht Mahmouds historisches Battle-Panel; dessen Mittelwert 87,6 % ist deshalb kein unmittelbarer Vergleichswert. Ein vollständiges Kursspiel umfasst drei Matches; alle Leistungszeilen enthalten 303 Schritte und Punktezählung Version 2.

## Training und Auswahl

Die beiden Trainingsarme starteten vom selben V14-Mitglied 18, mit frischem Optimierer und Replay Buffer. Lernrate 0,0001, Exploration 0,05, bestehende Belohnung und gemeinsame Gegnerfolge. Nur der Rettungsarm erlaubte Kandidatenrettung auch beim Lernen. Jeder Arm führte **180.000 Lernupdates** aus. Verwendet wurde jeweils der feste Endstand, nicht der günstigste Zwischenstand.

Die unabhängige Trainingsabnahme bestätigte echte Gewichtsänderungen, endliche Werte, unveränderten Lernzustand während Validierungen sowie die endgültig ausgeführten Aktionen im Replay. Die Rettungshelfer änderten im R-Lernteil 2.001 Zwischenaktionen; nachfolgende Regeln können diese nochmals ändern. Das belegt die aktive Behandlung, nicht deren Nutzen. Einzelheiten und Grenzen: [Trainingsarchiv](../experiments/analysis/final_battle_20261103/completed_training/README.md), [begrenzte Nachanalyse](RESCUE_NACHTRAINING_DIAGNOSE_20261103.md).

| Variante | Inhalt | Paneländerung in der Auswahl | Solution-Siege / 160 |
|---|---|---:|---:|
| PAIR18 | 18 vorhandene Netze aus festgelegten Original-/Nachtrainingspaaren | −5,10 pp | 147 |
| PAIR24 | 24 vorhandene Netze aus solchen Paaren | −0,73 pp | 154 |
| FT18 | Vorhandene V14-Netze 18–35 | +0,94 pp | 152 |
| Z36 | Alle V14-Netze, zonenweise Rettung aktiviert | +0,83 pp | 152 |
| C36 | Ein Mitglied durch neues Kontroll-Endnetz ersetzt; nur methodische Kontrolle | −0,10 pp | 152 |
| R36 | Ein Mitglied durch neues Rettungs-Endnetz ersetzt | −2,71 pp | 143 |

V14 erreichte in der Auswahl 150/160 gegen Solution. FT18 und Z36 erfüllten die Auswahlbedingungen; die vorab festgelegte Rangfolge nominierte ausschließlich FT18. Sein Auswahl-Panelintervall [−3,23; +4,90] pp enthielt bereits null. Die komplette [Auswahl mit Daten und Abnahme](../experiments/analysis/final_battle_20261103/performance_selection/README.md) bleibt erhalten. Nach gescheiterter Bestätigung gibt es gemäß Plan keinen nachrückenden Kandidaten und keinen zweiten Versuch.

## Unabhängige Bestätigung: sieben feste Bedingungen

| Bedingung | Tatsächliches FT18-Ergebnis | Erfüllt |
|---|---|---|
| Panelgewinn mindestens +1 pp | 79,3125 % statt 80,2292 %; Δ −0,9167 pp | Nein |
| Untere 95%-Grenze des Panelgewinns über 0 | Intervall [−2,8130; +0,9583] pp | Nein |
| Solution nicht schlechter als V14 | 755/800 statt 761/800; Δ −0,75 pp | Nein |
| Untere 95%-Grenze der Solution-Änderung über −1 pp | Intervall [−2,375; +0,875] pp | Nein |
| default mindestens 99 % | 799/800 = 99,875 % | Ja |
| default-Änderung mindestens −1 pp | V14 800/800; Δ −0,125 pp | Ja |
| Untere 95%-Grenze im Direktduell über 50 % | 56,625 %, Intervall [51,75; 61,375] % | Ja |

Alle 12.000 vorgesehenen Zeilen und Schlüssel sind vorhanden; keine ausgeschlossenen Spiele oder nachträglichen Teilgruppen. Quellen, Interpreter, Engine, Gewichte und Auswertungsregeln blieben über Auswahl und Bestätigung identisch. Bootstrap: 5.000 Ziehungen mit festem Zufallsstart, ganze Karten einschließlich beider Seiten und aller Panelgegner. Der unabhängige Prüfer verwendet keine statistischen Hilfsfunktionen des Repositorys und bestätigt sämtliche Zahlen, Intervalle und Entscheidungen. [Originaldaten, Prüfsummen und unabhängiger Review](../experiments/analysis/final_battle_20261103/performance_confirmation/README.md).

## Abgabe und technische Prüfung

Die vorhandene **V14-Abgabe mit 36 Netzen** wird beibehalten. Es wurde kein FT18-Paket gebaut oder freigegeben, kein neuer Kandidat installiert und kein bestehendes Gewicht ersetzt. Vorhandene Sicherungen, insbesondere `experiments/releases/20261020_old3_sym3` und `experiments/releases/20261101_v14_baseline`, bleiben erhalten. Weil keine Veröffentlichung eines neuen Kandidaten erfolgt, ist keine neue Rücksetztransaktion nötig.

| Datei / Angabe | Wert |
|---|---|
| Abgabe-ZIP | `/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/Gruppe15.zip` |
| Größe | 22.228.404 Bytes |
| ZIP SHA-256 | `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6` |
| Beide aktiven Rohgewichte SHA-256 | `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8` |
| Klasse für den Professor | `Gruppe15.main.Agent_x` |
| Gewichte für beide Seiten | `Gruppe15/agent.pth` |
| Moodle-Frist | 04.11.2026, 23:59 Uhr Berlin |

Die unveränderte ZIP wurde bereits konkret unter Python 3.10 geprüft: acht vollständige Kursspiele, API-Prüfungen an beiden Ablageorten einschließlich `train=True` und ein Replay mit 303 Schritten ohne Aktionsabweichung. Das gilt für genau diese erneut per Hash kontrollierte ZIP. Keine erneute Ausführung dieser Spiele in diesem Abschluss behauptet. Es handelt sich um macOS-Prüfungen, nicht um eine Windows-Zertifizierung. [Tatsächliche frühere Paketprüfung](MORGENBERICHT_20261103.md).

Die gesamte lokale Testsuite bestand vor dem eingefrorenen Lauf mit **1.075 Tests und 126 Untertests**. Seitdem wurde kein spielrelevanter Quellcode verändert. Die ZIP enthält die Laufzeitdateien und Gewichte, keine internen Arbeitsprotokolle oder `CLAUDE.md`. Kein Moodle-Upload ausgeführt.

## Übergabe und nächste Schritte

Abgeschlossene Implementierung, Training, Auswahl und Datenkorrektur wurden in getrennten sinnvollen Commits übertragen: `7eb105c`, `f2688ea`, `2050645`, `7c906e1`, `898cfe0`, `85732df`, `24f9d76`, `6c4f953`, `c40bf4d`, `16581a5`. **`9c29b75` mit vollständigen Bestätigungsdaten und Abnahme ist auf `main` veröffentlicht.** Alle 28 originalen Belegdateien des Abschlussarchivs einschließlich Laufzeitabschluss wurden zusätzlich direkt aus dem tatsächlich committed Git-Archiv per SHA-256 geprüft; CSV-Zeilenumbrüche sind erhalten. Dieser Bericht und die gemeinsame Orientierung bilden den anschließenden separaten Dokumentationscommit; seine Kennung steht in der Git-Historie.

Der primäre Checkout enthält den aktuellen gemeinsamen Stand. Die experimentelle Arbeitskopie bleibt auf der geprüften Quelle `7c906e1`, um ihre Herkunft und lokalen Trainingsartefakte zu erhalten. Neue fremde Commits wurden beim abschließenden Remote-Abgleich nicht beobachtet. Die Leistungsprozesse sind beendet. **Um 06:35:43 Berlin wurden der eigene Remote-Wächter und Wachhalter nach Prüfung ihrer konkreten Prozesskennungen beendet; beide Sherlock-Automationen sind pausiert.** [Abschlussnachweis](../experiments/analysis/final_battle_20261103/closure/runtime.json). Fremde unversionierte Dateien bleiben erhalten. Es laufen keine weiteren eigenen Trainings oder Leistungsspiele dieses Programms.

Für die Abgabe jetzt die oben genannte ZIP verwenden. Für Freitag die zehnminütige Präsentation auf den **tatsächlichen V14** ausrichten: Gedächtnis und Zielwahl, 79 Merkmale, sechs Aktionswerte je Netz, Mittelung von 36 Netzen, Aktionsmasken und die genaue Reihenfolge nachgelagerter Regeln. Die Regeln können Netzvorschläge ändern; das muss im Flowchart sichtbar sein. Ein [quellengestützter Ablauf](../experiments/analysis/final_battle_20261103/preflight/decision_flow_sources.md) ist vorbereitet, die finalen Vortragsfolien wurden in diesem Durchlauf nicht neu erstellt.

Ein späteres Trainingsprogramm sollte die konkrete Ursache vor zusätzlichem Training prüfen: Beiträge einzelner Netze und Q-Abstände auf einem festen Beobachtungssatz, dann mehrere unabhängige Trainingsstarts. Das sind dokumentierte Vorschläge, keine gestarteten Versuche. Für diese Studie bleibt die Entscheidung geschlossen.
