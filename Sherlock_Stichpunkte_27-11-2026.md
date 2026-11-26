# Sherlock V16 · Stichpunkte für die Abschlusspräsentation am 27. November

[Präsentations-PDF](Sherlock_Finale_27-11-2026.pdf) · [Editierbare Folien (HTML)](docs/presentation/finale_2711/Sherlock_Finale_27-11-2026.html) · [Gemeinsame Generalprobe](docs/presentation/finale_2711/GENERALPROBE_2711.md)

## Das Wichtigste für Freitag (Stand 26.11.)

| Was | Stand |
|---|---|
| **Abgabe-ZIP** | Für „Submission Battle Session 2“ die Datei `dist/Gruppe15.zip` mit dem Ordner `Gruppe15/` verwenden. Agentenklasse `Gruppe15.main.Agent_x`, Gewichte für beide Startseiten `Gruppe15/agent.pth`, SHA-256 `8347ea2b…ae95`. Die gleichnamige ZIP im Projektstamm enthält noch V14. |
| **ZIP geprüft** | Am 24.11. beide neu gebaut, bytegleich mit dem Release. Beide Seiten laden, auch mit `train=True`, mit dem Ordner unter `agents/` und in der Projektwurzel. Die Battle-ZIP gewann im unveränderten Kursrunner gegen Solution_92 von jeder Startseite ein ganzes Spiel mit 3:0 Matches. Der Agent braucht nur torch und numpy und läuft auf der CPU. Python 3.10 hat Moe am 22.11. geprüft (9.696 gleiche Befehle). |
| **Präsentation** | `Sherlock_Finale_27-11-2026.pdf`: 10 Folien und 5 Reservefolien. Neu am 26.11.: Folie 10 schließt das Projekt ab. Die zweite Reliktgruppe steht dort jetzt als Ausblick und nicht mehr als nächstes Ziel, die Fußzeile nennt V16 unsere finale Version. Dazu neuer Sprechtext für die Folien 1 und 10. Am 24.11.: Stand nach V16 auf Folie 10, neue Zahlen auf R1, neue Reservefolie R5. |
| **Abgabefrist** | Der Agent war laut Moodle bis **Mittwoch, 25.11.2026, 23:59 Uhr** fällig (`dist/Gruppe15.zip`). Vor dem Vortrag in Moodle nachsehen, ob dort diese Datei mit V16 liegt. Eine eigene PDF-Uploadfrist oder Slotzeit nennt dieser Moodle-Eintrag nicht. |
| **Ablauf am 27.11.** | Laut Kursfolie 10 stellen zwei Teams ihre Agenten je 10 Minuten vor. Danach spielen die Agenten drei Spiele mit je drei Matches, das Replay läuft in doppelter Geschwindigkeit. Turniermodus mit Preis. Benotet werden die drei Präsentationen mit je 33 % (Kursfolie 8). Es ist unsere letzte Präsentation, danach ist das Modul abgeschlossen. |
| **Mitnehmen** | Laptop mit der PDF offline, die Replay-Datei zu Folie 7 (`docs/presentation/finale_2711/replays/V16_Kaggle_4247.html`), die PDF zusätzlich auf einem USB-Stick. |
| **Proben** | Zweimal mit Stoppuhr nach der [Generalprobe](docs/presentation/finale_2711/GENERALPROBE_2711.md), Ziel 9:50. |

**Planzeit 9:50 Minuten für 10 Folien, dazu 5 Reservefolien für Fragen. Noch keine gemeinsame Zeitprobe.**
Moe: Einstieg, Weg bis zum Battle, Schalter und Handtaktiken, Ergebnis, Fazit (5:05). Mahmoud: wie V16 lernt und
entscheidet, mit einem echten Zug (4:45). Die Zeiten enthalten Zeige- und Übergabepausen. In eigenen Worten sprechen,
die Folien nur als Stütze nehmen.

**Kernaussage, die am Ende hängen bleiben soll:** Sherlock hat das Kämpfen vom Kaggle-Dritten gelernt und schlägt
damit unsere beste frühere Version in 194 von 200 Spielen. Handregeln helfen dem gelernten Netz kaum noch.

