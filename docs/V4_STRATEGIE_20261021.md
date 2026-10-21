# V4: gemeinsame Entscheidungen statt weiterer gleichartiger Netze

Stand 21.10.2026. Strategie auf Moayeds Wunsch, nach zwei unabhängigen Code-Reviews. **Noch kein implementierter neuer V4-Kandidat und kein neuer Stärkegewinn.** Dieser Entwurf ersetzt weder die abgeschlossenen Resultate noch die eingefrorenen Protokolle. Umsetzung erfolgt in getrennten, kleinen Arbeitsschritten; vor jedem datenabhängigen Versuch werden genaue Parameter und Karten festgeschrieben.

## Ziel und Ausgangspunkt

- Ein deutlich stärkerer, vorzeigbarer Agent für das nächste Review/Battle, mit nachvollziehbarem gelerntem Entscheidungsanteil. Ziel: 100 % gegen Solution_92 auf einem vorher festgelegten, unberührten Testsatz. Das wäre keine Garantie für alle Karten oder andere Gegner. Remis zählen nicht als Sieg.
- Freigegebene Basis ist `all18_v3`, 18 DQN-Netze, beide Abgabe-Dateien SHA-256 `aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935`. Auf 200 frischen Karten: 313/400 Siege gegen Solution_92 statt 170/400 der alten Abgabe. Dies ist Mahmouds Modellfortschritt, den Codex bestätigt hat.
- Der bereits vorhandene Checkpoint `all18_v4.pth` hat keinen bestätigten Vorteil. Neue Versuchsnamen beginnen mit `v4_joint_...`; vorhandene V4-Dateien nicht überschreiben oder als Erfolg umetikettieren.
- Eigene jüngste Variante `enemy_tie_energy`: 105/120 statt 102/120, gepaartes 95%-Kartenintervall der Differenz [−2,5; +8,33] Prozentpunkte. Kein qualifizierter Ersatz. Mehr Exploration, mehrere Regelvarianten und zusätzliche ähnliche Ensembles lieferten ebenfalls keinen bestätigten Gewinn.

## Warum dieser Ansatz?

In der gezielt verlustangereicherten Diagnose mit 20 Spielen gewann V3 Match 1 in 16 Fällen, Match 2 in sechs und Match 3 in drei. In späteren Matches lag die produktive Feldbelegung trotz hoher Feldkenntnis zurück. Die Auswahl ist nicht repräsentativ; die Ursache ist damit noch nicht bewiesen. Quelle: [Verlustdiagnose](../experiments/analysis/continuous_20261021/loss_observation/README.md).

Der Code enthält aber eine konkrete Struktur, die bisherige Versuche kaum ändern:

- `agents/sherlock/main.py`, `act`: Q-Werte mitteln, erlaubte beste Aktion weitgehend pro Schiff getrennt bestimmen.
- `agents/sherlock/features.py`, `assign_targets`: eindeutige Zielzuordnung über feste Prioritäten und schrittweise Auswahl aus einer Kostenmatrix. Das koordiniert Ziele, aber nicht die tatsächlich gewählten nächsten Aktionen.
- Sap-Zielpositionen kommen aus einer Heuristik. Das Netz entscheidet unter sechs Aktionsklassen, nicht frei über das Angriffsziel.
- Das vorhandene CNN gibt ebenfalls sechs Klassen pro Einheit aus. Ein größeres CNN oder der bloße Wechsel von DQN zu PPO löst diese Entscheidungsgrenze nicht automatisch.

**Hypothese:** Gemeinsame Auswahl weniger gelernter Aktionsalternativen kann unnötige Mehrfachbelegung vermeiden und Feldübergaben verbessern. Ob dies ausreichend häufig vorkommt und Spiele gewinnt, muss der erste Versuch zeigen.

## Reihenfolge

### 1. Kleine gemeinsame Aktionsauswahl auf unveränderter V3

Zunächst ausschließlich STAY/Bewegung kleiner Gruppen benachbarter, interagierender Schiffe betrachten. Die bereits gelernte V3-Bewertung liefert wenige erlaubte Alternativen; ein begrenzter Suchschritt bewertet ihre gemeinsame bekannte Punktefeldbelegung. Alle anderen Situationen und Sap bleiben zunächst wie V3. Kein universelles Verbot mehrerer Schiffe auf einem Feld: Stacking kann im Kampf sinnvoll sein. Keine Änderung aus dem bereits widerlegten Sapkosten/Kollisionsargument ableiten.

