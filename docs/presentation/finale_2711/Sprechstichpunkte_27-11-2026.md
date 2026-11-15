# Sherlock · Stichpunkte für den 27. November

[Präsentations-PDF](Sherlock_Finale_27-11-2026.pdf) · [Editierbare Folien](Sherlock_Finale_27-11-2026.html)

**Planzeit 9:55 Minuten, noch keine gemeinsame Zeitprobe.** Moe übernimmt den Einstieg, die Spielanalyse und den Schluss (4:50). Mahmoud erklärt Aktionswahl, Training, Bewegungsberatung und Gegnertest (5:05). Die Zeiten enthalten Zeige- und Übergabepausen. In eigenen Worten sprechen.

| Folie | Wer | Dauer | Bis |
|---|---|---:|---:|
| 1 · Sherlock | Moe | 0:40 | 0:40 |
| 2 · Verborgene Punktefelder | Moe | 1:10 | 1:50 |
| 3 · Entscheidungsablauf | Moe | 1:10 | 3:00 |
| 4 · Der gesperrte Zug | Mahmoud | 1:25 | 4:25 |
| 5 · Lernen | Mahmoud | 1:15 | 5:40 |
| 6 · Wann R3 den Zug ändert | Mahmoud | 1:05 | 6:45 |
| 7 · Turnier und lokale Gegner | Mahmoud | 1:20 | 8:05 |
| 8 · Energie im ersten Match | Moe | 1:10 | 9:15 |
| 9 · R3 auf frischen Karten | Moe | 0:40 | 9:55 |

### 1 · Moe

- Im Kurs-Battle belegten wir mit Sherlock Platz drei. Sherlock muss verborgene Punktefelder erst finden und sie dann lange genug halten.
- Am einfachen Beispiel zeigen, wie Sherlock aus Punkten auf Felder schließt. Danach erklärt Mahmoud an einem echten Zug, wie V14 entscheidet und wann unser neuer Bewegungsberater R3 eingreift. Am Ende zeigen wir, wie oft das gegen andere Agenten hilft.

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

- Links beginnen. „V14 hat hier schon alles gemacht, was wir gerade gezeigt haben. Der Befehl für diese Einheit steht also fest. Jetzt kommt ein einzelnes zusätzliches Netz dazu. Es sieht die Karte und die Merkmale der Einheit.“
- Den Pfeil verfolgen. „Nehmen wir an, V14 will nach rechts. Empfiehlt der Schüler mit 80 Prozent Sicherheit einen erlaubten Zug nach oben, spielen wir oben. Bei 60 Prozent bleibt es bei rechts. Hatte V14 bereits einen Schuss gewählt, führen wir ihn mit genau diesem Ziel aus.“ Das Beispiel ist zur Veranschaulichung konstruiert. 70 Prozent ist die Mindestschwelle für den Schülerzug.
- „Der Schüler lernt auf 152 Trainingskarten aus Zügen des Kaggle-Agenten. Er bekommt für geeignete Stellungen außerdem dessen Bewertungen der anderen Richtungen. So sieht er auch, wann zwei Züge für den Lehrer fast gleich gut sind.“
- Überleitung in einem Satz. „Woran messen wir, ob diese Änderung hilft? Dafür brauchen wir Gegner mit unterschiedlichen Stärken.“

### 7 · Mahmoud

- Links der echte Kurswettbewerb. Im Halbfinale verlor Sherlock dreimal gegen das Team, das später Zweiter wurde. Rechts zwei lokale Testgegner. V14 gewann auf denselben 100 Entwicklungskarten 188 der 200 Spiele gegen Solution und acht gegen den Kaggle-Drittplatzierten. Gezählt werden ganze Spiele aus drei Matches.
- „Wir haben auch ausprobiert, unserem Schüler für bestimmte Einheiten den ganzen Befehl zu überlassen. Dieser andere Hybrid hieß v3. Auf diesen Entwicklungskarten gewann er 194 gegen Solution und sechs gegen Kaggle. Auf der letzten Folie sehen wir den unabhängigen Test des Bewegungsberaters R3 auf neuen Karten.“
- **Übergabe an Moe.** „Warum ist der Kaggle-Agent so schwierig für Sherlock? Das sieht man schon im ersten Match.“

### 8 · Moe

