# Robustheit des reinen Schülers v9 gegen andere Spielweisen (festgelegt am 17.11.2026, 12:37, vor dem ersten Spiel)

Nur zur Information für die Teamentscheidung, keine Auswahl. Bisher wurde der reine Schüler v9 (P9) nur gegen
Solution, Kaggle und R3 gemessen. Im Turnier spielen andere Teams mit eigenen Spielweisen.

- **Spieler:** R3-Paket (`r3zip:`, SHA-256 `8aabdc73…a64d`) und das P9-Kurspaket
  (`experiments/candidates/deve_20261117/agent_p9_reiner_schueler.zip`, SHA-256 `1579eb83…253f`), beide als echte
  Kurspakete.
- **Gegner:** default, Zufall (random), Rush, Solution mit quadratischer Zielwahl (sol92_sq), das DQN aus der Vorlage
  (dqn) und V14 (`self:agents/sherlock/weights/agent_p0.pth`).
- **Karten:** 7263000–7263024 (25 Karten, bisher unbenutzt), beide Seiten: je Gegner 50 Spiele, je Spieler 300.
- **Warnzeichen:** P9 gewinnt gegen einen dieser Gegner mindestens 3 Spiele weniger als R3. Das wird dem Team gemeldet,
  hat aber keine automatische Folge.
- Startet nach Dev F, streng nacheinander, 10 Prozesse ([Skript](run_robust.sh)).
