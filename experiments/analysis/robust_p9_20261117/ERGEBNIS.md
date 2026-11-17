# Ergebnis: Robustheit des reinen Schülers v9 gegen sechs weitere Spielweisen (17.11.2026)

**Kurz: kein Warnzeichen.** Das P9-Kurspaket gewann gegen default, Zufall, Rush, die quadratische Solution-Variante und
das DQN der Vorlage alle 50 Spiele, genau wie R3. **Gegen V14 gewann P9 48/50, R3 nur 34/50.**

Vorab festgelegt im [Plan](PLAN.md) (Commit `f519e73`). Karten 7263000–7263024, beide Seiten, je Gegner 50 Spiele;
beide Spieler als echte Kurspakete (`r3zip:`), eingefrorene Quelle `ab34c54`, 14:13–14:18
([Skript](run_robust.sh), [Protokoll](run_robust.log), [Auswertung](analyze_robust.py)). Alle Spiele über 303 Schritte
ohne abgefangenen Fehler.

| Gegner | R3 Spiele | P9 Spiele | R3 Matches | P9 Matches | R3 Punkteanteil | P9 Punkteanteil | Warnzeichen |
|---|---:|---:|---:|---:|---:|---:|---|
| default | 50/50 | 50/50 | 150/150 | 150/150 | 89,7 % | 86,7 % | nein |
| DQN der Vorlage | 50/50 | 50/50 | 150/150 | 150/150 | 99,1 % | 98,3 % | nein |
| Zufall | 50/50 | 50/50 | 150/150 | 150/150 | 93,4 % | 91,8 % | nein |
| Rush | 50/50 | 50/50 | 150/150 | 148/150 | 95,1 % | 94,3 % | nein |
| V14 (Battle-Agent vom 06.11.) | 34/50 | **48/50** | 92/150 | **134/150** | 57,4 % | 62,8 % | nein |
| Solution quadratisch (sol92_sq) | 50/50 | 50/50 | 141/150 | 142/150 | 66,1 % | 67,3 % | nein |

Gegen die schwachen Gegner holt P9 einen etwas kleineren Punkteanteil, gewinnt aber alle Spiele. 25 Karten sind wenig;
ein Spiel weniger oder mehr liegt im Zufall. Die Prüfung sollte nur grobe Schwächen finden, und es gibt keine.
