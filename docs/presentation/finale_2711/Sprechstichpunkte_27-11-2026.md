# Sherlock · Stichpunkte für den 27. November

[Präsentations-PDF](Sherlock_Finale_27-11-2026.pdf) · [Editierbare Folien](Sherlock_Finale_27-11-2026.html)

**Planzeit 9:55 Minuten, noch keine gemeinsame Zeitprobe.** Moe übernimmt den Einstieg, die Spielanalyse und den Schluss (4:50). Mahmoud erklärt Aktionswahl, Training, den R3-Berater mit zwei Ansichten und den separaten V15-Vergleich (5:05). Die Zeiten enthalten Zeige- und Übergabepausen. In eigenen Worten sprechen.

| Folie | Wer | Dauer | Bis |
|---|---|---:|---:|
| 1 · Sherlock | Moe | 0:40 | 0:40 |
| 2 · Verborgene Punktefelder | Moe | 1:10 | 1:50 |
| 3 · Entscheidungsablauf | Moe | 1:10 | 3:00 |
| 4 · Der gesperrte Zug | Mahmoud | 1:25 | 4:25 |
| 5 · Lernen | Mahmoud | 1:15 | 5:40 |
| 6 · Ein Schüler, zwei Kartenansichten | Mahmoud | 1:05 | 6:45 |
| 7 · V15-Kandidat mit v4-Schüler | Mahmoud | 1:20 | 8:05 |
| 8 · Energie im ersten Match | Moe | 0:55 | 9:00 |
| 9 · 118 Siege gegen Solution | Moe | 0:55 | 9:55 |

### 1 · Moe

- Im Kurs-Battle belegten wir mit Sherlock Platz drei. Sherlock muss verborgene Punktefelder erst finden und sie dann lange genug halten.
- Am einfachen Beispiel zeigen, wie Sherlock aus Punkten auf Felder schließt. Danach erklärt Mahmoud an einem echten Zug, wie V14 entscheidet und wann ein zusätzliches Netz die Bewegung ändern darf. Am Ende lösen wir die Frage vom Titel auf. Gegen wen hilft das auf neuen Karten wirklich?

### 2 · Moe

- Auf die zwei bekannten Felder zeigen. Vier **verschiedene** besetzte Felder, drei Punkte Zuwachs. Zwei Punkte sind erklärt. Wo steckt der dritte? Kurz Zeit zum Mitdenken lassen.
- Eins der beiden offenen Felder bringt einen Punkt. Welche Seite es ist, kann eine spätere Beobachtung klären. Sherlock merkt sich bestätigte Punktefelder über die Matches hinweg.
- Bekannte Felder besetzen, Kandidaten testen, freie Einheiten erkunden lassen. Der begehbare Weg fließt in die Zuteilung ein.

### 3 · Moe

- Eine Einheit durch die vier Stationen verfolgen. Sherlock weist ihr ein Ziel zu. Ihre Energie und die Richtung zum Ziel werden zu Zahlen.
- Jedes Netz sieht dieselben 79 Zahlen der Einheit und bewertet sechs mögliche Aktionen. Für jeden Zug mitteln wir die 36 Werte.
- Vor der Auswahl steht fest, welche Aktionen gesperrt sind. Auch anschließend kann eine Weg- oder Schussregel eingreifen. **Übergabe an Mahmoud:** „Was passiert, wenn der beste Netzvorschlag direkt in einen Asteroiden führt?“

### 4 · Mahmoud

- „Runter“ und „Rechts“ in der Tabelle zeigen. 53,8 für „Runter“ ist der höchste Wert. Der Asteroid sperrt diese Richtung. 52,2 ist der höchste verbleibende Wert. Hier geht die Einheit nach rechts.
- Q steht für die geschätzte künftige Belohnung. Für jede Aktion zählt ihr über die 36 Netze gemittelter Zahlenwert. Die Zahl 52,2 ist keine Prozentangabe.
- Die Maske schließt auch einen Zug über den Kartenrand aus. Ein eigener Schuss braucht in der Netzauswahl ein sichtbares, erreichbares Ziel und genügend Energie. Nachgelagerte Spezialregeln prüfen andere Fälle gesondert.

