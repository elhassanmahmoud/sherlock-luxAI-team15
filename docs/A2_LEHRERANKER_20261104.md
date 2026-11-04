# A2: Niederlagendiagnose und Lehreranker – 04.11.2026

**Abgeschlossen: Der Lehreranker verbessert das gewöhnliche RL-Nachtraining in beiden Starts, liefert aber keinen nachgewiesenen Vorteil gegenüber A2 und keinen qualifizierten V14-Ersatz. V14 bleibt die Abgabe.** Ausgangspunkt ist das A2-Einzelnetz der abgeschlossenen Aktionsschüler-Studie. Maßgeblich sind [Spezifikation](superpowers/specs/2026-11-04-a2-teacher-anchor.md) und [Umsetzungsplan](superpowers/plans/2026-11-04-a2-teacher-anchor.md).

## 1. Ausgangspunkt und gemessene Präferenzänderung

Die abgeschlossene [Aktionsschüler-Studie](AKTIONSSCHUELER_20261104.md) ergab gegen Solution A2 **38/40** statt S30 **16/40**, V14 ebenfalls **38/40**. Im Dreierpanel erreichte A2 **94/120**, V14 **98/120**; direkt gegen V14 gewann A2 **14/40**. Alle vier damaligen RL-Endnetze lagen im beobachteten Panel unter A2. Diese historischen Zahlen gehören zur vorigen Studie und werden nicht als neue Ankerergebnisse gezählt.

Jetzt wurden A2 und die vier damaligen RL-Endnetze auf denselben **68.687 ausgeschlossenen Entwicklungszeilen** der beiden vorhandenen Sammlungen geprüft. Diese Zeilen dienen der Diagnose und erhalten keine Gradienten. Die **356.415 Lernzeilen** bleiben davon getrennt.

| Modell | Gleiche beste legale Aktion wie Lehrer | Lehrerregret ↓ | Zentrierter Q-Fehler ↓ |
|---|---:|---:|---:|
| A2 | 86,70 % | 0,02339 | 0,08275 |
| CONTROL27 | 76,74 % | 0,06063 | 0,38925 |
| CONTROL28 | 81,03 % | 0,05815 | 0,44487 |
| SAP027 | 76,65 % | 0,06286 | 0,32766 |
| SAP028 | 79,92 % | 0,05911 | 0,43467 |

Lehrerregret misst den vom Lehrer bewerteten Nachteil der Schüleraktion. Der zentrierte Fehler entfernt gemeinsame Q-Wertversätze und misst Unterschiede legaler Aktionspräferenzen. Alle vier RL-Endstände stimmen seltener mit dem Lehrer überein und weichen stärker in diesen Präferenzen ab. **Diese Veränderung ist gemessen; dass sie die geringere Spielstärke verursacht, bleibt eine Hypothese.** Der durchschnittliche legale Q-Wert steigt zusätzlich von 13,23 auf 16,09–16,73; Streuungen und Aktionsabstände stehen im [Retentionsbericht](../experiments/analysis/a2_anchor_20261104/retention_before/report.json).

Die unabhängige Prüfung berechnete sämtliche fünf Netze auf allen 68.687 Zeilen mit einem separat aufgebauten Vorwärtslauf und eigenen NumPy-Formeln erneut; Daten-, Modell- und Quellenprüfungen bestanden. [Prüfnachweis](../experiments/analysis/a2_anchor_20261104/preflight/retention_independent.json)

## 2. Was in bekannten Niederlagen tatsächlich passiert

Zwölf gezielte Fälle: A2/V14 gegen Solution auf 866000/866008 und A2 direkt gegen V14 auf den ersten beiden sortierten Verlustkarten 866101/866102, jeweils beide Seiten. Jeder Fall wurde einmal normal und einmal beobachtet ausgeführt: **24 Spielausführungen**, keine neue Gewinnquotenmessung. Jedes vollständige Spiel umfasst **drei Matches** und hier 303 ausgeführte Umgebungsschritte. Ganze Aktionsarrays beider Spieler, Ergebnisse und Matchdaten waren zwischen normalem und beobachtetem Lauf exakt gleich; die unabhängige Analyse umfasst 48.218 Prüfungen und 52 unveränderte Datei-/Interpreter-Pins. [Fallanalyse](../experiments/analysis/a2_anchor_20261104/preflight/trace_analysis.md)

