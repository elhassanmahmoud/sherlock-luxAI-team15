# R3 gegen Solution auf drei ausgewählten Sitzpartien

Auf Karte 7273148 als Spieler 0 kippte allein Match 2. V14 gewann 263:244, R3 verlor 229:245. Solution erzielte auf beiden Verläufen fast gleich viele Punkte. R3 kam auf diesem Sitz 20 Züge später zum ersten Punkt und zur ersten Belegung eines bereits bestätigten Punktefelds. Genau auf der Gegenseite derselben Karte gewann R3 das Gesamtspiel 3:0.

| Karte · Sitz | V14 oder R3 | Match 1 | Match 2 | Match 3 | Spiel |
|---|---|---:|---:|---:|---:|
| 7273148 · P0 | V14 | 173:62 | 263:244 | 326:445 | 2:1 |
| 7273148 · P0 | R3 | 315:17 | 229:245 | 343:398 | 1:2 |
| 7273148 · P1 | V14 | 131:53 | 398:270 | 375:441 | 2:1 |
| 7273148 · P1 | R3 | 270:19 | 303:194 | 357:295 | 3:0 |
| 7273116 · P1 | V14 | 427:22 | 178:225 | 170:282 | 1:2 |
| 7273116 · P1 | R3 | 554:4 | 434:101 | 168:222 | 2:1 |

Links vom Doppelpunkt stehen die eigenen Punkte beziehungsweise Matchsiege. Alle 18 Matches wurden nach Punkten entschieden. Im verlorenen Gesamtspiel hatte R3 mit 887:660 mehr Punkte als Solution. Ein großer Vorsprung in Match 1 liefert genau einen Matchsieg.

## Wann Match 2 auf 7273148/P0 auseinanderlief

Beide Agenten kannten am Matchanfang bereits acht bestätigte Punktefelder. V14 erzielte seinen ersten Punkt in Zug 20 mit einer eigenen Einheit auf (9,11). R3 erreichte seinen ersten Punkt in Zug 40 auf (10,11). Bis einschließlich Zug 39 änderte R3 auf seinem tatsächlich besuchten Verlauf 63 Bewegungsbefehle. Keiner davon bewegte einen bestätigten Halter von einem Feld, auf dem V14 ihn stehen lassen wollte.

Die erste Abweichung des gesamten Spiels betraf in Match 1, Zug 9 die Einheit 0 auf (5,3). Auf genau dieser Beobachtung wollte V14 nach (5,4). R3 spielte nach (6,3), wo die Einheit im Folgezug aktiv sichtbar war. Die erste Änderung in Match 2 lag in Zug 5. Einheit 0 auf (2,2) sollte nach V14s Berechnung nach (3,2) gehen und kam mit R3 auf (2,3) an.

In Match 2, Zug 42, schlug V14 für Einheit 2 mit 136 Energie auf dem bestätigten Feld (10,11) Stillstand vor. R3 schickte sie nach (10,12), im folgenden Zustand stand sie dort. Über Match 2 gab es 15 solche Abgänge eines von V14 gehaltenen Felds. Ob jeweils eine andere Einheit das Feld weiter besetzte, wurde in dieser Zählung nicht erhoben. Der erste solche Abgang lag zwei Züge nach dem ersten Punkt.

| Abschnitt in Match 2 | Bestätigte belegte Felder, aufsummiert V14 / R3 | Ø aktive eigene Einheiten V14 / R3 | Ø eigene aktive Gesamtenergie V14 / R3 | Erkennbare UID-Abgänge V14 / R3 |
|---|---:|---:|---:|---:|
| Züge 1–33 | 11 / 0 | 6,2 / 6,3 | 761 / 781 | 1 / 0 |
| Züge 34–66 | 137 / 105 | 14,7 / 15,1 | 1.418 / 1.776 | 2 / 1 |
| Züge 67–100 | 106 / 122 | 13,5 / 12,9 | 1.305 / 848 | 12 / 14 |