### 5 · Mahmoud

- Im Training speichert jede Einheit Erfahrungen. Beispiel: Sie zieht auf ein Punktefeld, erhält ein Signal und sieht danach die neue Situation. Aus zufällig gezogenen Beispielen werden später ihre Aktionswerte korrigiert.
- Bei Double DQN wählt das lernende Netz die nächste erlaubte Aktion für das Lernziel. Ein zweites, zeitweise festes Netz schätzt ihren Wert. So hängt das Lernziel weniger direkt von der gerade geänderten Bewertung ab.
- Zu jedem der 18 Grundnetze gehört eine über 5.500 Spiele weitertrainierte Fassung. Das ergibt 36 unterschiedliche Gewichtsstände. Im Turnier wächst das Kartenwissen weiter, die Gewichte sind eingefroren.

### 6 · Mahmoud

- „V14 hat seinen Befehl schon gewählt. Jetzt schaut sich ein zusätzliches Netz dieselbe Stellung zweimal an. Einmal normal, einmal mit vertauschter x- und y-Achse. Was vorher rechts war, zeigt in der zweiten Ansicht nach unten.“
- „Wir übersetzen die Bewertungen zurück, damit rechts mit rechts gemittelt wird. Dann sperren wir unzulässige Aktionen. Will V14 schießen, bleiben Schuss und Ziel erhalten. Wollte V14 nach rechts und empfiehlt der Schüler einen erlaubten Zug nach oben mit 80 Prozent, spielen wir oben. Bei 60 Prozent bleibt es bei rechts.“ Das Zahlenbeispiel ist konstruiert. Die Schwelle beträgt 70 Prozent.
- „Die Gewichte sind in beiden Ansichten identisch. Gelernt hat der Schüler auf 152 Karten aus den Befehlen des Kaggle-Lehrers und dessen Bewertungen alternativer Richtungen.“
- Überleitung. „Bei unserem zweiten Kandidaten darf der Schüler auch das Schussziel wählen.“

### 7 · Mahmoud

- „Unser separater V15-Kandidat verwendet den Schüler v4. Dieser Schüler wurde ebenfalls anhand der Befehle des Kaggle-Agenten trainiert. Bei diesem Ansatz wählen wir für jede Einheit aus, wer den **ganzen** Befehl gibt. Dazu gehört bei einem Schuss auch das Zielfeld.“
- Links zeigen. „Sieht die Einheit einen Gegner höchstens fünf Felder entfernt, übernimmt der Schüler. Ist kein Gegner so nah, hält V14 die bekannten Punktefelder und steuert Einheiten dorthin. Für die übrigen Einheiten entscheidet wieder der Schüler.“
- Rechts zeigen. „Diesen Kandidaten haben wir auf einem eigenen Satz von 400 neuen Karten jeweils auf beiden Seiten gespielt. Direkt gegen V14 gewinnt der Hybrid 730 von 800 Spielen. Gegen Solution liegen beide fast gleichauf, hier hat V14 drei Siege mehr. Gegen den Kaggle-Agenten gewinnen beide zwölfmal. Das direkte Duell allein verrät uns also noch wenig über einen anderen Gegner.“
- **Übergabe an Moe.** „Woran liegt es, dass wir den Kaggle-Agenten so selten schlagen? Moe zeigt eine Analyse von V14s ersten Matches.“

### 8 · Moe

- „Hier seht ihr das erste Match von V14 gegen den Kaggle-Agenten. Dafür haben wir 30 Karten von beiden Seiten ausgewertet. Sherlock verliert im Durchschnitt 23 Einheiten. Dem Gegner geht im Mittel nur gut eine Einheit verloren.“
- „Vor dem letzten Zug hat Sherlock als Team noch rund 390 Energie, der Gegner über 3.300. Das ist wichtig, weil jeder Schuss Energie kostet. Unsere Vermutung ist, dass uns die Verluste daran hindern, bereits gefundene Punktefelder lange genug zu halten.“
- Bei Nachfrage ein echtes Beispiel. Auf Karte 7150000, Sherlock auf Seite 0, verliert V14 18 Einheiten und der Gegner zwei. Der Gegner schießt 25-mal, Sherlock neunmal.
- Überleitung. „Jetzt zurück zu R3. Was bringen die zwei Ansichten gegen neue Karten und verschiedene Gegner?“