Vor dem ersten Spiel feste Gruppengröße, Zahl der Alternativen, Bewertung und Rechenzeitgrenze bestimmen. Beispieltests müssen sinnvolle Doppelbelegung ebenso erhalten wie unnötige Doppelbelegung erkennen. Der unveränderte V3-Zug bleibt eine Option und der technische Rückfall bei fehlenden gültigen Alternativen. Nur eigene Beobachtung und Belief als Eingabe; keine zukünftigen Gegneraktionen, versteckten Engine-Daten oder Seed-Sonderregeln.

Ein Kandidat, keine große Parameter-Suche. Umsetzung und kurzer Entwicklungsvergleich sind das erste begrenzte Arbeitspaket. Wird daraus wider Erwarten ein großes Suchsystem, den Umfang reduzieren statt zunächst Infrastruktur auszubauen. Dieses Paket braucht kein neues Training.

### 2. Kurzer Entwicklungsvergleich mit klarer Entscheidung

60 bekannte Entwicklungskarten 500720–500779, beide Seiten: je 120 Spiele gegen Solution_92 und Default. Eine unveränderte, vollständig passende V3-Referenz darf nach Prüfung von Code, Konfiguration, Engine, Gewichten und Spielschlüsseln wiederverwendet werden; ansonsten neu messen. Keine wiederholten Kontrolltrainings.

Für die Weiterprüfung vorsehen: mindestens +5 Prozentpunkte gegen Solution_92, keine verschlechterte Default-Siegzahl und eingehaltene Rechenzeitgrenze. Dies ist ein Auswahlkriterium auf bekannten Karten, noch kein Wirksamkeitsnachweis. Keine Verlängerung des Versuchs nach Sichtung eines knapp positiven Ergebnisses. Ein schwacher oder negativer Versuch wird dokumentiert und begründet beendet.

### 3. Lernen auf die nachgewiesene Schwäche ausrichten

Wenn gemeinsame Aktionswahl nützt, danach einen kleinen lernenden Bewerter für gemeinsame Alternativen oder strategische Ziele untersuchen. Zuerst prüfen, ob er auf getrennten Daten bessere Entscheidungen als die feste Bewertung vorhersagt; anschließend einen begrenzten Spiel-/Trainingsversuch. Neue Merkmale, Ziele oder Rewards jeweils getrennt testen. Bereits trainierte V3-Netze bleiben die Referenz; keine unkontrollierte Veränderung ihrer Eingabebedeutung.

Ein möglicher erster Datenpilot umfasst sechs Trainingskarten mit beiden Seiten, also zwölf Spiele, mit Aufzeichnung beider Agenten aus ihrer jeweils eigenen erlaubten Sicht. Datenobergrenze 128 MB, ein kleiner Lernkopf mit höchstens 15 Minuten Fit-Budget; dies sind Abbruchbudgets, keine Laufzeitversprechen. Trainings-/Validierungstrennung nach Karten, nicht nach einzelnen Schiffszeilen. Beobachtete Spielausgänge sind keine korrekten Werte für nicht ausgeführte Alternativen: Für einen Aktionsbewerter braucht es passende Vergleichsdaten; Imitationsgenauigkeit allein genügt nicht.

Wenn Stufe 1/2 keinen Vorteil zeigt, ist gelernte strategische Zielauswahl die nächste eigenständige Hypothese, keine automatisch aktivierte weitere Trainingsschleife. Sie müsste zusätzliche Informationen wie Erreichbarkeit, Energie, Bedrohung und verbleibende Matchzeit sinnvoll nutzen. Der feste Greedy-Zielverteiler ist dann die konkrete Vergleichsbasis. Erst nach billigem Machbarkeitstest ein Modell trainieren.

Imitation von V3/Solution mit anschließender Verbesserung durch RL bleibt eine Alternative, aber kein schneller Schalter: Der aktuelle Datensammler erwartet Sherlock-interne Zustände; sechs Aktionsklassen verlieren die freie Sap-Zielposition. Vorhandene Diagnose-JSONL enthalten nicht alle legalen CNN-Eingaben, und komplette alte BC-Daten fehlen lokal. Keine versteckte Enginewahrheit als Trainings-/Deployment-Merkmal übernehmen. Auf dem M3/8GB zuerst kleine Datenportionen und Lernprobe, kein erneuter großer BC/PPO-Lauf ohne Zusatznutzen. Die kleine PPO-Quantisierungsabweichung ist keine belegte Erklärung für die fehlenden Gewinne.

