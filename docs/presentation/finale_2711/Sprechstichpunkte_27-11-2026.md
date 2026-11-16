# Sherlock · Stichpunkte für den 27. November

[Präsentations-PDF](Sherlock_Finale_27-11-2026.pdf) · [Editierbare Folien](Sherlock_Finale_27-11-2026.html)

**Planzeit 9:55 Minuten, noch keine gemeinsame Zeitprobe.** Moe übernimmt den Einstieg, die Spielanalyse und den Schluss (4:50). Mahmoud erklärt Aktionswahl, Training, den R3-Bewegungsberater und die Befehlswahl des V15-Kandidaten (5:05). Die Zeiten enthalten Zeige- und Übergabepausen. In eigenen Worten sprechen.

| Folie | Wer | Dauer | Bis |
|---|---|---:|---:|
| 1 · Sherlock | Moe | 0:40 | 0:40 |
| 2 · Verborgene Punktefelder | Moe | 1:10 | 1:50 |
| 3 · Entscheidungsablauf | Moe | 1:10 | 3:00 |
| 4 · Der gesperrte Zug | Mahmoud | 1:25 | 4:25 |
| 5 · Lernen | Mahmoud | 1:15 | 5:40 |
| 6 · Wann R3 die Bewegung ändert | Mahmoud | 1:05 | 6:45 |
| 7 · V15-Kandidat mit v4-Schüler | Mahmoud | 1:20 | 8:05 |
| 8 · Energie im ersten Match | Moe | 0:55 | 9:00 |
| 9 · 98,5 % gegen Solution | Moe | 0:55 | 9:55 |

### 1 · Moe

- „Beim letzten Kurs-Battle wurde unser V14 Dritter. Heute spielt sein Nachfolger Original-R3. Wir zeigen euch an einem Zug, wann der Berater entscheidet.“ Sherlock muss verborgene Punktefelder erst finden und sie dann lange genug halten.
- Am einfachen Beispiel zeigen, wie Sherlock aus Punkten auf Felder schließt. Danach erklärt Mahmoud an einem echten Zug, wie V14 entscheidet und wann ein zusätzliches Netz die Bewegung ändern darf. Am Schluss vergleichen wir, wie oft die drei Versionen auf denselben Karten gewinnen.

### 2 · Moe

- Auf die zwei bekannten Felder zeigen. Vier **verschiedene** besetzte Felder, drei Punkte Zuwachs. Zwei Punkte sind erklärt. Wo steckt der dritte? Kurz Zeit zum Mitdenken lassen.
- Eins der beiden offenen Felder bringt einen Punkt. Welche Seite es ist, kann eine spätere Beobachtung klären. Sherlock merkt sich bestätigte Punktefelder über die Matches hinweg.
- Bekannte Felder besetzen, Kandidaten testen, freie Einheiten erkunden lassen. Der begehbare Weg fließt in die Zuteilung ein.

### 3 · Moe

- Eine Einheit durch die vier Stationen verfolgen. Sherlock weist ihr ein Ziel zu. Ihre Energie und die Richtung zum Ziel werden zu Zahlen.
- Jedes Netz sieht dieselben 79 Zahlen der Einheit und bewertet sechs mögliche Aktionen. Für jeden Zug mitteln wir die 36 Werte.
- Vor der Auswahl steht fest, welche Aktionen gesperrt sind. Auch anschließend kann eine Weg- oder Schussregel eingreifen. Ausgegeben werden pro Einheit eine Aktion und zwei Zahlen für das Schussziel relativ zur Einheit. **Übergabe an Mahmoud:** „Was passiert, wenn der beste Netzvorschlag direkt in einen Asteroiden führt?“

### 4 · Mahmoud

- „Das ist Zug 45 aus einem echten Spiel von V14. Einheit 6 steht bei (12, 4). Die 36 Netze bewerten jede der sechs Aktionen. Q ist ihre Schätzung: Welche Aktion bringt uns langfristig mehr Belohnung?“
- „Im Durchschnitt liegt runter mit 11,46 vorn. Direkt darunter liegt ein Asteroid. Nur diese Richtung fällt weg. Rechts hat mit 11,08 den höchsten erlaubten Wert. Darum zieht die Einheit nach rechts.“ Auf die beiden Tabellenzeilen zeigen.
- „Was passiert nach der Auswahl? In diesem Zug spielt Sherlock genau den gewählten Befehl. In anderen Situationen kann eine Regel danach noch eingreifen, etwa einen unnötigen zweiten Schuss streichen. Jetzt schauen wir uns an, wie die Netze zu ihren Bewertungen kommen.“

