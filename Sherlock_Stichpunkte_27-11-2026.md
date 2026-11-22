# Sherlock V16 · Stichpunkte für die Abschlusspräsentation am 27. November

[Präsentations-PDF](Sherlock_Finale_27-11-2026.pdf) · [Editierbare Folien (HTML)](docs/presentation/finale_2711/Sherlock_Finale_27-11-2026.html) · [Gemeinsame Generalprobe](docs/presentation/finale_2711/GENERALPROBE_2711.md)

**Planzeit 9:50 Minuten für 10 Folien, dazu 4 Reservefolien für Fragen. Noch keine gemeinsame Zeitprobe.**
Moe: Einstieg, Weg bis zum Battle, Schalter und Handtaktiken, Ergebnis, Fazit (5:05). Mahmoud: wie V16 lernt und
entscheidet, mit einem echten Zug (4:45). Die Zeiten enthalten Zeige- und Übergabepausen. In eigenen Worten sprechen,
die Folien nur als Stütze nehmen.

**Kernaussage, die am Ende hängen bleiben soll:** Sherlock hat das Kämpfen vom Kaggle-Dritten gelernt und schlägt
damit unsere beste frühere Version in 194 von 200 Spielen. Handregeln helfen dem gelernten Netz kaum noch.

| Folie | Wer | Dauer | Bis |
|---|---|---:|---:|
| 1 · Sherlock V16 | Moe | 0:30 | 0:30 |
| 2 · Wo gibt es Punkte? | Moe | 0:55 | 1:25 |
| 3 · Eigenes RL brachte uns auf Platz 3 | Moe | 1:10 | 2:35 |
| 4 · Die Idee: vom Kaggle-Dritten lernen | Mahmoud | 1:10 | 3:45 |
| 5 · Nur zuschauen reicht nicht: DAgger | Mahmoud | 1:15 | 5:00 |
| 6 · So entscheidet V16 in jedem Zug | Mahmoud | 1:10 | 6:10 |
| 7 · Kein Gegner sichtbar, trotzdem vier Treffer | Mahmoud | 1:10 | 7:20 |
| 8 · Drei Schalter helfen, 17 Handtaktiken nicht | Moe | 1:00 | 8:20 |
| 9 · 194 von 200 gegen unsere vorige Version | Moe | 0:55 | 9:15 |
| 10 · Was wir mitnehmen | Moe | 0:35 | 9:50 |

## Folie für Folie

### 1 · Sherlock V16 (Moe)

- „Im Battle am 6. November wurde Sherlock Dritter. Heute zeigen wir, was danach passiert ist: Sherlock hat vom
  Drittplatzierten des Kaggle-Wettbewerbs gelernt.“
- Frage aufwerfen, die am Ende beantwortet wird: „Was macht man, wenn das eigene Training nicht mehr weiterkommt?“

### 2 · Wo gibt es Punkte? (Moe)

- Links das Rätsel: vier verschiedene Felder besetzt, drei Punkte mehr. Zwei Felder sind bekannt, also bringt genau
  eines der beiden offenen Felder den dritten Punkt. Kurz Zeit zum Mitdenken lassen.
- Rechts: Das ist Sherlocks Gedächtnis. Es merkt sich Relikte und Punktefelder über alle Matches, nutzt die
  Spiegelsymmetrie der Karte und verfolgt wandernden Nebel, Asteroiden und das Energiefeld.
- Überleitung: „Dieses Gedächtnis haben wir selbst gebaut. Es ist bis heute die Eingabe für Sherlocks Netz.“

### 3 · Eigenes RL brachte uns auf Platz 3 (Moe)

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

- Links: Drei kleine Schalter haben wir aus der Spielanalyse abgeleitet. Weil das Netz zu oft stehen blieb, wird
  Stehen abgewertet. Wollen mehrere auf demselben Feld stehen bleiben, werden sie nach Möglichkeit verteilt.
  Zusammen hoben die beiden Schalter unser erstes Netz gegen Solution_92 von
  49,5 % auf 78 %.
- Die Halter-Regel am Beispiel: Ohne sie würde Einheit 2 ihr Punktefeld verlassen (rechts 59 %). Mit ihr bleibt sie
  stehen (65 %) und holt weiter jeden Zug einen Punkt. Mit milderer Stehstrafe zusammen brachte das auf frischen
  Karten +1,6 Prozentpunkte Punkteanteil gegen Kaggle.
- Rechts: 17 Handtaktiken, je 800 Spiele. Granaten, Nebel-Schüsse, gemeinsame Abschüsse und Ausweichen kosten Punkte.
  Alles gleichzeitig kostet am meisten: −1,64 Prozentpunkte und nur 7 statt 24 Siege von 400 gegen Kaggle.
  „Öfter schießen“ sah zuerst gut aus, fiel aber in der frischen Bestätigung durch.
- „Das Netz hat Schießen und Ausweichen schon gelernt. Feste Regeln stören es eher.“

### 9 · 194 von 200 Spielen gegen unsere vorige Version (Moe)

- Kurz einordnen: R3 war bis zum 17. November unsere Finalversion, V14 mit einem kleinen nachgeahmten Berater für
  Bewegungen.
- Links: Auf 400 frischen Karten gewinnen beide 787 von 800 Spielen gegen Solution_92. Gegen den Kaggle-Dritten
  verdoppelt V16 die gewonnenen Spiele (20 statt 10) und gewinnt fast dreimal so viele Matches (216 statt 76).
  Direkt gegen R3: 194 von 200.