| Folie | Wer | Dauer | Bis |
|---|---|---:|---:|
| 1 · Sherlock V16 | Moe | 0:30 | 0:30 |
| 2 · Wo gibt es Punkte? | Moe | 0:55 | 1:25 |
| 3 · Platz 3 mit V14 | Moe | 1:10 | 2:35 |
| 4 · Die Idee: vom Kaggle-Dritten lernen | Mahmoud | 1:10 | 3:45 |
| 5 · Nur zuschauen reicht nicht: DAgger | Mahmoud | 1:15 | 5:00 |
| 6 · So entscheidet V16 in jedem Zug | Mahmoud | 1:10 | 6:10 |
| 7 · Kein Gegner sichtbar, trotzdem vier Treffer | Mahmoud | 1:10 | 7:20 |
| 8 · Drei Schalter helfen, 17 Handtaktiken nicht | Moe | 1:00 | 8:20 |
| 9 · 194 Siege gegen R3 | Moe | 0:55 | 9:15 |
| 10 · Was wir mitnehmen | Moe | 0:35 | 9:50 |

## Folie für Folie

### 1 · Sherlock V16 (Moe)

- „Im Battle am 6. November wurde Sherlock Dritter. Heute, in unserer letzten Präsentation, zeigen wir, was danach
  passiert ist: Sherlock hat vom Drittplatzierten des Kaggle-Wettbewerbs gelernt.“
- Frage aufwerfen, die am Ende beantwortet wird: „Was macht man, wenn das eigene Training nicht mehr weiterkommt?“

### 2 · Wo gibt es Punkte? (Moe)

- Links das Rätsel: vier verschiedene Felder besetzt, drei Punkte mehr. Zwei Felder sind bekannt, also bringt genau
  eines der beiden offenen Felder den dritten Punkt. Kurz Zeit zum Mitdenken lassen.
- Rechts: Das ist Sherlocks Gedächtnis. Es merkt sich Relikte und Punktefelder über alle Matches, nutzt die
  Spiegelsymmetrie der Karte und verfolgt wandernden Nebel, Asteroiden und das Energiefeld.
- Überleitung: „Dieses Gedächtnis haben wir selbst gebaut. Es ist bis heute die Eingabe für Sherlocks Netz.“

### 3 · Platz 3 mit V14 (Moe)

- Auf die Kurve zeigen: vom Review am 16.10. mit 47 % gegen Solution_92 bis 95 % mit V14 im Battle. Dahinter stecken
  DQN-Netze (erst 18, dann 36) und viele Regeln für Wege, Schüsse und Nebel.
- Rechts: Gegen den Kaggle-Dritten gewann V14 nur 12 von 800 Spielen. Im ersten Match verliert V14 im Mittel 23
  Einheiten, der Kaggle-Dritte nur gut eine. Er gewinnt den Kampf um Energie: mehr Energie heißt öfter schießen und
  Zusammenstöße gewinnen.
- „17 Handregeln haben wir dagegen getestet. Wir haben V14 sogar alle Punktefelder verraten, ein Orakel. Nichts
  davon brachte einen Durchbruch. Uns fehlte Kampfstärke, nicht Wissen.“
- **Übergabe an Mahmoud:** „Wenn wir das Kämpfen nicht selbst hinbekommen: Warum lernen wir es nicht vom Besten?“

### 4 · Die Idee: vom Kaggle-Dritten lernen (Mahmoud)

- **Offenlegen:** „Unser Lehrer ist lux3-bot, Platz 3 im Kaggle-Wettbewerb zu Lux AI Season 3. Er ist öffentlich
  unter der Apache-Lizenz. Er hat selbst aus Replays der besten Kaggle-Teams gelernt. Sein Code ist nicht in unserer
  Abgabe. Sherlock spielt mit eigenen Netzen.“
- Die drei Schritte: Der Lehrer spielt 1.800 Spiele. Sherlock läuft unsichtbar mit und schreibt für jede Einheit und
  jeden Zug auf, was Sherlock selbst sieht und was der Lehrer tut. Das sind rund 9 Millionen Beispiele.
- Das Netz lernt, die Entscheidung des Lehrers vorherzusagen: welche der sechs Aktionen und bei Schüssen welches Feld.
  Kreuzentropie einfach erklären: Je höher das Netz die Lehreraktion einschätzt, desto kleiner der Fehler.
- Unten zeigen: Das Netz bekommt nur Sherlocks eigene Sicht. Was der Lehrer intern weiß, sieht es nicht.

### 5 · Nur zuschauen reicht nicht: DAgger (Mahmoud)

