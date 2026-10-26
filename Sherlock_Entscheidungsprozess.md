# Wie Sherlock entscheidet – Erklärung für die nächste Präsentation

Stand 26.10.2026, Abgabe **V10** (18 Netze, SHA-256 `03cf8bdc…8c67`). Geschrieben für Mahmoud und Moayed nach der Review. Der Prof wollte genauer wissen:

1. Was ist **Action Masking**?
2. Wie läuft der **Entscheidungsprozess** ab: wer macht was, wer bekommt was?
3. Wie werden die **18 Netze** auf die Spiele verteilt?

Alle Zahlen unten stammen aus dem Code, den Trainingsprotokollen oder aus einer neuen Messung (Abschnitt 11). Mit ihr lässt sich jede Aussage nachprüfen.

---

## 0. Die Kurzfassung (zum Auswendiglernen, ca. 45 Sekunden)

> Jede unserer bis zu 16 Units entscheidet in jedem Step selbst. Zuerst aktualisiert das **Gedächtnis** die Karte, Relics und Punkte-Tiles. Dann bekommt jede Unit ein **eigenes Ziel**. Aus beidem bauen wir für jede Unit **79 Zahlen**. Diese 79 Zahlen gehen gleichzeitig in **alle 18 Netze**. Jedes Netz bewertet die 6 Aktionen mit einem Q-Wert. Wir **mitteln** die 18 Bewertungen. Dann **streicht die Maske** alle Aktionen, die gerade unmöglich oder gefährlich sind, und wir nehmen die beste erlaubte. Zum Schluss prüfen wenige **Regeln** die Wahl, zum Beispiel ob der Weg in eine Sackgasse führt. In unserer Messung blieb die Netzwahl in **92 von 100** Entscheidungen unverändert.

---

## 1. Kurze Antworten auf die drei Fragen

### Was ist Action Masking?

Bevor das Netz eine Aktion auswählt, setzen wir alle **verbotenen Aktionen auf „unmöglich“** (Q-Wert = −∞). Danach wird die beste **erlaubte** Aktion genommen. Das Netz bewertet also alle 6 Aktionen, darf aber nur unter den erlaubten wählen.

Beispiel: Das Netz möchte „runter“, aber dort liegt ein Asteroid. Die Maske verbietet „runter“, also wird die beste erlaubte Aktion gespielt (echtes Beispiel in Abschnitt 7).

In den Spielen unserer Messung war im Mittel **4,3 von 6 Aktionen** erlaubt. In **20 %** der Entscheidungen war die Lieblingsaktion der Netze verboten, und die Maske hat eingegriffen.

### Wie läuft eine Entscheidung ab?

Gedächtnis → Ziel je Unit → 79 Merkmale → 18 Netze → Mittelwert → Maske → beste erlaubte Aktion → Regelprüfung → Aktion an das Spiel. Der genaue Ablauf steht in Abschnitt 3.

### Wie werden die 18 Netze auf die Spiele verteilt?

**Gar nicht – alle 18 Netze arbeiten in jedem Spiel, in jedem Step, für jede Unit.** Es gibt kein „Netz für Match 1“ oder „Netz für Spieler 2“. Jedes Netz bekommt dieselben 79 Zahlen und gibt 6 Q-Werte aus. Wir bilden den Mittelwert aus den 18 Bewertungen. Das ist ein **Ensemble**: Das Team entscheidet gemeinsam, nicht ein einzelnes Netz.

Die 18 Netze haben dieselbe Bauart. Sie unterscheiden sich nur durch ihr **Training** (Abschnitt 9): andere Zufallsstartwerte, andere Trainingskarten, drei verschiedene Gegner-Mischungen und in einer Gruppe eine etwas andere Belohnung. Darum machen sie unterschiedliche Fehler, und der Mittelwert gleicht diese Fehler aus.

---

## 2. Was der Agent bekommt (Eingang) und was er zurückgibt (Ausgang)

**Einmal pro Spiel** (`set_env_cfg`): bekannte Spielparameter, z. B. `max_units = 16`, Kartengröße 24 × 24, Zugkosten, Sap-Kosten, Sap-Reichweite, Sichtweite.
Unbekannt bleiben andere Parameter, z. B. wie viel Energie Nebel abzieht oder wie stark der Streuschaden eines Saps ist. Die schätzt der Agent selbst aus seinen Energieverläufen (`agents/sherlock/param_est.py`).

