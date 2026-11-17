# Kandidat „reiner Schüler v9“ (17.11.2026)

`agent_p9_reiner_schueler.zip` ist ein Kurspaket im Format des R3-Finalpakets (`paths.csv`, Ordner `sherlock/`,
Klasse `agents.sherlock.main.Agent_x`, eine Gewichtsdatei `sherlock/weights/agent.pth` für beide Seiten).

- SHA-256 `1579eb8338d1e9a98e52a96e0777633578e99e3d6e81365660f526852655253f`, 9,5 MB.
- Inhalt: Agentencode aus `agents/sherlock/` (Stand `ab34c54`) und das Imitations-Ensemble v9 + v8L
  (`ens_v9_v8L.pth`, SHA-256 `a9f551f8a3b866e42199faf9342eb9cd0c901b493cb7818992d395a9c3b6e7ea`) mit den
  Spielschaltern imit_stay_bias 1,5, imit_unstack und frozen. Kein Kaggle-Code im Paket.
- Gebaut mit `python -m scripts.build_student_package --student ens9 --out …` aus der eingefrorenen Quelle `ab34c54`;
  zwei Bauläufe ergaben dieselbe Prüfsumme. Ladeprüfung des Kursrunners auf beiden Seiten bestanden.
- Dev E: [Ergebnis](../../analysis/deve_20261117/ERGEBNIS.md). Frische Bestätigung auf 7260000–7260399 bestanden:
  [Ergebnis](../../analysis/deve_20261117/BESTAETIGUNG_ERGEBNIS.md).
- **Keine Abgabe.** Ein Wechsel von R3 braucht das ausdrückliche Ja von Mahmoud und Moayed und vorher das Nachspielen
  unter Python 3.10.
