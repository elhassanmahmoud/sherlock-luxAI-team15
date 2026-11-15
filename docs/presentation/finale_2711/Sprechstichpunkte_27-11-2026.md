# Sherlock · Stichpunkte für den 27. November

[Präsentations-PDF](Sherlock_Finale_27-11-2026.pdf) · [Editierbare Folien](Sherlock_Finale_27-11-2026.html)

**Planzeit 9:55 Minuten, noch keine gemeinsame Zeitprobe.** Moe übernimmt den Einstieg, die Spielanalyse und den Schluss (4:50). Mahmoud erklärt Aktionswahl, Training und Tests (5:05). Die Zeiten enthalten Zeige- und Übergabepausen. In eigenen Worten sprechen.

| Folie | Wer | Dauer | Bis |
|---|---|---:|---:|
| 1 · Sherlock | Moe | 0:40 | 0:40 |
| 2 · Verborgene Punktefelder | Moe | 1:10 | 1:50 |
| 3 · Entscheidungsablauf | Moe | 1:10 | 3:00 |
| 4 · Der gesperrte Zug | Mahmoud | 1:25 | 4:25 |
| 5 · Lernen | Mahmoud | 1:15 | 5:40 |
| 6 · Versuch mit sechs neuen Netzen | Mahmoud | 1:05 | 6:45 |
| 7 · Turnier und lokale Gegner | Mahmoud | 1:20 | 8:05 |
| 8 · Energie im ersten Match | Moe | 1:10 | 9:15 |
| 9 · Fazit | Moe | 0:40 | 9:55 |

### 1 · Moe

- Im Kurs-Battle belegten wir mit Sherlock Platz drei. Unser Spielziel war, verborgene Punktefelder zu finden und zu halten. Beides erfordert unterschiedliche Entscheidungen.
- Am einfachen Beispiel zeigen, wie Sherlock aus Punkten auf Felder schließt. Danach erklärt Mahmoud einen echten Zug. Am Ende zeigen wir, was ein stärkerer Gegner aufdeckt.

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

- Nach dem Battle tauschten wir sechs Netze aus. Anzahl, Architektur und Regeln blieben im Vergleich gleich. Können die neuen Gewichte mehrere Gegnertypen besser schlagen?
- Direkt gewann der Kandidat 206 von 400 Spielen. Das Intervall umfasst 50 %. Im Test mit sechs Gegnern holte er insgesamt 32 Siege weniger als V14. Wir behielten V14.
- Die 194 von 200 auf **dieser** Folie gelten für die frischen Karten des Ensembleversuchs. Auf der nächsten Folie beginnt ein anderer Test auf anderen Karten.

### 7 · Mahmoud

- Links der echte Hochschulwettbewerb. Im Halbfinale verlor Sherlock dreimal gegen das Team, das später Zweiter wurde. Der rechte Teil zeigt zwei lokale Testgegner.
- Auf exakt denselben 100 Karten, jeweils beide Seiten: 188 von 200 Spielen gegen Solution_92 gewonnen, acht gegen den Kaggle-Agenten. Er war Dritter im öffentlichen Kaggle-Wettbewerb und diente uns als Testgegner.
- Beim Kaggle-Gegner verwenden wir seine ursprüngliche Einstellung. In unserem Kurs dauern die Partien drei Matches. **Übergabe an Moe:** „Was macht dieser Gegner schon im ersten Match anders?“

### 8 · Moe

- Ein Spiel umfasst im Kurs drei Matches. Hier vergleichen wir ausschließlich das **erste** Match auf 30 Karten, jede auf beiden Seiten.
- Für ein greifbares Einzelbeispiel: Auf Karte 7150000, Sherlock auf Seite 0, verliert Sherlock 18 Einheiten, der Gegner zwei. Der Gegner schießt 25-mal, Sherlock neunmal. Dann auf die Mittelwerte aller 60 ersten Matches zeigen.
- Sherlock verliert im Mittel 23 Einheiten und hat vor dem letzten Zug nur noch rund 390 Teamenergie. Der Gegner verliert gut eine Einheit und hat über 3.300 Energie. Wer Energie übrig hat, kann weiter schießen.
- Der erste Punkt kommt bei Sherlock meist ähnlich früh. Beim früheren Tanken überleben tatsächlich mehr Einheiten. Ob sie auch punkten, zeigt die nächste Folie.

### 9 · Moe