- Problem: Ein Netz, das nur Lehrerspiele gesehen hat, macht kleine Fehler und landet dann in Lagen, die der Lehrer
  nie hatte. Unser erstes Netz blieb dann oft einfach stehen.
- DAgger erklären (Dataset Aggregation): Sherlock spielt selbst. Der Lehrer sagt zu jeder Lage, was er an Sherlocks
  Stelle tun würde. Diese Lagen kommen zu den Beispielen, das Netz lernt weiter, nächste Runde. So lernt das Netz
  gerade die Lagen, in die es sich selbst bringt.
- Auf die Kurve zeigen: nur mit Lehrerspielen 78 % gegen Solution_92, nach vier Runden 98 %. Ab Runde 3 lag das Netz
  auf denselben Karten über V14 (94 %). Runden 5 und 6 brachten kaum noch etwas.
- „Insgesamt: 6 Runden mit 3.400 Spielen und zusammen 19 Millionen Entscheidungen.“

### 6 · So entscheidet V16 in jedem Zug (Mahmoud)

- Links von oben nach unten: Eingabe sind 16 Kartenebenen aus dem Gedächtnis (24 × 24 Felder) und je Einheit 79
  Merkmale plus ihre letzte Bewegung. Ein CNN aus Residual-Blöcken erkennt Muster auf der ganzen Karte. Für jede
  Einheit liest es den Wert an ihrer Position. Zwei Köpfe: Wahrscheinlichkeiten für die sechs Aktionen und eine
  Bewertung jedes Feldes als Schussziel.
- Rechts zeigen: v9 (0,7 Mio. Parameter) und v8L (1,8 Mio.) bewerten dieselben sechs Aktionen. Die Maske blendet
  gesperrte Aktionen wie einen Zug in einen Asteroiden aus. Für jede übrige Aktion multipliziert Sherlock die beiden
  Wahrscheinlichkeiten. Den Wert fürs Stehen multipliziert er mit 0,37, außer beim Halter eines bekannten Punktefelds.
- Jede Einheit wählt zunächst die Aktion mit dem höchsten Wert. Wählen mehrere vom selben Feld aus „stehen“, darf
  eine bleiben. Die übrigen wechseln zu ihrer besten erlaubten Bewegung, wenn sie ziehen können. Ein bereits
  gewählter Schuss bleibt erhalten. Bei einem Schuss bestimmt die Zielkarte das beste erreichbare Feld.
- Unterschied zu V14 in einem Satz: „V14 hat Belohnungen geschätzt, V16 schätzt, was der Lehrer tun würde.“

### 7 · Kein Gegner sichtbar, trotzdem vier Treffer (Mahmoud)

- „Das ist ein echter Zug von V16 gegen den Kaggle-Dritten.“ Karte 4247, Match 3, Zug 66. Helle Felder sieht
  Sherlock, graue nicht. Die roten Kreise sind die Kaggle-Einheiten, die Sherlock in diesem Moment nicht sieht.
- Die Einheit sieht keinen einzigen Gegner. Trotzdem wählt das Netz mit 88 % „schießen“. Die Zielkarte wählt Feld
  (17, 13), sieben Felder weit: ein Punktefeld neben dem gegnerischen Relikt, das Sherlock aus dem Gedächtnis kennt.
- Auf dem Feld und direkt daneben standen vier Kaggle-Einheiten: ein direkter Treffer, drei durch Streuschaden.
- Unten: In 10 Spielen gegen den Kaggle-Dritten gingen 286 von 1.438 Schüssen auf Felder ohne sichtbaren Gegner, und
  82 % davon trafen. Unsere Erklärung: „Wer Punkte holen will, muss auf einem Punktefeld stehen. Also schießt man
  dorthin, auch wenn man niemanden sieht. Das hat das Netz vom Lehrer übernommen.“
- **Übergabe an Moe:** „Wenn das Netz so viel selbst kann: Brauchen wir unsere alten Regeln noch?“

### 8 · Drei Schalter helfen, 17 Handtaktiken nicht (Moe)

**Merkfolge für die Minute:** Maske → Stehen bewerten → Aktion wählen → doppelte Stehbefehle auflösen.

