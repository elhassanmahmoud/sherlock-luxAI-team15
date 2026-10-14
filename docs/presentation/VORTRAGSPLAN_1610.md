# Sherlock: Vortragsplan für den 16.10.2026

Stand: 14.10.2026. Auf Moayeds Wunsch wieder die ursprüngliche Fassung; sie ist die einzige aktuelle Präsentation im Repository. **11 Vortragsfolien + 2 ausgeblendete Reservefolien. Ziel 10:40 Minuten, maximal 12 Minuten Vortrag.** Die Zeiten sind Planwerte, keine gemessene Probe. Fragen im Anschluss sind nicht in den 10:40 enthalten; genaue Slotaufteilung vor Ort bestätigen.

## Dateien und Bearbeitung

- [Bearbeitbare PowerPoint mit Sprechernotizen](Sherlock_Review_16-10-2026.pptx)
- [PDF für Vortrag und Upload](Sherlock_Review_16-10-2026.pdf)
- [Gemeinsame Checkliste](CHECKLISTE_REVIEW_1610.md)
- [Folieninhalte, Notizen und Quellen als JSON](source/slides.json)
- [Bildquellen und fachliche Nachweise](source/QUELLEN.md)

Die PowerPoint ist die bearbeitbare Fassung: Text, Tabellen und Ergebnisdiagramm sind native Elemente; Spielbilder sind Screenshots. Nach Änderungen auch die PDF neu exportieren und prüfen. Die PDF enthält den Anhang als Seiten 12–13; beim normalen Vortrag auf Seite 11 enden. In PowerPoint sind die beiden Reservefolien ausgeblendet. Sprechernotizen sind Lern- und Probenhilfe, kein Text zum Ablesen. Auf dem tatsächlichen Präsentationsrechner Schriftbild und Notizenansicht vorab testen.

## Aufteilung und Zeitplan

**Moayed: 5:15 Minuten.** Aufgabe, Grundidee, Ergebnisse und Spielbeispiel. Keine Herleitung von Formeln; dafür verständlich erklären, was man auf den Bildern sieht und was die Zahlen aussagen.

**Mahmoud: 5:25 Minuten.** Merkmale, Netzarchitektur, Lernverfahren, Trainingsaufbau und technische nächste Schritte.

| Folie | Thema | Person | Dauer | Zeitfenster |
|---|---|---|---|---|
| 1 | Sherlock | Moayed | 0:30 | 0:00–0:30 |
| 2 | Spielidee und Ziel | Moayed | 1:00 | 0:30–1:30 |
| 3 | Unser Agent | Moayed | 0:55 | 1:30–2:25 |
| 4 | Merkmale und Gedächtnis | Mahmoud | 1:05 | 2:25–3:30 |
| 5 | Netzarchitektur und Ensemble | Mahmoud | 1:05 | 3:30–4:35 |
| 6 | Double DQN | Mahmoud | 1:15 | 4:35–5:50 |
| 7 | Training und Auswertung | Mahmoud | 1:05 | 5:50–6:55 |
| 8 | Benchmark-Ergebnisse | Moayed | 1:05 | 6:55–8:00 |
| 9 | Spielbeispiel | Moayed | 1:20 | 8:00–9:20 |
| 10 | Erkenntnisse und Ausblick | Mahmoud | 0:55 | 9:20–10:15 |
| 11 | Fazit und Fragen | Moayed | 0:25 | 10:15–10:40 |

Folie 3 enthält links den einfachen Überblick und rechts den Pseudocode beim Spielen. Moayed erklärt den Ablauf in eigenen Worten und liest nicht jede Codezeile vor. Folie 7 zeigt die wichtigsten Trainingsparameter direkt; Mahmoud erklärt insbesondere Exploration und den Unterschied zur Auswertung. Weitere Parameter bleiben auf Reservefolie 12. Die bisherigen 55 bzw. 65 Sekunden bleiben Planwerte und müssen gemeinsam geprobt werden.