- Das Gedächtnis hilft Sherlock, Punktefelder zu finden. Gegen den Kaggle-Agenten sehen wir, wie schnell Einheiten im Kampf verloren gehen.
- „Wir haben das Tanken vorgezogen. Dadurch verlieren wir im ersten Match im Schnitt fünf Einheiten weniger. Vor dem letzten Zug stehen im Mittel 79 statt 82 Punkte auf der Anzeige. Deshalb trainieren wir jetzt einen Schüler mit Entscheidungen des Kaggle-Agenten. Er lernt unter anderem, welche Einheit auf welches Feld schießen soll.“
- Der letzte bestätigte Abgabestand ist V14 (Datenstand 15.11.). Vor einer Änderung brauchen wir neue Karten, den bisherigen Vergleichsgegner und das direkte Duell. Mit einer kurzen Pause enden, dann Fragen aufnehmen.

## Stand und Quellen für das Team

- **Finale am 27.11.** Die Kursfolien „Reinforcement Learning_upload“ aus Moodle nennen drei benotete Präsentationen zu je 33 % (Folie 8), ein Finalturnier (Folie 10), die Bewertungsrubrik (Folie 11) und die Abgabe von Präsentation und Agenten-ZIP (Folie 51). Die zehn Minuten auf Folie 10 stehen beim Zwischen-Battle. Genaue Dauer, Frist und Benennung der Final-ZIP in Moodle prüfen. Diese Fassung zeigt den belegten Stand vom 15.11. und ist für eine erste Probe gedacht.
- **Rubrik für die Probe.** Die Frage vom Einstieg am Ende beantworten. Jede Übergabe an einem Spielzug oder Befund festmachen. Begriffe wie Q-Wert einmal in Alltagssprache erklären. Auf eine Zahl zeigen, sie einordnen und frei weitersprechen. Die eigene Entscheidung am Beispiel des verworfenen Netzaustauschs erläutern.
- **Folien 2–5.** [Ablauf von V14](../../ENTSCHEIDUNGSABLAUF_V14_P.md), [Geprüfte Battle-Fassung mit Beispiel und Training](../Sherlock_Battle_06-11-2026.html), [Nachweis zur Netzarchitektur und Herkunft](../source/ENSEMBLE_BATTLE_0611_20261104.json).
- **Folie 6.** [Ensemblevergleich vom 8.11.](../../ENSEMBLE_ABSCHLUSS_20261108.md). 100 Panelkarten × beide Seiten pro Gegner, 200 separate Direktkarten × beide Seiten. Das 95-%-Intervall wurde über ganze Karten berechnet.
- **Folie 7.** [Turnierbericht im Arbeitsstand vom 15.11.](../../ARBEITSSTAND.md), [lokaler Vergleich und zweite Kaggle-Einstellung](../../../experiments/analysis/kaggle3_20261115/README.md), [Einzelspiele gegen Solution_92](../../../experiments/analysis/kaggle3_20261115/v14_devA.csv) und [200 native Kaggle-Spiele, 8 Siege](../../../experiments/analysis/kaggle3_20261115/screen1/baseline.csv).
- **Folie 8.** [Native Matchverläufe für die 30 Karten](../../../experiments/analysis/kaggle3_20261115/trace_v14_k3_30maps.csv). Mittelwerte über 60 erste Matches, einschließlich beider Seiten. Median bis zum ersten eigenen Punkt unter den Matches mit Punktgewinn: Schritt 39 (58 von 60) für Sherlock und 43 (60 von 60) für den Gegner. Der dokumentierte Zählfehler bei Einheitenverlusten nach einem Matchwechsel betrifft die hier gewählte erste Runde nicht.
- **Folie 9.** [Verluste und Energie ohne frühes Tanken](../../../experiments/analysis/kaggle3_20261115/trace2_base_30maps.csv), [dieselben Karten mit Tanken](../../../experiments/analysis/kaggle3_20261115/trace2_charge_30maps.csv) und [Plan für den CNN-Schüler](../../superpowers/plans/2026-11-15-umbau-imitation.md). Vor der Schlussprobe Folie 9 und den letzten Sprechpunkt anhand des jüngsten geprüften Vergleichs aktualisieren. Gegner, Zahl der Karten/Spiele und Prüfstatus nennen. Eine kleine Vorauswahl genügt allein nicht für einen neuen Abgabeagenten.

**Bearbeiten und exportieren.** Die HTML-Quelle ist eigenständig. Bei Änderungen im Browser öffnen und als PDF drucken, mit Hintergrundgrafiken, ohne Browser-Kopf- und Fußzeilen, bei 100 % und mit der im Dokument definierten Seitengröße (16:9). Ergebnis vor dem Vortrag im Vollbild prüfen.