**Jeden Step** (`act(step, obs)`, aufgerufen vom unveränderten Kurs-Runner `lux/runner.py`):

| Feld in `obs` | Inhalt |
|---|---|
| `units` | Position und Energie aller **sichtbaren** Units beider Teams |
| `units_mask` | welche Units existieren und sichtbar sind |
| `sensor_mask` | welche Felder wir gerade sehen |
| `map_features` | Feldenergie und Feldtyp (leer / Nebel / Asteroid), nur für sichtbare Felder |
| `relic_nodes`, `relic_nodes_mask` | sichtbare Relics |
| `team_points`, `team_wins` | Punkte im laufenden Match und gewonnene Matches |
| `steps`, `match_steps` | Zähler für das ganze Spiel und für das laufende Match (0–100) |

Was wir nicht sehen, steht als −1 in den Daten. **Welche Felder Punkte bringen, sieht niemand.** Das muss der Agent aus dem Punktezuwachs erschließen (Gedächtnis, Schritt 1).

**Ausgang:** ein Array mit **16 × 3** Zahlen, eine Zeile pro Unit: `[Aktion, dx, dy]`. Die Aktionen sind 0 = stehen, 1 = hoch, 2 = rechts, 3 = runter, 4 = links, 5 = Sap auf das Feld (dx, dy).
In den Prüfspielen über den Kurs-Runner am 22.10. dauerte ein `act`-Aufruf höchstens **11,4 ms**.

---

## 3. Der Ablauf eines Steps – wer macht was

```
 obs vom Spiel
     │
 ①  Gedächtnis (Belief)        merkt sich Karte, Relics, Punkte-Tiles über alle 3 Matches
     │
 ②  Kanonische Sicht           Karte so spiegeln, dass unser Start immer oben links (0,0) liegt
     │
 ③  Zielzuweisung              jede Unit bekommt ein EIGENES Ziel (Punkte-Tile > Kandidat > Erkunden)
     │
 ④  Pro Unit: 79 Merkmale + bestes Sap-Ziel + Aktionsmaske
     │
 ⑤  18 Netze (alle Units auf einmal) → je 6 Q-Werte → Mittelwert
     │
 ⑥  Maske anwenden → beste ERLAUBTE Aktion
     │
 ⑦  Regelprüfung (Sackgasse, Nebel, Saps auf dem Punkte-Tile, kein doppelter Abschuss …)
     │
 ⑧  Zurückspiegeln (falls wir Spieler 2 sind) → 16 × 3 Aktionen ans Spiel
```

| Schritt | Wer | bekommt | liefert | Datei / Funktion |
|---|---|---|---|---|
| ① | **Gedächtnis** | `obs` | Karte (Asteroiden, Nebel, Energie), Relics, **Kandidaten-Tiles** (5 × 5 um jedes Relic), **bewiesene Punkte-Tiles**, erkundete Felder | `belief.py` `Belief.observe` |
| ② | **Geometrie** | Positionen | für Spieler 2 an der Diagonale gespiegelte Positionen | `geometry.py` |
| ③ | **Zielzuweisung** | Gedächtnis + Unit-Positionen | ein Ziel pro Unit | `features.py` `assign_targets` |
| ④ | **Merkmale, Maske** | Gedächtnis + Ziel + Gegner | 79 Zahlen, Maske mit 6 Ja/Nein-Werten, Sap-Ziel | `features.py` `build_features`, `main.py` `_action_mask`, `_best_sap_target` |
| ⑤ | **18 Netze** | 79 Zahlen je Unit | Mittel aus 18 × 6 Q-Werten | `main.py` `_act` (Zeile 263–269) |
| ⑥ | **Maske** | Q-Werte + Maske | Aktion des Netzes | `main.py` `_act` (Zeile 273–274) |
| ⑦ | **Regeln** | Netzaktion + Lage | endgültige Aktion | `main.py` `_act` ab Zeile 308 |
| ⑧ | **Ausgabe** | Aktionen | 16 × 3-Array | `main.py` `_act` (Zeile 448–460) |

### ① Das Gedächtnis findet die Punkte-Tiles

