# Ergebnis der dritten frischen Bestätigung: reiner Schüler v9 mit Stay-Bias 1,0 und Halter-Regel (17.11.2026)

**Kurz: Bestanden, alle fünf Bedingungen erfüllt, und besser als der zuvor bestätigte Schüler.** Das Kurspaket
`agent_p9_s10_halter.zip` (SHA-256 `0c59706b…6099`) gewann auf 400 frischen Karten 787/800 Spiele gegen Solution (wie
R3), **20/800 gegen Kaggle** (R3 10/800) und **216 statt 76 von 2.400 Matches gegen Kaggle**. Gepaart gegen R3:
Punkteanteil gegen Kaggle **+5,51 [+4,66; +6,34]** Prozentpunkte, Spiele gegen beide Gegner zusammen +0,62 [−0,38;
+1,62] (auch nach der alten, strengeren Regel bestanden). Auf denselben Karten lag er **+1,64 [+0,96; +2,32]
Prozentpunkte** Punkteanteil gegen Kaggle vor dem zuvor bestätigten reinen Schüler v9 (P9), bei gleich vielen Siegen.
**Er ist damit der empfohlene Ersatz für R3**, sobald Mahmoud und Moayed zustimmen und das Nachspielen unter Python 3.10
bestanden ist.

## Was gelaufen ist

Vorab festgelegt im [Dev-F-Plan](PLAN.md) (Abschnitt „Danach“; Regel aus
[BESTAETIGUNG_PLAN.md](../deve_20261117/BESTAETIGUNG_PLAN.md); Kandidat im Nachtrag, Commit `7429db5`, vor dem ersten
Spiel). Karten 7261000–7261399, beide Seiten, bisher unbenutzt. Eingefrorene Quelle `ab34c54`, 10 Prozesse, 14:18 bis
15:10 ([Skript](run_bestaetigung3.sh), [Protokoll](run_bestaetigung3.log)). R3, der Kandidat und P9 spielten als echte
Kurspakete (`r3zip:`). Alle 4.800 Spiele liefen über 303 Schritte ohne abgefangenen Fehler.

## Ergebnisse

| | R3 | P9 (Information) | **Kandidat: P9 + Stay-Bias 1,0 + Halter-Regel** |
|---|---:|---:|---:|
| gewonnene Spiele gegen Solution | 787/800 | 786/800 | **787/800** |
| gewonnene Spiele gegen Kaggle | 10/800 | 20/800 | **20/800** |
| gewonnene Matches gegen Kaggle | 76/2.400 | 192/2.400 | **216/2.400** |
| gewonnene Matches gegen Solution | 2.259/2.400 | 2.303/2.400 | **2.307/2.400** |
| Punkteanteil gegen Kaggle | 33,4 % | 38,1 % | **39,3 %** |
| Punkteanteil gegen Solution | 67,6 % | 69,1 % | 68,2 % |
| direkt gegen R3 (7261000–7261099, nur Information) | – | – | 194/200 Spiele, 558/600 Matches |

**Regel** (Kandidat gegen R3, gepaart nach Karte, 10.000 Ziehungen, Seed 2711, [Auswertung](analyze_bestaetigung3.py)):

| Bedingung | verlangt | gemessen | erfüllt |
|---|---|---|---|
| 1. Punkteanteil gegen Kaggle | Mittel ≥ +2,0, untere Grenze > 0 | +5,51 [+4,66; +6,34] | ja |
| 2. Spiele gegen Solution und Kaggle zusammen | Mittel ≥ −0,5, untere Grenze ≥ −1,5 | +0,62 [−0,38; +1,62] | ja |
| 3. Spiele gegen Solution | Mittel ≥ −0,5 | 0,00 [−1,38; +1,25] | ja |
| 4. Matches je Spiel gegen Kaggle | Mittel > 0 | +0,175 [+0,127; +0,225] | ja |
| 5. Technik | keine Fehler, 303 Schritte | 4.800 Spiele fehlerfrei | ja |

**Kandidat gegen P9** (nur Information, dieselben Karten): Punkteanteil gegen Kaggle +1,64 [+0,96; +2,32], Spiele
zusammen +0,06 [−0,94; +1,06], Solution +0,13 [−1,00; +1,13], Matches je Spiel gegen Kaggle +0,030 [−0,023; +0,080].
P9 selbst lag auch auf diesen Karten klar vor R3 (Punkteanteil +3,87 [+3,11; +4,61], Spiele +0,56 [−0,44; +1,69]).

## Einordnung

- Der Vorsprung von Stay-Bias 1,0 mit Halter-Regel vor P9 aus Dev F (+1,15) **wiederholt sich auf frischen Karten**
  (+1,64). Mehr Punkte gegen Kaggle, gleich viele Siege gegen Solution.
- Gegen R3 sind beide Schüler gegen Solution gleich stark und gegen Kaggle klar stärker. Die Schalter sind nur zwei
  Zahlen in der Config des Schülers; Netz und Code sind dieselben wie bei P9.
- Für den Wechsel gilt die vorbereitete [Anleitung](../deve_20261117/WECHSEL_ANLEITUNG.md) mit diesem Paket statt P9.

## Dateien

- Rohdaten: `bestaetigung3_r3.csv`, `bestaetigung3_kandidat.csv`, `bestaetigung3_p9.csv`, `bestaetigung3_direkt.csv`.
- Kurspaket: `experiments/candidates/devf_20261117/agent_p9_s10_halter.zip`, SHA-256
  `0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099`.