Die Sprechzeiten schließen kurze Übergaben und das Zeigen auf die Bilder ein. Es gibt keine zusätzliche Live-Demo im Zeitbudget. Die Spielbilder auf Folie 9 funktionieren auch ohne Internet.

### Übergaben

- Nach Folie 3, Moayed: „Mahmoud erklärt jetzt, welche Informationen in die Netze eingehen und wie das Training funktioniert.“
- Nach Folie 7, Mahmoud: „Damit steht unser Agent fest. Moayed zeigt jetzt, wie er in der Auswertung abschneidet.“
- Nach Folie 9, Moayed: „Das war ein gelungenes Beispiel. Mahmoud ordnet jetzt die Grenzen und unsere nächsten Schritte ein.“
- Nach Folie 10, Mahmoud: „Damit zurück an Moayed für unser Fazit.“

### Wenn ihr auf genau zehn Minuten kommen müsst

40 Sekunden einsparen: Folie 4 um 10 Sekunden kürzen (das längere Inferenzbeispiel auslassen), Folie 5 um 10 Sekunden (Begriffstrennung in die Fragen verschieben), Folie 9 um 20 Sekunden (nur die beiden Zustände und die Kernaussage erklären). Keine Pflichtfolie streichen.

Kontrollpunkt: Folie 8 beginnt geplant bei 6:55. Wenn ihr dort erst bei 8:00 seid, die kurze Version von Folie 9 nehmen und Folie 10 auf die drei Kernaussagen begrenzen. Vortragsende spätestens bei 12:00; Anhang nur auf Nachfrage. Eine verspätete erste Probe ist ein Anlass zum Kürzen, nicht zum schnelleren Ablesen.

## Vorbereitung mit begrenzter Zeit

1. **15 Minuten gemeinsam:** Folien durchgehen. Mahmoud erklärt Moayed Belief, Q-Wert, Ensemble und Double DQN jeweils an einem Beispiel. Offene Fragen direkt klären.
2. **20 Minuten einzeln:** Eigene Folien in eigenen Worten erklären. Moayed braucht vor allem die Zahlen 60/60, 28/60 und „30 Karten auf beiden Seiten“ sowie die Bildgeschichte auf Folie 9. Mahmoud prüft die technischen Aussagen gegen den tatsächlichen Code.
3. **Zwei vollständige Proben mit Uhr:** Je rund elf Minuten plus kurze Rückmeldung. Erste Probe zur Verständlichkeit, zweite zur Zeit. Übergaben mitproben und auf der PDF nach Folie 11 stoppen.
4. **10 Minuten Abschluss:** Export auf dem Vortragsrechner öffnen, Schriftbild/Diagramm/Spielbilder prüfen, PDF lokal sichern, Upload erledigen.

Das ergibt ungefähr 70–80 Minuten konzentrierte Vorbereitung, verteilt auf kurze Blöcke. Mehr Zeit einplanen, falls die Grundbegriffe noch unklar sind. Frei sprechen; Stichworte dürfen beim Üben helfen, sollen aber beim Vortrag nicht abgelesen werden.

## Moayeds Begriffe in einfachen Worten

| Begriff | Eine brauchbare Erklärung |
|---|---|
| Agent | Das Programm, das aus seiner Beobachtung eine Spielaktion auswählt. |
| Belief / Gedächtnis | Eine regelbasierte Sammlung dessen, was der Agent gesehen oder daraus erschlossen hat. |
| Feature / Merkmal | Eine Zahl, die einen Teil der Situation beschreibt, z. B. Energie oder Richtung zum Ziel. |
| Q-Wert | Geschätzter langfristiger Nutzen einer Aktion; keine Gewinnwahrscheinlichkeit. |
| Ensemble | Mehrere trainierte Netze bewerten dieselben Aktionen; ihre Q-Werte werden gemittelt. |
| Double DQN | Beim Lernen wählt ein Netz die nächste Aktion und ein verzögertes Netz bewertet sie. |
| Dueling | Das Netz bildet Zustandswert und Aktionsvorteile getrennt und setzt sie zu Q-Werten zusammen. |
| Reward Shaping | Zusätzliche Belohnungssignale, damit der Agent auch zwischen Matchenden Rückmeldung bekommt. |
| Aktionsmaske | Schließt unzulässige Aktionen aus, bevor die beste verbleibende gewählt wird. |
| Training / Auswertung | Im Training ändern sich Gewichte; in der Auswertung bleiben sie fest. |

