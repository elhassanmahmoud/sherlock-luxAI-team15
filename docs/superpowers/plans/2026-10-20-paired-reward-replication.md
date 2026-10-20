# Bedingte Fortsetzung des Reward-Piloten

Vor den Auswertungen des laufenden 400+400-Piloten am 20.10. festgelegt.
Noch kein Auftrag gestartet und kein Arm ausgewählt. Dieser Plan ergänzt
den autonomen Nachtauftrag; technische Freigabe und Zeitbudget bleiben nötig.

## Entscheidung nach dem Pilot

Zuerst müssen beide Trainings und vollständige Auswertungen einschließlich
Initialisierung, Quellcode-/Gewichtsidentität und endlicher gelernter Tensoren
geprüft sein. Bei einem klaren Nachteil der Korrektur zuerst Ursache prüfen,
nicht automatisch größere Trainings starten: Solution_92-Differenz höchstens
−5 Prozentpunkte mit vollständig negativem gepaarten Kartenintervall oder
beobachteter Default-Verlust größer als 2 Prozentpunkte. Ein breites Intervall
allein beweist weder Nutzen noch Schaden.

Die getrennten Inferenzvarianten werden vor einem längeren Trainingsblock
ausgewertet, damit ein schneller belegter Gewinn zuerst geprüft werden kann.

## Fester größerer Vergleich, falls sinnvoll und rechtzeitig abschließbar

- Drei frische, gepaarte Initialisierungen 47, 48, 49.
- Je 3.000 Spiele pro Arm; insgesamt 18.000, ein Trainer zur Zeit.
- Falls die gemessene Laufzeit samt Auswertung und mindestens einer Stunde
  Abschlussreserve nicht passt: vor irgendeinem Start **einheitlich**
  2.000 Spiele für alle sechs Läufe wählen. Auswahl dokumentieren.
- Einziger Unterschied `terminal_death_potential`, gleiche Anfangsgewichte,
  Karten, Gegnerfolge, sonstige Config. Inferenzvarianten ausgeschaltet.
- Keine Wiederaufnahme des Piloten, keine Zwischencheckpoint-Auswahl.
  Beide Arme jedes Starts vollständig durchführen.
- Seedbereiche bei 3.000 Spielen: 470000–471499, 480000–481499,
  490000–491499. Vor Start Remote auf Kollision prüfen.
- 25 % Default-Aufwärmphase, danach `sol92_frac=.7`, kein Pool,
  `--no-test --val-every 0`. Das entspricht dem bestehenden längeren
  Curriculum. Exploration sinkt schon nach etwa 200 Spielen; daher ist der
  Pilot mit 100 reinen Default-Spielen kein verkürztes Äquivalent zu den
  750 reinen Default-Spielen eines frischen 3.000er-Laufs.
- Finale Einzelnetze auf denselben 60 Entwicklungskarten 500720–500779,
  beide Seiten/default/Solution_92. Alle drei Startdifferenzen ausweisen.
  Kartenbootstrap allein erfasst die Streuung der Initialisierungen nicht.

Entwicklungsregel für die Trainingsmethode: mittlere Solution_92-Differenz
mindestens +3 Prozentpunkte, mindestens zwei von drei Starts positiv,
Default im Mittel höchstens −2 Prozentpunkte. Diese Regel wählt eine
weiter zu bestätigende Richtung; sie ist kein allgemeiner Stärkenachweis.
Keine Aussage nur aus niedrigerem Loss oder Siegquoten während des Trainings.

## Ensembles und mögliche Übernahme

Keine Auswahl der besten Einzelnetze. Wenn die Trainingsrichtung die obige
Regel erfüllt, zuerst `control3` gegen `fix3`, dann dieselbe feste Basis plus
alle drei Kontrollnetze gegen dieselbe Basis plus alle drei korrigierten
Netze auswerten. Identische Inferenzconfig und Netzanzahl.

Rohe Q-Werte werden gemittelt. Konstante Offsets ändern Argmax nicht, aber
unterschiedliche Abstände zwischen Aktionen können Netze stärker gewichten.
Diese Abstände auf legalen Aktionen prüfen; keine neue Normalisierung in
diesem Versuch. Zusätzliche Netze allein sind kein Verbesserungsnachweis.

Ein eventueller Abgabekandidat benötigt zusätzlich einen vorab reservierten,
noch unbenutzten Bestätigungsblock sowie die normalen technischen und
direkten Vergleichsprüfungen. 510000–510199 sind bereits für genau einen
Gewinner der Inferenzvarianten reserviert und dürfen nicht doppelt als
frische Trainingsmethoden-Bestätigung verwendet werden. Ohne klaren Vorteil
bleibt die geprüfte Abgabe bestehen, alle alten Sicherungen bleiben erhalten.
