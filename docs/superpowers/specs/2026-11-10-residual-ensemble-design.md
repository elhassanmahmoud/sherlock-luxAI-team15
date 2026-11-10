# V14 gezielt korrigieren: Planvorschlag vom 10.11.2026

**Abschluss10.11.2026:** Nach späterer Nutzerfreigabe umgesetzt. Beide Starts haben die feste200er-Auswahl verfehlt; Pilot nach448 Ausführungen geschlossen, V14/ZIP unverändert. [Endergebnis](../../../experiments/analysis/residual_ensemble_20261110/ERGEBNIS.md). Der folgende Planungs-/Freigabeverlauf bleibt als ursprüngliche Festlegung erhalten; er autorisiert keinen Neustart.


**Status: Vorschlag zur Besprechung, keine Ausführungsfreigabe aus diesem Dokument.** Moayed beauftragt zunächst Planung. Kein Training, keine Agentenänderung, kein Gewichtstausch, keine reaktivierte Automation. Neue Budgetgrenze: mindestens 5 % Codex-Kontingent erhalten. Die folgenden Zahlen sind vorab vorgeschlagene Entscheidungen, keine gemessenen Resultate.

## Ziel und belegter Ausgangspunkt

Ein Kandidat soll V14 im direkten Vergleich verlässlich schlagen und gegen Solution_92 mindestens dessen Stärke behalten. Näher an 100 % gegen Solution zu kommen bleibt ein Entwicklungsziel; eine allgemeine 100%-Garantie lässt sich durch keinen endlichen Testsatz belegen.

Ausgangsstand ist Commit `346e013e345496ba4dc16b4a68f9926544131eea`. Geschützte V14-Dateien: SHA256 `98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`; vorhandene ZIP: `88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6`.

Die Belege rechtfertigen keine weitere ungezielte Vergrößerung:

| Abgeschlossener Ansatz | Tatsächliche Grenze |
|---|---|
| ALL42 / Austausch von sechs Netzen | ALL42 direkt nur 18/40; REPLACE36 in frischer Bestätigung 206/400 direkt und schwächeres Gegnerpanel. |
| Einzelner Aktionsschüler A2 | Gute Steigerung gegenüber dem Ausgangsschüler, aber direkt nur 14/40 gegen V14. Lehreranker qualifizierten ebenfalls keinen Nachfolger. |
| Ensemble-Aktionsauswahl beim Training | BEHAVIOR38 gegen Solution 40/40, direkt nur 16/40. |
| Training zusätzlich gegen den aktuellen V14 | EXPOSURE38 gegen Solution 37/40 wie V14, direkt 22/40; keine Überlegenheit nachgewiesen. |

Diese Zahlen stammen aus unterschiedlichen Kartenreihen und werden nicht untereinander als kontrollierte Leistungssteigerung verglichen. Quellen: `docs/ENSEMBLE_ABSCHLUSS_20261108.md`, `docs/AKTIONSSCHUELER_20261104.md`, die jeweiligen README-/Ergebnisberichte unter `experiments/analysis/`.

Im tatsächlichen Code mittelt `Agent_x._act` die Netze bei der Auswertung, während `_learn` allein `self.q` und `self.target_q` verwendet (`agents/sherlock/main.py`, derzeit Zeilen 353–360 und 1627–1640). `BehaviorEnsemble` verändert nur die Aktionsphase (`scripts/ensemble_behavior_study.py`, Klasse ab Zeile 37). Auch EXPOSURE verwendet dieses getrennte Lernziel. **Das ist ein konkreter Ansatzpunkt, aber kein Beweis, dass dies die Niederlagen verursacht.**

## Entscheidung und Alternativen

Empfohlen: ursprüngliche 36 Netze unverändert einfrieren und ein zusätzliches Netz lernen lassen, das ihre gemeinsame Bewertung korrigiert. Das bewahrt den vollständigen V14 als Ausgangspunkt und untersucht ein bisher nicht implementiertes Lernziel.

Weitere Mitglieder, neue Rewards und gleichzeitig neue Regeln werden zunächst zurückgestellt: mehrere nahe Varianten sind bereits ohne bestätigten Erfolg abgeschlossen. Ein vollständiger CNN-/PPO-Neustart wäre ein größeres eigenes Projekt und verliert den direkten Anschluss an den funktionierenden Agenten.

Eine ernsthafte Alternative sind gelernte Aktionskorrekturen aus gepaarten Fortsetzungen bis zum Matchende. Sie wären stärker auf Gewinnen ausgerichtet, brauchen aber teure neue Daten und einen gesonderten Umgang mit verborgenem Spielzustand. Der abgeschlossene HOLD-Versuch nutzte nur STAY und zwölf Schritte Punktedifferenz; er ist keine Prüfung dieser Alternative. Diese Alternative wird hier nicht automatisch gestartet.

