# Bedingter Backup-Studiencheck vor frischen P-Ergebnissen

**Empfehlung: A ist methodisch vertretbar, aber nur bedingt zeitlich zulassbar; B nicht bevorzugen. Kein automatischer Start.** Falls P bereits die Auswahl verfehlt, darf eine vorher festgelegte, vollständig getrennte Ein-Kandidaten-Studie PT2 folgen. Nach einer begonnenen P-Bestätigung bleibt der Backup-Zweig geschlossen, auch bei Fehler, Unvollständigkeit oder Misserfolg dieser Bestätigung. V14 bleibt bis zu vollständiger unabhängiger Qualifikation der Referenz-/Auslieferungsstand.

Diese Prüfung liest ausschließlich bestehende Design-/Timingunterlagen, keine frischen P-/Baseline-Ergebnisse. Keine Modelle, Torch, Spiele, Trainings, Tests, Repository-/Quelländerungen oder Implementierung. Einzige neue Datei ist diese Notiz.

## Methodische Zulässigkeit

A: neue Kohorte, Komponenten 18/19 aus genau der bekannten V14, neue Seeds 30/31, zwei Treatment-Läufe gleichzeitig, je unveränderte 120 Prefill + 600 Training und bekannte diagnostische Validierungen. Beide Endstände müssen vollständig, endlich, tatsächlich gelernt und unabhängig technisch zugelassen sein. Neuer Adam/Replay und dieselben tatsächlich geladenen Initialtensoren; keine Auswahl von Seeds, Komponenten oder Zwischenständen anhand von Validierung. PT2 ersetzt genau die beiden vorgesehenen Komponenten innerhalb derselben 36 Netze; alle anderen 34 bleiben unverändert, P-Konfiguration bleibt identisch. Entweder beide vollständigen Endstände oder kein PT2.

Ohne Kontrollen kann die Studie ausschließlich die Leistungsfähigkeit dieses konkreten Pakets PT2 gegenüber V14 prüfen. Sie erlaubt weder einen kausalen Nachweis für Anpassung an die neuen Regeln noch eine Verbesserung gegenüber P zu behaupten; P wird im Backup nicht als Referenz gemessen. Zwei unterschiedliche Seeds sind hier zwei Komponenten, keine unabhängigen Replikationen der gesamten Methode. Das muss auch bei Erfolg so berichtet werden.

Die Abhängigkeit „Backup nur nach P-Auswahl ohne Nominee“ ist zulässig, wenn sie vor der ersten Ergebnislektüre festgeschrieben wird. Genau eine tatsächlich begonnene Bestätigung insgesamt, auf ungesehenen Bestätigungskarten und ohne Zwischenstandsentscheidungen, erhält die unabhängige Bestätigung. Mehrere Auswahlmöglichkeiten schaffen keinen zweiten Bestätigungsversuch. Die Auswahl mit nur 50 Karten ist lauter; ihre geringere Treffsicherheit rechtfertigt weder nachträgliche Vergrößerung noch niedrigere Gates. Keine probabilistische Leistungsgarantie aus dem Plan.

B ist prinzipiell als ausdrücklich historisch gemischter Leistungskandidat möglich, falls sämtliche trainingsrelevanten Quellen, Konfigurationen, geladenen Startzustände, Gegner, Bibliotheken/Interpreter und Endcheckpoint-Belege exakt gebunden sind. Sie ist jedoch keine Vervollständigung des alten Vierarm-Piloten. Ein neuer control19 zusammen mit adap19 macht die historische adap18-Kombination nicht zu einer frischen gepaarten Vierarmstudie. Beide Varianten B und A starten zwei Jobs gleichzeitig; ein zuverlässiger Zeitvorteil für B ist daher nicht belegt. B erhöht Provenienz-/Auditkomplexität und Fehlerrisiko im knappen Zeitfenster. A ist vorzuziehen, falls überhaupt ein Backup gestartet wird.

## Zwingend vor Freigabe festschreiben

