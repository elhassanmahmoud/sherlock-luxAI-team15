# Warum Sherlock das Punktefeld auf 7150096 verlor

**Auf 7150096, Seite 1, verlor Sherlock sein bekanntes Punktefeld (18,8) in Match 2 durch eine Einheit mit negativer Energie nach einem eigenen Schuss.** Feld, Zielzuweisung und Halter waren vor Aktion 76 bekannt. Eine unmittelbar benachbarte Einheit verlor im selben Zug ebenfalls ihre Einsatzfähigkeit. Ab Aktion 92 konnte kein eigenes Schiff das Feld vor Matchende erreichen. Die anderen Vergleichskarten liefern keinen Anlass, pauschal auf Halterschüsse zu verzichten.

## Messung und Herkunft

20 vollständige Partien V14 gegen Solution_92, genau 6.060 Engine-Schritte. Vier vorgewählte Fälle, dann 16 Spiele auf acht anderen vorab bestimmten Kontrollkarten. Jeweils beide Sitze. Der Agent nutzte nur seine üblichen Beobachtungen. Direkt nach seiner echten Aktionswahl las der Beobachter den vorhandenen Entscheidungscache. Er erfasste die öffentlichen Zustände **vor** den Aktionen 25–100 in M2 und M3, zusammen 3.040 Frames. Der letzte Aktionsübergang ist außerhalb des Fensters; für Räumungen werden 25→26 bis 99→100 ausgewertet.

Beide Phasen liefen nacheinander auf einem Worker, jeweils regulär bis Exit 0. Keine Wiederholungen oder technischen Fehlaufnahmen. Für jede Partie wurden Ergebnis, Punkte, Siege und alle übrigen numerischen Nichtzeit-Spalten der historischen CSV geprüft. Alle stimmen innerhalb des vorgegebenen absoluten Vergleichs von 1e−10. Alle zwanzig gespeicherten Rohdateien wurden zusätzlich einzeln mit den SHA-256 aus den Manifesten abgeglichen. Für die Kontrolle wurden lediglich die zwei öffentlichen Matchsiegzähler im selben Beobachter zusätzlich gespeichert. So ist die Zuordnung zu gewonnenen und verlorenen Matches auch ohne Engine-Wahrheit exakt. Die Matchausgänge für die vier Fälle stammen aus der gesonderten, vollständigen Scoring-Beobachtung.

Isolierter Quellstand `ece525b24e85cbcc81f6d263a14106fdd929abb7`. V14-Gewichte `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`, historische CSV `4af3e6712e217e679d5393e03f61db5d8fe820a79f16523e05de347ba8c62e78`. SHA der Ergebnismanifeste für Fälle/Kontrollen `5c105e7bb0cb24ce15a220b65e3fe41791b58c8c27bcffa8b378fa2fd5e94a40` / `fd3a5f6c45ad6b3ab8f7ff98c43f17ecab8a7a7612eebe80cadc64a6d0f8f748`. Vollständige Rohbelege, Beobachterfassungen, Auswertungsskript, Ereignisse pro UID, Prozesslogs und weitere Prüfsummen liegen unter `experiments/analysis/solution_public_20261115/` im Desktop-Hauptprojekt. Kein Training oder pytest.

## 7150096 im Detail

Alle Koordinaten sind in Sherlocks kanonischem Raum angegeben. Die Aktion t verändert die Belegung, die der Agent in Beobachtung t+1 sieht.