Punkte-Tiles sind unsichtbar. Das Gedächtnis rechnet so: Wir bekommen in diesem Step **3 Punkte**. Unsere Units stehen auf **4 Feldern**, davon sind 2 schon als Punkte-Tiles bewiesen. Also bringen von den 2 übrigen Feldern genau 1 einen Punkt. Das Gedächtnis merkt sich diese Gleichung. Mit weiteren Beobachtungen wird sie eindeutig. Dazu kommt die **Spiegelsymmetrie** der Karte: Was wir auf unserer Seite beweisen, gilt auch für das Spiegelfeld beim Gegner.

### ③ Die Zielzuweisung verteilt die Units

Jede Unit bekommt ein **eigenes** Ziel, denn ein Feld bringt höchstens einen Punkt. Die Reihenfolge ist: bewiesene Punkte-Tiles, dann Kandidaten-Tiles, dann unerkundete Felder. Gerechnet wird mit der echten Weglänge um Asteroiden herum (Breitensuche), nicht mit der Luftlinie. Weit entfernte Punkte-Tiles in der Gegnerhälfte kommen erst nach unseren eigenen Kandidaten. Das Ziel wird dem Netz als Merkmal mitgegeben (`assigned_dx/dy/dist`).

### ⑤ Die Netze bewerten, sie planen nicht

Das Netz **bewertet** die 6 Aktionen: Ein Q-Wert schätzt, wie viel Belohnung ab jetzt noch zu erwarten ist, wenn die Unit diese Aktion wählt. Es plant keinen Weg und sucht kein Sap-Ziel. Beim Sap entscheidet das Netz nur, **ob** gesappt wird. **Wohin** gesappt wird, berechnet eine feste Formel (`_best_sap_target`): Sie wählt das Feld, auf dem am meisten Gegner-Energie getroffen wird, einschließlich des Streuschadens auf den Nachbarfeldern.

---

## 4. Die 79 Merkmale (was ein Netz pro Unit „sieht“)

| Gruppe | Anzahl | Beispiele |
|---|---:|---|
| Eigene Lage und Spielparameter | 10 | Position, Energie, „zu wenig Energie für einen Zug“, Fortschritt im Match, Zug-/Sap-Kosten, Sap-Reichweite, Sichtweite |
| Punktestand | 4 | eigene Punkte, Punktedifferenz, gewonnene Matches beider Teams |
| Nächstes Ziel je Klasse | 20 | Richtung und Abstand zum nächsten Punkte-Tile, Kandidaten-Tile, Relic, unerkundeten Feld und **zugewiesenen Ziel** (je dx, dy, Abstand, vorhanden) |
| Aktuelles Feld | 5 | auf Punkte-Tile?, auf Kandidat?, im Nebel?, eigene Units hier, „ich stehe doppelt“ |
| Umgebung (hier + 4 Nachbarn) | 30 | je Feld: begehbar, Energie, Punkte-Tile, Kandidat, unerkundet, eigene Units |
| Gegner | 6 | Richtung und Abstand zum nächsten Gegner, Energievergleich, Gegner in Sap-Reichweite, sichtbare Gegner |
| Globale Zähler | 4 | eigene Units, bekannte Punkte-Tiles, erkundeter Anteil, Kandidaten |

Alle Zahlen liegen zwischen −1 und 1 (z. B. Position geteilt durch 24). Die Liste mit allen Namen steht in `features.py` (`FEATURE_NAMES`).

---

## 5. Ein Netz und das Ensemble

```
79 Merkmale → 256 → 256 ─┬─ Wert-Kopf    128 → 1  (V: „wie gut ist die Lage?“)
                          └─ Vorteil-Kopf 128 → 6  (A: „wie viel besser ist Aktion a?“)
Q(a) = V + A(a) − Mittelwert(A)        („Dueling“-Netz, ReLU, 152.967 Parameter)
```

- **Ein Netz für alle Units:** Alle Units teilen sich dieselben Gewichte, jede Unit hat aber ihre eigenen 79 Merkmale. Im Code geht das in einem Durchlauf für alle Units zusammen.
- **Ein Netz für beide Seiten:** Wegen der kanonischen Sicht (Schritt ②) spielt dasselbe Netz als Spieler 1 und als Spieler 2.
- **Ensemble:** 18 solche Netze, zusammen etwa 2,75 Millionen Parameter. Jedes Netz liefert 6 Q-Werte, wir bilden den **Mittelwert je Aktion** und wenden dann die Maske an.

