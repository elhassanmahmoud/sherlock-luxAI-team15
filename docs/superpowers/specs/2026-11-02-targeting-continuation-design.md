# Sherlock: gezielte Fortsetzung 02./03.11.

## Auftrag und Ausgang

Moayed hat am 02.11. selbstständige Weiterarbeit bis **03.11.2026, 06:00 Europe/Berlin**
autorisiert. Subagents, Training, aussagekräftige Vergleiche, sinnvolle Commits und
Push sind weiter freigegeben. Präsentation erst auf gesonderten Auftrag bearbeiten.
V14 bleibt die Referenz, solange kein neuer Kandidat die vorab festgelegten Gates
nachweislich besteht. Die abgeschlossene Studie vom 01./02.11. wird nicht verlängert
oder nachträglich umgedeutet; ihr CONTROL-Kandidat scheiterte in der Bestätigung.

Start: main/origin/main `3a7e782`; V14-SHA-256
`98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8`.
Die vorhandene Sicherung unter `experiments/releases/20261101_v14_baseline/`
und die ältere Sicherung `20261020_old3_sym3` bleiben unverändert.

## Ansätze und Entscheidung des Koordinators

1. **Zielplanung und Energie zuerst erklären.** Bekannte freie Felder ohne Ziel
   waren eine Beobachtung, kein Bugnachweis. Ein externer passiver Trace soll
   unbekannte/unerreichbare Ziele, knappe Units, andere sinnvolle Ziele und
   tatsächliche Endaktionen auseinanderhalten. Erst dann eine minimale Änderung.
2. **Begrenzte exakte Inferenz separat technisch prüfen.** Der vorhandene
   Gauß-Prototyp auf dem Followup-Branch ist noch nicht für echte Agentenspiele
   zugelassen. Reine Tests und ein Mikrobenchmark ersetzen weder Kompatibilität
   noch einen Shadow-Test. Ein eigenständiger neuer Admissionpfad ist möglich.
3. **Nachtraining erst mit begründeter Fragestellung.** Ein weiteres einzelnes
   Netz in einem 36er-Ensemble oder ein geänderter Reward ohne passende
   Planungsinformation ist keine belegte Lösung. Falls ein Planungsproblem
   bestätigt und behoben wird, Rollout und Auswertung konsistent halten;
   Trainingsstart, Lernrate, Gegner, Endcheckpoint und Vergleich vorher festlegen.

Diese Reihenfolge ist eine Umsetzungsauswahl des Koordinators innerhalb des
ausdrücklich autonomen Auftrags, keine vom Nutzer zugesicherte Wirkung.
Pauschale Heimpriorität, feste Energiereserven, Sticky-Ziele und unstack werden
wegen der dokumentierten negativen Versuche nicht blind wiederholt.

## Verbindliche Grenzen

- Maximal zwei schwere Rechenworker auf dem M3/8 GB, kein Volltest parallel dazu.
- Nutzer-Nachtrag 02.11., 13:17 Berlin: Netzteil kommt später, Weiterarbeit auf
  Akku ausdrücklich gewünscht. Bei Start 85–86 %. Rechenläufe auf Akku sind
  deshalb erlaubt; Ladestand überwachen, unter 35 % keine neue lange Phase,
  bei 25 % eigene schwere Jobs kontrolliert beenden/sichern. Teilblöcke bleiben
  unvollständig und liefern keine Übernahmeentscheidung. Netzbetrieb hebt diese
  Akkugrenzen auf. Diese aktuelle Nutzeranweisung ersetzt die anfängliche
  vorsichtige Netzteilvoraussetzung.
- Mindestens 30 % Codex-Kontingent erhalten; ab 65 % Verbrauch Abschluss
  einleiten, spätestens bei 70 % keine Entwicklung. Kein Reset.
- Wahrheit aus der Engine ausschließlich in getrennter Diagnose nachgelagert
  auswerten, niemals an Agent, Reward oder neue Produktionsregel weiterreichen.
- Neue Quellen, HEAD und Gewichte während eines festgelegten Vergleichs
  einfrieren. Eigene Arbeit isoliert im bestehenden Worktree
  `sherlock-v10-mechanics`, Branch `improvement/targeting-20261102`.