R3s frühe Serie ohne Punkte fiel in einen Abschnitt mit mindestens ebenso vielen aktiven Einheiten und höherer durchschnittlicher Energie. Erst im letzten Drittel hatte R3 weniger aktive Einheiten und deutlich weniger Gesamtenergie. Über ganz Match 2 wurden auf beiden Verläufen je 15 Abgänge sichtbar.

## Was die Kontrollsitze zeigen

Auf 7273148/P1 gewann R3 das zuvor verlorene Match 3 mit 357:295. V14 hatte es 375:441 verloren. R3 punktete in diesem Match drei Züge später als V14 (16 gegenüber 13), verzeichnete aber 13 gegenüber 22 erkennbaren Abgängen. Zum Sieg auf dieser Seite trug der um 146 Punkte niedrigere Endstand des Gegners bei.

Auf dem geretteten Sitz 7273116/P1 kippte Match 2 von 178:225 auf 434:101. Beide Agenten punkteten erstmals in Zug 18. R3 hatte über das Match 431 bestätigte Feldbelegungen über alle Züge, V14 175. Im Schlussdrittel waren bei R3 im Mittel 15,2 eigene Einheiten aktiv, bei V14 10,2. R3 verzeichnete über das ganze Match 10 erkennbare Abgänge, V14 22. Auch auf diesem gewonnenen Verlauf verließ R3 14-mal mit einem Halter ein Feld, auf dem V14 ihn hätte stehen lassen.

## Messung und Einordnung

Sechs Vollspiele mit je 303 Schritten gegen die native Solution-Implementierung, jeweils R3 und V14 aus dem Bestätigungslauf. Alle sechs Spiele reproduzierten die archivierten Felder einschließlich Ergebnis, Matchsiegen, beiden Punktesummen und R3-Eingriffszählern. Die Laufzeit ging nicht in den Vergleich ein. Prüfbare Rohdateien liegen in [v14](v14/) und [r3](r3/), der [gepaarte Vergleich](comparison.json) enthält die Match- und Abschnittszähler. Die SHA-256 der historischen Spielzeilen lauten für V14 `2da38e26a9c863a348632ab3b558eae1d83fc9a3a1b26b319ce505181c98955e` und für R3 `5a7818a6333b036e476f11786f2013355e121cb1e6d8618f230d3b49a6630bf0`.

Belegung bezeichnet unterschiedliche, bereits vor der Aktion bestätigte Felder mit mindestens einer aktiven eigenen Einheit danach. Ein sichtbarer UID-Abgang erfasst Maskenverlust, Übergang in negative Energie oder einen erkennbaren Slot-Neuspawn. Unmittelbare Wiederverwendung am gleichen oder benachbarten Feld kann öffentlich verborgen bleiben. Die Abweichungsprotokolle vergleichen beide Befehle auf derselben R3-Beobachtung. Die nachfolgenden Matchsummen stammen aus zwei gespielten Verläufen. Welcher der einzelnen Eingriffe ein Spiel gekostet oder gerettet hätte, wurde hier nicht gemessen.


### Reproduktion

Die beiden Messmodule aus diesem Bericht werden in einer sauberen Archivkopie von `0105658188b2ec5eaf5c3a4b0ef477be9a1412f8` mit dessen Agenten und Skripten ausgeführt. `CONF` verweist auf den abgeschlossenen Ordner `movement_soft_20261115/confirmation`, `R3` auf den publizierten R3-Checkpoint. Beide Ausgabeverzeichnisse müssen neu sein.

```sh
python -m scripts.r3_solution_retrace --arm v14 --confirmation "$CONF" --out CASES/v14
python -m scripts.r3_solution_retrace --arm r3 --confirmation "$CONF" --r3 "$R3" --out CASES/r3
python -m scripts.r3_solution_retrace compare --v14 CASES/v14 --r3 CASES/r3 > CASES/comparison.json
```

Der Rekorder erfasst auf dem R3-Verlauf die Ein- und Ausgabe genau eines `_advise`-Aufrufs und gleicht die Ausgabe vor dem einzigen regulären Umgebungsschritt mit dem eingereichten Weltbefehl ab. Der Spielzähler bestätigt 583, 635 und 473 tatsächlich geänderte Befehle auf den drei jeweiligen R3-Verläufen.