Warum 18 Netze und nicht eins? Einzelne DQN-Netze schwanken stark von Checkpoint zu Checkpoint, das Mitteln glättet diese Schwankung. Mehr Netze haben nicht weiter geholfen: 30 Netze (18 alte und 12 neue) erreichten geschätzt dieselben 90,3 % gegen Solution_92 wie V10 (Arbeitsstand 22.10.).

In der Messung waren sich die Netze oft **nicht** einig:

| Wie einig sind die 18 Netze? | Anteil der Entscheidungen |
|---|---:|
| alle 18 wählen dieselbe Aktion | 32 % |
| höchstens 9 von 18 wählen einzeln die Aktion, die das Ensemble wählt | 24 % |
| im Mittel wählen so viele Netze einzeln die Ensemble-Aktion | 13,4 von 18 |
| Mittelwert entscheidet anders als eine einfache Mehrheitswahl | 8 % |

---

## 6. Action Masking im Detail

Die Maske wird für jede Unit neu berechnet (`main.py` `_action_mask`):

| Aktion | erlaubt, wenn … | im Training | im Spiel (V10) |
|---|---|:---:|:---:|
| stehen | immer | ✓ | ✓ |
| Zug (hoch/rechts/runter/links) | genug Energie für die Zugkosten **und** Zielfeld auf der Karte **und** kein Asteroid (laut Gedächtnis) | ✓ | ✓ |
| Zug, zusätzlich | kein sichtbarer, mindestens gleich starker Gegner **auf** dem Zielfeld (`safe_moves`) | – | ✓ |
| Zug, zusätzlich | kein beweglicher, mindestens gleich starker Gegner **neben** dem Zielfeld, der im selben Step dorthin ziehen könnte (`collision_guard`) | – | ✓ |
| Sap | sichtbarer Gegner in Sap-Reichweite **und** Energie ≥ Sap-Kosten | ✓ | ✓ |

**Warum das wichtig ist:**

1. **Keine verschwendeten Züge.** Ohne Maske lernt das Netz erst durch Strafe, dass man nicht gegen Asteroiden läuft. Mit Maske kommt das gar nicht vor.
2. **Im Training:** Die Zufallsaktionen der Erkundung (ε-greedy) werden nur unter erlaubten Aktionen gezogen. Auch das Lernziel nutzt die Maske. Im DQN-Ziel `y = r + γ · Q_target(s', argmax Q(s', a'))` zählen nur Aktionen a', die im nächsten Zustand erlaubt sind (`main.py` `_learn`, Zeile 1186).
3. **Im Spiel:** Zwei zusätzliche Sicherheitsregeln sind Teil der Maske. Sie verhindern Zusammenstöße mit stärkeren Gegnern (die schwächere Unit stirbt).

**Was die Maske in der Messung verhindert hat** (Anteil aller Entscheidungen, insgesamt 20 %):

| Lieblingsaktion der Netze war verboten | Anteil |
|---|---:|
| Sap, aber kein Gegner in Reichweite oder zu wenig Energie | 9,8 % |
| runter (Asteroid, Rand, zu wenig Energie oder Gefahr) | 7,2 % |
| rechts | 2,9 % |
| hoch oder links | 0,5 % |

Dass vor allem „runter“ und „rechts“ betroffen sind, liegt an der kanonischen Sicht: Unser Start liegt immer oben links, die Relics liegen weiter innen, also zieht man meistens nach rechts oder unten.

---

## 7. Vier echte Entscheidungen

Alle aus Karte 690000, wir als Spieler 1 gegen Solution_92 (Diagnosespiel). Q-Werte gerundet, Reihenfolge: stehen / hoch / rechts / runter / links / Sap. „–“ heißt: von der Maske verboten.

**A – Alle 18 Netze sind sich einig** (Step 117, Match 2, Unit 0 auf Feld (1, 14), 92 Energie)
Links daneben liegt ein bewiesenes Punkte-Tile, das ist das zugewiesene Ziel.
Mittel: 43,6 / 40,4 / 41,2 / 42,4 / **51,0** / – → **links**. Alle 18 Netze wählen links.

