# Experimentelle Einzelnetze – keine Abgabe

Alle vier Modelle wurden am 04.11.2026 geprüft und liegen im frischen Diagnosepanel hinter V14. **Nicht als Abgabegewichte übernehmen.** [Versuchsbericht](../../../docs/SCHUELERNETZ_REWARD_20261104.md) · [Hashes](../../analysis/student_reward_20261104/candidate_manifest.json).

- `S3.pth`: drei Epochen Destillation des V14-Q-Mittels.
- `S30.pth`: vor neuen Spielresultaten festgelegte 30 Epochen.
- `CONTROL30.pth`: S30 + 160 RL-Lernspiele, bestehender SAP-Reward.
- `SAP0_30.pth`: gleicher Start und Lernumfang, SAP-Reward-Koeffizient null.

Jeweils ein aktives 79→512→512-Dueling-Netz, keine zusätzlichen Ensemblemitglieder. RL-Dateien enthalten zusätzlich Optimizerzustand; die Replay-Puffer bleiben lokal. Sherlock verwendet weiterhin sein bisheriges Belief und Regelwerk. V14 und die bestehende Gruppe15.zip wurden nicht geändert.
