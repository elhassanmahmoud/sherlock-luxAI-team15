# Matchausgang-Pilot: kein ausreichendes Lernsignal, V14 bleibt

Stand: 10.11.2026. Der freigegebene Plan ist bis zur vorab festgelegten Stoppen-/Fortsetzen-Entscheidung umgesetzt. Der technisch reparierte Vergleich ist vollständig und unabhängig geprüft. **43 von 48 Alternativen ändern tatsächlich die Teamaktion; nur eine verbessert den Matchausgang und eine verschlechtert ihn.** Die Voraussetzung für einen neuen Entscheidungskopf ist verfehlt. Deshalb kein anschließendes Training, keine Verlängerung und kein Austausch von V14 oder ZIP.

## Was tatsächlich geprüft wurde

Auf acht bekannten Entwicklungskarten, jeweils als Player 0 und Player 1 gegen Solution, wurde pro Match einmal der zweitbeste legale Netzvorschlag einer Einheit ausprobiert. Auswahl ausschließlich aus aktuellen öffentlichen Informationen: erster geeigneter Schritt zwischen 40 und 70, Einheit mit kleinstem Abstand zwischen den beiden besten erlaubten Q-Werten. In allen 48 tatsächlichen Fällen war das Matchschritt 40. Danach greifen weiterhin alle unveränderten Sherlock-Regeln; anschließend spielt V14 normal bis zum Ende dieses Matches weiter.

Karten: `11011000, 11011001, 11011002, 11011004, 11011007, 11011011, 11011013, 11011017`. Diese Karten sind **keine neue Leistungsstichprobe**. Verglichen wurden einzelne alternative Fortsetzungen, kein neuer spielbarer Agent über mehrere Spiele. Versteckte Engineinformationen liefern ausschließlich externe Endlabels, keine Eingaben eines neuen Modells.

| Vorab festgelegte Bedingung | Tatsächlicher Befund | Entscheidung |
|---|---|---|
| A: Originalverlauf und Messung stimmen überein | Alle Referenzen, passiven Sammler, Originalpräfixe und acht Wiederholungen stimmen exakt überein | Bestanden |
| B: Mindestens 24 wirksame Paare auf mindestens 6 Karten | 43 wirksame Paare auf allen 8 Karten; 5 unverändert | Bestanden |
| C: Mindestens 3 positive Matchflips auf mindestens 3 Karten | 1 positiver Flip auf 1 Karte | **Verfehlt** |

Insgesamt: **1 positiver, 1 negativer und 46 unveränderte Matchausgänge**. Beide Änderungen des Gewinners wurden durch Punkte entschieden, nicht durch einen Energie- oder Zufallsgleichstand. Die Summe der Änderungen der Punktmargen beträgt zwar +144, aber der Saldo der Matchflips ist null. Diese Summe ist keine höhere Siegquote und kein addierbarer Gewinn eines ausführbaren Agenten.

## Die beiden konkreten Fälle

Die Punkte sind hier stets als Sherlock : Solution angegeben. Matchnummern beginnen für Leser bei 1, im Roharchiv bei 0.

| Karte / Seite | Eingriff | V14 am Matchende | Alternative am Matchende |
|---|---|---|---|
| 11011001 / Player 1 | Match 2, Schritt 141 insgesamt, Einheit 3 | 246 : 276, Niederlage | 320 : 231, Sieg |
| 11011002 / Player 1 | Match 1, Schritt 40, Einheit 12 | 104 : 95, Sieg | 91 : 104, Niederlage |

Bei **beiden** Fällen war die Änderung der Punktmarge nach zwölf weiteren Schritten noch null. Außerdem gab es drei Fälle, in denen kurzfristige und endgültige Änderungen der Punktmarge unterschiedliche Vorzeichen hatten. Das stützt die methodische Entscheidung, echte Matchenden zu messen. Es zeigt noch nicht, dass ein öffentliches Modell gute Eingriffe zuverlässig auswählen kann.

Die unveränderte Referenz verliert in diesen 48 Matches überhaupt nur fünf Matches auf drei Karten. Ein positiver Flip ist deshalb eine kleine Ausbeute mit sehr wenig unabhängiger Kartenvielfalt. Die vorab gesetzte Mindestmenge wurde nicht nachträglich abgesenkt. Weder „ein neues Netz kann das schon lernen“ noch „V14 lässt sich grundsätzlich nicht verbessern“ folgt aus diesen Daten.

## Technischer Fehler und begrenzte Reparatur

Der erste Versuch kopierte laufende Spielzustände. Dabei wich auf Karte 11011007 / Player 0 eine Baselinefortsetzung bei Schritt 175 vom Original ab. Die Daten dieses Versuchs sind **nicht für Lernen oder eine Stärkeaussage freigegeben**. Separat wurde demonstriert, dass das Kopieren von Sets Solutions Reihenfolge bei gleichwertigen Zielentscheidungen ändern kann. Der konkrete interne Gegnerzustand am realen Fehlerschritt fehlt; deshalb ist das keine abschließende Einzelursachendiagnose. [Fehlerbericht](SNAPSHOT_FEHLER.md).

