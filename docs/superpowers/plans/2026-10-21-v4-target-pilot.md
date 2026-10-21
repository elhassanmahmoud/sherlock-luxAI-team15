# Separater V4-Zielpilot: zuerst Wirkung, dann Lernen

Vor neuen Daten am 21.10.2026 festgelegt. User autorisiert eigenständige
Folgearbeit bis 22.10.06:00 Berlin. V3 bleibt geschützt. Der erste
Paar-Koordinator ist negativ abgeschlossen; seine Grenzen werden nicht
nachträglich geändert. Dies ist die nächste Hypothese aus der
[freigegebenen Strategie](../../V4_STRATEGIE_20261021.md).

## Frage und kleinster erster Schritt

Andere strategische Ziele beeinflussen V3 hauptsächlich über vier der
79 Merkmale. Bevor ein Bewerter trainiert wird, muss eine Änderung des
Ziels die wirklich ausgeführte Aktion beeinflussen. Nur neue Zielnamen
oder bessere Trainingsgenauigkeit wären kein Fortschritt.

Basis: unveränderte V3-Gewichte, `joint_moves=False`, keine CNN-Policy,
kein Training des bestehenden Ensembles. Ein Modellprozess. Produktion
zunächst unverändert; Probe und Tests liegen im eigenen Experimentordner.

Karten reserviert: **524000–524005 Training**, **524006–524007 gehaltene
Prüfung**, beide Seiten gegen Solution_92. 523 CSVs lokal am 21.10. geprüft,
keine Seedüberschneidung; Remote zuletzt ohne fremde Änderungen. Diese
Karten sind ab Nutzung Entwicklungs-/Lerndaten, keine frischen Spielstärke-
Bestätigung. Bereiche 523000–523399 und 520000–520999 bleiben unangetastet.

Nur Matchindex 1/2, jeweils Matchschritt **25,45,65,85**. Diese acht
Zeitpunkte gelten für Probe, Datensammlung UND spätere Ausführung.

Einheitenauswahl: lebend, gültige Position, Energie mindestens Bewegungskosten,
nicht auf bekanntem Punktefeld; ihr bestehendes zugewiesenes Ziel muss
ein bekanntes Punktefeld sein. Alternative Ziele sind bekannte passierbare
Punktefelder, aktuell von keiner eigenen Einheit mit nichtnegativer Energie
besetzt und keinem anderen Schiff zugewiesen. Baselineziel ausschließen.
BFS auf dem bekannten `passable`-Raster, höchstens sechs Bewegungen;
Richtungsgleichstände UP, RIGHT, DOWN, LEFT. Höchstens drei Alternativen,
geordnet nach BFS-Distanz, dann Koordinaten. Unter Einheiten mit Alternativen
die mit größter Manhattan-Distanz zum Baselineziel nehmen, dann kleinste UID.
Kein verborgenes Kartenwissen und keine zukünftigen Gegneraktionen.

**Einflussprobe:** nur 524000/524001, beide Seiten, maximal 32 Zeitpunkte.
Jeweils reine V3-Kontrolle und identischer Lauf mit passiven Schattenaktionen
(acht volle Spiele zusammen). Schattenklone bekommen das andere Ziel nur
für genau diesen Zug. Alle vier Zielmerkmale neu bauen, tatsächliches `act`
inklusive nachgeschalteter Regeln aufrufen; keine bloße Q-Argmax-Auswertung.
Nur exakt unterschiedliche komplette Aktionsarrays zählen. Falls weniger
als **acht Zeitpunkte** irgendeine abweichende Aktion erlauben: Pilot
beenden, keine Erweiterung der Zielmenge, keine Schwellenänderung, kein Fit.

Kontrollprüfung: alle Spielaktionen und legalen Beobachtungen der fortgesetzten
V3-Trajektorie müssen mit/ohne Schattenaufrufe bitgenau übereinstimmen.
Vor und nach Schattenaufrufen Zustand der lebenden Instanzen prüfen; auch
Fehlerpfad darf sie nicht ändern. Beide Spielseiten testen. Bekannte blockierte
Zielzelle explizit abweisen (bestehende distance_map initialisiert ihr Ziel).

## Bedingter Lernpilot bei bestandener Einflussprobe

Sechs Trainings- und zwei gehaltene Karten, beide Seiten, acht Zeitpunkte:
maximal128 Ausgangszustände. Baseline plus bis zu drei unterschiedliche
erste Aktionsarrays. Identische Arrays deduplizieren. Jede Alternative
wird in einer getrennten Simulatorfortsetzung **zwölf Schritte** ausgeführt;
nur im ersten Schritt anderes Ziel, danach normale V3. Label ist die
Differenz des tatsächlichen Team-Punktevorsprung-Zuwachses zur Baseline
dieses Zustands. Kein Matchreset in den gewählten Fenstern. Keine eigenen
Distanz-Shaping-Rewards als Zielwert und keine Endresultate für ungespielte
Alternativen verwenden.