| V14 vor der Aktion | Tatsächliche Folge |
|---|---|
| Seite 1, M2/75. Zwei Schiffe stehen auf (18,8). UID 9 bleibt mit Energie 42 auf seinem zugewiesenen Feld. UID 10 fährt mit Energie 16 nach (19,8). | Das Feld punktet nach 75 weiter. |
| Seite 1, M2/76. UID 9, Energie 38, schießt für 32 auf (20,8). Dort steht ein sichtbarer Gegner mit Energie 90. UID 10 hat als Nachbar noch Energie 6 bei Bewegungskosten 5. Sie bleibt stehen. | Vor 77 steht UID 9 am selben Ort mit −26, UID 10 auf (19,8) mit −58. Keine von beiden kann punkten. Die tatsächlichen gegnerischen Befehle wurden nicht aufgezeichnet. Der sichtbare Gegner auf dem Ziel beweist nicht, wer traf. |
| Seite 1, M2/78. UID 12 erhält (18,8) aus zehn Manhattan-Schritten Entfernung. UID 8 steht sechs Schritte entfernt und verfolgt das andere bestätigte Feld (19,11). | Die Zuweisung konkurrierte mit einem anderen echten Ziel. Die Region war nicht einfach vergessen. 84 wechselt UID 12 ebenfalls auf (19,11), erreicht es bis vor 87 und schießt dort. |
| Seite 1, M2/92. Die nächste eigene lebende Einheit steht zehn Schritte von (18,8) entfernt, bei neun verbleibenden Aktionen einschließlich 92. | Eine Rückeroberung durch Bewegung ist ab dieser Lage selbst ohne Hindernisse geometrisch ausgeschlossen; neue Spawns am eigenen Ursprung liegen noch weiter entfernt. Der nach 95 entstandene Rückstand kann auf dieser Seite nicht mehr durch einen Endspurt zu genau diesem Feld ausgeglichen werden. |
| Seite 0, M2/75–77. UID 8 wird drei Schritte entfernt zugewiesen, geht dreimal in Folge direkt zum Ziel. Nach 77 punktet das Feld. | UID 8 bleibt dort, später mit Energie 0. In Aktion 97 bleibt sie erneut stehen und erscheint danach mit −1. Auch hier ist der spätere Belegungsverlust kein freiwilliger Wegzug. Sherlock gewinnt das Match trotzdem 471:442. |

**Ein-Schritt-Gegenfakt, analytisch.** Bei ausschließlich ausgetauschtem abgesendeten Befehl von UID 9 in Aktion 76 und ansonsten identischen simultanen Befehlen hätte STAY den Punkt **auf (18,8) in genau diesem Schritt** gesichert. Die installierte Engine nimmt für die gleichzeitigen gegnerischen Schüsse, Kollisionen und den Energie-Sog die betreffenden Positionen und Energien nach Bewegung. Der Halter stand mit SAP und mit STAY am selben Ort. Ein als negativ ausgegebener Endwert von −26 bewahrt hier den Wert vor Feld/Nebel; mit gesparten 32 betrüge dieser +6. Von einem nichtnegativen Zwischenwert kann Feld/Nebel allein die Energie höchstens auf 0 kappen. Die UID wäre aktiv und auf dem nachweislich punktenden Feld. Ein eingesparter Schuss könnte zugleich einen Gegner am anderen Ende schonen. Damit sind weder die Netto-Punktdifferenz, der nächste Schritt, die 21 folgenden gegnerischen Besetzungen noch ein Matchsieg bestimmt. Es wurde keine Gegenpartie gespielt. Im gesamten Match waren es auf Seite 1 478:499 Punkte.

## 7150052 unterscheidet sich davon

In M2 waren vor Aktion 50 auf **beiden** Seiten 14 eigene lebende Schiffe in den kanonischen Kartenbereich x≥18, y≤4 beordert. Anfangs war Sherlock dort kein Punktefeld bestätigt. Auf Seite 0 kamen bis vor Aktion 100 keine bestätigten Felder aus dieser Region hinzu. Vor Aktion 90 hatten 13 Einheiten Ziele dort, aber keine stand dort. Fünf davon standen auf (22,7), drei weitere auf (17,5). Die zugewiesenen Ziele waren über mehrere Zellen verteilt. Diese Stapel sind beobachtet; eigene Schiffe können in der Engine übereinander stehen und blockieren einander nicht körperlich.

Auf Seite 1 erschienen vor Aktion 89 die ersten zwei bestätigten Felder in der Region, vor 95 waren es vier und vor 100 sieben. Vor 95 standen zehn lebende eigene Schiffe dort, drei unterschiedliche bestätigte Felder waren besetzt. Im letzten Schritt punktete V14 dann 9:0 über die ganze Karte und verlor M2 knapp mit 179:191. Seite 0 verlor 117:217. In M3 begann Seite 1 bereits im ersten erfassten Frame mit sieben bestätigten regionalen Feldern, Seite 0 kam erst vor Aktion 75 zu den ersten beiden. Die beobachteten Unterschiede liegen in Zeitpunkt von Ankunft und Wissensgewinn. Ob andere Routen dies verbessert hätten, bleibt offen; aus den Stapeln folgt kein wirksamer Entstauungsbefehl.

## Vergleich mit anderen Siegen und Niederlagen