- **Frühe Entdeckung reicht nicht immer zum Sieg.** Auf 866000/player1 kennt A2 Punkte ab Schritt 35 und punktet ab 34; V14 erst ab 42 beziehungsweise 41. Trotzdem verliert A2 Match 1 mit **56:269**, während V14 **275:75** gewinnt. A2 hält bei Schritt 65 noch zwei bekannte Punkte und führt 44:22; bei Schritt 75 hält es keinen mehr und liegt 54:55 zurück. Später sind auch Energieeinbrüche sichtbar. Das stützt eine Untersuchung von Halten und Besetzung; die genaue Schadensquelle und ihr Anteil an der Niederlage sind nicht kausal isoliert.
- **Gesamtpunkte und Spielgewinn sind verschieden.** Auf 866008/player1 erzielt A2 insgesamt **1012:947**, verliert aber **1:2 Matches**. V14 gewinnt mit **993:889** insgesamt **2:1 Matches**. Im zweiten Match punktet A2 nicht später, hält gegen Ende aber weniger bekannte Punkte. Auf player0 gewinnt A2 dieselbe Karte, während V14 verliert. Es gibt keinen universellen A2-Nachteil auf dieser Karte.
- **Direktverluste können knapp sein.** Auf 866101 enden die Matches 348:379, 496:496 und 475:480. Das punktgleiche zweite Match wird laut aufgezeichnetem Ergebnis V14 zugesprochen. Ohne vollständige terminale Energie bleibt offen, ob Energievergleich oder Zufall entschied. Beide Seiten sind keine zusätzlichen unabhängigen Karten.

Netzpräferenz und finale Aktion sind getrennt erfasst. Abweichungen belegen weder einen bestimmten Regelnamen noch die Ursache der späteren Niederlage.

**Der Lehreranker kann auch Lehrerschwächen bewahren.** Auf exakt kopierten A2-Eingaben wurden zusätzlich die 36 eingefrorenen V14-Netze ausgewertet. Bei 866000/player1, Schritt 27, UID3 bevorzugt A2 STAY und der Lehrer LEFT: eine konkrete Imitationsabweichung. Beim Abgang von einem bekannten zugewiesenen Punktefeld in Schritt 35, UID2, bevorzugen dagegen **A2 und Lehrer beide LEFT**. Eine stärkere Lehrerbindung würde diesen konkreten Abgang nicht zu STAY korrigieren. Das beweist weder, dass LEFT grundsätzlich falsch ist, noch dass der vollständige V14-Agent mit seinem eigenen Zustand genauso gehandelt hätte. [Inputs und Einordnung](../experiments/analysis/a2_anchor_20261104/preflight/teacher_on_trace_rows.md)

## 3. Kontrollierter Eingriff: Lernen und Retention geprüft

Abgeschlossen sind genau **CONTROL25/26 und ANCHOR25/26**, jeweils ab identischem A2: pro Arm 40 Vorlauf-, 160 Lern- und 32 bekannte Validierungsspiele sowie 24.000 TD-Updates. Insgesamt **928 tatsächliche Ausführungen und 96.000 Updates**. Verwendet werden ausschließlich die Endstände, ohne Auswahl anhand der bekannten Validierung.

CONTROL lernt wie bisher. ANCHOR ergänzt in demselben Optimierungsschritt **0,1 × maskierten Lehrer-Aktionsverlust**: zentrierter Fehler legaler Q-Präferenzen, geteilt durch die gemeinsame Lernskala², plus KL-Verlust. Pro Update werden 256 Lehrer-Lernzeilen mit Zurücklegen gezogen. Keine zusätzlichen Lehreraufrufe beim Spielen, Reward-/Regeländerungen oder Ensembles. Innerhalb jedes Paars bleiben Startgewichte, Karten-/Gegnerplan, Lernrate 0,0001, anfänglicher Optimierer und Zufallszustand gleich. Lehrerzeilen nutzen einen eigenen Zufallsgenerator; gelernte Aktionen dürfen spätere Spielzustände verändern.