## Vorgeschlagene Architektur

Sei `M(s,a)` der unveränderte Mittelwert der 36 ursprünglichen Netze. Der neue Aktionswert ist:

```
Q(s,a) = M(s,a) + R(s,a)
```

`R` ist ein 79→256→256-Dueling-Netz mit sechs Ausgaben. Rumpf und innere Kopfschichten stammen aus V14-Mitglied 18. Ausschließlich die letzten Gewichte und Biases beider Ausgabeköpfe werden genullt: `R=0`, aber lernfähige innere Merkmale. Nicht sämtliche Schichten nullen. Online- und Target-R beginnen identisch; nur Online-R besitzt Optimierer und Gradienten.

**Keine 37-fach-Mittelung und keine Skalierung der alten Tensoren.** Ein expliziter optionaler Zusatz nach der bisherigen Mittelung vermeidet die Rundungs-/Gewichtungsprobleme einer umskalierten 37er-Montage. Ohne Zusatz muss der alte Rechenweg erhalten bleiben. Ein Export muss diese additive Semantik ausdrücklich enthalten; ein normaler Ensembleexport wäre falsch.

Das Double-DQN-Lernziel verwendet die Summe durchgängig:

```
a* = argmax über gespeicherte zulässige Aktionen von [M(s') + R_online(s')]
y  = r + (1-done) * gamma * [M(s',a*) + R_target(s',a*)]
loss = Huber(M(s,a_executed) + R_online(s,a_executed), y)
```

`M` bleibt überall ohne Gradienten. Rewards, Merkmale, Belief, Masken und Regeln werden in diesem Versuch nicht fachlich verändert. Der Sammler benutzt die vollständige Auswertungs-Regelkette; Sammlung und Lernen werden getrennt. Exploration mit epsilon 0,05 erfolgt vor dieser Regelkette, nicht durch nachträglichen Austausch einer bereits geprüften Weltaktion. Evaluation verwendet epsilon 0. Der tatsächliche finale kanonische Aktionstyp und die Weltaktion einschließlich SAP-Offset werden gespeichert.

**Verbleibende Grenze:** Der nächste DDQN-Argmax bildet nicht die gesamte nachgelagerte Regelkette ab. Tatsächliche Replayaktionen und gleiche Sammlung beseitigen diese Approximation nicht. Die 79 Merkmale sind ebenfalls kein vollständiger globaler Markovzustand. Deshalb keine Behauptung vollständiger Policy-Konsistenz oder garantierter Konvergenz.

### Rechenaufwand und Replay

Die eingefrorenen sechs Werte `M(s)` und `M(s')` dürfen pro tatsächlicher float32-Replayzeile zwischengespeichert werden. Das vermeidet zwei vollständige 36er-Auswertungen bei jedem Lernupdate. Zusatzspeicher bei 300.000 Übergängen: 14,4 MB für die zwölf float32-Werte, zuzüglich Metadaten.

Cache und Replay verwenden dieselben Ringpositionen, Überschreibgenerationen und genau einen gezogenen Indexsatz. Gespeicherte Werte sind roh, endlich und unmaskiert. Modellhash, Reihenfolge, Merkmalsbytes und numerische Konvention gehören zur Cacheidentität. Falsche oder fehlende Werte führen zum Fehler, nicht zu Nullen. Tote/neu gespawnte Einheiten und Matchgrenzen behalten die bisherigen Terminalregeln. Ein frisches oder größeres Replay ist kein Anlass für einen neuen allgemeinen Trainingsframeworkbau.

## Ablauf mit festen Grenzen

### 1. Technische Abnahme: acht vollständige Ausführungen

Vier Vergleichspaare auf bekannten Entwicklungssituationen: die Schlüssel `(9946007, player_0)` und `(831006, player_1)`, jeweils gegen Solution und eingefrorenen V14; pro Fall Stock-V14 und Nullkorrektur. Das sind **acht Ausführungen insgesamt**, nicht acht Paare. Keine Gradienten.

Der Nullkorrekturpfad muss die finale Aktionsfolge und Ergebnisse exakt reproduzieren. Dies prüft sowohl die Kandidaten-Auswertung als auch den Sammler bei epsilon 0. Technisch zusätzlich mit synthetischen Zuständen/DDQN-Beispielen prüfen: Summenformel, Masken, Target, Ringcache, finale Labels, Tod/Respawn, Matchreset, unveränderte ursprüngliche Gewichte und neuronale Gradienten.

An diesen Daten Laufzeit und Speicher messen. Abbruch bei unerklärter Abweichung, nicht endlichen Werten, still abgefangenen Fehlern oder nicht tragbarem Ressourcenbedarf. Noch keine Aussage zur Spielstärke.