**B – Die Maske greift ein** (Step 114, Match 2, Unit 0 auf (0, 12), 101 Energie)
Ohne Maske: 47,4 / 47,8 / 48,6 / **50,4** / 47,4 / 42,2. Am liebsten **runter**, aber unten liegt ein Asteroid. Die Maske verbietet „runter“, „links“ (Kartenrand) und Sap (kein Gegner sichtbar).
Mit Maske: 47,4 / 47,8 / **48,6** / – / – / – → gespielt wird die beste erlaubte Aktion: **rechts**.

**C – Netze uneinig, der Mittelwert entscheidet** (Step 114, Match 2, Unit 2 auf (0, 6))
Einzelwahlen der 18 Netze: 6 × rechts, 8 × runter, 4 × stehen.
Mittel: 25,4 / 24,7 / **25,9** / 25,8 / – / – → **rechts**, knapp vor runter. Beides führt zum Ziel unten rechts.
Hier hat die **Mehrheit** (8 × runter) nicht gewonnen: Der Mittelwert berücksichtigt auch, **wie sicher** sich jedes Netz ist.

**D – Eine Regel greift ein** (Step 94, Match 1, Unit 5 steht auf einem eigenen Punkte-Tile, 81 Energie, ein Gegner direkt daneben)
Mittel: **9,98** / 8,5 / 8,4 / – / – / 9,81 → das Netz wählt **stehen**, sehr knapp vor Sap (8 Netze wollen sappen, 10 stehen).
Die Regel `pt_sap` sagt: Wer auf seinem Punkte-Tile steht, genug Energie hat und einen stehenden Gegner treffen kann, sappt. Ein Sap bewegt die Unit nicht, der Punkt bleibt also erhalten und der Gegner bekommt trotzdem Schaden. Gespielt wird **Sap**.

---

## 8. Die Regeln nach dem Netz – und wie oft sie eingreifen

Messung über 36.258 Entscheidungen (Abschnitt 11):

| | Anteil |
|---|---:|
| **Netzwahl bleibt unverändert** | **92,4 %** |
| Regel ändert die Aktion | 7,3 % |

| Regel | was sie tut | greift ein bei |
|---|---|---:|
| `scripted_explore` | Unit hat nur ein Erkundungsziel → läuft direkt hin (das Netz wartet am Matchanfang sonst gern auf Energiefeldern) | 4,3 % |
| `nebula_avoid` (weich) | Zug in schädlichen Nebel durch einen gleich guten Zug ohne Nebel ersetzen | 1,2 % |
| `sap_no_overkill` | kein Sap auf einen Gegner, den schon geplante Saps dieses Steps zerstören | 0,9 % |
| `path_fix` | Zug nach Luftlinie führt in eine Sackgasse → ersten Schritt des echten kürzesten Wegs nehmen | 0,6 % |
| `pt_sap` mit `sap_still` | auf eigenem Punkte-Tile stehen bleiben **und** auf einen stehenden Gegner sappen | 0,5 % |
| `art_sap` | aus sicherer Entfernung sappen, wenn mindestens 3 Gegner getroffen werden | 0,25 % |
| Nebel verlassen | wartende Unit im schädlichen Nebel zieht heraus | 0,1 % |

**Wie man das ehrlich erklärt:** Das Netz trifft fast alle Entscheidungen. Die Regeln korrigieren wenige, aber wichtige Fälle. Die Verbesserungen von V3 zu V10 (Kartenfehler im Gedächtnis, Zielwahl nach Weglänge, Sackgassen, Mehrfach-Saps, Kollisionen) brachten gegen Solution_92 den Sprung von rund 76 % auf 90,3 %, mit denselben 18 Netzen (gemessen auf verschiedenen frischen Kartenblöcken, siehe Übernahmeberichte). Umgekehrt gilt: Am 19.10. ersetzten wir das Netz testweise durch eine einfache Regel mit denselben Leitplanken. Sie gewann nur 3 % gegen Solution_92, die damalige Abgabe mit Netz 38 %. Das Netz ist also der Kern, die Regeln sind Leitplanken.

---

## 9. Wie die 18 Netze trainiert wurden

**Verfahren (für jedes Netz gleich):** Double DQN mit Dueling-Kopf, Replay Buffer (300.000 Übergänge), Target-Netz (alle 500 Lernschritte kopiert), Huber-Loss, Lernrate 0,0003, γ = 0,99, Batch 256.

