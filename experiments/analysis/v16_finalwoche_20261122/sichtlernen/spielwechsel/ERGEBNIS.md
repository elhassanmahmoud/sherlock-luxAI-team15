# Welches Match drehte der Sichtberater?

Auf den 120 unabhängigen Bestätigungskarten wechselten gegen Solution_92 genau drei Spielausgänge. Die beiden zusätzlichen Siege des Sichtberaters entstanden einmal **in Match 3** und einmal **in Match 2**. Auf dem verlorenen Sitz gab der Sichtberater **Match 1 und Match 2** ab. Ein früheres erstes Relikt oder ein früher bestätigtes Punktefeld tritt in diesen drei Verläufen nicht einheitlich zusammen mit einem späteren Sieg auf. [Gepaarter Gesamtvergleich](../bestaetigung_ergebnis.json).

### Was Sherlock selbst erfuhr

Je Zelle **V16 → Sichtberater**. Alle Angaben ohne Matchpräfix gehören zu Match 1. „Relikt gesehen“ ist die erste tatsächlich sichtbare Reliktposition in der eigenen Beobachtung. „Punktefeld bestätigt“ ist der erste positive Eintrag in Sherlocks Punktefeld-Gedächtnis. „Erster Punkt“ ist der erste Wertungsschritt, an dessen Ende ein eigenes Feld einen Punkt brachte. Deshalb kann die Gutschrift früher liegen als die Identifikation eines Feldes. Für die Siegentscheidung zählen die offiziell vergebenen Matches.

| Karte und Sitz | Erstes Relikt gesehen | Erstes Punktefeld bestätigt | Erster Punkt | Scout-Eingriffe |
|---|---:|---:|---:|---:|
| 160370081, P1 | 31 → **20** | 31 → 31 | 30 → 30 | 9 |
| 160370093, P0 | 35 → 37 | 41 → **39** | 36 → 38 | 18 |
| 160370099, P1 | M1/76 → M2/32 | 68 → **57** | 47 → 56 | 25 |

### Wo die Siege entstanden

Die Punktepaare sind jeweils aus Sicht von Sherlock angegeben (Sherlock:Gegner). Fett markiert sind die Matches mit geändertem Sieger.

| Karte | Match 1, V16 → Scout | Match 2, V16 → Scout | Match 3, V16 → Scout | Ganze Partie |
|---|---|---|---|---|
| 160370081 | 403:134 → 472:126 | 231:441 → 250:333 | **267:484 → 392:302** | 1:2 → 2:1 |
| 160370093 | 237:117 → 227:82 | **350:352 → 354:344** | 248:270 → 256:307 | 1:2 → 2:1 |
| 160370099 | **118:101 → 42:308** | **429:322 → 267:376** | 521:503 → 528:469 | 3:0 → 1:2 |

Auf 160370081 sah der Scout das erste Relikt elf Züge früher, sammelte den ersten Punkt jedoch genau zum selben Zeitpunkt. Auf 160370093 genügten vier zusätzliche eigene und acht vermiedene Gegnerpunkte im zweiten Match, um aus zwei Punkten Rückstand zehn Punkte Vorsprung zu machen. Auf 160370099 erkannte der Scout das erste Punktefeld elf Züge früher und verlor dennoch beide zuvor gewonnenen ersten Matches. Für die nächste Entwicklung lohnt sich deshalb der Blick auf **welche Felder danach gehalten werden, wie lange sie Punkte liefern und wo der Gegner selbst punktet**. Die sechs kompletten Verläufe zeigen die zeitliche Abfolge. Sie isolieren den Beitrag eines einzelnen Erkundungsbefehls noch nicht.

**Prüfung.** Beide tatsächlichen Agenten wurden auf denselben drei archivierten Seeds, Sitzen und mit der ursprünglichen Solution-Fassung über jeweils 303 Züge nachgespielt. Alle sechs Spiele reproduzierten die gespeicherten Spiel- und Matchsiege, Punkte beider Teams und tatsächlichen Eingriffszahlen. Die drei unabhängig rekonstruierten Matchpunktestände summieren sich jeweils zu den archivierten ganzen Punkteständen. Es gab keine neue Variante und kein Training. [V16-Verläufe](verlauf_0.json) · [Scout-Verläufe](verlauf_1.json) · [Messskript](nachspielen.py).