- Fremde unversionierte Dateien erhalten; kein Reset/Force-Push. Remote-Watch
  darf abrufen, Integration erst an einem sicheren Phasenübergang.
- Keine Teilresultate als vollständigen Block ausgeben. Keine nachträgliche
  Karten-/Kandidatenwahl nach einer gescheiterten Bestätigung.

## Passiver Trace

Die Ausgangsmetrik ist in
`experiments/analysis/night_20261101/targeting_metric_notes.md` definiert.
Der Trace beobachtet einen unveränderten Agenten und protokolliert getrennt:

- Zeitpunkt, Spiel/Seite/Match, Belief-Ziele, eigene Position/Energie,
  bekannte Karte, sichtbare Gegner, Eingabemerkmale, gemittelte Q-Werte,
  Aktionsmasken und endgültige Aktion in kanonischen Koordinaten.
- Agentensichtig freie bewiesene eigene Punktefelder, zugewiesene Ziele,
  BFS-Erreichbarkeit nach damaligem Wissen und verfügbare bewegungsfähige
  Nicht-Halter. Aktuelle Energie genügt nicht automatisch für einen ganzen Weg;
  Regeneration und unbekannte Wegenergie nicht als bekannt behandeln.
- Nachgelagerte wahre Belegung, tatsächliche Bewegung und Verluste. Unsichtbare
  Gegner dürfen den Nenner erklären, nicht die Entscheidung steuern.
- Veränderung der Netzentscheidung durch beobachtete Regelstufen. Nicht
  instrumentierte Inline-Regeln ehrlich als unaufgelöste Differenz kennzeichnen.

Ein Trace muss bei identischem Seed/Seite **identische Aktionen und Ergebnisse**
gegenüber dem unbeobachteten Agenten liefern. Er darf keine Vorhersage der
zukünftigen Karte, erfolgreiche Versorgung oder kausale verpasste Punkte behaupten.
Zunächst nur verbrauchte Diagnosekarten, Verluste und vorab bestimmte Kontrollen.

## Neue Leistungsstudie

Neue Reservierung (nach Seed-Audit): Diagnose 840000–840039,
Auswahl 841000–841099, Bestätigung 842000–842299,
Direkt 843000–843299, Technik 844000–844099.
Nicht alle reservierten Karten müssen gespielt werden; konkrete Umfänge und
Kandidaten werden vor dem ersten Leistungsresultat in einem verbindlichen
Nachtrag festgelegt. Abgeschlossene November-Auswahl und -Bestätigung sind
verbraucht und werden ausschließlich als Entwicklungs-/Diagnosedaten verwendet.

Lokales Panel unverändert: Solution_92, Quadrat-Solution, eingefrorene V3, V7,
V10, V13; default getrennt. Kein stiller Ersatz fehlender historischer Gegner.
Neue Stärkekandidaten nur nach technischem Review/Regression/realem Spiel.
Maximal ein Nominierter in eine unabhängige Bestätigung; kein Nachrücken.

Übernahmebedingungen bleiben gemeinsam erforderlich: Panel-Δ mindestens +1 pp
und untere 95-%-Grenze > 0; Solution-Δ mindestens 0 und untere Grenze mindestens
−1 pp; default mindestens 99 % und Δ mindestens −1 pp; Direktduell untere Grenze
> 50 %. Kartenweiser gepaarter Bootstrap, 5000 Ziehungen, Zufallsseed 0.
V14s frühere Team-Ausnahme senkt diese Hürden nicht. 100 % auf einem endlichen
Testsatz wären keine Garantie für alle unbekannten Karten/Gegner.

Vor 05:00 keine neue Phase beginnen, die nicht vollständig mit Schlussreserve
bis 05:30 passt; 05:30–06:00 Abschluss. Qualifizierten Nachfolger vor Austausch
sichern, Kurs-/ZIP-Prüfung durchführen; sonst V14 belassen. Dokumentation nennt
auch negative Ergebnisse und unvollständige Arbeit.
