# Kandidat „reiner Schüler v9, Stay-Bias 1,0, Halter-Regel“ (17.11.2026) – empfohlener Ersatz für R3

`agent_p9_s10_halter.zip` ist ein Kurspaket im Format des R3-Finalpakets (`paths.csv`, Ordner `sherlock/`, Klasse
`agents.sherlock.main.Agent_x`, eine Gewichtsdatei `sherlock/weights/agent.pth` für beide Seiten).

- SHA-256 `0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099`, 9,5 MB.
- Inhalt: Agentencode aus `agents/sherlock/` (Stand `ab34c54`) und das Imitations-Ensemble v9 + v8L
  (`ens_v9_v8L.pth`, SHA-256 `a9f551f8a3b866e42199faf9342eb9cd0c901b493cb7818992d395a9c3b6e7ea`) mit den
  Spielschaltern imit_stay_bias 1,0, imit_unstack, imit_hold_points und frozen. Kein Kaggle-Code im Paket.
- Gebaut mit `python -m scripts.build_student_package --student ens9 --set imit_stay_bias=1.0 --set imit_unstack=true
  --set imit_hold_points=true --out …` aus der eingefrorenen Quelle `ab34c54`; zwei Bauläufe ergaben dieselbe
  Prüfsumme. Ladeprüfung des Kursrunners auf beiden Seiten bestanden; 16 Dev-F-Spiele genau wie die gemessene Variante.
- Dev F: [Ergebnis](../../analysis/devf_20261117/ERGEBNIS.md). Frische Bestätigung auf 7261000–7261399 bestanden:
  [Ergebnis](../../analysis/devf_20261117/BESTAETIGUNG3_ERGEBNIS.md).
- **Keine Abgabe.** Ein Wechsel von R3 braucht das ausdrückliche Ja von Mahmoud und Moayed und vorher das Nachspielen
  unter Python 3.10 ([Anleitung](../../analysis/deve_20261117/WECHSEL_ANLEITUNG.md)).