Der unabhängige Abschlussaudit aller vier Arme ist bestanden. Innerhalb jedes Paars stimmen tatsächliche Anfangsgewichte, Optimierer-/Zufallszustände und vollständige Vorlaufnachweise überein. Je Ankerarm wurden **6.144.000 Lehrerzeilen** gezogen; sämtliche **24.000 Updates** hatten einen positiven endlichen Ankergradienten. Alle 12.288.000 Ziehungen wurden unabhängig rekonstruiert: ausschließlich aus den 356.415 Lernzeilen, **null ausgeschlossene Diagnosezeilen**. Je Update erfolgte genau ein Optimiererschritt mit `Gesamtverlust = TD-Verlust + 0,1 × Ankerverlust`. Quellen, Ausgangsdaten, geschützte Dateien und eingefrorener Quellstand blieben unverändert. [Abschlussaudit](../experiments/analysis/a2_anchor_20261104/completion/learning_completion_audit.json)

Auf denselben 68.687 ausgeschlossenen Zeilen ergibt die nachträgliche, ebenfalls unabhängige Retentionsprüfung:

| Start | Kontrolle: Lehrerübereinstimmung | Anker: Lehrerübereinstimmung | Anker minus Kontrolle |
|---|---:|---:|---:|
| 25 | 73,20 % | 78,77 % | +5,57 Prozentpunkte |
| 26 | 77,37 % | 80,94 % | +3,57 Prozentpunkte |

A2 bleibt bei **86,70 %**. Der Anker mindert also die Präferenzänderung gegenüber der gepaarten Kontrolle in beiden Starts, erhält aber nicht das volle A2-Niveau. Auch Lehrerregret und zentrierter Q-Fehler sind mit Anker geringer als ohne. **Der Anker erhält Lehrerpräferenzen besser als die jeweilige Kontrolle; die Leistungsprüfung unten bewertet davon getrennt den Nutzen im Spiel.**

## 4. Frische Leistungsprüfung und Entscheidung

Alle **920 frischen Diagnosepartien** sind vollständig: sechs Rollen auf 20 Karten 867000–867019, beide Seiten gegen Solution/default/V13 (**720**), sowie fünf Schülerrollen auf 20 getrennten Karten 867100–867119 direkt gegen V14 (**200**). Die lokale [Inventur](../experiments/analysis/a2_anchor_20261104/seed_inventory/short.md) fand vorab keine beobachtete Nutzung dieser Bereiche; seedlose Daten und andere Rechner bleiben eine Grenze.

| Rolle | Solution, Siege/40 | Panel, Siege/120 | Direkt gegen V14, Siege/40 |
|---|---:|---:|---:|
| V14 | 40 | 101 | – |
| A2 | 39 | 95 | 16 |
| CONTROL25 | 34 | 81 | 12 |
| CONTROL26 | 31 | 75 | 6 |
| ANCHOR25 | 36 | 96 | 14 |
| ANCHOR26 | 36 | 88 | 12 |

Es gab keine Unentschieden. Gegenüber ihrer gepaarten Kontrolle verbessern die Anker das Panel um **+12,50 Prozentpunkte [2,50; 23,33]** beziehungsweise **+10,83 [0,83; 20,83]**. Damit hilft der feste Anker in diesen beiden Starts gegenüber gewöhnlichem RL. Gegenüber A2 liegt ANCHOR25 im Panel nur **+0,83 [−8,33; 10,00]**, ANCHOR26 **−5,83 [−15,83; 4,17]**; gegen Solution erreichen beide 36/40 statt A2 39/40. A2 gegenüber V14 liegt im Panel bei **−5,00 [−13,33; 3,33]**. Retention und Leistung zeigen somit Fortschritt gegenüber den Kontrollen, keinen belegten Fortschritt über A2 oder V14 hinaus.

**Kein Ankerstand besteht die vorab festgelegte Auswahl.** Beide verfehlen Solution ≥ A2 und mindestens 24/40 Direktgewinne; ANCHOR26 verfehlt zusätzlich Panel ≥ A2. Deshalb **keine Bestätigung, kein weiteres Experiment und kein Abgabewechsel**. Die kleine Diagnose allein hätte ohnehin keine Abgabe qualifiziert. V14s **40/40 gegen Solution gilt ausschließlich für diese Stichprobe**, nicht als allgemeine 100-%-Garantie. [Vollständige unabhängige Auswertung](../experiments/analysis/a2_anchor_20261104/completion/diagnostic_review.json)

