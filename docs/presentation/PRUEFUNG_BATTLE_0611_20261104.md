# Battle-Präsentation: Prüfung und Aufteilungsvorschlag

Stand: 04.11.2026, abends. Codex mit unabhängigen Reviews zu Fachinhalt und Vortragsaufteilung.

Moayed hat die Trainingsarbeit ausdrücklich beendet. Nach seiner Mitteilung hat Mahmoud den Agenten bereits abgegeben. Der Moodle-Upload selbst wurde hier nicht eingesehen. Geprüft wurde der aktuelle Repository-Stand `36a68ab`, der weiterhin V14 mit 36 Netzen dokumentiert. Kein Training, keine neuen Spiele, keine Änderung an Agent, Gewichten, ZIP oder Präsentationsdateien.

## Geprüfte Grundlage

- [Battle-PDF](../../Sherlock_Battle_06-11-2026.pdf), 17 Seiten: 13 Hauptfolien und vier Reservefolien. Dokumentinhalt zuletzt am 01.11. aktualisiert (`93a2ddd`), nicht am Datum der lokalen Dateikopie.
- [HTML-Quelle](Sherlock_Battle_06-11-2026.html) und [Stichpunkte](../../Sherlock_Stichpunkte_06-11-2026.md).
- Agentenablauf in `agents/sherlock/main.py`, Gedächtnis in `belief.py`, Architektur in `model.py`, V11-/V14-Übernahmeberichte und jüngste abgeschlossene Studienberichte.
- GitHub-Abgleich: keine neueren Remote-Commits zum Prüfzeitpunkt. Primäre lokale PDF und Studienkopie SHA-256 identisch: `f2de3cb834cb74c26c041aedc3329f1a10c8bf4f0d3884cb0f06707826dd1469`.
- Alle 17 PDF-Seiten gerendert und visuell geprüft: kein sichtbarer abgeschnittener Inhalt; bestehendes Design kann bleiben. Folien 11, 12 und Reserve 14 sind inhaltlich dicht. Keine PowerPoint-Prüfung behauptet.

Die Grundstruktur passt zur Battle-Aufgabe: ungefähr zehn Minuten, Funktionsweise und Training des eigenen Agenten, neueste Entwicklungen. Keine allgemeine Lux-/DQN-Einführung nötig. Das Feedback des Profs zur Reihenfolge von Netz, Maske und Regeln wird bereits aufgegriffen, ist aber an den folgenden Stellen noch zu ungenau.

## Vor dem Einüben korrigieren

1. **Folie 4: Wer entscheidet über einen Schuss?** Die Aussage „Das Netz entscheidet … ob geschossen wird“ ist zu absolut. Nach der maskierten Netzauswahl können Regeln beispielsweise Stehen in Sap ändern (`fog_sap`, `pt_sap`, `art_sap`; `main.py`, etwa Zeilen 451–491). Vorschlag: „Die Netze bewerten Aktionen. Nach der maskierten Auswahl können Regeln die Aktion ändern oder einen Schuss auslösen.“ Sichtbare Ziele werden heuristisch bewertet; für verdeckte Ziele gibt es einen eigenen Regelpfad. Eine einzige Formel für sämtliche Schussziele wäre ebenfalls zu pauschal.
2. **Folien 4 und 6: Maske und spätere Eingriffe unterscheiden.** Die Maske wird vor der Netzauswertung vorbereitet und nach dem Mitteln auf die Q-Werte angewandt (`_decide`, `_act`). „Die Aktion wird nie gewählt“ gilt für diese Netzauswahl. Der spätere Nebelschuss kann Sap auch dann auslösen, wenn kein sichtbares Sap-Ziel vorhanden war; er prüft seine eigenen Bedingungen. Das ist keine Aufhebung der Spielregeln. Im Flow deutlich machen: vorbereitete Merkmale/Maske → Q-Mittel → maskierte Auswahl → Regelkorrekturen → Ausgabe. Beim Overkill-Schutz wird ein überflüssiger Sap zu Stehen, nicht zur zweitbesten Netzempfehlung (`main.py`, etwa Zeilen 571–576).
3. **Folie 5: Gedächtnis präzisieren.** „Alles bleibt über die 3 Matches erhalten“ ist wörtlich falsch. Relic-/Punktewissen bleibt erhalten; Erkundungs- und Sichtzeitstempel werden beim Matchwechsel zurückgesetzt (`belief.py`, `reset_match`). Vorschlag: „Relic- und Punktewissen bleibt über die drei Matches erhalten.“ Neues Spiel: neues Gedächtnis; trainierte Gewichte bleiben fest.
4. **Folie 7 und Stichpunkte: Q-Werte sind keine Sicherheit.** „Wie sicher sich jedes Netz ist“ ersetzen durch „wie hoch jedes Netz die Aktion bewertet“. Gemittelt werden geschätzte Aktionswerte, keine Wahrscheinlichkeiten und keine Mehrheitsstimmen.
5. **Folien 8, 10 und 11: Trainingszeitpunkt richtig benennen.** Das Nachtraining der 18 Kopien erfolgte unter den V10-Regeln. „Alle heutigen Regeln“ ist für V14 falsch: V11–V14 enthalten spätere Regeländerungen. Die 66.000 + 99.000 Spiele beschreiben die Herkunft dieser Netzfamilien, nicht sämtliche Projektversuche. Belohnungen werden schrittweise berechnet; der Matchergebnis-Anteil fällt beim Matchergebnis an, nicht in jedem Schritt erneut.
6. **Folien 9 und 12: Messungen nicht als universelle V14-Eigenschaft darstellen.** Die 91-%-Aussage stammt aus zehn Diagnosespielen mit V12; dies steht auf Folie 9 klein im Fußtext, muss aber auch im Sprechtext klar sein. Sie beschreibt Übereinstimmung mit der maskierten Netzauswahl, nicht „91 % ohne programmierte Einflüsse“. Ziele, Merkmale und Maske sind bereits programmiert. Der Vergleich 3 % gegen 38 % stammt aus einem älteren, konkreten Regelersatz-Versuch; daraus folgt nicht, dass jeder regelbasierte Bot schwach wäre.
7. **Folien 11/12 und Reserve 14: V14-Ausnahme vollständig erklären.** Die historische Übernahme war eine dokumentierte Teamentscheidung trotz zwei verfehlter Hürden: Panelgewinn +0,86 statt mindestens +1 Prozentpunkt und untere Grenze im Direktduell 49,25 % statt über 50 %. Aktuelle Stichpunkte erwähnen vor allem die erste. Auf der Hauptfolie kurz halten, in der Reserve beide nennen. Quelle: [V14-Übernahme](../../experiments/analysis/release_20261101_v14/RELEASE.md).
8. **Folie 12: aktuelle Versuche und vorsichtige Schlussfolgerungen.** „Fehler suchen bringt mehr als weitertrainieren“, „Netze ausgereizt“ (Stichpunkte) und „Was noch fehlt, ist Information“ sind zu allgemein. Besser: gezielte Fehlersuche brachte bei uns große Fortschritte; die zuletzt geprüften Trainingsvarianten belegten keinen ausreichenden Gesamtvorteil; bessere Information bleibt ein möglicher Ansatz. Ein Orakel-Test ist eine Diagnose mit unzulässigem Zusatzwissen, kein einsetzbarer Agent und keine garantierte erreichbare Siegquote.
9. **Aktueller Stand 02.–04.11. fehlt.** Eine knappe Ergänzung genügt: kleinere/größere Ensembles, Einzelnetz-Schüler und weiteres Nachtraining wurden geprüft; kein Kandidat war ausreichend als Ersatz belegt, daher blieb V14. Die jüngsten 40/40 von V14 gegen Solution sind ein kleiner separater Testsatz und ersetzen nicht die historische Angabe 95,44 % aus 1.600 Spielen. Experimentnetze sind kein Bestandteil der Abgabe.
10. **Stichpunkte organisatorisch aktualisieren.** „Upload bis Mittwoch“ nach Moayeds Mitteilung als erledigt kennzeichnen; die dortige ZIP-Bauzeit vom 01.11. ist historisch. Die pauschale Antwort „auf einem Punktefeld muss man stehen bleiben“ präzisieren: Punkte entstehen durch Besetzung; Sap lässt die Einheit ebenfalls auf dem Feld, und auch eine Bewegung auf ein anderes Punktefeld kann punkten. Sichtbaren internen Hinweis „Reservefolie 17“ auf Hauptfolie 12 entfernen.