- Ein Spiel umfasst im Kurs drei Matches. Hier vergleichen wir ausschließlich das **erste** Match auf 30 Karten, jede auf beiden Seiten.
- Für ein greifbares Einzelbeispiel: Auf Karte 7150000, Sherlock auf Seite 0, verliert Sherlock 18 Einheiten, der Gegner zwei. Der Gegner schießt 25-mal, Sherlock neunmal. Dann auf die Mittelwerte aller 60 ersten Matches zeigen.
- Sherlock verliert im Mittel 23 Einheiten und hat vor dem letzten Zug nur noch rund 390 Teamenergie. Der Gegner verliert gut eine Einheit und hat über 3.300 Energie. Wer Energie übrig hat, kann weiter schießen.
- Der erste Punkt kommt bei Sherlock meist ähnlich früh. Die Verluste im Kampf sind groß. Überleitung zur letzten Folie. „Jetzt zu unserem Bewegungsberater. Hilft seine veränderte Zugwahl auch auf Karten, die wir vorher nicht zum Auswählen benutzt haben?“

### 9 · Moe

- Auf die erste Zeile zeigen. „Auf 60 frischen Karten gewinnt V14 mit R3 119 von 120 Spielen gegen Solution. V14 allein gewinnt 115. Fünf Niederlagen drehen wir in Siege, dafür verlieren wir ein Spiel neu.“
- „Das sind gut drei Prozentpunkte mehr. Die Spanne rechts beginnt bei null. Gegen Kaggle gewinnt keiner der beiden.“
- „Im direkten Duell gewinnt R3 88 von 120 Spielen gegen V14. Da ist der Vorteil deutlich. Für einen Wechsel wollen wir auch gegen die externen Gegner einen klaren Vorsprung sehen. Deshalb bleibt V14 vorerst unser Abgabeagent. Vielen Dank!“

## Stand und Quellen für das Team