### 2. Zwei kurze Lernläufe

- Feste Starts 61 und 62, dieselbe Anfangsfunktion und derselbe vorab gespeicherte Karten-/Gegnerplan; getrennte Zufallszustände, Optimierer und Replay.
- Je 40 Vorlaufspiele ohne Updates und 80 Lernspiele. Je 12.000 Updates bei `train_every=2` und 300 lernfähigen Schritten pro Spiel. Insgesamt 240 Ausführungen, davon 160 Lernspiele, 24.000 Updates.
- Adam `lr=5e-5`, gamma 0,99, Batch 256, Replaykapazität 300.000, mindestens 5.000 Einträge, Targetkopie alle 500 Updates, Gradientennorm höchstens 5. Ausgangswerte aus dem letzten kontrollierten Versuch; keine Suche über diese Parameter.
- Gegner pro Kartenindex modulo fünf: Solution, Solution, Solution, eingefrorener V14, eingefrorener V14. Jede Karte von beiden Seiten. Originalgegner pro Spiel mit frischem Gedächtnis, keine versteckten Informationen im Agenten.
- Ausschließlich der vollständige Endcheckpoint je Start. Kein Best-of-Zwischencheckpoint, kein Ensemble der zwei neuen R-Netze, kein automatisches Nachtrainieren.

TD-Loss, gemeinsame Wertverschiebung gegenüber aktionsabhängiger Korrektur, Gradienten, Masken-/Regelübersteuerung und finale Aktionsänderungen dienen der Diagnose. Kein solcher Hilfswert ersetzt gewonnene Spiele. 80 Lernspiele sind bewusst ein begrenzter Pilot; ein negatives Ergebnis bedeutet nur „kein geeigneter Kandidat mit dieser Rezeptur und diesem Budget“.

### 3. Kleine Auswahl: genau 200 Spiele

Je Kandidat 40 Spiele gegen Solution und 40 direkt gegen V14, plus einmal 40 V14–Solution-Spiele auf denselben Solution-Karten. Zwei getrennte Kartenbereiche mit je 20 Karten, immer beide Seiten.

Für die Fortsetzung müssen **beide Starts** jeweils mindestens 24/40 direkte Siege und mindestens so viele Solution-Siege wie V14 erreichen. Remis zählen nicht als Sieg. Das ist eine konservative Auswahlregel, kein statistischer Beweis. Bei Erfolg höchstens einen Kandidaten nominieren: zuerst mehr direkte Siege, dann mehr Solution-Siege, zuletzt kleinere Startnummer. Training und Auswahl zusammen mit Technik: höchstens **448 Ausführungen**.

Bei Nichterfüllung keine Verlängerung, Kartenverschiebung, Rewardänderung oder nachträgliche Mischung. Bisherige erfolgreiche Studienphasen bleiben archiviert. Ein weiterer Ansatz benötigt eine neue begründete Entscheidung.

### 4. Nur bei Erfolg: separate frische Bestätigung mit 600 Spielen

| Prüfung | Karten | Ausführungen |
|---|---:|---:|
| Nominierter direkt gegen V14 | 100, beide Seiten | 200 |
| Nominierter und V14 gegen Solution | 50, beide Seiten, beide Agenten | 200 |
| Beide gegen sol92_sq | 20, beide Seiten | 80 |
| Beide gegen festen V13 | dieselben 20 Panelkarten, beide Seiten | 80 |
| Beide gegen default | 10, beide Seiten | 40 |

Der Kandidat und alle Bedingungen werden vor diesen Ergebnissen eingefroren. V13 stammt aus `experiments/releases/20261101_v13_neb/agent_p0.pth`, SHA256 `6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62`.

Übernahme nur, wenn sämtliche Bedingungen erfüllt sind:

1. Direkt mehr als 50 % echte Siege und untere Grenze des 95%-Kartenbootstrap-Intervalls des Ergebniswertes strikt über 50 %.
2. Gegen Solution mindestens so viele echte Siege wie V14 und mindestens 95/100 Siege. Das ist ein Mindestschutz; 100/100 ist das Wunschresultat dieses Tests, keine Garantie für weitere Karten.
3. Gleich gewichtetes Ergebniswertmittel über Square/V13 mindestens wie V14; pro Gegner höchstens zwei Siege weniger aus 40. Dies sind praktische Regressionsgrenzen, keine nachgewiesene statistische Nichtunterlegenheit.
4. Gegen default 20/20 Siege, keine Laufzeit-/Formatfehler oder abgefangenen Agentenausnahmen.