## Empfohlene Aufteilung

Die vorhandene MD nennt bisher ausdrücklich einen Vorschlag: Moayed 1–5, 10, 12–13 (5:20), Mahmoud 6–9 und 11 (4:30). Noch keine neue Aufteilung vom Team bestätigt.

Empfehlung: Folie 10 zu Mahmoud ziehen. Dadurch entfällt ein kurzer Hin-und-zurück-Wechsel, und Moayed behält den leichteren Teil.

| Person | Folien | Inhalt | Richtzeit |
|---|---|---|---:|
| Moayed | 1–5 | Begrüßung, Agenda, Ein-/Ausgabe, Ablaufübersicht, Gedächtnisbeispiel | 3:05 |
| Mahmoud | 6–11 | Maske, Netze, Training, Regeln, Ergebnisse und neue Versionen | 5:25 |
| Moayed | 12–13 | Erkenntnisse, Fazit und Übergang zum Battle | 1:20 |
| **Gesamt** | **1–13** | **Zwei Sprecherwechsel** | **9:50** |

Das sind Planzeiten aus den vorhandenen Folienzeiten, keine gemessene Probe. Mit Übergaben und Pausen etwa zehn bis elf Minuten anstreben. Reserve 14–17 nur auf Nachfrage; keine weitere Hauptfolie erforderlich.

- Nach Folie 5, Moayed: „Damit ist klar, welche Informationen Sherlock sammelt. Mahmoud zeigt jetzt, wie daraus eine Aktion entsteht.“
- Nach Folie 11, Mahmoud: „Das ist der Stand unseres abgegebenen Agenten. Moayed fasst zum Schluss unsere wichtigsten Erkenntnisse zusammen.“

Folie 11 kürzen: V11-Training nicht erneut ausführlich erklären, V12 und V14 als Beispiele hervorheben, V13 in einem Satz. Folie 12 für Moayed auf drei einfache Aussagen verdichten: Netze und Regeln ergänzen sich; Verbesserungen müssen auf neuen Karten bestehen; mehr Training oder mehr Netze ist nicht automatisch besser. Detaillierte Auswahlhürden und Orakelwerte bleiben als Antworten vorbereitet.

## Nächster Schritt

Die PDF und die bisherigen Stichpunkte sind in diesem Prüfschritt unverändert. Als Nächstes gezielt die genannten Stellen in Quelle, PDF und Übungsnotizen angleichen, das bestehende Design beibehalten und dann Moayeds Folien 1–5 und 12–13 einfach durchgehen. Kein Training oder erneute Agentenabgabe dafür erforderlich. Aufteilung bis zur Rückmeldung ausdrücklich Vorschlag.