## Typische Fragen und ehrliche Antworten

- **Ist das alles Reinforcement Learning?** Nein. Die Aktionsbewertung wird gelernt. Gedächtnis, Merkmale, Zielzuweisung, Masken, Shaping und konkretes Sap-Ziel sind programmiert. Genau diese Kombination ist unser Ansatz.
- **Warum sechs Netze?** Einzelne DQN-Läufe schwanken. Wir kombinieren mehrere trainierte Bewertungen. Das Ensemble wurde anhand von Vergleichen ausgewählt; daraus folgt keine allgemeine Garantie, dass mehr Netze immer besser sind.
- **Sind 100 Prozent ein Beweis für einen perfekten Agenten?** Nein, nur das Ergebnis gegen default auf diesen 30 Karten und beiden Seiten. Gegen Solution_92 gewinnen wir 28 von 60 Spielen.
- **Sind es 60 unabhängige Karten?** Nein, 30 Karten mit zwei Seiten. Bei Vergleichen werden beide Seiten einer Karte zusammen ausgewertet.
- **Wie viel wurde trainiert?** Die sechs Basisläufe liefen je 3.000 Spiele: insgesamt 18.000 Laufspiele. Gewählte Checkpoints können früher liegen. Über alle 34 Projektmanifeste sind 99.000 Trainingsspiele dokumentiert; das ist eine andere, größere Bezugsmenge. Keine Validierungs- oder Testspiele als Training mitzählen.
- **Kann der Agent die gelben Felder im Bild einfach sehen?** Nicht vollständig. Die Folie zeigt die Zuschaueransicht des Replays. Der Agent bekommt eingeschränkte Beobachtungen und erschließt Punktefelder.
- **Gewinnt die höhere Gesamtpunktzahl automatisch das Spiel?** Entscheidend sind die gewonnenen Matches. Der Stand 374:11 auf Folie 9 ist nur ein Zwischenstand im ersten Match.
- **Was ist m1_early?** Ein untersuchter Kandidat für frühere Punktefeld-Inferenz. Noch nicht in den aktuellen Abgabe-Gewichten aktiviert; erst nach dem Review weiter bearbeiten.
- **Sind die Gewichte durch die Korrektur der Statistik besser geworden?** Nein. Punktezählung und Statistik wurden berichtigt; die Gewichte und die Spielentscheidungen blieben gleich.
- **Was habt ihr jeweils gemacht?** Nur die tatsächliche Arbeitsteilung nennen. Vortragsanteile sind keine Behauptung, dass beide gleich viel implementiert haben. Die bisherige Implementierung stammt überwiegend von Mahmoud; Moayed hat die gemeinsame Prüfung, Korrekturen und Vorbereitung mit Codex begleitet. Vor der Präsentation gemeinsam präzisieren, welche Beiträge jeder sicher erklären kann.

Wenn eine Rückfrage zu technisch wird, zuerst den Grundgedanken selbst erklären und dann an Mahmoud übergeben: „Die Grundidee ist … Die genaue Umsetzung im Training kann Mahmoud ergänzen.“ Nichts erfinden; beide sollen den Gesamtablauf verstehen.

## Sprechernotizen pro Folie

Dies sind Formulierungsvorschläge zum Üben. Nicht wortwörtlich auswendig lernen. Die Quellen beziehen sich auf Dateien im Repository; der Folienstand verändert keine dieser Quellen.

### Folie 1: Sherlock

**Moayed · 0:30**