- Rechts: Im Kampf verliert V16 weniger Einheiten (17 statt 24 je Match), zerstört mehr gegnerische (8 statt 3) und
  trifft dreimal so oft direkt. Kaggle holt gegen V16 rund 300 statt 377 Punkte je Match.
- „Diese Prüfung war vorher festgelegt und lief auf Karten, die wir vorher nie benutzt hatten.“

### 10 · Was wir mitnehmen (Moe)

- Drei Sätze: Vom Besten lernen hat mehr gebracht als alle Handregeln. Nur frische Karten mit fester Regel zeigen
  echte Fortschritte, viele gute Ideen fielen dort durch. Der Lehrer bleibt stärker: Wir holen gegen ihn rund 40 %
  der Punkte und etwa jedes zehnte Match.
- Nächste Schritte nennen: das nachgeahmte Netz mit RL weitertrainieren (zum Beispiel PPO, das nahe am Lehrer
  bleibt), Schüsse besser erkennen, am Matchende mehr Punktefelder besetzen.
- Zur Eingangsfrage zurück: „Wenn das eigene Training nicht weiterkommt, hilft ein guter Lehrer, wenn man ihn ehrlich
  nennt und sauber prüft.“ Dann: „Danke! Habt ihr Fragen?“

## Fragen, mit denen wir rechnen

| Frage | Antwort in zwei Sätzen |
|---|---|
| Ist das noch Reinforcement Learning? | Bis zum Battle haben wir RL gemacht (DQN und PPO mit CNN, zusammen 662.504 Trainingsspiele). V16 lernt durch Nachahmung und DAgger; der nächste Schritt wäre RL-Feintuning ab diesem Netz. |
| Habt ihr den Kaggle-Bot kopiert? | Nein. Wir haben weder seinen Code noch seine Gewichte übernommen, er läuft nur beim Sammeln der Daten. Unser Netz hat eigene Eingaben aus Sherlocks Gedächtnis, eine eigene Architektur und eigene Gewichte; die Kursfolie 50 verweist ausdrücklich auf die Kaggle-Rangliste. |
| Warum ist der Lehrer im direkten Duell häufiger erfolgreich? | Im Training übt Sherlock, aus seiner eigenen Sicht dieselbe Aktion wie der Lehrer zu wählen. Das gelingt in Lehrerspielen bei 87 % der Aktionen, bei den Schüssen erkennt Sherlock aber nur 36–50 %. Die internen Pläne des Lehrers kennt unser Netz nicht. |
| Was ist DAgger genau? | Dataset Aggregation (Ross, Gordon, Bagnell 2011): Der Schüler spielt, der Lehrer beschriftet die Lagen des Schülers, alles kommt in einen gemeinsamen Datensatz. So lernt das Netz die Lagen, die es selbst erzeugt. |
| Warum zwei Netze? | Ein Ensemble aus zwei unterschiedlich großen Netzen entscheidet stabiler. Ein drittes Netz brachte im Test nichts mehr (+0,18 Prozentpunkte, verlangt waren +1,0). |
| Wozu noch die Maske? | Sie verhindert offensichtlich unsinnige oder gefährliche Züge (Rand, Asteroid, zu wenig Energie, stärkerer Gegner). Ohne Masken lag das Netz im Test 0,71 Prozentpunkte Punkteanteil gegen Kaggle schlechter (nicht gesichert, das Intervall enthält null). |
| Warum die Stehstrafe? | Der Lehrer verfolgt Pläne über mehrere Züge, die das Netz nicht sieht. Im Zweifel blieb es stehen (58–67 % der Züge statt 46 % beim Lehrer); die Strafe gleicht das aus. |
| Wie habt ihr getestet? | Jede Karte von beiden Seiten, Regel vor dem ersten Spiel festgelegt, Auswahl auf Entwicklungskarten, Bestätigung auf nie benutzten Karten, gepaarte Auswertung nach Karte mit Bootstrap. Insgesamt 1,54 Millionen Spiele seit dem 10. Oktober. |
| Was war euer eigener Beitrag? | Gedächtnis und Merkmale (16 Kartenebenen, 79 Merkmale), die ganze Lernkette mit DAgger, die Schalter aus der Spielanalyse wie die Halter-Regel, die schrittgenaue Nachrechnung der Kämpfe und die Prüfungen. |
| Warum ist V16 gegen Solution nicht besser als R3? | Beide liegen bei rund 98 %; auf einem weiteren frischen Kartensatz lag V16 sogar 11 Spiele von 800 hinter R3 (778 statt 789). Wir haben V16 gewählt, weil es gegen den viel stärkeren Kaggle-Dritten klar besser ist und R3 direkt 194 von 200 Mal schlägt. |
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

## Für die Probe

- Zweimal gemeinsam mit Uhr proben, die Übergaben (nach Folie 3 und nach Folie 7) üben.
- Auf jeder Folie höchstens zwei Zahlen laut sagen; die übrigen stehen für Nachfragen bereit.
- Vor dem Vortrag prüfen: PDF im Vollbild, Moodle-Frist und Dateiname der Abgabe.

**PDF neu erzeugen** (nach Änderungen an der HTML-Datei oder den Diagrammen):

```sh
python docs/presentation/finale_2711/diagramme.py
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-pdf-header-footer \
  --print-to-pdf=Sherlock_Finale_27-11-2026.pdf docs/presentation/finale_2711/Sherlock_Finale_27-11-2026.html
cp Sherlock_Finale_27-11-2026.pdf docs/presentation/finale_2711/
```

Die Fassung vom 16.11. mit R3 und V15 (Moes Entwurf) liegt im Git-Verlauf (Commit `e9a655c`).
