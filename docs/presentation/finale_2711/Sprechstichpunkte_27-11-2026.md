# Sherlock · Stichpunkte für den 27. November

[Präsentations-PDF](Sherlock_Finale_27-11-2026.pdf) · [Editierbare Folien](Sherlock_Finale_27-11-2026.html)

**Planzeit 9:55 Minuten, noch keine gemeinsame Zeitprobe.** Moe übernimmt den Einstieg, die Spielanalyse und den Schluss (4:50). Mahmoud erklärt Aktionswahl, Training, Hybrid und Gegnertest (5:05). Die Zeiten enthalten Zeige- und Übergabepausen. In eigenen Worten sprechen.

| Folie | Wer | Dauer | Bis |
|---|---|---:|---:|
| 1 · Sherlock | Moe | 0:40 | 0:40 |
| 2 · Verborgene Punktefelder | Moe | 1:10 | 1:50 |
| 3 · Entscheidungsablauf | Moe | 1:10 | 3:00 |
| 4 · Der gesperrte Zug | Mahmoud | 1:25 | 4:25 |
| 5 · Lernen | Mahmoud | 1:15 | 5:40 |
| 6 · Wie der Hybrid je Einheit entscheidet | Mahmoud | 1:05 | 6:45 |
| 7 · Turnier und lokale Gegner | Mahmoud | 1:20 | 8:05 |
| 8 · Energie im ersten Match | Moe | 1:10 | 9:15 |
| 9 · Der Hybrid im Vergleich | Moe | 0:40 | 9:55 |

### 1 · Moe

- Im Kurs-Battle belegten wir mit Sherlock Platz drei. Unser Spielziel war, verborgene Punktefelder zu finden und zu halten. Beides erfordert unterschiedliche Entscheidungen.
- Am einfachen Beispiel zeigen, wie Sherlock aus Punkten auf Felder schließt. Danach erklärt Mahmoud einen echten Zug und unseren neuen Hybrid aus zwei Agenten. Am Ende sehen wir, gegen wen die Kombination mehr Spiele gewinnt.

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

- Auf die beiden Kästen links zeigen. „Beide bekommen dieselbe Beobachtung. V14 macht zuerst seinen vollständigen Zugvorschlag. Der Schüler berechnet seinen eigenen, auch mit Schussziel, wenn er schießen möchte.“
- Den Pfeil nach rechts verfolgen. Beispiel: Eine Einheit hält ein bestätigtes Punktefeld, eine zweite erkundet. Für den Halter übernimmt der Hybrid den gesamten V14-Befehl. Für den Erkunder übernimmt er den gesamten Schülerbefehl. Auch für Einheiten, die V14 gerade einem bestätigten Punktefeld zugewiesen hat, gilt der V14-Befehl.
- „Der Schüler hat zuerst Züge des Kaggle-Agenten nachgeahmt. Dann haben wir ihn in 400 Spielen selbst ziehen lassen. In den Stellungen, in die er dadurch kommt, fragen wir den Lehrer nach seinem Zug. Mit diesen zusätzlichen Beispielen trainieren wir weiter. Das nennt man DAgger.“
- Übergang: „Wie viel bringt die Kombination? Zum Vergleich schauen wir erst, wo V14 im Turnier und gegen unsere beiden Testgegner stand.“

### 7 · Mahmoud

- Links der echte Hochschulwettbewerb. Im Halbfinale verlor Sherlock dreimal gegen das Team, das später Zweiter wurde. Der rechte Teil zeigt zwei lokale Testgegner.
- Auf exakt denselben 100 Karten, jeweils beide Seiten: 188 von 200 Spielen gegen Solution_92 gewonnen, acht gegen den Kaggle-Agenten. Er war Dritter im öffentlichen Kaggle-Wettbewerb und diente uns als Testgegner.
- Für die acht Siege lief der Kaggle-Agent mit seiner ursprünglichen Einstellung für fünf Matches. Der Kursrunner beendet jedes Spiel nach drei. Die frühere Vergleichszahl 6/200 mit anderer Gegnereinstellung gehört nicht zu dieser Grafik. **Übergabe an Moe:** „Was macht dieser Gegner schon im ersten Match anders?“