- „Die Maske sperrt zuerst die Aktionen, die für das Schiff ausscheiden. Die beiden Netze bewerten die übrigen Möglichkeiten. Weil Sherlock früher zu oft stehen blieb, bekommt Stehen einen Abzug.“
- „Schaut auf Einheit 2 links. Sie hält ein bekanntes Punktefeld. Für sie entfällt der Abzug. Dadurch wird Stehen ihre beste Aktion und sie sammelt dort weiter Punkte. Sie dürfte das Feld auch verlassen.“
- „Erst nach der Auswahl schaut Sherlock, ob mehrere Schiffe auf demselben Feld stehen bleiben wollen. Eines bleibt. Die anderen nehmen ihre beste erlaubte Bewegung, wenn es eine gibt.“
- Auf die Balken rechts zeigen: „Zusätzliche feste Taktiken haben wir auch getestet. Alle zusammen verschlechterten unser Ergebnis gegen den Kaggle-Dritten.“

**Für Rückfragen:** Am gezeigten Zug steigt der Wert fürs Stehen von 41 % auf 65 %. Der gemessene Zuwachs von 1,6 Prozentpunkten beim Punkteanteil gegen Kaggle gehört zur Halter-Regel **zusammen mit** der milderen Stehstrafe. Beim ersten Netz halfen Stehabzug und Entstapeln zusammen gegen Solution (49,5 % auf 78 % auf Entwicklungskarten).

### 9 · 194 Siege gegen R3 (Moe)

- Kurz einordnen: R3 war bis zum 17. November unsere Finalversion, V14 mit einem kleinen nachgeahmten Berater für
  Bewegungen.
- Links: Auf 400 frischen Karten gewinnen beide 787 von 800 Spielen gegen Solution_92. Gegen den Kaggle-Dritten
  verdoppelt V16 die gewonnenen Spiele (20 statt 10) und gewinnt fast dreimal so viele Matches (216 statt 76).
  Direkt gegen R3: 194 von 200.
- Rechts: Im Kampf verliert V16 weniger Einheiten (17 statt 24 je Match), zerstört mehr gegnerische (8 statt 3) und
  trifft dreimal so oft direkt. Kaggle holt gegen V16 rund 300 statt 377 Punkte je Match.
- „Diese Prüfung war vorher festgelegt und lief auf Karten, die wir vorher nie benutzt hatten.“

### 10 · Was wir mitnehmen (Moe)

**Merkfolge für die 35 Sekunden:** Antwort auf die Eingangsfrage → ein Sieg mehr reicht nicht → V16 spielt heute → mit mehr Zeit: zweite Reliktgruppe → „Das war Sherlock.“

„Unsere Antwort auf die Frage vom Anfang: vom Besten lernen, so hat Sherlock das Kämpfen gelernt. Zuletzt testeten wir, ob ein freies Schiff bei schlechter Sicht das erste Relikt früher findet. Dieser Kundschafter gewann gegen Solution 178 von 192 Spielen, V16 177. Ein Sieg mehr reicht nicht, deshalb spielt V16 heute im Turnier. Mit mehr Zeit hätten wir an der zweiten Reliktgruppe angesetzt: früh finden, ein freies Schiff hinschicken, das Punktefeld halten. Das war Sherlock. Danke! Habt ihr Fragen?“

**Für Rückfragen:** Reservefolie R5 zeigt die anderen Versuche. Auf den elf Startplätzen, auf denen beide Varianten gegen Solution verloren, lag V16 in allen 18 verlorenen zweiten oder dritten Matches bei den später aktivierten Reliktgruppen hinten.

## Fragen, mit denen wir rechnen