Die einmalig vorab dokumentierte Reparatur spielt jede Alternative vom echten Spielanfang mit frischen Agenten ab. Jeder Schritt vor dem Eingriff muss genau dem Original entsprechen. Sie verändert weder Sherlock noch Solution. Auch die zehn bereits im alten Versuch vollständig archivierten Originalreferenzen wurden exakt reproduziert, einschließlich der damaligen Fehlerkarte. Historische gewöhnliche Vollspielbenchmarks sind durch den Snapshotbefund nicht automatisch ungültig.

| Rechenaufwand | Tatsächlich |
|---|---|
| Alter abgebrochener Snapshotversuch | 19 vollständige + 1 teilweise Referenz-/Sammelausführung; einschließlich Gegenfakten 10.203 Engine-Schritte |
| Reparierter Vergleich | 88 abgeschlossene Ausführungen: 48 vollständige Partien + 40 kurze Präfixläufe |
| Zusammensetzung der 88 | 32 Referenz-/Sammelläufe, 48 Alternativläufe, 8 Wiederholungen |
| Reparierte Engine-Schritte | 20.200; vorab maximal 21.816 erlaubt |
| Engine-Schritte beider Versuche zusammen | 30.403 |
| Neue Trainingsupdates | **0** |

Die 48 vollständigen Partien der Reparatur enthalten 16 Alternativen bis zum dritten Matchende. Sie werden nicht als zusätzliche unabhängige Karten oder als nur 32 Spiele ausgegeben. Alle alten Dateien bleiben zur Nachvollziehbarkeit erhalten.

## Tatsächliche Prüfungen und Grenzen

- Vor dem reparierten Modelllauf: 59 gezielte synthetische Tests bestanden; unabhängiger enger Implementierungsreview und Root-Quellenprüfung. Keine echten Spiele in diesen Tests. [Prüfstand](PREFIX_REVIEW.md).
- Root-Nachrechnung aller realen Daten: 41.772 Prüfungen bestanden. Unabhängige Nachrechnung: 268.489 Prüfungen bestanden. Zähler, Endlabels, Gates, vollständige Referenzen, Präfixe, Wiederholungen und gebundene Dateien stimmen überein.
- Quelle `53ee70c0c46a0fab0f9a6b9554b26c639883e507`, Eingaben und Schutzdateien blieben bis zur tatsächlichen Abschlussabnahme unverändert. Modellworker und eigener Wachhalter beendet; erst danach Quellenfreeze aufgehoben.
- Die Auditanzahlen sind technische Konsistenzprüfungen, keine statistisch unabhängigen Versuche. Energietotale sind ohne gespeicherte Einheitenarrays nicht neu summierbar; rohe Spielzustände liegen als Hashes vor. Die Auswahl über alle Einheiten ist aus der einzelnen archivierten Q-Zeile nicht allein rekonstruierbar und beruht zusätzlich auf geprüftem, eingefrorenem Code.
- Das Endlabel erfasst nur das aktuelle Match. Spätere Gedächtnisfolgen und eine wiederholt eingreifende vollständige Policy wären getrennt zu prüfen. Keine frische Generalisierungsprüfung und kein direkter Kandidat-gegen-V14-Benchmark wurden begonnen.

## Übergabe an Mahmoud

Dieser konkrete Pilot ist geschlossen. Phase B wird gemäß Plan **nicht gestartet**; kein Nachschlag, keine Auswahl eines anderen Fensters oder weiterer Aktionen auf denselben Ergebnisdaten. Die funktionsfähige Rekonstruktion und Rohdaten können später einer getrennt begründeten Hypothese dienen. Vor einem neuen Lernversuch müsste zuerst eine andere, kausal begründete Auswahl der kritischen Situationen festgelegt werden. Einfach mehr Netze oder mehr Beispiele dieses seltenen Eingriffs sind durch diesen Versuch nicht begründet.

V14 bleibt der produktive Agent mit denselben 36 Netzen. Beide Gewichte haben weiterhin SHA-256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; `Gruppe15.zip` weiterhin `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`. Die gewünschte Reserve von mindestens 5 % gilt weiter; bei der Abschlussprüfung waren 18 % übrig. Remote-Automation bleibt pausiert.

Belege: [Root-Nachrechnung](prefix_remaining/root_audit.json), [unabhängiger Audit mit Grenzen](prefix_remaining/independent_audit.json), [versiegelte Abschlussabnahme](prefix_remaining/accepted.json), [Technikmanifest](prefix_technical/manifest.json), [Restmanifest und Gesamtzahlen](prefix_remaining/manifest.json). Die konservierten Prüfer stehen in [Root-Prüfer](prefix_root_audit.py.txt) und [unabhängigem Prüfer](prefix_independent_audit.py.txt); sie beziehen sich auf die gebundene historische Quelle und sind keine neuen Spielstarter.