### 8 · Moe

- Ein Spiel umfasst im Kurs drei Matches. Hier vergleichen wir ausschließlich das **erste** Match auf 30 Karten, jede auf beiden Seiten.
- Für ein greifbares Einzelbeispiel: Auf Karte 7150000, Sherlock auf Seite 0, verliert Sherlock 18 Einheiten, der Gegner zwei. Der Gegner schießt 25-mal, Sherlock neunmal. Dann auf die Mittelwerte aller 60 ersten Matches zeigen.
- Sherlock verliert im Mittel 23 Einheiten und hat vor dem letzten Zug nur noch rund 390 Teamenergie. Der Gegner verliert gut eine Einheit und hat über 3.300 Energie. Wer Energie übrig hat, kann weiter schießen.
- Der erste Punkt kommt bei Sherlock meist ähnlich früh. Die Verluste im Kampf sind groß. Übergang: „Kann uns der neue Hybrid helfen, aus unseren Punktefeldern mehr gewonnene Spiele zu machen?“

### 9 · Moe

- „Hier spielt jeder Agent dieselben hundert Karten von beiden Seiten. Gegen Solution gewinnt V14 188 Spiele, der Schüler allein 179. Zusammen gewinnen sie 194.“
- Auf Strich und Punkt zeigen. „Zehn Niederlagen drehen sich in Siege, vier Siege gehen verloren. Das sind sechs Siege mehr, also drei Prozentpunkte. Die Spanne reicht von minus eins bis plus sieben. Auch null liegt darin.“
- „Gegen den Kaggle-Agenten gewinnt der Hybrid sechs Spiele, V14 acht. Der nächste Vergleich braucht neue Karten. Bis dahin bleibt V14 unser Abgabeagent.“

## Stand und Quellen für das Team