Kontrollkarten mit mindestens einer historischen Spielniederlage: 7150003, 7150011, 7150035, 7150037. Karten mit zwei historischen Spielgewinnen: 7150000, 7150001, 7150002, 7150004. Dies ergibt fünf verlorene und elf gewonnene ganze Partien. Innerhalb dieser Partien wurden elf verlorene und 21 gewonnene Matches 2/3 beobachtet.

Gezählt wird der Verlust einer **vor der Aktion bestätigten und von einer aktiven eigenen Unit belegten** Zelle, die in der Folgebeobachtung keine aktive eigene Unit mehr hält. Mehrere Ereignisse pro Feld und Match sind möglich. Nicht jedes gegnerische Risiko war sichtbar; bei Slotwechseln bleibt der genaue Todesgrund offen. Auf diesen Kontrollkarten waren Sherlocks bestätigte Felder öffentlich abgeleitet. Die wahre Punktekarte wurde dafür nicht eingelesen.

| Art der Räumung | Verlorene Matches (11) | Gewonnene Matches (21) |
|---|---:|---:|
| Sämtliche Feldräumungen | 165 | 281 |
| Letzter Halter bewegte sich wie angewiesen und überlebte | 55 | 103 |
| Letzter Halter blieb/schoss und erschien mit negativer Energie am selben Ort | 69 | 116 |
| Halter blieb/schoss, verschwand oder seine ID wurde andernorts neu vergeben | 13 | 29 |
| Mehrere ursprüngliche Halter | 13 | 24 |
| Bewegung oder ID-Fortbestand uneindeutig | 15 | 9 |
| Mindestens drei folgende Beobachtungen leer / mit vollständigem Dreischrittfenster | 114/164 | 179/269 |
| Geometrisch benachbarter, beweglicher Nicht-Halter mit laut V14 erlaubtem Schritt auf das Feld | 17 | 18 |
| Analytisch durch reinen Schussverzicht im selben Schritt rettbarer Halter | 8 in 5 Matches | 15 in 11 Matches |

Die 23 rechnerisch rettbaren Fälle unterliegen demselben Kriterium wie UID 9 in Aktion 76. Es sind etwa 0,73 pro verlorenem und 0,71 pro gewonnenem Match. Die Maßnahme könnte einzelne Halter retten, ihr Vorkommen unterscheidet in dieser kleinen Auswahl Siege und Niederlagen kaum. Der Zugewinn eines ganzen Spiels ist damit nicht identifiziert. Auch Rettung durch sofortige Ablösung war meist nicht praktikabel: Beim zusätzlichen Ausschluss von Nachbarn mit geplantem SAP oder produktivem Zieleinlauf blieben zwölf Räumungen in den Niederlagen und sechs in den Siegen mit überhaupt denkbarem Nachbarn. Bei keiner der 23 rechnerischen Schussrettungen gab es auf diesen Kontrollkarten einen derartigen Nachbarn. Diese Nachbarschaftszählung verwendet rückblickend die tatsächlich aufgetretene Räumung; vor der Aktion kann der Agent sie nur prognostizieren.

**Folgerung für den nächsten Versuch.** Den belegten Einzelfall als Beispiel für einen zu teuren Halterschuss nutzen. Der frühere gezielte Schussverzicht scheiterte bereits an der Stabilität über ganze Matches; die unabhängigen Kontrollzahlen liefern keinen Grund, dieselbe Regel erneut zu bauen oder zu trainieren. Für einen andersartigen Ansatz auf 7150052 wäre ein ursächlicher Nachweis nötig, dass eine konkrete alternative Bewegung mehrere Schritte vor der späten Ankunft ein zusätzliches bekanntes Ziel rechtzeitig erreichbar macht, ohne eine andere Wertung zu verdrängen. Die hier verlangte passive Prüfung weist einen solchen Befehlswechsel bisher nicht nach.

## Reproduktion aus dem gemeinsamen Repo

Vom Projektordner aus genügt Python mit der Standardbibliothek. Das Werkzeug prüft die archivierten Hashes und berechnet die Ereignisse aus den komprimierten Beobachtungen neu.

```sh
python3 experiments/analysis/solution_public_20261115/evidence/analyze_public_windows.py --out /tmp/sherlock-public-events.json
cmp /tmp/sherlock-public-events.json experiments/analysis/solution_public_20261115/evidence/public_events.json
```

Als Ausgabepfad eine neue Datei verwenden. Der aufgezeichnete Quellstand des V14-Agenten steht in der Provenienzdatei.