Wir sind Mahmoud und Moayed, Team 15. Unser Agent heißt Sherlock. Er spielt Lux AI Season 3 und verbindet gelerntes Verhalten mit einem Gedächtnis für die Karte. Wir zeigen zuerst die Spielidee und den Ablauf, dann das Training und zum Schluss Ergebnisse und ein Beispiel. Unser Stand ist das Sechser-Ensemble old3_sym3.

### Folie 2: Spielidee und Ziel

**Moayed · 1:00**

Lux AI ist ein Strategiespiel auf einer Karte mit 24 mal 24 Feldern. Zwei Teams steuern jeweils bis zu 16 Einheiten. Im Kurs besteht ein Spiel aus drei Matches. Wer mehr Matches gewinnt, gewinnt das Spiel. Die Herausforderung ist, dass der Agent nicht die ganze Karte sieht und die Punktefelder zunächst unbekannt sind. Er muss erkunden, Energie sinnvoll einsetzen und geeignete Felder besetzen. Auf dem Bild ist Sherlock blau und der Gegner rot. Die gelben Markierungen gehören zu Relics und Punktefeldern. Wichtig: Das ist die vollständige Replay-Ansicht für uns Zuschauer. Der Agent bekommt diese vollständige Information nicht.

### Folie 3: Unser Agent

**Moayed · 0:55**

Links stehen die drei Grundideen, rechts derselbe Ablauf als Pseudocode. Bei jedem Spielschritt aktualisiert Sherlock zuerst sein Gedächtnis mit den neuen Beobachtungen. Für jede eigene aktive Einheit berechnet er dann 79 Merkmale. Sechs trainierte Netze bewerten ihre möglichen Aktionen; wir mitteln diese Bewertungen und wählen die beste erlaubte Aktion. Die Aktionen aller Einheiten gehen anschließend an das Spiel. Das Gedächtnis folgt programmierten Regeln, die Netzbewertungen wurden gelernt. Beim Spielen bleiben die Gewichte fest. Der Pseudocode zeigt den vereinfachten Hauptablauf. Mahmoud erklärt jetzt die Merkmale und das Training.

### Folie 4: Merkmale und Gedächtnis

**Mahmoud · 1:05**

Wir verwenden ein MLP mit 79 numerischen Merkmalen pro Einheit, keine vollständige Bildkarte. Die Merkmale beschreiben zum Beispiel Energie und Position, Umgebung, Ziele und Gegner. Das Belief speichert bekannte Relics, erkundete Bereiche und erschlossene Punktefelder. Vereinfachtes Beispiel: Eine einzige eigene Einheit steht auf einem noch unbekannten Kandidatenfeld und der Punktestand steigt um eins. Unter diesen Voraussetzungen lässt sich das Feld als Punktefeld erkennen. Bei mehreren Kandidaten braucht man weitere Beobachtungen. Außerdem verwenden wir die Kartensymmetrie. Davon zu unterscheiden sind kanonische Koordinaten: Beide Spielseiten werden aus vergleichbarer Perspektive beschrieben. Diese Regeln liefern Informationen an die gelernte Aktionsbewertung; sie ersetzen sie nicht.

### Folie 5: Netzarchitektur und Ensemble

**Mahmoud · 1:05**

Jedes Mitglied des Ensembles ist ein Dueling-Netz. Es bekommt 79 Merkmale. Der gemeinsame Teil besteht aus zwei voll verbundenen Schichten mit jeweils 256 Neuronen und ReLU. Danach gibt es einen Kopf für den Zustandswert und einen Kopf für die Vorteile der sechs Aktionen; beide haben eine Zwischenschicht mit 128 Neuronen. Daraus entstehen sechs Q-Werte. Beim Spielen mitteln wir die Q-Werte der sechs trainierten Netze und wählen dann die beste erlaubte Aktion. Die sechs Aktionen sind Stehenbleiben, vier Bewegungsrichtungen und Sap. Das konkrete Sap-Ziel wird heuristisch gewählt. Double DQN bezeichnet unser Lernverfahren, Dueling die Netzarchitektur und Ensemble die Kombination mehrerer trainierter Netze.