1. Trigger ausschließlich endgültige, vollständige P-Auswahl ohne Nominee; keine Kenntnis frischer Outcome-Werte bei der Wahl zwischen A/B/keinem Backup. Kein Backup nach begonnener Bestätigung. Defekte/unvollständige P-Auswahl ist kein statistischer Auswahlmisserfolg; hierfür keine spontane Ersatzregel.
2. Eigener Studienname, eigenes Manifest/Sourcefreeze und unveränderliche Rollen baseline/PT2; keine Ergänzung im aktuellen P-only-Master. Legacy-Vierarm-ACCEPTED darf weder fingiert noch umgedeutet werden. Vorhandene Archiv-/Unvollständigkeitsbefunde bleiben bestehen.
3. Vollständiger Freshnessaudit aller exakten Map-Seeds, auch gegen frühere Trainings-, Validierungs-, Diagnose- und Archivdaten sowie gegen die neuen Trainingskarten. Die neuen Bereiche allein sind kein Freshnessbeweis. Bei Kollision vor Ausführung neu festlegen; keine ergebnisabhängige Kartenersetzung. Trainings-Seed 30/31 und Mapoffset sind getrennte Parameter; tatsächliche Trainingsmapformel explizit binden.
4. Auswahl exakt 845000–845049: baseline/PT2 je 7 Gegner × 2 Seiten × 50 = 1400 plus PT2 direkt gegen V14 auf beiden Seiten = 100, insgesamt 1500. Panelmetriken weiter nur sechs Gegner; default separat. Auswahlgates wie bisher: Paneldelta ≥0,5 pp, Solutiondelta ≥0, default ≥99 %, direkt ≥50 %. Nur PT2 als möglicher Nominee.
5. Bestätigung exakt 846000–846299 (8400 Panel/defaultspiele) und 847000–847299 (600 direkte), insgesamt 9000. Unveränderte +1-pp-Panel-/95%-CI-, Solution-, Default- und Direkt-Gates; gleicher Whole-map-Paired-Bootstrap, 5000, RNG0, 2,5/97,5-Perzentile. Gleiche Sources/Weights zwischen Auswahl und Bestätigung; kein Nachrücken/zweiter Bestätigungsversuch.
6. Bestehender P-only-Driver akzeptiert weder diese anderen Seedblöcke noch 50 Auswahlkarten als unveränderten Plan. Neue getrennte Protokoll-/Runner-/Statistikbindung und unabhängige synthetische Prüfung sind echte Vorarbeiten, keine bereits vorhandene Startfreigabe. Während die aktuelle Studie läuft keine ihrer eingefrorenen Quellen ändern.

## Ressourcenrechnung (WALL-Zeit, keine weitere Division durch zwei)

Floors: combined_panel 2,22 s/Spiel, direct 3,0; 20 % Reserve auf komplette Spielzeit, anschließend 60 min Abschlussreserve.

| Arbeit | Rechnung | Budget |
|---|---|---:|
| Auswahl 1500 | 1,2 × (1400 × 2,22 + 100 × 3) | 68,16 min |
| Bestätigung 9000 | 1,2 × (8400 × 2,22 + 600 × 3) | 408,96 min |
| Abschluss | zusätzlich | 60 min |
| Auswertung + Abschluss | Summe | 537,12 min = 8 h 57 min 7 s |

Die alte erste Zweiworker-Welle lief laut vorhandenen Supervisorzeitstempeln ungefähr von 14:35:08 bis 15:15:08 UTC, rund 40 min. Das Ende enthält den bekannten Supervisor-Schemafehler nach Kinderende; dies ist nur eine Zeitreferenz und kein neuer Leistungs-/Trainingsnachweis. 40 × 1,2 + 2 min ergibt eine vorläufige Trainingsprovision von **50 min**. Zwei neue adaptierte Komponenten sind keine garantierte exakte Laufzeitkopie dieser Kontroll-/Treatment-Welle. Bis zur Zulassung besser einen festen Oberwert und Abbruchzeitpunkt mit vollständiger späterer Evaluationsreserve vorsehen.

Gesamt mit dieser Provision: **587,12 min = 9 h 47 min 7 s**, noch ohne neue Vorbereitungs-/Auditzeit außerhalb der 60-min-Abschlussreserve. Start 19:15 Berlin → rechnerischer Abschluss 05:02:07. Das lässt 57:53 bis zum Nutzerlimit 06:00, aber nur **27:53 bis zum bisherigen strengeren Abschlussziel 05:30** (04:30 UTC). Der bisherige harte Spielecutoff 04:30 Berlin/03:30 UTC plus 60 min Abschluss sollte beibehalten werden; die letzte halbe Stunde bis 06:00 nicht stillschweigend als zusätzliche Rechenzeit ausgeben.

Mit diesem strengeren Ziel liegt der späteste Start der 50-min-Trainingsprovision bei **19:42:53**, der späteste Auswahlstart bei **20:32:53**, der späteste Bestätigungsstart weiterhin bei **21:41:02**. Jegliche vorher noch nötige Vorbereitungs-/Auditzeit muss von diesen Grenzen abgezogen werden. Beispielsweise weitere 20 min Vorbereitung/Audit verschieben den Trainingsbeginn auf spätestens 19:22:53. Diese Zahlen sind theoretische späteste Starts bei den Floors, keine Zusage.