Die Intervalle stammen aus 5.000 gepaarten Bootstrapziehungen ganzer Karten, Seed 0, mit beiden Seiten und beim Panel allen drei Gegnern zusammen. Sie sind explorative, nicht für Mehrfachvergleiche korrigierte 95-%-Intervalle. 20 Karten je Bereich und zwei getrennt ausgewiesene Trainingsstarts erlauben keine präzise Verallgemeinerung über alle Karten oder Trainingsstarts.

## 5. Prüfung, Abgabe und Übergabe

Zwei unbeabsichtigte technische Testvorfälle sind separat erfasst; sie liefern keine Studien-Leistungsevidenz:

1. Bei den Punktzählungsregressionen liefen vor der vorgesehenen Freigabe **fünf vollständige bekannte Spiele** mit V14/default auf 900011 sowie **15 zusätzliche terminale Gegenproben**. Ein sechstes Spiel wurde unterbrochen; seine genaue Schrittzahl ist unbekannt. Diese Ausführungen gehören nicht zu den 24 beobachteten/normalen Entwicklungsläufen.
2. Ein zunächst unzureichend abgegrenzter Anker-Regressionstest startete mit temporärem synthetischem Schüler und winzigem Testdatensatz **13 vollständige Vorlaufspiele** auf 455000–455006; ein 14. wurde unterbrochen, seine Schrittzahl ist unbekannt. **Null RL-Updates**, keine Validierung und kein Abschlussbeleg. Der Test besitzt inzwischen eine sofort abbrechende Grenze zum echten Spieltrainer; Originalbelege bleiben erhalten.

Davon getrennt scheiterten im ersten Gesamttest zwei STOP-Aufräumtests an inzwischen vergangenen historischen Zeitgrenzen. Nur ihre Testzeitbasis wurde korrigiert; Produktionsdeadlines blieben erhalten. Danach bestanden **1.307 Tests und 126 Untertests**. Die Gesamttests enthalten selbst weitere Engine-Integrationstests. **Studienumfang: 1.872 tatsächliche Spielausführungen = 24 Entwicklung + 928 Lernen/Vorlauf/Validierung + 920 frische Diagnose.** Diese Zahl umfasst ausdrücklich nicht alle technischen Engine-Ausführungen der Tests und Vorfälle. Keine dieser Testzahlen misst eine Verbesserung des Agenten.

Der erste Abschlussaudit scheiterte an einem mit NumPy 2.5.4 inkompatiblen privaten NPY-Leser. Nur das temporäre Prüfwerkzeug wurde auf öffentliche Leser umgestellt; ursprünglicher Fehlbericht und Prüfskript sind erhalten. Daten und eingefrorene Quellen blieben unverändert; danach bestand der Audit.

Originalagent, beide V14-Gewichte und vorhandene ZIP bleiben geschützt und unverändert; es wurde für diesen Diagnosestand keine neue Abgabe freigegeben. V14-SHA256: `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; vorhandene ZIP: `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.

Die unabhängige Datenprüfung bestätigt sämtliche 920 eindeutigen Datensätze, 303 Schritte je Spiel, Punktezählung v2 und konsistente Ergebnisse. Alle elf Jobs wurden vollständig beendet. Der zusätzliche Abschlussabgleich bestätigt **236 Zahlen-/Intervallgleichheiten**, **266 unveränderte Quellen und 153 unveränderte Eingaben**, bytegleiche Kandidatenkopien und geschützte Dateien; keine abgefangenen Fehler in den Spiellogs. Er berechnet Zahlen erneut, rekonstruiert aber nicht nochmals die Engine-Punktzählung. [Abschlussabgleich](../experiments/analysis/a2_anchor_20261104/completion/root_crosscheck.json)

**Für Mahmoud:** V14 und vorhandene ZIP für die Professorenabgabe beibehalten; keine blinde weitere Trainingswelle. Der feste Anker ist als hilfreiche Stabilisierung gegenüber diesen Kontrollen belegt, aber kein freigegebener neuer Agent. Ein Fehlschlag der Auswahl mit Gewicht 0,1 widerlegt nicht alle Ankergewichte oder stabilisierten Lernverfahren. Nach der Abgabe wären gezielte Untersuchungen von Lehrerschwächen, Punktehalten, Energie und der Zuordnung von Lernerfolg zu tatsächlich ausgeführten Aktionen sinnvoll. Das sind Hypothesen und Vorschläge, keine bereits implementierten Änderungen oder gestarteten Versuche.