### 5 · Mahmoud

- Im Training speichert jede Einheit Erfahrungen. Beispiel: Sie zieht auf ein Punktefeld, erhält ein Signal und sieht danach die neue Situation. Aus zufällig gezogenen Beispielen werden später ihre Aktionswerte korrigiert.
- Bei Double DQN wählt das lernende Netz die nächste erlaubte Aktion für das Lernziel. Ein zweites, zeitweise festes Netz schätzt ihren Wert. So hängt das Lernziel weniger direkt von der gerade geänderten Bewertung ab.
- Zu jedem der 18 Grundnetze gehört eine über 5.500 Spiele weitertrainierte Fassung. Das ergibt 36 unterschiedliche Gewichtsstände. Im Turnier wächst das Kartenwissen weiter, die Gewichte sind eingefroren.

### 6 · Mahmoud

- „V14 hat für jede Einheit schon entschieden. Zu seinen 36 Netzen kommt genau ein Netz hinzu. Dieser Schüler sieht die Karte in 16 Ebenen und dieselben 79 Merkmale der Einheit. Er bewertet die sechs Aktionen. Ungültige Vorschläge fallen heraus.“
- „Schießt V14, bleiben Schuss und Ziel erhalten. Wollte V14 nach rechts und empfiehlt der Schüler eine zulässige Bewegung nach oben mit 80 Prozent, spielen wir oben. Bei 60 Prozent bleibt es bei rechts.“ Die 70-Prozent-Schwelle bezieht sich auf die maskierte Aktionsempfehlung.
- „Beim ursprünglichen R3 sieht das Netz die Karte einmal. Bei der Variante rechnen wir mit denselben Gewichten zweimal, tauschen x und y, übersetzen die Richtungen zurück und mitteln die Bewertungen. Ein zweites Netz brauchen wir dafür nicht.“
- „Unser anderer Schüler, v4, kann auch das Schussziel übernehmen.“

### 7 · Mahmoud

- „Zum Vergleich zeigen wir kurz den anderen Kandidaten. V15 kombiniert die 36 V14-Netze mit dem v4-Schüler. Wir entscheiden für jede Einheit, wer den ganzen Befehl vorgibt. Der Schüler wurde an Beispielen des Kaggle-Agenten und später auch auf den eigenen Spielverläufen trainiert.“
- „Rechts steht ein einzelnes Schiff auf einem sicheren Punktefeld. Ist der nächste sichtbare Gegner sieben Felder entfernt, entscheidet V14. Rückt der Gegner auf drei Felder heran, entscheidet v4, auch über einen möglichen Schuss. Die Grenze liegt bei fünf Feldern, auch diagonal. Ohne nahen Gegner darf v4 die Schiffe steuern, die gerade kein bestätigtes Punktefeld halten oder ansteuern.“
- „Direkt gegen V14 gewinnt dieser Hybrid 730 von 800 Partien. Was das gegen ganz andere Gegner bedeutet, schauen wir uns zum Schluss an.“
- **Übergabe an Moe.** „Zuerst zeigt Moe, warum der Kaggle-Agent für uns so schwierig ist.“

### 8 · Moe

- „Hier seht ihr das erste Match von V14 gegen den Kaggle-Agenten. Dafür haben wir 30 Karten von beiden Seiten ausgewertet. Sherlock verliert im Durchschnitt 23 Einheiten. Dem Gegner geht im Mittel nur gut eine Einheit verloren.“
- „Vor dem letzten Zug hat Sherlock als Team noch rund 390 Energie, der Gegner über 3.300. Das ist wichtig, weil jeder Schuss Energie kostet. Unsere Vermutung ist, dass uns die Verluste daran hindern, bereits gefundene Punktefelder lange genug zu halten.“
- Bei Nachfrage ein echtes Beispiel. Auf Karte 7150000, Sherlock auf Seite 0, verliert V14 18 Einheiten und der Gegner zwei. Der Gegner schießt 25-mal, Sherlock neunmal.
- Überleitung. „Zum Schluss vergleichen wir die drei Versionen auf einem gemeinsamen Kartensatz. Bei R3 prüfen wir zusätzlich, ob eine zweite Ansicht mehr Spiele gewinnt.“