Alle verfügbaren abgeschlossenen Job-Zeitmessungen der jetzigen Studie müssen rein zeitbasiert berücksichtigt werden, ohne Outcomes zu lesen: je Klasse nicht unter Floor/Maximum zurücksetzen und den bereits festgelegten globalen relativen Slowdown auf beide Klassen anwenden. Modellgröße/Workerzahl bleiben gleich. Bereits 6 % zusätzliche Verlangsamung der Evaluationsarbeit verbrauchen rund 28,63 min und damit praktisch den gesamten strengeren Puffer eines Starts um 19:15, bevor zusätzliche Auditarbeit gezählt ist. Laufzeitprognosen anhand des günstigsten Jobs oder Rücksetzen auf historische Floors wären keine belastbare Zulassung.

## Entscheidung

**A nur, wenn** die getrennte Registrierung/Implementierungsprüfung fertig ist, die P-Auswahl vollständig ohne Nominee endet, die echte zeitbasierte Restprognose inklusive 9000 Bestätigungsspielen und Abschlussreserve noch passt, und AC-/Ressourcen-/Quotaguards zulassen. Keine Überlappung von zwei Trainingsjobs mit den laufenden zwei Evaluationsworkern. Keine reduzierte Bestätigung, abgebrochene Läufe als Erfolg oder vorgezogene Freigabe.

Wenn diese Bedingungen nicht erfüllt sind: **kein Leistungs-Backup über Nacht**. V14 beibehalten; vollständige P-Studie und Trainingsprovenienz abschließen, Mahmouds DQN-Linie anhand der vorhandenen Source-/Mechanismusbelege vorbereiten. Eine neue Trainingskohorte kann getrennt für einen späteren vollständigen Versuch geplant werden, ohne morgen früh eine unbestätigte Stärkeverbesserung zu behaupten. Der Nutzerwunsch nach Verbesserung rechtfertigt keinen Ersatz des unabhängigen Leistungsnachweises durch abgeschlossene Trainingsupdates.

## Verbindliche Präzisierung vor Root-Ergebnislektüre: separate Route A / PT2

Das letzte Methodenvotum ersetzt die zuvor nur vorgeschlagenen 845/846/847-Blöcke: **Auswahl 844000–844049**, 50 Karten und 1500 Spiele; einzige gemeinsame, bislang unbenutzte Bestätigungsreserve **842000–842299 plus 843000–843299**, 9000 Spiele. Die frühere Reservierung für P allein verbraucht diese Karten nicht. Bestehender Seed-Audit deckt 840000–844999 ab; unmittelbar vor A weiterhin Nichtbenutzung/Freshness einschließlich etwaiger Technikjobs und neuer Lern-/Valkarten prüfen. Neue Trainingskarten sind laut Protokoll 504200–504499/505000–505059 für Seed30 und 514200–514499/515000–515059 für Seed31, Validation bekannte500000–500007; sie liegen außerhalb der frischen Testblöcke.

A ausschließlich nach vollständiger 3000-Spiel-P-Auswahl, unabhängiger ACCEPTED-Abnahme und NoNominee. **Null begonnene P-Bestätigungen**, auch ein Fehler/Abbruch ohne persistiertes Spiel sperrt A. Kein Einstieg nach unvollständiger/technisch verworfener P-Auswahl. Insgesamt genau eine begonnene Bestätigung im gesamten Pfad. Dies jetzt vor Outcomelektüre festschreiben; eigener A-Master/Sourcefreeze, keine PT-Ergänzung im aktuellen P-Master und keine Umdeutung des alten Vierarm-Piloten. Zwei neue vollständige adaptierte18/19, keine historischen Ersatznetze/Kontroll-/Kausalbehauptung. Alle statistischen Gates unverändert.

Setup-/Auditbudget nun **explizit 20 min zusätzlich**: 50 Training +68,16 Auswahl +408,96 Bestätigung +20 Setup/Audit +60 Abschluss = **607,12 min =10 h 7 min 7 s**. Ab19:15 rechnerisches Ende05:22:07, nur **7:53 Minuten** zusätzlicher Puffer bis05:30 Berlin. Beibehalten: Spielecutoff04:30 Berlin,60minAbschluss,HardEnd05:30 Berlin. Spätester Beginn bei diesen Floors inklusive20minSetup ist19:22:53. Diese Rechnung ist nur die Unterkante der Zulassungsprognose; aktuelle Klassenmaxima/globaler relativer Slowdown aus der P-Auswahl müssen übernommen werden. AC, aktuelle Quoten und keine gleichzeitigen schweren P-/Trainingsworker bleiben Bedingungen. Ein 70-min-Trainingsoberlimit ersetzt nicht die vor Start notwendige Zulassung der gesamten Restfolge; bei geringerem Zeitrest früher sicher abbrechen und unbestätigte Endstände ausschließlich als Forschung behandeln.

Methodenvotum bleibt: **A bedingt vertretbar, keine automatische Freigabe**. Bei fehlendem vollständigem Zeitfit keine neue lange Phase; V14 behalten. Diese Ergänzung liest keine frischen P-Outcomes und verändert keine aktive Quelle.