Simulatorzustand dient ausschließlich zur Durchführung der Trainingszweige.
Merkmalsfunktion erhält nur legalen Kontext. Keine Enginewahrheit, vollen
Parameter oder Seeds als Modellinput. Höchstens512 Zweige×12 Schritte,
16 vollständige Sammelspiele,128MB Daten;30Minuten Datenerhebung nach
Laufzeitprobe,15Minuten Fitbudget. Zeitgrenzen sind Abbruchgrenzen.

### Fester kleiner Bewerter

Für Ziel t: kanonische Koordinaten; Manhattan m, BFS d (unerreichbar49),
ein deterministischer kürzester Weg P ohne Start, mit Ziel. Energie gilt
als bekannt, wenn `belief.tile_type != -1`; Unbekanntes trägt0 bei.
E=Einheitenenergie, c=beobachtete Bewegungskosten,
r=clip((E−c*d+Summe bekannter Wegenergien)/100,−4,4),
h=(100−Matchschritt)/100. Sichtbare gültige Gegner mit Energie>=0.
q=Anteil Wegzellen in beobachteter Sap-Reichweite (Chebyshev) eines Gegners.
Leerer/unerreichbarer Weg: Mittel/Minimumenergie0, unbekannter Anteil1,
Nebelanteil0,q0. Das sind Näherungsmerkmale, keine Physiksimulation.

20 Merkmale in fester Reihenfolge:
dx/24,dy/24,m/48,d/48,erreichbar,(d−m)/48,Gegnerhälfte,
Zielenergie bekannt,Zielenergie/20,Wegmittelenergie/20,Wegminimumenergie/20,
Weganteil unbekannt,Weganteil bekannter Nebel,r,
Gegnerzahl in Sap-Reichweite des Ziels/16,deren Energiesumme/6400,
kleinste Gegnerdistanz zum Ziel/24 (ohne Gegner1),q,h*d/48,r*q.
Energie-Merkmale9–11 auf[−1,1] begrenzen; unbekannte Energie0.

Input ist Kandidat minus Baseline. Pro Spalte Trainings-RMS, unter1e−8
durch1 ersetzen; keine Zentrierung. Ridge alpha1, kein Intercept, keine
Hyperparametersuche. Baselinevorhersage genau0. Alternative nur bei
höchster Vorhersage strikt>0,25 Punkten, Gleichstand nach Kandidatenreihenfolge.
Speicher-/Ladetest muss dieselben Vorhersagen und Handlungen liefern.

Vor Fit mindestens20 unterschiedliche aktionsändernde Trainingszustände
und positive tatsächliche Alternativen auf mindestens3/6 Trainingskarten.
Gehaltene Prüfung: mindestens8 aktionsändernde Zustände; positiver kumulierter
tatsächlicher Gewinn der gewählten Alternative auf JEDER gehaltenen Karte;
gesamt mindestens+0,25 Punkte pro geplantem Zeitpunkt, ausgelassene/Fallback-
Zeitpunkte zählen0. Kein Nachfitten oder Nachlegen nach Sichtung dieser Daten.
Erst danach ein normaler Entwicklungstest gegen Solution/Default/V3 mit
den unveränderten Gates des ersten Plans. Keine Freigabe allein aus Zweiglabels.

### Isolation der Simulatorzweige

Unverpackte Gym-Env flach kopieren: immutable JAX-state/rng_key/env_params,
jax_env teilen, nie reset/render in Zweigen. Sherlock dynamisch tief kopieren;
nur eingefrorene q/target_q/extra_q,Optimizer und leerer unbenutzter Buffer
teilen. Kein update/save/moduswechsel. Beliefalias/cache/paths/rng bleiben
im Klon konsistent. Solution-Instanz, sämtliche nichtaufrufbaren Global-
Datenattribute, Sherlock und Beobachtungen gemeinsam kopieren, damit
Node-Verweise erhalten bleiben. Live-Global-Objektreferenzen in finally
wiederherstellen, neu erzeugte Datenattribute entfernen. Python-/NumPy-/
Torch-CPU-RNG vor jedem Zweig wiederherstellen; JAX-Key liegt in der Env.

Vor Labels: wiederholter Baselinezweig reproduziert echte zwölf Folgeschritte
inklusive Aktionen, Beobachtungen, Punkte, finalem Zustand/Key; umgekehrte
Alternativenreihenfolge liefert dieselben Labels. Fortgesetzter Liveverlauf
bleibt inklusive Fehlerfall unverändert. Keine Erweiterung zu einem
allgemeinen Suchframework; scheitert die Isolation, endet der Pilot.

## Arbeitsteilung und Abnahme

Root besitzt Plan, Daten/Gates, Ressourcen und Integration. Frischer
Implementer zunächst nur Einflussprobe; unabhängiger Review vor Ausführung.
Kein Modelljob durch Subagents ohne ausdrückliche Root-Zuteilung. Nach
abgeschlossener Stufe sinnvoll committen/pushen und Arbeitsstand ergänzen.
Fremde Änderungen erhalten. V3/alte Sicherung vor/nach jedem Modelljob per
Hash prüfen. Quellen während Läufen einfrieren. 05:15 Berlin intern Schluss
für Experimente,06:00 harte Usergrenze. Eine fehlgeschlagene kleine Probe
rechtfertigt keinen erneuten großen Trainingslauf.