- **Finale am 27.11.** Die Kursfolien „Reinforcement Learning_upload“ aus Moodle nennen drei benotete Präsentationen zu je 33 % (Folie 8), ein Finalturnier (Folie 10), die Bewertungsrubrik (Folie 11) und die Abgabe von Präsentation und Agenten-ZIP (Folie 51). Die zehn Minuten auf Folie 10 stehen beim Zwischen-Battle. Genaue Dauer, Frist und Benennung der Final-ZIP in Moodle prüfen. Diese Fassung zeigt den belegten Stand vom 15.11. und ist für eine erste Probe gedacht.
- **Rubrik für die Probe.** Die Frage vom Einstieg am Ende beantworten. Jede Übergabe an einem Spielzug oder Befund festmachen. Begriffe wie Q-Wert einmal in Alltagssprache erklären. Auf eine Zahl zeigen, sie einordnen und frei weitersprechen. Die eigene Entscheidung am Beispiel der Aufgabenverteilung im Hybrid erläutern.
- **Folien 2–5.** [Ablauf von V14](../../ENTSCHEIDUNGSABLAUF_V14_P.md), [Geprüfte Battle-Fassung mit Beispiel und Training](../Sherlock_Battle_06-11-2026.html), [Nachweis zur Netzarchitektur und Herkunft](../source/ENSEMBLE_BATTLE_0611_20261104.json).
- **Folie 6.** [Mahmouds Training und Auswahlvergleich](../../../experiments/analysis/umbau_20261115/README.md) und [Hybrid im Modus points](../../../agents/sherlock/hybrid_agent.py), ausgewertet ab Teamstand `b2033c1` / Integration `e724ce6`. V14 und v3 berechnen nacheinander je einen vollständigen Befehl pro Einheit aus derselben Beobachtung. Auf einem mehrfach belegten bestätigten Feld gilt nur die zuerst geführte Einheit als Halter. Weitere Einheiten erhalten den V14-Befehl, wenn ihr eigenes zugewiesenes Ziel ein bestätigtes Punktefeld ist. Alle übrigen erhalten den Schülerbefehl. Beim Schülerteil in beiden ausgewerteten v3-Varianten waren Stay-Bias 1,5 und Entstapeln aktiv. Für die DAgger-Runde wurden 400 Schülerpartien mit rund 1,36 Mio. Lehrerentscheidungen ergänzt. Der Lehrer verfolgt die tatsächlich gespielte Zughistorie.
- **Folie 7.** [Turnierbericht im Arbeitsstand vom 15.11.](../../ARBEITSSTAND.md), [lokaler Vergleich und zweite Kaggle-Einstellung](../../../experiments/analysis/kaggle3_20261115/README.md), [Einzelspiele gegen Solution_92](../../../experiments/analysis/kaggle3_20261115/v14_devA.csv) und [200 native Kaggle-Spiele, 8 Siege](../../../experiments/analysis/kaggle3_20261115/screen1/baseline.csv).
- **Folie 8.** [Native Matchverläufe für die 30 Karten](../../../experiments/analysis/kaggle3_20261115/trace_v14_k3_30maps.csv). Mittelwerte über 60 erste Matches, einschließlich beider Seiten. Median bis zum ersten eigenen Punkt unter den Matches mit Punktgewinn: Schritt 39 (58 von 60) für Sherlock und 43 (60 von 60) für den Gegner. Der dokumentierte Zählfehler bei Einheitenverlusten nach einem Matchwechsel betrifft die hier gewählte erste Runde nicht.
- **Folie 9.** [V14-Referenz](../../../experiments/analysis/kaggle3_20261115/v14_ref_devA.csv), [Schüler v3 allein](../../../experiments/analysis/kaggle3_20261115/student_v3_b15u.csv), [Hybrid v3 points](../../../experiments/analysis/kaggle3_20261115/student_hyb_v3_points.csv). Eigene Nachrechnung aus den ganzen Spielen auf Dev A (Seeds 7150000–7150099) mit den Schlüsseln Gegner, Karte und Sitz. Gegen Solution gewinnt der Hybrid zehn zuvor verlorene Spiele und verliert vier zuvor gewonnene, gegen den nativen Kaggle-Agenten gewinnt er keines hinzu und verliert zwei. 95-%-Perzentilintervall der Differenz der Spielsiegquoten aus 10.000 Ziehungen mit Zurücklegen (PCG64, Seed 2711), beide Sitze einer Karte gemeinsam. Gegen Solution +3 Prozentpunkte [−1; +7], gegen Kaggle −1 [−3; 0]. Mahmouds ebenfalls positives Matchintervall zählt einzelne Matches eines Spiels und beantwortet eine andere Frage.
- **Einordnung für Rückfragen.** Der separat entwickelte Bewegungsberater R1 darf nur sichere Bewegungen/Stillstände ersetzen und überlässt alle Schüsse V14. Seine 20/32 direkt gegen V14, 30/32 gegen Solution und 0/32 gegen Kaggle stammen von anderen Karten. [Vergleich des Bewegungsberaters](../../../experiments/analysis/combat_advice_20261115/BEWEGUNGSSPIELE.md). Der auf Folie 6 und 9 gezeigte Hybrid verwendet Mahmouds eigenständigen v3-Schüler.
- **Vor der letzten Probe.** Für einen inzwischen abgeschlossenen, unabhängigen Vergleich Folie 9, Datenstand und Moes letzten Sprechpunkt aktualisieren. Falls ein anderer Agent präsentiert wird, auch dessen Auswahlregel auf Folie 6 abgleichen. Für Hybrid v3 points stehen eine unabhängige Bestätigung, direkte Duelle mit V14 und die Kursprüfung laut ausgewertetem Teamstand noch aus.

**Bearbeiten und exportieren.** Die HTML-Quelle ist eigenständig. Bei Änderungen im Browser öffnen und als PDF drucken, mit Hintergrundgrafiken, ohne Browser-Kopf- und Fußzeilen, bei 100 % und mit der im Dokument definierten Seitengröße (16:9). Ergebnis vor dem Vortrag im Vollbild prüfen.