### 9 · Moe

- Auf die linke Tabelle zeigen. „Auf denselben 400 Karten gewinnt der ursprüngliche R3 788 von 800 Spielen gegen Solution, V14 767. Das sind 21 zusätzliche Siege gegen Solution. Gegen den Kaggle-Agenten bleiben beide bei 12 von 800. Im separaten direkten Duell gewann R3 88 von 120 Spielen gegen V14.“
- Rechts zeigen. „Bei den ersten 100 dieser Karten haben wir eine zweite Ansicht getestet. Mit einer Ansicht gewinnt R3 192 Spiele, mit zwei Ansichten 191 von je 200. Auf diesen Karten bleibt ein Vorteil der zweiten Ansicht offen.“
- „Für das Finale spielt Original-R3 mit einer Kartenansicht. Vielen Dank! Habt ihr Fragen?“

## Stand und Quellen für das Team

- **Finale am 27.11.** Die Kursfolien „Reinforcement Learning_upload“ aus Moodle nennen drei benotete Präsentationen zu je 33 % (Folie 8), ein Finalturnier (Folie 10), die Bewertungsrubrik (Folie 11) und die Abgabe von Präsentation und Agenten-ZIP (Folie 51). Die Zehn-Minuten-Angabe auf Folie 10 steht im Abschnitt zum Zwischen-Battle. Für diese Probe planen wir nach Teamvorgabe rund zehn Minuten. Dauer, Frist und Benennung der Final-ZIP vor der tatsächlichen Finalabgabe mit der aktuellen Moodle-Angabe abgleichen. Die Ergebnisfolie beruht auf den abgeschlossenen Berichten zu den gemeinsamen Karten und ist für die gemeinsame Probe gedacht.
- **Rubrik für die Probe.** Die Frage vom Einstieg am Ende beantworten. Jede Übergabe an einem Spielzug oder Befund festmachen. Begriffe wie Q-Wert einmal in Alltagssprache erklären. Auf eine Zahl zeigen, sie einordnen und frei weitersprechen. Die eigene Entscheidung an der Schwelle für den Bewegungsberater erläutern.
- **Folien 2–5.** [Ablauf von V14](../../ENTSCHEIDUNGSABLAUF_V14_P.md), [Geprüfte Battle-Fassung mit Beispiel und Training](../Sherlock_Battle_06-11-2026.html), [Nachweis zur Netzarchitektur und Herkunft](../source/ENSEMBLE_BATTLE_0611_20261104.json).
- **Spielszene auf Folie 4.** V14, Karte 4242, Spieler 0, erstes Match, Schritt 45, Einheit 6 bei (12, 4). Das öffentlich sichtbare Feld (12, 5) ist ein Asteroid. Nur die Richtung dorthin wird gesperrt. Die mittleren Q-Werte sind auf zwei Nachkommastellen gerundet. Die beste erlaubte Aktion führte zum Weltbefehl `[2, 0, 0]`. Die technischen Daten gleichen alle 303 Befehlsmatrizen des untersuchten Sitzes mit der Kursaufnahme ab. [Originalwerte, Maske und Weltbefehl](../../../experiments/analysis/v14_course_trace_20261116/folienbeispiel.json).
- **Folie 6.** Die 36 V14-Netze bewerten sechs Aktionen. Der zusätzliche Schüler hat eine andere Architektur und ein anderes Lernziel. Seine Eingaben sind 16 räumliche Kartenebenen und 79 Merkmale je Einheit. Beim Spielen wählt das einzelne CNN die wahrscheinlichste zulässige Aktionsklasse. Die 70 % beschreiben seine eigene Bewertung dieser Klasse nach Maskierung, nicht die Gewinnchance der Partie. Nur wenn beide Befehle Bewegung oder Stillstand sind, der Schüler hinreichend sicher ist und sein Befehl die Ausführbarkeitsprüfung besteht, kann er V14s fertigen Befehl ersetzen. Matchanfänge sind ausgenommen. Der Lehrer ist nur beim Sammeln der Lernbeispiele dabei. Das Training umfasst 32 ursprüngliche V14-Karten und 120 weitere Karten mit tatsächlich gespielten Schülerverläufen, fünf Trainingsdurchgänge. Die Zusatzsignale sind die relativen Bewertungen der legalen Bewegungen auf geeigneten Stellungen. [Training und Vergleich](../../../experiments/analysis/movement_soft_20261115/TRAINING.md) · [Spielverläufe und Kartentrennung](../../../experiments/analysis/movement_dagger_20261115/SAMMLUNG.md) · [Entscheidungsweg](../../../scripts/selective_advice_agent.py) · [Prüfung des endgültigen Befehls](../../../scripts/combat_teacher_counterfactual.py).
- **Warum zwei Ansichten?** Es ist ein einziges R3-Netz mit denselben Gewichten. Die zweite Ansicht vertauscht die Kartenachsen. Dabei werden 16 Kartenebenen, Einheitspositionen und richtungsabhängige der 79 Merkmale passend transformiert. Rechts wird zu unten, oben zu links, Stillstand und SAP behalten ihre Aktionsklasse. Vor dem Mitteln werden die sechs rohen Aktionsbewertungen der zweiten Ansicht wieder den Originalrichtungen zugeordnet. Dann erst folgen Maske und die Wahrscheinlichkeitsschwelle von 70 %. R3 ändert ausschließlich zulässige Bewegungen oder Stillstand. Der SAP-Zielkopf greift bei dieser Bewegungsvariante nicht ein. Durch diesen Aufbau entsteht keine zusätzliche Trainingsrunde für die zweite Ansicht. [Umsetzung](../../../scripts/r3_diagonal.py) · [Versuchsplan](../../../experiments/analysis/movement_reflection_20261115/PLAN.md) · [Vorauswahl](../../../experiments/analysis/movement_reflection_20261115/VORAUSWAHL.md).
- **Folie 7.** Mahmouds gemischter v4-Hybrid wurde als V15-Kandidat geprüft. Er enthält den eigenen, in zwei DAgger-Runden weiter trainierten Imitationsschüler. V14 steuert den ersten Halter eines bestätigten Punktefelds bzw. Einheiten mit bestätigtem Punktziel. Ist ein sichtbarer Gegner höchstens fünf Felder in Chebyshev-Distanz entfernt, hat der Schüler Vorrang. Sein Befehl kann das Schussziel enthalten. Auf allen 400 Karten spielt jeder Kandidat beide Seiten (je 800 ganze Spiele). Direkt gewinnt v4 730/800, 91,25 % mit einem 95-%-Kartenintervall von 88,49 bis 94,00 %. Gegen Solution gewinnt er 764/800, V14 767/800. Gegen Kaggle 12/800 für beide. Die Hürde für einen Vorsprung gegen Kaggle wurde verfehlt. Folie 9 vergleicht V14, Original-R3 und V15 extern auf denselben 400 Karten. Das hier besprochene direkte Duell von V15 und V14 ist eine andere Paarung. [Gegnervergleich](../../../experiments/analysis/umbau_20261115/confirm/ERGEBNIS.md) · [Hybridentscheidung](../../../agents/sherlock/hybrid_agent.py).
- **Folie 8.** [Native Matchverläufe für die 30 Karten](../../../experiments/analysis/kaggle3_20261115/trace_v14_k3_30maps.csv). Mittelwerte über 60 erste Matches, einschließlich beider Seiten. Median bis zum ersten eigenen Punkt unter den Matches mit Punktgewinn: Schritt 39 (58 von 60) für Sherlock und 43 (60 von 60) für den Gegner. Der dokumentierte Zählfehler bei Einheitenverlusten nach einem Matchwechsel betrifft die hier gewählte erste Runde nicht.
- **Folie 9 links.** Original-R3 (eine Ansicht), V14 und V15 auf Karten 7158000–7158399, zwei Startseiten. Die Referenzen V14 und V15 waren bereits publiziert. Ergebnisse sind Siege in ganzen Spielen. Die gepaarte Differenz von Original-R3 gegen V14 zusammen über beide externen Gegner hat ein 95-%-Kartenintervall von +0,25 bis +2,44 Prozentpunkten. Gegen Solution beträgt das Intervall für die Differenz Original-R3 minus V14 +1,00 bis +4,38 Prozentpunkte. Von den 800 Solution-Spielen hat Original-R3 12 verloren. Die drei Agenten traten jeweils gegen Solution oder Kaggle an. [400-Karten-Auswertung](../../../experiments/analysis/movement_soft_20261115/shared_400/measured/assessment.json).
- **Folie 9 rechts.** Das erste Viertel des 400er-Satzes wurde vorab für Solution festgelegt. Die zusätzlichen 200 Ausführungen betreffen nur den Diagonal-R3. Seine 191 Siege stehen den 192 Siegen des ursprünglichen R3 aus demselben 200er-Teilsatz gegenüber. Die 200 Original-R3-Spiele dürfen nicht noch einmal zur Gesamtstichprobe addiert werden. Beide Sitze jeder Karte bleiben beim Bootstrap zusammen. [Teilmenge mit beiden Ansichten](../../../experiments/analysis/movement_reflection_20261115/solution_quarter/diagonal/assessment.json).
- **Frühere Tests bei Nachfragen.** Diagonal-R3 gewann 118/120 gegen Solution (V14 109/120), 0/120 gegen Kaggle (V14 4/120) und 100/120 direkt gegen V14. Original-R3 gewann auf einem anderen Satz 119/120 gegen Solution (V14 115/120), 0/120 gegen Kaggle (V14 0/120) und 88/120 direkt gegen V14. Der direkte Vergleich der Ansichten auf denselben Karten steht rechts auf Folie 9. [Diagonal-R3](../../../experiments/analysis/movement_reflection_20261115/BESTAETIGUNG.md) · [Original-R3](../../../experiments/analysis/movement_soft_20261115/BESTAETIGUNG.md).
- **Optional nach dem Vortrag: drei echte V15-Kursspiele.** Die Zahlen sind Matchsiege innerhalb jeweils eines einzelnen Spiels. V15 gewinnt [2:1 gegen V14 auf Karte 7171000](replays/7171000/partie.html) und [3:0 gegen Solution auf Karte 7171001](replays/7171001/partie.html). [Gegen Kaggle auf Karte 7171002 verliert V15 mit 0:3](replays/7171002/partie.html). Die Aufnahmen veranschaulichen V15s Spielweise. Das direkte V15-Duell auf Folie 7 und die externen Vergleiche auf Folie 9 sind jeweils eigene Messungen. [Übersicht und Originalaufnahmen](replays/README.md).
- **Szene zum Vorzeigen.** Im ersten Replay **„Zur Vortragsszene“** anklicken. Match 1, Zug 35: „Vor dem Zug steht es 1:1. Dieses Feld bei (0, 9) bringt V15 einen Punkt. V14 wertet in diesem Zug kein Feld, also geht V15 mit 2:1 in Führung.“ Mit „−1“ und „+1“ lässt sich der Wechsel zeigen. Die Karte im Replay ist die Schiedsrichtersicht; im Spiel hat jeder Agent nur seine eigenen sichtbaren Informationen. Die Szene passt zur Punktevergabe aus Folie 2 und bleibt außerhalb der geplanten 9:55.
- **Festgelegte Finaleversion.** Original-R3 übernimmt mit einer Kartenansicht ausschließlich zulässige Bewegung oder Stillstand. V14 lieferte die Kursabgabe am 6. November. V15 ist der separat verglichene Hybrid. [Freigabe für das Finale](../../../experiments/releases/20261116_r3_finale/README.md).
- **Für die letzte Probe.** Gemeinsam mit Uhr sprechen und Übergaben üben. Vor dem Finale den tatsächlichen Abgabeagenten, Datenstand, Moodle-Frist und Dateinamen kontrollieren. Für die Probe auf Folie 9 nur die zwei wichtigsten Werte vortragen. Die Intervalle und die übrigen Gegnerzahlen stehen für Nachfragen bereit.

**Bearbeiten und exportieren.** Die HTML-Quelle ist eigenständig. Bei Änderungen im Browser öffnen und als PDF drucken, mit Hintergrundgrafiken, ohne Browser-Kopf- und Fußzeilen, bei 100 % und mit der im Dokument definierten Seitengröße (16:9). Ergebnis vor dem Vortrag im Vollbild prüfen.