### Folie 6: Double DQN

**Mahmoud · 1:15**

Im Training sammeln wir Erfahrungen pro Einheit: Situation, Aktion, Belohnung und Folgesituation. Zufällige Mini-Batches aus dem Replay Buffer verringern die direkte Abhängigkeit aufeinanderfolgender Erfahrungen. Double DQN trennt die Wahl der nächsten Aktion von ihrer Bewertung: Das aktuelle Online-Netz wählt die beste erlaubte Folgeaktion, das verzögert aktualisierte Target-Netz bewertet genau diese Aktion. Aus Belohnung und diskontiertem Folgewert entsteht das Lernziel. Am Ende eines Übergangs entfällt der Folgewert. Das Online-Netz wird an dieses Ziel angepasst; das Target-Netz wird alle 500 Lernupdates kopiert. Im Training probiert der Agent mit abnehmender Wahrscheinlichkeit Aktionen aus. Zusätzlich zu Punkten und Matchsiegen gibt es Shaping-Signale, etwa für Annäherung, Erkundung und Energie. Deren Gestaltung ist eine Modellierungsentscheidung mit eigenen Grenzen.

### Folie 7: Training und Auswertung

**Mahmoud · 1:05**

Die sechs Basisläufe umfassen jeweils 3.000 Spiele, zusammen 18.000. Die ausgewählten Checkpoints können früher liegen. Zuerst trainieren wir gegen default, danach abwechselnd gegen default und Solution_92. Checkpoints wählen wir auf getrennten Validierungskarten. Rechts stehen die wichtigsten Einstellungen: Lernrate 0,0003, Gamma 0,99, Batchgröße 256 und 300.000 Einheitenübergänge im Buffer. Epsilon steuert die zufällige Exploration: Es sinkt über 60.000 Umgebungsschritte von eins auf 0,05. Das Target-Netz wird alle 500 Lernupdates aktualisiert. In der Auswertung spielen wir beide Seiten mit Epsilon null und festen Gewichten. Moayed zeigt jetzt die Ergebnisse.

### Folie 8: Benchmark-Ergebnisse

**Moayed · 1:05**

Hier sehen wir die Ergebnisse des aktuellen Agenten. Gegen default gewinnt Sherlock 60 von 60 Spielen. Gegen den stärkeren regelbasierten Gegner Solution_92 sind es 28 von 60, also ungefähr 47 Prozent. Pro Gegner wurden 30 Karten auf beiden Spielseiten gespielt. Damit sind es 60 Spiele, aber nicht 60 unabhängige Karten. Diese Zahlen wurden mit den unveränderten Gewichten erneut bestätigt. Wir sollten daraus nicht ableiten, dass Sherlock immer gegen default gewinnt: Das Ergebnis gilt für diese Stichprobe. Außerdem wurden die Karten im Projekt bereits mehrfach ausgewertet. Für eine unabhängige Schlussbewertung brauchen wir später neue, zurückgehaltene Karten. Insgesamt funktioniert unser Ansatz, aber gegen den stärkeren Gegner gibt es noch deutliches Verbesserungspotenzial.

### Folie 9: Spielbeispiel

**Moayed · 1:20**

Das sind zwei echte Bilder aus demselben Spiel gegen default. Sherlock ist blau, der Gegner rot. Links, bei Schritt 23, sind unsere Einheiten noch über die Karte verteilt und beide Teams haben null Punkte. Rechts, bei Schritt 90 im ersten Match, stehen viele blaue Einheiten im Bereich der gelb markierten Punktefelder. Der Zwischenstand ist 374 zu 11. Man sieht: Bewegung allein ist nicht das Ziel. Sobald geeignete Punktefelder bekannt sind, kann Stehenbleiben sinnvoll sein, weil ein besetztes Feld wiederholt Punkte bringt. Das Gedächtnis hilft dabei, einmal gewonnene Informationen weiterzuverwenden. Die Bilder zeigen die vollständige Zuschaueransicht, nicht den Wissensstand des Agenten. Dieses Spiel veranschaulicht einen gelungenen Ablauf; es beweist nicht, dass Sherlock in jedem Spiel so handelt. Die Niederlagen gegen Solution_92 gehören ebenfalls zu unserer Auswertung.

