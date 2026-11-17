# Dev H: „Beast“ – alle Taktiken auf dem empfohlenen Schüler (17.11.2026, 19:42–22:23)

**Kurz:** Auf Mahmouds Wunsch („alles Mögliche eingebaut“) liefen 17 Varianten des empfohlenen Schülers K auf 200
unbenutzten Karten, je 800 Spiele. Getestet wurden alle Taktiken, ein neuer Matchende-Sturm in drei Versionen, vier
nie gemessene Schüler-Schalter und der Schüler ohne die alten Sicherheitsmasken. **Fast keine Handregel hilft dem
Schüler.** Die meisten bringen nichts oder schaden leicht. **Alles gleichzeitig einzuschalten schadet deutlich:**
−1,64 [−2,54; −0,75] Prozentpunkte Punkteanteil gegen Kaggle, nur 7 statt 24 von 400 Spielen gegen Kaggle gewonnen.
Nach der vorab festgelegten Regel hilft nur „öfter schießen“ (`imit_sap_bias=0.5`), und das knapp (+0,52 bei
verlangten +0,5). **In der frischen Bestätigung 5 fiel es durch** (+0,13 gegenüber K); K bleibt die beste Version und ist
seit dem Abend die Abgabe.

[Plan mit zwei Nachträgen](PLAN.md) · [Auswertung](analyze_devh.py) · Protokolle [Hauptlauf](run_devh.log),
[Nachträge](run_devh_nachtrag.log). Eingefrorene Quellen `0cd2ce3` (Hauptlauf) und `9d8ebfb` (ENDE10F, MASKFREI);
alle Spiele über 303 Schritte, kein abgefangener Fehler.

## Ergebnisse (7266000–7266199, beide Seiten)

| Agent | Solution | Kaggle | Matches gegen Kaggle | Punkteanteil gegen Kaggle | Punkte je Match gegen Kaggle (wir / Kaggle) |
|---|---:|---:|---:|---:|---:|
| **K** (empfohlen, Kontrolle) | 392/400 | 24/400 | 134/1.200 | 40,0 % | 206 / 308 |
| ENDE10 (Matchende-Sturm, 10 Schritte) | 395/400 | 24/400 | 138/1.200 | 40,1 % | 206 / 308 |
| ENDE20 (Matchende-Sturm, 20 Schritte) | 397/400 | 24/400 | 132/1.200 | 40,1 % | 208 / 310 |
| ENDE10F (Sturm ohne Masken, erobert) | 395/400 | 22/400 | 142/1.200 | 40,0 % | 206 / 308 |
| **ALLE** (alles gleichzeitig) | 391/400 | **7/400** | **89/1.200** | **38,4 %** | 194 / 311 |
| ENDSAP (Restenergie verschießen) | 392/400 | 20/400 | 134/1.200 | 40,0 % | 205 / 307 |
| GRANATE | 395/400 | 19/400 | 116/1.200 | 39,4 % | 202 / 311 |
| NEBEL (Granate + Nebel-Schüsse) | 392/400 | 22/400 | 125/1.200 | 39,4 % | 200 / 308 |
| SOG (Ausweichen) | 394/400 | 20/400 | 123/1.200 | 39,6 % | 202 / 308 |
| FOCUS (gemeinsame Abschüsse) | 393/400 | 22/400 | 108/1.200 | 39,4 % | 200 / 307 |
| SPAREN | 391/400 | 24/400 | 124/1.200 | 39,7 % | 205 / 310 |
| WECHSEL (Halterwechsel) | 395/400 | 36/400 | 144/1.200 | 40,2 % | 206 / 307 |
| EROBERN | 393/400 | 22/400 | 138/1.200 | 40,2 % | 206 / 307 |
| TANKEN | 395/400 | 28/400 | 154/1.200 | 40,3 % | 207 / 306 |
| COVER (Tarnung) | 392/400 | 30/400 | 162/1.200 | 40,0 % | 204 / 307 |
| **SAPBIAS** (öfter schießen) | 394/400 | 22/400 | 152/1.200 | 40,3 % | 205 / 304 |
| MASKFREI (ohne Sicherheitsmasken) | 394/400 | 24/400 | 132/1.200 | 39,2 % | 200 / 311 |

**Gepaart gegen K** (Prozentpunkte, 95-%-Kartenintervall, 10.000 Ziehungen, Seed 2711):