| Frage | Antwort in zwei Sätzen |
|---|---|
| Ist das noch Reinforcement Learning? | Bis zum Battle haben wir RL gemacht (DQN und PPO mit CNN, zusammen 662.504 Trainingsspiele). V16 lernt durch Nachahmung und DAgger; der nächste Schritt wäre RL-Feintuning ab diesem Netz. |
| Habt ihr den Kaggle-Bot kopiert? | Nein. Wir haben weder seinen Code noch seine Gewichte übernommen, er läuft nur beim Sammeln der Daten. Unser Netz hat eigene Eingaben aus Sherlocks Gedächtnis, eine eigene Architektur und eigene Gewichte; die Kursfolie 50 verweist ausdrücklich auf die Kaggle-Rangliste. |
| Warum ist der Lehrer im direkten Duell häufiger erfolgreich? | Im Training übt Sherlock, aus seiner eigenen Sicht dieselbe Aktion wie der Lehrer zu wählen. Das gelingt in Lehrerspielen bei 87 % der Aktionen, bei den Schüssen erkennt Sherlock aber nur 36–50 %. Die internen Pläne des Lehrers kennt unser Netz nicht. |
| Was ist DAgger genau? | Dataset Aggregation (Ross, Gordon, Bagnell 2011): Der Schüler spielt, der Lehrer beschriftet die Lagen des Schülers, alles kommt in einen gemeinsamen Datensatz. So lernt das Netz die Lagen, die es selbst erzeugt. |
| Was unterscheidet die zwei Netze? | Beide sehen dieselbe Karte. Das kleinere Netz v9 hat sechs Blöcke und lernte bis zur sechsten DAgger-Runde. Das größere v8L hat acht Blöcke und stammt aus Runde fünf. In separat aufgezeichneten Lehrerspielen trafen sie gemeinsam bei 87,28 % der Aktionen die Lehrerwahl, v9 allein bei 86,90 %. Bei Schüssen lag v9 allein etwas öfter richtig. Der kleine Gesamtvorteil betrifft die Nachahmung. Die Spielstärke haben wir in echten Duellen geprüft. [Messwerte](experiments/analysis/umbau_20261115/v9/ERGEBNIS.md) |
| Warum habt ihr kein drittes Netz genommen? | Das haben wir ausprobiert. Mit dem dritten Netz stieg unser Punkteanteil gegen Kaggle um 0,18 Prozentpunkte. Für diesen Versuch hatten wir vorab mindestens einen Prozentpunkt verlangt. [Spielvergleich](experiments/analysis/devg_20261117/ERGEBNIS.md) |
| Wozu noch die Maske? | Sie verhindert offensichtlich unsinnige oder gefährliche Züge (Rand, Asteroid, zu wenig Energie, stärkerer Gegner). Ohne Masken lag das Netz im Test 0,71 Prozentpunkte Punkteanteil gegen Kaggle schlechter (nicht gesichert, das Intervall enthält null). |
| Warum die Stehstrafe? | Der Lehrer verfolgt Pläne über mehrere Züge, die das Netz nicht sieht. Im Zweifel blieb es stehen (58–67 % der Züge statt 46 % beim Lehrer); die Strafe gleicht das aus. |
| Wie habt ihr getestet? | Jede Karte von beiden Seiten, Regel vor dem ersten Spiel festgelegt, Auswahl auf Entwicklungskarten, Bestätigung auf nie benutzten Karten, gepaarte Auswertung nach Karte mit Bootstrap. Insgesamt über 1,55 Millionen Spiele seit dem 10. Oktober. |
| Was war euer eigener Beitrag? | Gedächtnis und Merkmale (16 Kartenebenen, 79 Merkmale), die ganze Lernkette mit DAgger, die Schalter aus der Spielanalyse wie die Halter-Regel, die schrittgenaue Nachrechnung der Kämpfe und die Prüfungen. |
| Warum ist V16 gegen Solution nicht besser als R3? | Beide liegen bei rund 98 %; auf einem weiteren frischen Kartensatz lag V16 sogar 11 Spiele von 800 hinter R3 (778 statt 789). Wir haben V16 gewählt, weil es gegen den viel stärkeren Kaggle-Dritten klar besser ist und R3 direkt 194 von 200 Mal schlägt. |
| Wo fehlen euch gegen Solution noch Siege? | „Wir haben alle 35 Niederlagen aus zwei Tests mit insgesamt 1.600 Spielen nachgespielt. 27-mal haben wir das erste Match gewonnen und danach beide verloren. Das knappere verlorene Match war meistens das zweite. In den untersuchten verlorenen Matches 2 und 3 holte Solution an den später erscheinenden Relikten jedes Mal mehr Punkte, 18 von 18. Genau dort hätten wir als Nächstes angesetzt.“ [Rekonstruierte Matchstände](experiments/analysis/v16_finalwoche_20261122/spielabstand/ERGEBNIS.md) · [Punkte je Reliktgruppe](experiments/analysis/relictsuche_20261123/gemeinsame_niederlagen/ERGEBNIS.md) |
| Habt ihr nach dem V16-Release eine stärkere Version gefunden? | „Wir haben danach über 20 Ideen geprüft, allein in den Vergleichen auf Reservefolie R5 9.176 Spiele auf neuen Karten. Am nächsten kam ein Kundschafter, der bei kurzer Sicht ein freies Schiff das erste Relikt suchen lässt: 319 von 320 Spielen gegen Solution, V16 316. In der vorab festgelegten Wiederholung waren es nur noch 178 zu 177 von 192, direkt 102 von 192. Das reicht nicht für einen Wechsel, deshalb spielt V16.“ [160 Karten](experiments/analysis/relictsuche_20261123/abschlusspruefung/ERGEBNIS.md) · [Wiederholung](experiments/analysis/relictsuche_20261123/sicht1_wiederholung/ERGEBNIS.md) · [alle Vergleiche](docs/MORGENBERICHT_20261123.md) |
| Wie geht es mit Sherlock weiter? | „Mit dem Modul endet heute auch unser Projekt, V16 ist die finale Version. Wer weitermacht, sollte bei der zweiten Reliktgruppe ansetzen und das Netz durch eigenes Spielen mit RL nachtrainieren, zum Beispiel mit PPO nahe am Lehrer.“ |
| Läuft eure Abgabe sicher beim Prof? | Sie braucht nur torch und numpy und läuft auf der CPU. Im unveränderten Kursrunner lief sie unter Python 3.10 und 3.14; nach dem letzten Bau am 24.11. hat sie gegen Solution_92 auf beiden Seiten je ein ganzes Spiel 3:0 gewonnen. Liegt der Ordner woanders, findet der Agent seine Gewichte direkt neben `main.py`. |
| Wie lange dauert ein Zug? | Im Kursrunner im Median 5–6 ms, die Abgabedatei ist 9,5 MB groß und unter Python 3.10 und 3.14 geprüft. |