### 9 · Moe

- „Gegen Solution gewinnt R3 mit zwei Ansichten 118 von 120 Spielen. V14 gewinnt auf genau denselben Karten 109. Das sind neun Siege mehr. Die obere Linie zeigt, dass der Vorsprung auch unter Berücksichtigung der Unterschiede zwischen den Karten über null bleibt.“
- „Direkt schlägt R3 unseren V14 in 100 von 120 Spielen. Gegen Kaggle dreht sich das Bild. R3 gewinnt kein Spiel, V14 gewinnt vier. Deshalb reicht die untere Linie für beide Gegner zusammen über die Null.“
- „Für unseren Zielgegner Solution ist der neue Ansatz also ein Fortschritt. Für einen allgemeinen Austausch reicht das Ergebnis noch nicht. Unsere bisherige Abgabe ist V14. Vielen Dank!“

## Stand und Quellen für das Team

- **Finale am 27.11.** Die Kursfolien „Reinforcement Learning_upload“ aus Moodle nennen drei benotete Präsentationen zu je 33 % (Folie 8), ein Finalturnier (Folie 10), die Bewertungsrubrik (Folie 11) und die Abgabe von Präsentation und Agenten-ZIP (Folie 51). Die Zehn-Minuten-Angabe auf Folie 10 steht im Abschnitt zum Zwischen-Battle. Für diese Probe planen wir nach Teamvorgabe rund zehn Minuten. Dauer, Frist und Benennung der Final-ZIP vor der tatsächlichen Finalabgabe mit der aktuellen Moodle-Angabe abgleichen. Diese Fassung zeigt den belegten Stand vom 15.11. und ist für eine erste Probe gedacht.
- **Rubrik für die Probe.** Die Frage vom Einstieg am Ende beantworten. Jede Übergabe an einem Spielzug oder Befund festmachen. Begriffe wie Q-Wert einmal in Alltagssprache erklären. Auf eine Zahl zeigen, sie einordnen und frei weitersprechen. Die eigene Entscheidung an der Schwelle für den Bewegungsberater erläutern.
- **Folien 2–5.** [Ablauf von V14](../../ENTSCHEIDUNGSABLAUF_V14_P.md), [Geprüfte Battle-Fassung mit Beispiel und Training](../Sherlock_Battle_06-11-2026.html), [Nachweis zur Netzarchitektur und Herkunft](../source/ENSEMBLE_BATTLE_0611_20261104.json).
- **Folie 6.** Die 36 V14-Netze bewerten sechs Aktionen. Der zusätzliche Schüler hat eine andere Architektur und ein anderes Lernziel. Seine Eingaben sind 16 räumliche Kartenebenen und 79 Merkmale je Einheit. Beim Spielen wählt das einzelne CNN die wahrscheinlichste zulässige Aktionsklasse. Die 70 % beschreiben seine eigene Bewertung dieser Klasse nach Maskierung, nicht die Gewinnchance der Partie. Nur wenn beide Befehle Bewegung oder Stillstand sind, der Schüler hinreichend sicher ist und sein Befehl die Ausführbarkeitsprüfung besteht, kann er V14s fertigen Befehl ersetzen. Matchanfänge sind ausgenommen. Der Lehrer ist nur beim Sammeln der Lernbeispiele dabei. Das Training umfasst 32 ursprüngliche V14-Karten und 120 weitere Karten mit tatsächlich gespielten Schülerverläufen, fünf Trainingsdurchgänge. Die Zusatzsignale sind die relativen Bewertungen der legalen Bewegungen auf geeigneten Stellungen. [Training und Vergleich](../../../experiments/analysis/movement_soft_20261115/TRAINING.md) · [Spielverläufe und Kartentrennung](../../../experiments/analysis/movement_dagger_20261115/SAMMLUNG.md) · [Entscheidungsweg](../../../scripts/selective_advice_agent.py) · [Prüfung des endgültigen Befehls](../../../scripts/combat_teacher_counterfactual.py).
- **Warum zwei Ansichten?** Es ist ein einziges R3-Netz mit denselben Gewichten. Die zweite Ansicht vertauscht die Kartenachsen. Dabei werden 16 Kartenebenen, Einheitspositionen und richtungsabhängige der 79 Merkmale passend transformiert. Rechts wird zu unten, oben zu links, Stillstand und SAP behalten ihre Aktionsklasse. Vor dem Mitteln werden die sechs rohen Aktionsbewertungen der zweiten Ansicht wieder den Originalrichtungen zugeordnet. Dann erst folgen Maske und die Wahrscheinlichkeitsschwelle von 70 %. R3 ändert ausschließlich zulässige Bewegungen oder Stillstand. Der SAP-Zielkopf greift bei dieser Bewegungsvariante nicht ein. Durch diesen Aufbau entsteht keine zusätzliche Trainingsrunde für die zweite Ansicht. [Umsetzung](../../../scripts/r3_diagonal.py) · [Versuchsplan](../../../experiments/analysis/movement_reflection_20261115/PLAN.md) · [Vorauswahl](../../../experiments/analysis/movement_reflection_20261115/VORAUSWAHL.md).
- **Folie 7.** Mahmouds gemischter v4-Hybrid wurde als V15-Kandidat geprüft. Er enthält den eigenen, in zwei DAgger-Runden weiter trainierten Imitationsschüler. V14 steuert den ersten Halter eines bestätigten Punktefelds bzw. Einheiten mit bestätigtem Punktziel. Ist ein sichtbarer Gegner höchstens fünf Felder in Chebyshev-Distanz entfernt, hat der Schüler Vorrang. Sein Befehl kann das Schussziel enthalten. Auf allen 400 Karten spielt jeder Kandidat beide Seiten (je 800 ganze Spiele). Direkt gewinnt v4 730/800, 91,25 % mit einem 95-%-Kartenintervall von 88,49 bis 94,00 %. Gegen Solution gewinnt er 764/800, V14 767/800. Gegen Kaggle 12/800 für beide. Die Hürde für einen Vorsprung gegen Kaggle wurde verfehlt. Den R3-Wert auf Folie 9 mit seiner dortigen V14-Referenz vergleichen, da dieser Vergleich andere Karten verwendet. [Gegnervergleich](../../../experiments/analysis/umbau_20261115/confirm/ERGEBNIS.md) · [Hybridentscheidung](../../../agents/sherlock/hybrid_agent.py).
- **Folie 8.** [Native Matchverläufe für die 30 Karten](../../../experiments/analysis/kaggle3_20261115/trace_v14_k3_30maps.csv). Mittelwerte über 60 erste Matches, einschließlich beider Seiten. Median bis zum ersten eigenen Punkt unter den Matches mit Punktgewinn: Schritt 39 (58 von 60) für Sherlock und 43 (60 von 60) für den Gegner. Der dokumentierte Zählfehler bei Einheitenverlusten nach einem Matchwechsel betrifft die hier gewählte erste Runde nicht.
- **Folie 9 und die beiden Linien.** Unabhängige Bestätigung mit 600 vollständig gespielten Partien. Auf 60 externen Karten (7286100–7286159) spielen R3 mit zwei Ansichten und V14 je beide Sitze gegen Solution und den nativen Kaggle-Agenten. Gegen Solution gewinnt R3 118/120, V14 109/120. Zehn vormals verlorene Spiele werden gewonnen, ein früherer Sieg geht verloren. Differenz +7,50 Prozentpunkte, gepaartes 95-%-Kartenintervall [+1,67; +15,00]. Gegen Kaggle 0/120 zu 4/120. Über beide externen Gegner sind das 118/240 zu 113/240, also +2,08 Prozentpunkte mit einem Intervall von −2,08 bis +6,25. Der Vorteil gegen Solution und die Unsicherheit über beide Gegner gehören zusammen. Die vier Kaggle-Siege der Referenz genügen nicht, um allein daraus auf einen gesicherten Nachteil gegen Kaggle zu schließen.
- **Direktvergleich und Abgabe.** Auf 60 getrennten Karten (7286200–7286259) gewinnt R3 mit zwei Ansichten direkt gegen V14 100/120, entsprechend 83,33 %, mit 95-%-Kartenintervall von 73,33 bis 91,67 %. Die Intervalle verwenden 10.000 Ziehungen ganzer Karten. Beide Sitze bleiben zusammen, bei der gemeinsamen Auswertung auch beide Gegner. Für eine allgemeine Freigabe musste auch die Untergrenze über beide externen Gegner positiv sein. Sie liegt bei −2,08 Prozentpunkten. Die bestätigten Stärken lassen sich benennen; eine Übernahme als neue Turnierversion wurde dadurch nicht begründet. [Geprüfter Bestätigungsbericht mit Rohdaten-Prüfsummen](../../../experiments/analysis/movement_reflection_20261115/confirm/assessment.json).
- **Bei Nachfrage zum ursprünglichen R3.** Mit genau einem Durchlauf je Stellung gewann der ursprüngliche R3 auf zwei anderen Solution-Sätzen zusammen 239/240 (V14 234/240). Die direkte erste Bestätigung ergab 88/120 gegen V14. Daraus lässt sich der Einfluss der zweiten Ansicht auf die Siegquote nicht durch Subtraktion bestimmen. Nur in der früheren Vorauswahl traten beide R3-Varianten und V14 auf denselben 16 Karten an. [R3 ohne zweite Ansicht](../../../experiments/analysis/movement_soft_20261115/BESTAETIGUNG.md) · [Zweiter Solution-Satz](../../../experiments/analysis/movement_soft_20261115/restart_route/FRISCHE_KARTEN.md) · [Gemeinsame Vorauswahl](../../../experiments/analysis/movement_reflection_20261115/VORAUSWAHL.md).
- **Optional nach dem Vortrag: drei echte V15-Kursspiele.** Die Zahlen sind Matchsiege innerhalb jeweils eines einzelnen Spiels. V15 gewinnt [2:1 gegen V14 auf Karte 7171000](replays/7171000/partie.html) und [3:0 gegen Solution auf Karte 7171001](replays/7171001/partie.html). [Gegen Kaggle auf Karte 7171002 verliert V15 mit 0:3](replays/7171002/partie.html). Die Aufnahmen veranschaulichen V15s Spielweise. Die Vergleiche auf 400 Karten (Folie 7) und der unabhängige R3-Test (Folie 9) sind eigene Messungen. [Übersicht und Originalaufnahmen](replays/README.md).
- **Szene zum Vorzeigen.** Im ersten Replay **„Zur Vortragsszene“** anklicken. Match 1, Zug 35: „Vor dem Zug steht es 1:1. Dieses Feld bei (0, 9) bringt V15 einen Punkt. V14 wertet in diesem Zug kein Feld, also geht V15 mit 2:1 in Führung.“ Mit „−1“ und „+1“ lässt sich der Wechsel zeigen. Die Karte im Replay ist die Schiedsrichtersicht; im Spiel hat jeder Agent nur seine eigenen sichtbaren Informationen. Die Szene passt zur Punktevergabe aus Folie 2 und bleibt außerhalb der geplanten 9:55.
- **Für die letzte Probe.** Gemeinsam mit Uhr sprechen und Übergaben üben. Vor dem Finale den tatsächlichen Abgabeagenten, Datenstand, Moodle-Frist und Dateinamen kontrollieren. Wenn sich der Agent ändert, müssen sein Entscheidungsweg und die Messwerte auf den Folien zum selben Stand gehören.

**Bearbeiten und exportieren.** Die HTML-Quelle ist eigenständig. Bei Änderungen im Browser öffnen und als PDF drucken, mit Hintergrundgrafiken, ohne Browser-Kopf- und Fußzeilen, bei 100 % und mit der im Dokument definierten Seitengröße (16:9). Ergebnis vor dem Vortrag im Vollbild prüfen.