| Agent | Punkteanteil Kaggle | Spiele Solution | Spiele Solution + Kaggle | Spiele Kaggle | hilft |
|---|---:|---:|---:|---:|---|
| ENDE10 | +0,26 [−0,40; +0,93] | +0,75 [−0,50; +2,25] | +0,38 [−1,00; +1,88] | ±0,00 [−2,50; +2,50] | nein |
| ENDE20 | +0,01 [−0,69; +0,69] | +1,25 [−0,50; +3,25] | +0,62 [−1,00; +2,38] | ±0,00 [−3,00; +3,00] | nein |
| ENDE10F | +0,18 [−0,41; +0,76] | +0,75 [−0,50; +2,25] | +0,12 [−1,38; +1,62] | −0,50 [−3,00; +2,00] | nein |
| ALLE | **−1,64 [−2,54; −0,75]** | −0,25 [−2,50; +2,00] | −2,25 [−4,38; −0,12] | −4,25 [−7,75; −1,00] | nein |
| ENDSAP | −0,01 [−0,44; +0,46] | ±0,00 [−1,25; +1,25] | −0,50 [−2,00; +1,00] | −1,00 [−4,00; +1,50] | nein |
| GRANATE | −0,66 [−1,48; +0,18] | +0,75 [−0,50; +2,25] | −0,25 [−2,12; +1,50] | −1,25 [−4,75; +2,00] | nein |
| NEBEL | −0,67 [−1,50; +0,17] | ±0,00 [−1,50; +1,50] | −0,25 [−2,12; +1,50] | −0,50 [−3,75; +2,50] | nein |
| SOG | −0,43 [−1,03; +0,18] | +0,50 [±0,00; +1,25] | −0,25 [−1,75; +1,12] | −1,00 [−4,00; +1,50] | nein |
| FOCUS | −0,67 [−1,59; +0,25] | +0,25 [−1,00; +1,50] | −0,12 [−2,25; +2,00] | −0,50 [−4,50; +3,50] | nein |
| SPAREN | −0,10 [−0,79; +0,61] | −0,25 [−1,25; +0,50] | −0,12 [−1,62; +1,25] | ±0,00 [−3,00; +3,00] | nein |
| WECHSEL | +0,17 [−0,36; +0,70] | +0,75 [±0,00; +2,00] | +1,88 [+0,50; +3,50] | +3,00 [+0,50; +6,00] | nein |
| EROBERN | +0,35 [+0,04; +0,75] | +0,25 [±0,00; +0,75] | −0,12 [−0,75; +0,38] | −0,50 [−1,50; ±0,00] | nein |
| TANKEN | +0,21 [−0,29; +0,75] | +0,75 [±0,00; +2,00] | +0,88 [−0,50; +2,50] | +1,00 [−1,50; +3,50] | nein |
| COVER | +0,01 [−0,67; +0,71] | ±0,00 [−0,75; +0,75] | +0,75 [−0,50; +2,00] | +1,50 [−1,00; +4,00] | nein |
| **SAPBIAS** | **+0,52 [−0,39; +1,43]** | +0,50 [−0,50; +1,50] | ±0,00 [−2,12; +2,12] | −0,50 [−4,50; +3,50] | **ja** |
| MASKFREI | −0,71 [−1,67; +0,30] | +0,50 [−0,50; +1,50] | +0,25 [−1,88; +2,38] | ±0,00 [−4,00; +4,00] | nein |

## Was man daraus lernt

1. **Der Schüler macht das meiste schon selbst.** Er hat Schießen, Zielen und Ausweichen vom Kaggle-Lehrer gelernt.
   Handregeln, die über R3 noch bis +0,8 brachten, stören ihn: Granaten, Nebel-Schüsse, gemeinsame Abschüsse und
   Ausweichen kosten je 0,4–0,7 Prozentpunkte.
2. **Mehr ist nicht besser.** Alle Regeln zusammen kosten 1,6 Prozentpunkte und zwei Drittel der Siege gegen Kaggle.
   Die Regeln greifen gleichzeitig in dieselben Units ein und widersprechen dem Netz.
3. **Der Matchende-Sturm greift kaum.** Eine Nachmessung auf den Analysekarten 7256000–7256009 (20 Spiele,
   [punktefelder_ende10.csv](punktefelder_ende10.csv)) zeigt: In den letzten 10 Schritten stieg unsere Besetzung im
   zweiten Match von 2,2 auf 3,0 Felder, im dritten fiel sie von 3,2 auf 2,9. Weiter blieben rund 5 bekannte Felder leer.
   Ein protokolliertes Einzelspiel ([Skript](diag_endfill.py), 7256000) zeigt den Grund: Die Sicherheitsmasken sperren oft genau den Zug auf das freie Feld,
   und Units, die doch hinlaufen, sterben dort oft gegen Kaggles Ansturm. Auch ohne Masken (ENDE10F) blieb es bei +0,18.