## Quellen für jede Zahl

- **Folie 2:** Gedächtnis in `agents/sherlock/belief.py`, Kartenebenen in `agents/sherlock/cnn_model.py` (`map_planes`).
- **Folie 3:** Siege gegen Solution_92 aus den Übernahmeberichten der jeweiligen Abgaben (Werte und Pfade in
  [diagramme.py](docs/presentation/finale_2711/diagramme.py)). V14 gegen Kaggle 12/800 auf 7158000–7158399
  ([Vergleich](experiments/analysis/movement_soft_20261115/shared_400/ERGEBNIS.md)); 23 gegen 1,2 verlorene Einheiten im
  ersten Match, 17 Handregeln und das Orakel (4/200 statt 8/200 Spiele): [Befund](experiments/analysis/kaggle3_20261115/README.md),
  `screen_summary.txt`, `oracle_full_devA.csv`.
- **Folie 4:** Lehrer und Lehrerspiele: [Umbau](experiments/analysis/umbau_20261115/README.md) (b1–b3: 400 + 800 + 600
  Spiele, 1,87 + 4,17 + 3,02 Mio. Entscheidungen). Training: `scripts/imitate.py` (Kreuzentropie der Aktion + 0,5 ×
  Kreuzentropie des Schussziels).
- **Folie 5:** Dev A, reiner Schüler mit Stay-Bias 1,5 und Entstapeln: v2 78 %, v3 89,5 %
  ([Umbau](experiments/analysis/umbau_20261115/README.md)), v4 185/200 und v5 190/200
  ([v5](experiments/analysis/umbau_20261115/v5/ERGEBNIS.md)), v7 196/200 ([v7](experiments/analysis/umbau_20261115/v7/ERGEBNIS.md)),
  V14 188/200. Stehen 58–67 % statt 46 %: Diagnose im [Umbau](experiments/analysis/umbau_20261115/README.md). 19,0 Mio.
  Entscheidungen: [v9](experiments/analysis/umbau_20261115/v9/ERGEBNIS.md).
- **Folie 6:** Entscheidung in `agents/sherlock/imitation_agent.py` (`_policy_act`), Netz in
  `agents/sherlock/imitation_net.py`. Parameter 699.721 und 1.809.193 aus der Abgabedatei. 0,37 = e^−1, denn der Code
  zieht 1,0 vom Logarithmus der Stehwahrscheinlichkeit ab (`imit_stay_bias=1.0`).