- **Finale am 27.11.** Die Kursfolien „Reinforcement Learning_upload“ aus Moodle nennen drei benotete Präsentationen zu je 33 % (Folie 8), ein Finalturnier (Folie 10), die Bewertungsrubrik (Folie 11) und die Abgabe von Präsentation und Agenten-ZIP (Folie 51). Die zehn Minuten auf Folie 10 stehen beim Zwischen-Battle. Genaue Dauer, Frist und Benennung der Final-ZIP in Moodle prüfen. Diese Fassung zeigt den belegten Stand vom 15.11. und ist für eine erste Probe gedacht.
- **Rubrik für die Probe.** Die Frage vom Einstieg am Ende beantworten. Jede Übergabe an einem Spielzug oder Befund festmachen. Begriffe wie Q-Wert einmal in Alltagssprache erklären. Auf eine Zahl zeigen, sie einordnen und frei weitersprechen. Die eigene Entscheidung an der Schwelle für den Bewegungsberater erläutern.
- **Folien 2–5.** [Ablauf von V14](../../ENTSCHEIDUNGSABLAUF_V14_P.md), [Geprüfte Battle-Fassung mit Beispiel und Training](../Sherlock_Battle_06-11-2026.html), [Nachweis zur Netzarchitektur und Herkunft](../source/ENSEMBLE_BATTLE_0611_20261104.json).
- **Folie 6.** Die 36 V14-Netze bewerten sechs Aktionen. Der zusätzliche Schüler hat eine andere Architektur und ein anderes Lernziel. Seine Eingaben sind 16 räumliche Kartenebenen und 79 Merkmale je Einheit. Beim Spielen wählt das einzelne CNN die wahrscheinlichste zulässige Aktionsklasse. Die 70 % beschreiben seine eigene Bewertung dieser Klasse nach Maskierung, nicht die Gewinnchance der Partie. Nur wenn beide Befehle Bewegung oder Stillstand sind, der Schüler hinreichend sicher ist und sein Befehl die Ausführbarkeitsprüfung besteht, kann er V14s fertigen Befehl ersetzen. Matchanfänge sind ausgenommen. Der Lehrer ist nur beim Sammeln der Lernbeispiele dabei. Das Training umfasst 32 ursprüngliche V14-Karten und 120 weitere Karten mit tatsächlich gespielten Schülerverläufen, fünf Trainingsdurchgänge. Die Zusatzsignale sind die relativen Bewertungen der legalen Bewegungen auf geeigneten Stellungen. [Training und Vergleich](../../../experiments/analysis/movement_soft_20261115/TRAINING.md) · [Spielverläufe und Kartentrennung](../../../experiments/analysis/movement_dagger_20261115/SAMMLUNG.md) · [Entscheidungsweg](../../../scripts/selective_advice_agent.py) · [Prüfung des endgültigen Befehls](../../../scripts/combat_teacher_counterfactual.py).
- **Folie 7.** [Turnierbericht im Arbeitsstand vom 15.11.](../../ARBEITSSTAND.md), [lokaler Vergleich und zweite Kaggle-Einstellung](../../../experiments/analysis/kaggle3_20261115/README.md), [Einzelspiele gegen Solution_92](../../../experiments/analysis/kaggle3_20261115/v14_devA.csv) und [200 native Kaggle-Spiele, 8 Siege](../../../experiments/analysis/kaggle3_20261115/screen1/baseline.csv).
- **Mahmouds separater Versuch auf Folie 7.** Auf Dev A, 100 Karten mit beiden Sitzen, gewann der reine v3-Schüler 179/200 gegen Solution. Im Modus „points“ führt V14 den vollständigen Befehl für Punktehalter und Einheiten mit bestätigtem Punktefeld als Ziel aus. Die übrigen erhalten den vollständigen Schülerbefehl samt möglichem Schussziel. Dieser Hybrid gewann 194/200 gegen Solution und 6/200 gegen den nativen Kaggle-Gegner. Bei den acht V14-Siegen auf denselben Karten lief Kaggle mit seiner ursprünglichen Einstellung für fünf Matches, der Kursrunner beendet das Spiel nach drei. Diese Entwicklungszahlen erlauben keine direkte Rangliste mit R3s frischen Karten auf Folie 9. [Vergleich mit eigenständigem v3-Schüler und Hybrid](../../../experiments/analysis/umbau_20261115/README.md) · [Entscheidungsregel v3](../../../agents/sherlock/hybrid_agent.py).
- **Folie 8.** [Native Matchverläufe für die 30 Karten](../../../experiments/analysis/kaggle3_20261115/trace_v14_k3_30maps.csv). Mittelwerte über 60 erste Matches, einschließlich beider Seiten. Median bis zum ersten eigenen Punkt unter den Matches mit Punktgewinn: Schritt 39 (58 von 60) für Sherlock und 43 (60 von 60) für den Gegner. Der dokumentierte Zählfehler bei Einheitenverlusten nach einem Matchwechsel betrifft die hier gewählte erste Runde nicht.
- **Folie 9.** 60 unabhängige Karten gegen die externen Gegner (7273100–7273159), beide Spielerpositionen und je Agent dieselben Gegner und Karten. Für die direkten Duelle wurden 60 andere Karten (7273200–7273259) mit getauschten Seiten gespielt. Das ergibt 600 vollständige Partien, 480 extern und 120 direkt. Gegen Solution gewann R3 119/120 (99,17 %) gegenüber 115/120 (95,83 %). Der Unterschied von +3,33 Prozentpunkten hat ein gepaartes 95-%-Intervall von 0 bis +7,5. Im direkten Duell gewann R3 88 gegen 32 Spiele (73,33 %, Intervall 61,67 bis 83,33 %). Gegen den nativen Kaggle-Agenten gewannen beide 0/120. Unter beiden externen Gegnern zusammen beträgt der Vorteil +1,67 Prozentpunkte (0 bis +3,75). Die festgelegte Freigabe verlangt eine externe Untergrenze über null. Für die Intervalle wurden ganze Karten mit beiden Sitzen zusammen 10.000-mal mit Zurücklegen gezogen. Der Punkt auf der Folie gibt den beobachteten Solution-Unterschied wieder. [Unabhängige Vergleichsdaten](../../../experiments/analysis/movement_soft_20261115/confirmation/assessment.json) · [Vorher festgelegte Entscheidung](../../../experiments/analysis/combat_advice_20261115/SOFTZIELE.md).
- **Für die letzte Probe.** Gemeinsam mit Uhr sprechen und Übergaben üben. Vor dem Finale den tatsächlichen Abgabeagenten, Datenstand, Moodle-Frist und Dateinamen kontrollieren. Wenn sich der Agent ändert, müssen sein Entscheidungsweg und die Messwerte auf den Folien zum selben Stand gehören.

**Bearbeiten und exportieren.** Die HTML-Quelle ist eigenständig. Bei Änderungen im Browser öffnen und als PDF drucken, mit Hintergrundgrafiken, ohne Browser-Kopf- und Fußzeilen, bei 100 % und mit der im Dokument definierten Seitengröße (16:9). Ergebnis vor dem Vortrag im Vollbild prüfen.