- **Jede Unit erzeugt pro Step einen Übergang** (Zustand, Aktion, Belohnung, nächster Zustand, nächste Maske). Pro Spiel sind das etwa 3.700 Übergänge.
- **Erkundung:** ε fällt in den ersten 60.000 Steps (etwa 200 Spiele) von 1,0 auf 0,05. 70 % der Zufallszüge gehen in Richtung des zugewiesenen Ziels, sonst finden Units die Relics fast nie.
- **Belohnung jeden Step pro Unit**, nicht nur am Ende: + Unit steht als erste auf einem bewiesenen Punkte-Tile (1,0), + Annäherung ans Ziel (0,5, potentialbasiert), + neu erkundete Felder und neu bewiesene Punkte-Tiles (fürs Team), ± Energieänderung, − doppelt auf einem Punkte-Tile, − Tod (0,5), ± Sap-Treffer, ± Matchsieg (2,0) (`reward.py`).

**Die drei Gruppen** (alle am 19.10. trainiert, Endstand des jeweiligen Laufs):

| Gruppe | Netze | Spiele je Netz | Gegner im Training | Besonderheit |
|---|---:|---:|---|---|
| A | 6 (Starts 0–5) | 3.000 | erste 25 % gegen default, dann abwechselnd default / Solution_92 | – |
| B | 6 (Starts 6–11) | 4.000 | erste 25 % default, danach 70 % Solution_92 (Rest default) | – |
| C | 6 (Starts 12–17) | 4.000 | erste 25 % default, danach 60 % Solution_92, 20 % eigene alte Agenten (Rest default) | Strafe für Gegnerpunkte im Reward |

Insgesamt **66.000 Trainingsspiele**. Jedes Netz hat andere Zufallsstartwerte und andere Trainingskarten. Deshalb lernen sie leicht verschiedene Strategien, und ihre Fehler gleichen sich im Mittel aus.

**Training und Spiel sind nicht ganz gleich:** Im Training waren Gedächtnis, Zielzuweisung (damals nach Luftlinie), die Grundmaske und `scripted_explore` schon aktiv. Die zwei Sicherheitsregeln der Maske und die übrigen Regeln aus Abschnitt 8 kamen erst danach im Spiel dazu (V7–V10). Am 22.10. haben wir 12 neue Netze trainiert, bei denen die meisten dieser Regeln schon im Training aktiv waren (Stand V8). Zusammen mit den 18 alten waren sie nicht besser als V10 (geschätzt 90,3 %).

---

## 10. Mögliche Rückfragen des Profs

**„Ist das noch Reinforcement Learning, wenn Regeln eingreifen?“**
Ja. Das Netz wählt die Aktion in über 92 % der Fälle. Die Regeln greifen bei rund 7 % ein. Eine einfache Regel statt des Netzes gewann am 19.10. nur 3 % gegen Solution_92 (mit Netz 38 %).

**„Warum Mittelwert und keine Abstimmung?“**
Der Mittelwert berücksichtigt, wie stark ein Netz eine Aktion bevorzugt, eine Abstimmung zählt nur Stimmen (Beispiel C). In 8 % der Fälle entscheiden beide verschieden. Ehrliche Grenze: Netze mit größeren Unterschieden zwischen ihren Q-Werten haben mehr Gewicht. Eine normierte Mittelung haben wir noch nicht getestet.

**„Wer entscheidet beim Sap das Ziel?“**
Das Netz entscheidet, **ob** gesappt wird. Eine Formel wählt, **wohin**: das Feld mit der meisten getroffenen Gegner-Energie.

**„Woher weiß der Agent, wo es Punkte gibt?“**
Nicht vom Netz, sondern vom Gedächtnis: Es rechnet mit Gleichungen aus dem Punktezuwachs und nutzt die Spiegelsymmetrie (Abschnitt 3 ①).

**„Koordinieren sich die Units?“**
Ja, über zwei Wege: Die Zielzuweisung gibt jeder Unit ein eigenes Ziel, und beim Sap wird geplanter Schaden geteilt (`sap_no_overkill`). Die Netze selbst entscheiden pro Unit.

**„Warum stehen so viele Units still?“**
51 % aller Aktionen sind „stehen“. Wer auf einem Punkte-Tile steht, muss stehen bleiben, um zu punkten.

