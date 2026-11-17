# Wechsel von R3 auf den reinen Schüler v9: Ablauf (vorbereitet am 17.11.2026, noch nicht ausgeführt)

**Erst ausführen, wenn beide Bedingungen erfüllt sind:**

1. Mahmoud **und** Moayed haben ausdrücklich zugestimmt (im Arbeitsstand oder im Chat festhalten).
2. Das Kandidatenpaket hat das Nachspielen unter Python 3.10 bestanden: 0 abweichende Aktionen mit
   `scripts/xversion_replay.py` ([Codex-Auftrag](../../../docs/AUFTRAG_CODEX_20261117.md), Aufgabe 2).

## Schritte

1. **Release ablegen:** `experiments/releases/2026111X_p9_schueler/` mit `agent.zip` (Kopie von
   `experiments/candidates/deve_20261117/agent_p9_reiner_schueler.zip`, SHA-256 `1579eb83…253f`), `README.md`
   (Herkunft, Dev E, Bestätigung, 3.10-Prüfung) und `release.json` im Format des R3-Release.
2. **Abgabeweg umstellen:** In `scripts/build_submission.py` zeigt `copy_final_release` auf das neue Release, mit dessen
   Prüfsumme. Test `tests/test_r3_release_submission.py` entsprechend anpassen.
3. **Abgabedatei bauen:** `python -m scripts.build_submission` schreibt `dist/agent.zip` und prüft beide Seiten im
   Kursrunner. Prüfsumme von `dist/agent.zip` muss `1579eb83…253f` sein.
4. **Doku:** README, CLAUDE.md und Arbeitsstand auf den neuen Stand bringen; Folien (Mahmouds Teil) anpassen.

## Rückweg

Das R3-Release bleibt unverändert unter `experiments/releases/20261116_r3_finale/` (SHA-256 `8aabdc73…a64d`). Für den
Rückweg genügt es, `copy_final_release` wieder darauf zeigen zu lassen und `dist/agent.zip` neu zu bauen.

## Was das Team wissen sollte

- **Stärke:** gegen Solution gleich gut wie R3 (789 gegen 787 von 800), gegen Kaggle klar besser (28 gegen 16 Spiele,
  236 gegen 90 Matches von 2.400), direkt 192/200 gegen R3 ([Bestätigung](BESTAETIGUNG_ERGEBNIS.md)).
- **Agent:** ein gelerntes Netz-Ensemble (zwei CNNs), das den Kaggle-Dritten mit DAgger nachahmt; fest eingestellt sind
  nur „weniger stehen bleiben“ und „höchstens eine stehende Unit je Feld“. Kein Kaggle-Code im Paket. Das passt zur
  Kursvorgabe „trainierte Gewichte“, in der Präsentation offenlegen, von wem das Netz gelernt hat.
- **Größe und Tempo:** 9,5 MB statt 37 MB. Die 1.600 Bestätigungsspiele dauerten mit dem Schüler 1.104 s, mit R3
  914 s (je 10 Prozesse, einschließlich der Gegner). Eine Zeitgrenze des Kurses ist nicht bekannt; die Ladeprüfung
  des Kursrunners bestand er auf beiden Seiten; ganze Kursrunner-Spiele prüft Codex mit dem 3.10-Nachspielen.
- **Robustheit:** gegen default, Zufall, Rush, Solution-Variante und das DQN der Vorlage alle 50 Spiele gewonnen wie
  R3, gegen V14 48/50 (R3 34/50); kein Warnzeichen ([Ergebnis](../robust_p9_20261117/ERGEBNIS.md)).
- **Mögliche bessere Variante:** Stay-Bias 1,0 mit Halter-Regel war auf Dev F besser als P9
  ([Dev F](../devf_20261117/ERGEBNIS.md)); ihre eigene frische Bestätigung auf 7261000–7261399 läuft. Besteht sie,
  wäre sie der bessere Ersatz (gleicher Ablauf, anderes Paket).