Alle Unsicherheitsintervalle zusätzlich berichten, auch wenn sie eine Regression nicht ausschließen. Bootstrap über ganze Karten, 5.000 Ziehungen mit PCG64/Seed 0; Seiten und gepaarte Agenten zusammenhalten, Square/V13 auf gemeinsamer Karte gemeinsam resampeln. Kein Zusammenlegen mit Auswahl- oder Trainingsdaten. Diese Freigabe bewertet ein konkretes Modell, nicht die gesamte Methode aus nur zwei Trainingsstarts.

### 5. Freigabe und Paket

Erst nach unabhängiger Ergebnisnachrechnung: neue additive Architektur und gespeicherte Tensoren reproduzierbar laden, acht kurze Kursprüfungen (zwei bekannte Karten × beide Seiten × default/Solution), Speicher-/Aktionslatenz gegen V14 messen, ZIP separat bauen und entpackt prüfen. Bei Fehler keine Freigabe. Vor Ersatz V14/ZIP bytegleich sichern und Rückweg dokumentieren. Gesamtobergrenze einschließlich erfolgreicher Bestätigung und acht Kursausführungen: **1.056 vollständige Ausführungen**, davon nur 160 Lernspiele. Keine Netzanzahl-/Gewichtssuche am Bestätigungssatz.

## Karten, Zeit und Zusammenarbeit

Vorgeschlagene, **noch nicht auf historische Nutzung geprüfte** Bereiche: Vorlauf 11010000–11010019, Lernen 11010020–11010059; Auswahl Solution 11011000–11011019 und direkt 11011100–11011119; Bestätigung direkt 11012000–11012099, Solution 11012200–11012249, Square/V13 11012300–11012319, default 11012400–11012409. Vor Verwendung einmalig auf Überschneidung prüfen und exakte Listen speichern. Bei Konflikt vor jeglichem neuen Modelllauf Ersatzlisten festlegen; bisherige bekannte Technik-/Kurskarten ausdrücklich getrennt halten.

Historisch dauerten die letzten zwei 440-Spiel-Läufe parallel etwa 45 Minuten; der letzte 200er-Vergleich etwa zehn Minuten. Die Residualmethode ist neu, deshalb sind daraus keine verbindlichen Laufzeiten ableitbar. Erst technische Zeit-/Speichermessung, dann Laufzeitprognose. Zwei Modellprozesse maximal, je ein CPU-Thread; keine Tests parallel zu Modellläufen.

Root implementiert zusammenhängende Kernarbeit selbst. Ein unabhängiger Reviewer prüft die neue Lernformel/Cache-/Aktionsverträge einmal, ein begrenzter Datenreview folgt beim tatsächlichen Endergebnis. Kein dauerhaft arbeitender Commit-Subagent: Remote vor Beginn, vor Phasenwechsel/Publikation und bei langen Läufen spätestens nach drei Stunden prüfen. Laufende Quellen bleiben fest; Mahmouds Änderungen verlustfrei am sicheren Übergang integrieren.

Vor tatsächlicher Fortsetzung Quota frisch abfragen. Ab 92 % Verbrauch keine neue Phase; laufende Arbeit kontrolliert abschließen oder beenden, veröffentlichen und pausieren. 95 % ist absolute Arbeitsgrenze, keine Resets durch Codex. Unbekannte Quota erlaubt keinen langen Start. Planung verbraucht dieses Budget nicht absichtlich. Bereits pausierte Automation bleibt für diese reine Planungsrunde pausiert.

## Methodische Quellen und offene Risiken

Double DQN trennt Aktionsauswahl und Targetbewertung; das Prinzip wird hier auf die vorgeschlagene Summenfunktion angewandt ([Originalarbeit](https://arxiv.org/abs/1509.06461)). Die konkrete eingefrorene Ensemble-plus-R-Konstruktion ist ein eigener Projektvorschlag, kein aus einem Paper belegter Sherlock-Leistungsgewinn. Das ähnlich benannte [Residual Q-Learning](https://arxiv.org/abs/2306.09526) behandelt einen anderen Policy-Customization-Ansatz und wird nicht als identische Implementierung ausgegeben.

Wenige Trainingsstarts und nachträgliche Modellwahl können Ergebnisse verzerren; deshalb getrennte Karten, vollständige Ergebnisse und Intervalle ([Agarwal et al.](https://arxiv.org/abs/2108.13264)). Zusätzliche Risiken bleiben: Rewardkalibrierung statt besserer Aktion, begrenzte 79 Merkmale, geteilte Teambelohnung und Regelübersteuerung. Der Pilot testet praktischen Nutzen unter diesen Einschränkungen; er garantiert keinen Durchbruch.


**Freigabe 10.11.2026:** Moayed hat diesen Plan ausdrücklich zur selbstständigen Umsetzung freigegeben. Der frühere Planungsstatus oben ist historisch. V14 nur nach belegtem Vorteil ersetzen; mindestens 5 % Kontingent erhalten.