- **Folie 7:** [Messung und Beispiel](experiments/analysis/finale_20261119/ERGEBNIS.md): das unveränderte Abgabepaket
  als player_0 auf den Karten 4242–4251, jeder der 33.539 Züge gegen Kaggle exakt nachgerechnet. „Ohne sichtbaren
  Gegner“ heißt: kein sichtbarer Gegner höchstens zwei Felder vom Ziel; „trafen“ heißt: mindestens eine Kaggle-Einheit
  direkt oder durch Streuschaden. Schüsse mit sichtbarem Gegner trafen zu 95 %.
- **Folie 8:** Schalter: v2 pur 49,5 %, mit Stay-Bias 1,5 und Entstapeln 78 % gegen Solution_92
  ([Umbau](experiments/analysis/umbau_20261115/README.md)). Halter-Beispiel aus der Messung zu Folie 7. +1,64
  Prozentpunkte: Kandidat gegen P9 in der [dritten Bestätigung](experiments/analysis/devf_20261117/BESTAETIGUNG3_ERGEBNIS.md).
  Handtaktiken: [Dev H](experiments/analysis/devh_20261117/ERGEBNIS.md).
- **Folie 9:** [Dritte Bestätigung](experiments/analysis/devf_20261117/BESTAETIGUNG3_ERGEBNIS.md) und
  [Kampfdiagnose](experiments/analysis/deve_20261117/DIAGNOSE.md) (Nachtrag; direkte Treffer aus
  `experiments/analysis/r3t_20261117/diag_student_ens9_s10h/matches.csv`: 21,8 je Match, R3 6,7). Robustheit:
  [Ergebnis](experiments/analysis/robust_p9_20261117/ERGEBNIS.md), gemessen mit demselben Netz bei Stay-Bias 1,5.
- **Folie 10 und Reserve:** [Release V16](experiments/releases/20261117_sherlock_v16/README.md), Zahlen und Fakten in der
  [README](README.md#zahlen-und-fakten).
- **Folie 10 und Reserve R5 (Prüfungen nach V16):** sieben große Vergleiche mit 7.640 Spielen auf 960 Karten im
  [Morgenbericht vom 23.11.](docs/MORGENBERICHT_20261123.md), Kundschafter auf 160 Karten (960 Spiele,
  [Ergebnis](experiments/analysis/relictsuche_20261123/abschlusspruefung/ERGEBNIS.md)) und seine Wiederholung auf 96 Karten
  (576 Spiele, [Ergebnis](experiments/analysis/relictsuche_20261123/sicht1_wiederholung/ERGEBNIS.md)). Die übrigen
  Versuche vom 22. und 23.11. stehen im [Arbeitsstand](docs/ARBEITSSTAND.md) und in der
  [Übersicht zur Reliktsuche](experiments/analysis/relictsuche_20261123/ERGEBNIS.md). 35 Niederlagen:
  [spielabstand](experiments/analysis/v16_finalwoche_20261122/spielabstand/ERGEBNIS.md); 18 von 18:
  [gemeinsame Niederlagen](experiments/analysis/relictsuche_20261123/gemeinsame_niederlagen/ERGEBNIS.md).
- **Reserve R1:** `experiments/analysis/count_games.py` zählt bis 17.11. 1.541.960 Spiele; dazu die 9.176 Prüfspiele
  von R5 (7.640 + 960 + 576), die das Skript nicht erfasst. Commits mit `git shortlog -sn` am 24.11.: Moayed 652,
  Mahmoud 455 (452 + 3 unter anderen Adressen). Tests in `tests/` unverändert 3.298.

## Für die Probe

- Zweimal gemeinsam mit Uhr proben, die Übergaben (nach Folie 3 und nach Folie 7) üben.
- Auf jeder Folie höchstens zwei Zahlen laut sagen; die übrigen stehen für Nachfragen bereit.
- Vor dem Vortrag prüfen: PDF im Vollbild und in Moodle, ob `Gruppe15.zip` mit V16 hochgeladen ist.

**PDF neu erzeugen** (nach Änderungen an der HTML-Datei oder den Diagrammen):

```sh
python docs/presentation/finale_2711/diagramme.py
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer \
  --print-to-pdf=Sherlock_Finale_27-11-2026.pdf docs/presentation/finale_2711/Sherlock_Finale_27-11-2026.html
cp Sherlock_Finale_27-11-2026.pdf docs/presentation/finale_2711/
```

Die Fassung vom 16.11. mit R3 und V15 (Moes Entwurf) liegt im Git-Verlauf (Commit `e9a655c`).