### Folie 10: Erkenntnisse und Ausblick

**Mahmoud · 0:55**

Unser Agent kombiniert gelernte Entscheidungen mit explizitem Wissen über das Spiel. Die bisherigen Versuche sprechen dafür, Gedächtnis und mehrere Netzbewertungen zu kombinieren. Weitertraining und Self-Play haben in den getesteten Varianten keinen klaren zusätzlichen Gewinn gebracht; das ist keine allgemeine Aussage gegen diese Verfahren. Eine Arbeitshypothese ist, dass bessere frühe Erkundung und frühere Inferenz im ersten Match helfen. Der Kandidat m1_early ist untersucht, aber noch nicht in der Abgabe aktiviert. Vor weiterem Training prüfen wir außerdem Reward und Einheitenübergänge. Für die nächste belastbare Bewertung wollen wir neue Testkarten zurückhalten. Der Präsentationsstand und seine Gewichte bleiben dabei fest.

### Folie 11: Fazit und Fragen

**Moayed · 0:25**

Sherlock verbindet ein Gedächtnis für die Karte mit sechs trainierten Netzen. Auf unserem Benchmark gewinnen wir alle 60 Spiele gegen default und 28 von 60 gegen Solution_92. Gegen den stärkeren Gegner bleibt also Verbesserungspotenzial. Als Nächstes wollen wir die frühe Erkundung verbessern und auf neuen Karten prüfen. Vielen Dank – welche Fragen habt ihr?

### Folie 12: Trainingsparameter

**Mahmoud · Reserve, nicht im Zeitplan**

Reservefolie, nicht Teil des geplanten Vortrags. Diese Werte sind in der Konfiguration des aktuellen Ensemble-Checkpoints und in den sechs Laufmanifesten hinterlegt. 5.000 beim Lernbeginn bezeichnet Einheitenübergänge im Buffer, keine Spiele und keine Umgebungsschritte. Ein Update alle zwei Umgebungsschritte, sobald genügend Übergänge vorliegen. Target-Kopie nach 500 Lernupdates. Die sechs Läufe werden jeweils 3.000 Spiele trainiert; die aus der Validierung ausgewählten Gewichte können von einem früheren Checkpoint stammen.

### Folie 13: Gelernt und programmiert

**Mahmoud · Reserve, nicht im Zeitplan**

Reservefolie. Q bezeichnet eine geschätzte zukünftige Belohnung für eine Aktion. Dueling: Q(s,a)=V(s)+A(s,a)−Mittelwert_a A(s,a). Double DQN trennt Auswahl und Bewertung beim Lernziel. Belief ist eine regelbasierte Zustandsrekonstruktion, kein Zugriff auf versteckte Engine-Daten. Die Punktezählung außerhalb des Agenten nutzt für die Auswertung zusätzliche Endzustandsinformationen; diese dürfen nicht als Agentenwissen dargestellt werden. Die Mess- und Statistikkorrekturen verbessern die Bewertung, nicht die Spielstärke.

## Vor dem Upload noch offen

- Mahmoud und Moayed haben Inhalt und Aufteilung gemeinsam bestätigt.
- Mindestens zwei gemeinsame Proben, zweite innerhalb von 10–12 Minuten.
- Moodle-Slot/Buchung bestätigt.
- PowerPoint/PDF auf dem verwendeten Rechner geöffnet und geprüft.
- PDF bis **Freitag, 16.10.2026, 08:00 Uhr** hochgeladen und die hochgeladene Datei nochmals geöffnet.

Der Upload wurde durch Codex nicht vorgenommen. Die Vortragszeit ist noch nicht durch eine menschliche Probe bestätigt. Agentenlogik und aktuelle Abgabe-Gewichte bleiben unverändert.
