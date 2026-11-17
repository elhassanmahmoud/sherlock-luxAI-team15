# Ergebnis Dev G: Schüler v10 bringt im Spiel keinen gesicherten Fortschritt (17.11.2026)

**Kurz: Keine Variante besteht die vorab festgelegte Regel.** Gegenüber dem bestätigten Kandidaten PS (reiner Schüler
v9 mit Stay-Bias 1,0, Entstapeln und Halter-Regel) liegen das Ensemble v10 + v8L bei +0,47, das Dreier-Ensemble
v10 + v9 + v8L bei +0,18 und Stay-Bias 0,5 bei +0,37 Prozentpunkten Punkteanteil gegen Kaggle; verlangt waren
mindestens +1,0 mit unterer Grenze über 0. **Es gibt keine vierte Bestätigung; empfohlen bleibt PS**
(`experiments/candidates/devf_20261117/agent_p9_s10_halter.zip`). PS lag auch auf diesen 200 unbenutzten Karten
+5,02 [+3,92; +6,12] Prozentpunkte vor R3, der dritte unabhängige Kartensatz mit diesem Bild.

## Was gelaufen ist

Vorab festgelegt im [Plan](PLAN.md) (Commit `6d93636`, bevor v10 existierte; Nachtrag `3627246` mit den bestätigten
Schaltern und PS05, vor dem ersten Dev-G-Spiel). Karten 7264000–7264199, beide Seiten, gegen Solution und Kaggle, je
Agent 800 Spiele, zusammen 4.000. Eingefrorene Quelle `ab34c54`, 10 Prozesse, 16:08 bis 16:53
([Skript](run_devg.sh), [Protokoll](run_devg.log)). Alle Spiele liefen über 303 Schritte ohne abgefangenen Fehler.

## Ergebnisse

| Agent | Solution | Kaggle | Matches gegen Kaggle | Punkteanteil gegen Kaggle | Stehen gegen Kaggle |
|---|---:|---:|---:|---:|---:|
| R3 | 393/400 | 6/400 | 34/1.200 | 32,7 % | 31,8 % |
| **PS: v9 + v8L, Stay-Bias 1,0, Halter-Regel (bestätigt)** | **395/400** | **10/400** | **100/1.200** | **38,9 %** | 36,0 % |
| E10: v10 + v8L, gleiche Schalter | 395/400 | 22/400 | 128/1.200 | 39,1 % | 36,3 % |
| E3: v10 + v9 + v8L, gleiche Schalter | 397/400 | 8/400 | 116/1.200 | 38,9 % | 37,1 % |
| PS05: wie PS, Stay-Bias 0,5 | 396/400 | 10/400 | 112/1.200 | 39,0 % | 37,6 % |

**Gepaart** (Prozentpunkte, 95-%-Kartenintervall, 10.000 Ziehungen, Seed 2711, [Auswertung](analyze_devg.py)):

| Agent | gegen R3: Punkteanteil Kaggle | gegen R3: Spiele Solution | gegen PS: Punkteanteil Kaggle | gegen PS: Spiele Solution | gegen PS: Spiele Kaggle | besteht |
|---|---:|---:|---:|---:|---:|---|
| PS | +5,02 [+3,92; +6,12] | +0,50 [−1,00; +2,00] | – | – | – | – |
| E10 | +5,49 [+4,38; +6,62] | +0,50 [−1,00; +2,00] | +0,47 [−0,47; +1,43] | 0,00 [−0,75; +0,75] | +3,00 [−0,50; +6,50] | nein |
| E3 | +5,20 [+4,18; +6,23] | +1,00 [−0,75; +3,00] | +0,18 [−0,85; +1,16] | +0,50 [−0,50; +1,75] | −0,50 [−3,50; +2,50] | nein |
| PS05 | +5,38 [+4,36; +6,43] | +0,75 [−1,25; +2,75] | +0,37 [−0,62; +1,31] | +0,25 [−1,00; +1,75] | 0,00 [−3,00; +3,00] | nein |

## Einordnung

- **DAgger hat sich ausgereizt.** v10 ahmt den Lehrer kaum besser nach als v9 ([Nachahmung](../umbau_20261115/v10/ERGEBNIS.md))
  und spielt kaum besser. E10 gewann gegen Kaggle mehr Spiele (22 statt 10 von 400), das liegt aber im Zufall.
- **Die Schalter sind ausgereizt.** Stay-Bias 0,5 ist nicht besser als 1,0.
- **PS bleibt der empfohlene Ersatz für R3** ([dritte Bestätigung](../devf_20261117/BESTAETIGUNG3_ERGEBNIS.md),
  [Wechselanleitung](../deve_20261117/WECHSEL_ANLEITUNG.md)). Dev G wird für keine weitere Auswahl benutzt.