4. **Die alten Sicherheitsmasken ganz abzuschalten schadet** (MASKFREI −0,71). Sie schützen den Schüler also eher.
5. **Auffällig, aber nach Regel kein Gewinn:** WECHSEL gewann gegen Kaggle 36 statt 24 Spiele (+3,00 [+0,50; +6,00]),
   der Punkteanteil stieg aber nur um +0,17. Bei 17 Varianten und vier Kennzahlen ist ein solcher Ausreißer auch durch
   Zufall zu erwarten. Er bekommt nach dem Plan keine Bestätigung.
6. Das Ergebnis passt zu Dev G: Die Spielweise des Schülers ist durch Nachahmung und einfache Schalter weitgehend
   ausgereizt. Größere Fortschritte bräuchten etwas Neues im Lernen selbst, nicht mehr Regeln.

## Bestätigung 5 (7267000–7267399, 22:25–23:22): nicht bestanden

Kandidat SAPBIAS als Kurspaket (`agent_k_sapbias.zip`), K als Kurspaket (`agent_p9_s10_halter.zip`) und R3 je 1.600 Spiele
auf 400 frischen Karten, danach der Kandidat direkt gegen K ([Skript](run_bestaetigung5.sh),
[Protokoll](run_bestaetigung5.log), [Auswertung](analyze_bestaetigung5.py)):

| | Solution | Kaggle | Matches gegen Kaggle | Punkteanteil gegen Kaggle |
|---|---:|---:|---:|---:|
| Kandidat (K + öfter schießen) | 777/800 | 28/800 | 222/2.400 | 39,5 % |
| **K** | 778/800 | **34/800** | **238/2.400** | 39,3 % |
| R3 | 789/800 | 18/800 | 98/2.400 | 33,8 % |

| Bedingung | verlangt | gemessen | erfüllt |
|---|---|---|---|
| 1. gegen K: Punkteanteil gegen Kaggle | Mittel ≥ +1,0, untere Grenze > 0 | +0,13 [−0,55; +0,81] | nein |
| 2. gegen K: Spiele Solution + Kaggle | Mittel ≥ −0,5, untere Grenze ≥ −1,5 | −0,44 [−1,62; +0,81] | nein |
| 3. gegen K: Spiele Solution | Mittel ≥ −0,5 | −0,12 [−1,12; +0,88] | ja |
| 4. gegen K: Matches je Spiel gegen Kaggle | Mittel > 0 | −0,020 [−0,083; +0,040] | nein |
| 5a. gegen R3: Punkteanteil gegen Kaggle | Mittel ≥ +2,0, untere Grenze > 0 | +4,62 [+3,75; +5,48] | ja |
| 5b. gegen R3: Spiele Solution + Kaggle | Mittel ≥ −0,5, untere Grenze ≥ −1,5 | −0,12 [−1,50; +1,25] | ja |
| 5c. gegen R3: Spiele Solution | Mittel ≥ −0,5 | −1,50 [−3,12; ±0,00] | nein |
| 5d. gegen R3: Matches je Spiel gegen Kaggle | Mittel > 0 | +0,155 [+0,100; +0,210] | ja |
| 6. Technik | keine Fehler, 303 Schritte | geprüft | ja |

Direkt gegen K gewann der Kandidat 94/200 Spiele (298/600 Matches), also etwa gleich stark. **„Öfter schießen“ ist
damit verworfen, K bleibt die empfohlene Version.** Der knappe Dev-H-Wert (+0,52) hat sich auf frischen Karten nicht
bestätigt.

**Zur Information, K gegen R3 auf denselben frischen Karten:** Punkteanteil gegen Kaggle +4,49 [+3,66; +5,34]
Prozentpunkte, Spiele gegen beide Gegner +0,31 [−1,12; +1,81], gewonnene Matches gegen Kaggle 238 statt 98, Spiele gegen
Kaggle 34 statt 18. Gegen Solution gewann K hier 778/800, R3 789/800. In der dritten Bestätigung waren es 787 zu 787. Der
Vorsprung gegen Kaggle zeigt sich damit auf dem vierten unabhängigen Kartensatz. Gegen Solution liegt K hier etwas
hinter R3. Den Wechsel von R3 auf K haben Mahmoud und Moayed am Abend beschlossen
([Release](../../releases/20261117_sherlock_v16/README.md)).
