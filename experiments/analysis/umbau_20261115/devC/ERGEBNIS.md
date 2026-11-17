# Gegenprobe der Schüler-Hybride auf Dev C (17.11.2026)

**Kurz:** Kein Kandidat besteht die [vorab festgelegte Leseregel](PLAN.md). Verlangt waren mindestens +2
Prozentpunkte über R3 gegen Solution und Kaggle zusammen, und gegen Solution nicht unter R3. Der Hybrid v7L kommt
mit +1,75 am nächsten, genau wie auf Dev A. Das reine Ensemble v7 + v7L gewinnt auch auf neuen Karten **192/200
direkt gegen R3**, liegt gegen die externen Gegner aber 0,75 Prozentpunkte unter R3. **Keine Bestätigung, R3 bleibt
die Abgabe.**

## Was gelaufen ist

Karten 7164000–7164099, beide Seiten, bisher von niemandem benutzt. Eingefrorene Quelle `8324845`, 10 Prozesse,
streng nacheinander von 03:37 bis 04:16 ([Skript](run_e.sh), [Protokoll](run_e.log); reines Ensemble als Nachtrag
vor dem ersten Ergebnis: [Skript](run_e2.sh), [Protokoll](run_e2.log)). Alle Spiele liefen über alle 303 Schritte.

## Ergebnisse (gewonnene Spiele von 200, in Klammern Matches von 600)

| Agent | Solution | Kaggle | direkt gegen R3 | Punkteanteil gegen Kaggle | gegen R3, Solution + Kaggle | Regel erfüllt |
|---|---:|---:|---:|---:|---:|---|
| R3 (Abgabe) | 197 (573) | 4 (20) | – | 30,8 % | – | – |
| V15 | 195 (560) | 2 (20) | 148 (416) | 32,2 % | −1,0 [−3,5; +1,25] | nein |
| Hybrid v7L | 198 (567) | 10 (32) | 162 (456) | 33,1 % | +1,75 [−0,75; +4,5] | nein, knapp unter +2 |
| Hybrid Ensemble v7 + v7L | 199 (570) | 4 (22) | 174 (474) | 33,6 % | +0,5 [−1,75; +2,75] | nein |
| reines Ensemble v7 + v7L | 196 (566) | 2 (30) | **192** (556) | 34,1 % | −0,75 [−3,0; +1,5] | nein |

Gepaart nach Karte (Prozentpunkte ganze Spiele, 95-%-Kartenintervall, 10.000 Ziehungen, Seed 2711;
[Werkzeug](../tools/compare_dev.py)), getrennt nach Gegner:

- Hybrid v7L: Solution +0,5 [−2,5; +3,5], Kaggle +3,0 [−1,0; +8,0] (8 Spiele gewonnen, 2 verloren gegenüber R3).
- Hybrid Ensemble: Solution +1,0 [−1,0; +3,5], Kaggle 0,0 [−4,0; +4,0].
- reines Ensemble: Solution −0,5 [−3,5; +2,5], Kaggle −1,0 [−5,0; +2,0].
- V15: Solution −1,0 [−4,5; +2,5], Kaggle −1,0 [−5,0; +2,0].

## Einordnung

- Dev A und Dev C zeigen dasselbe Bild: Gegen Solution und Kaggle sind die Schüler-Hybride etwa so gut wie R3. Die
  Unterschiede liegen im Rahmen des Zufalls.
- Nur der Hybrid v7L lag auf beiden Kartensätzen bei +1,75, vor allem durch Kaggle (je 10/200 statt 4/200). Über
  beide Sätze zusammen (200 Karten) sind das +1,75 [0,0; +3,62]. Das ist nur eine Einordnung und keine erfüllte
  Regel: v7L wurde auch wegen seiner Dev-A-Werte ausgewählt.
- Das reine Ensemble ist ein sehr starker direkter Gegner für R3: 192/200 Spiele und 556/600 Matches auf neuen
  Karten. Gegen Solution und Kaggle ist es nicht besser. Stärke gegen unseren eigenen R3 überträgt sich also nicht
  automatisch auf andere Gegner.
- V15 liegt auch hier unter R3, passend zur Prüfung auf 400 Karten vom 16.11.
- Dev C ist damit verbraucht. Laut Plan wird es nicht mehr für Auswahlen zwischen diesen Kandidaten verwendet.

## Dateien

- Rohdaten: `r3_devC.csv`, `v15_devC.csv`, `hyb_v7L_mixed_devC.csv`, `hyb_ens_v7_v7L_mixed_devC.csv`,
  `student_ens_v7_v7L_devC.csv` (je Spiel eine Zeile).
- SHA-256 der gespielten Dateien: R3-Paket `8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d`,
  V15 `28933a3b7810037b0af37b9ccfbf261c7c9b2b1353c8e0e8ef3b25e2c77cae45`, Hybrid v7L
  `1b17f0fea626fb01bc9957d13f5fd0b91da7f8d8ce9f9363abada574d9e6a269`, Hybrid Ensemble
  `dbdbfe98debe376841a072a4c2c860ff094cd0cdfb5d91a8fced62e7a005b9d6`, reines Ensemble
  `dca29436b560c71e7fff3d8b71af7f14afb783718c092d474c0a6b19ff2c1047`.