---

## Folien und Sprechtext (etwa 3:30 Minuten)

Folien: `Sherlock_Entscheidungsablauf_Folien.pdf` im Projektordner (6 Folien und 1 Reserve), Quelle `docs/presentation/Sherlock_Entscheidungsablauf.html`. Für die nächste Präsentation lassen sie sich in den Hauptfoliensatz übernehmen. Vorschlag: Sie ersetzen dort die Pseudocode-Folie „Sherlock heute“.

1. **Was Sherlock bekommt und zurückgibt (30 s):** „In jedem Schritt bekommt Sherlock nur, was gerade sichtbar ist: Einheiten, Felder, Relics und den Punktestand. Welche Felder Punkte bringen, sieht niemand, das muss der Agent selbst herausfinden. Zurück gibt er für jede seiner 16 Einheiten eine Aktion. Das dauert höchstens 11 Millisekunden.“
2. **Ein Spielschritt (45 s):** „Ein Schritt läuft in sechs Stufen. Das Gedächtnis merkt sich Karte und Punktefelder. Jede Einheit bekommt ein eigenes Ziel. Daraus bauen wir 79 Zahlen je Einheit. Gelernt ist nur Stufe 4: 18 Netze bewerten die sechs Aktionen. Die Maske streicht Verbotenes, Regeln korrigieren wenige Fehler. Beim Sap entscheidet das Netz, ob geschossen wird. Wohin, berechnet eine Formel.“
3. **Action Masking (40 s):** „Action Masking heißt: Bevor das Netz wählt, streichen wir alle Aktionen, die gerade nicht gehen oder gefährlich sind. Hier wollten die Netze am liebsten nach unten, dort liegt aber ein Asteroid. Also wird die beste erlaubte Aktion gespielt: rechts. Das passiert in jeder fünften Entscheidung. Im Training gilt dieselbe Maske.“
4. **18 Netze (40 s):** „Die 18 Netze werden nicht auf Spiele verteilt. Alle 18 bewerten jede Einheit in jedem Schritt, und wir mitteln ihre Q-Werte. Oft sind sie uneinig: Hier wollten 8 Netze nach unten und 6 nach rechts. Der Mittelwert wählt trotzdem rechts, weil er zählt, wie sicher jedes Netz ist. Mehr als 18 Netze haben nicht geholfen.“
5. **Training (30 s):** „Alle 18 Netze haben dieselbe Bauart und dasselbe Verfahren, Double DQN. Sie unterscheiden sich durch Zufallsstart, Karten und Gegner, zusammen 66.000 Trainingsspiele. Belohnt wird jede Einheit in jedem Schritt, nicht nur am Ende.“
6. **Netz und Regeln (30 s):** „92 Prozent der Entscheidungen spielt Sherlock genau so, wie die Netze sie getroffen haben. Die Regeln greifen selten ein, aber an wichtigen Stellen. Eine einfache Regel statt der Netze gewann nur 3 Prozent gegen Solution_92.“

Die Reservefolie zum Gedächtnis zeigen wir nur, wenn jemand fragt, wie Sherlock Punktefelder findet.

## 11. Belege und Nachprüfung

```
.venv/bin/python -m scripts.decision_trace --seeds 690000-690004 \
    --out experiments/analysis/decision_trace_20261026.json
```

- 5 Karten (690000–690004) × beide Seiten = **10 Spiele gegen Solution_92, 36.258 Unit-Entscheidungen**. Das sind reine **Diagnosespiele**: Sie beschreiben den Ablauf und sind **kein Leistungsnachweis** (die gemessene Siegquote der Abgabe steht im Übernahmebericht: 90,3 % auf 800 frischen Karten).
- Rohdaten mit allen Anteilen und den Beispielen samt allen 18 × 6 Q-Werten: `experiments/analysis/decision_trace_20261026.json`.
- Gewichte nur gelesen, vorher und nachher `03cf8bdc…8c67`. Kein Training.
- Quellen der übrigen Zahlen: Checkpoint (`cfg`, `ensemble_sources`), Laufmanifeste `experiments/runs/20261019_full_rules_*`, [Übernahmebericht V10](experiments/analysis/release_20261022_v10/RELEASE.md), [Arbeitsstand](docs/ARBEITSSTAND.md) 19.–22.10.
