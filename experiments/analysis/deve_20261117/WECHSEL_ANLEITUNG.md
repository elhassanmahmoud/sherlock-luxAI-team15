# Wechsel von R3 auf den reinen Schüler: Ablauf (vorbereitet am 17.11.2026, ausgeführt am 17.11.2026, 23:24)

**Ausgeführt:** Mahmoud und Moayed haben zugestimmt, die 3.10-Prüfung ist bestanden. Release unter
`experiments/releases/20261117_sherlock_schueler/` (bytegleiche Kopie von `agent_p9_s10_halter.zip`, SHA-256
`0c59706b…6099`); `scripts/build_submission.py` zeigt mit `FINAL_RELEASE` darauf, `dist/agent.zip` ist neu gebaut
(„Check ok“ auf beiden Seiten). Rückweg: `FINAL_RELEASE`/`FINAL_ZIP_SHA256` auf `R3_RELEASE`/`R3_ZIP_SHA256` setzen.

**Stand 15:11: Empfohlen ist das Paket aus der dritten Bestätigung,** `experiments/candidates/devf_20261117/agent_p9_s10_halter.zip` (SHA-256 `0c59706b…6099`, reiner Schüler v9 mit Stay-Bias 1,0 und Halter-Regel). Es lag auf frischen Karten +1,64 Prozentpunkte Punkteanteil gegen Kaggle vor P9 und +5,51 vor R3 ([Ergebnis](../devf_20261117/BESTAETIGUNG3_ERGEBNIS.md)). Die Schritte unten gelten genauso, nur mit diesem Paket und seiner Prüfsumme.

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
- **Größe und Tempo:** 9,5 MB statt 37 MB. Im unveränderten Kursrunner spielte das empfohlene Paket 8 von 8 ganzen
  Spielen gegen default und Solution auf beiden Seiten (Gewichte und Schalter in jeder Instanz bitgenau geprüft,
  frisches Gedächtnis); ein Zug dauerte im Median 5–6 ms, höchstens 7 ms
  ([Protokoll](../devf_20261117/kursrunner_p9_s10_halter.json)). Eine Zeitgrenze des Kurses ist nicht bekannt.
- **Robustheit:** gegen default, Zufall, Rush, Solution-Variante und das DQN der Vorlage alle 50 Spiele gewonnen wie
  R3, gegen V14 48/50 (R3 34/50); kein Warnzeichen ([Ergebnis](../robust_p9_20261117/ERGEBNIS.md)).
- **Bessere Variante bestätigt:** Stay-Bias 1,0 mit Halter-Regel bestand die dritte frische Bestätigung auf
  7261000–7261399 (Solution 787/800 wie R3, Kaggle 20/800, Matches gegen Kaggle 216 statt 76, direkt 194/200). Die
  Robustheitsprüfung lief mit P9; die neue Variante hat dasselbe Netz und nur zwei andere Schalterwerte.