### 4. Kandidaten auf neuen Karten bestätigen

Erst den ausgewählten Kandidaten einfrieren. Einmalige Bestätigung auf 200 neuen Karten, beide Seiten gegen Solution_92 und Default; Referenz auf denselben Karten. Seeds vorab nach Remote-Abgleich auf Überschneidungen prüfen und reservieren. Nicht automatisch bisher reservierte Blöcke anderer Studien verwenden.

Übernahmekriterien des neuen Vorhabens: mindestens +5 Prozentpunkte gegen Solution_92, untere Grenze des gepaarten 95%-Kartenintervalls strikt über null, Default mindestens 99 % und höchstens ein Prozentpunkt unter V3. Zusätzlich direkter Vergleich auf 200 weiteren neuen Karten, beide Seiten: untere Grenze des über Kartenpaare ausgewerteten Kandidatenresultats strikt über 50 %. Remis dort als halbes Ergebnis; Siegquote separat berichten. Ganze Kartenpaare resampeln; Algorithmus und Zufallsseed vorab dokumentieren. Diese Zahlen sind neue geplante Kriterien, keine nachträglichen Änderungen alter Studien.

Nur ein vorab ausgewählter Kandidat betritt diese Bestätigung. Nach Fehlschlag nicht denselben Testsatz zur weiteren Optimierung als unberührt ausgeben. Keine Gewichtsübernahme allein wegen hoher Trainingssiegquote oder eines günstigen Entwicklungsresultats.

### 5. 100%-Ziel und Präsentation

Der bestehende finale Auditblock 520000–520999 bleibt bis zu einem qualifizierten, vollständig eingefrorenen Kandidaten unangetastet; vor Nutzung nochmals Remote-/Seedprüfung. 1.000 Karten × beide Seiten = 2.000 Spiele gegen Solution_92. Nur 2.000 tatsächliche Siege erlauben die Aussage „100 % auf diesem Testsatz“. Andernfalls das wirkliche Ergebnis einschließlich Unsicherheit berichten. Den Block nicht wiederholt testen, bis zufällig alles gewonnen wird.

Für den Prof: V3/V4 auf denselben frischen Karten, Ergebnisse pro Match, zwei nachvollziehbare Spielsequenzen, Laufzeit und ein Vergleich mit abgeschalteter neuer Komponente auf Entwicklungskarten. Ziel ist zu zeigen, welcher Mechanismus hilft, nicht nur einen neuen Versionsnamen.

## Ausführung und Zusammenarbeit

- Ein Implementierungsagent, ein unabhängiger Reviewer; Root integriert und kontrolliert Versuchsumfang. Keine parallelen Modelljobs jenseits eines Trainings oder zweier Evaluationsworker auf dem M3/8GB.
- Vor längeren Läufen eine kleine Laufzeitmessung und feste Versuchsdauer. Bei fehlendem Nutzen früh zwischen vollständigem negativem Ergebnis und technisch/organisatorisch unvollständigem Versuch unterscheiden.
- Bestehende Auswertungswerkzeuge verwenden. Nur Prüfungen, die für eine konkrete Änderung oder einen neuen Befund nötig sind. Keine zusätzliche allgemeine Audit-Infrastruktur.
- Sinnvolle getrennte Commits für Umsetzung und abgeschlossene Ergebnisse, Arbeitsstand/Experimentprotokoll für Mahmoud. Remote vor Beginn, vor Push und spätestens nach drei Stunden abgleichen; laufende Quellen einfrieren.
- V3 bleibt Abgabe bis zur nachgewiesenen Verbesserung samt Kurs-Runner-/Paketprüfung. Bei Austausch **die aktuelle V3** zusätzlich sichern; die alte Sechser-Sicherung unverändert erhalten.
- Statusberichte trennen laufendes Training, abgeschlossene Prüfung, neue Siege und Stillstand. Ein Repo-Monitor ersetzt keine aktive Entwicklungsarbeit.

Diese Strategie verspricht keinen bestimmten Siegquotensprung. Der nächste konkrete Liefergegenstand ist der erste kleine Koordinationskandidat mit einem vollständigen positiven oder negativen Vergleich, nicht eine weitere lange Trainingsserie.
