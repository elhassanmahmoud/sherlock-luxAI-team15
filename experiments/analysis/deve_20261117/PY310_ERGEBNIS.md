# Empfohlenes Paket unter Python 3.10 geprüft (17.11.2026, 19:35)

**Kurz: bestanden.** Das Paket `experiments/candidates/devf_20261117/agent_p9_s10_halter.zip` (SHA-256
`0c59706b…6099`) spielt unter Python 3.10 Zug für Zug dasselbe wie unter Python 3.14 (0 abweichende Aktionen in
606 Entscheidungen) und spielt im unveränderten Kursrunner unter Python 3.10 8 von 8 ganzen Spielen.

Durchgeführt von Claude Code auf Mahmouds Rechner, nachdem Mahmoud der Installation von Python 3.10 über Homebrew
zugestimmt hat (Aufgabe 2 aus dem [Codex-Auftrag](../../../docs/AUFTRAG_CODEX_20261117.md); Codex muss sie nicht
mehr machen). [Skript](run_py310.sh), [Protokoll](run_py310.log), Quelle eingefroren aus `8e5e595`.

## Umgebung

- Aufnahme: Projektumgebung, Python 3.14.6.
- Prüfung: Python 3.10.22 (Homebrew), torch 2.14.1, numpy 2.2.6, scipy 1.14.1, luxai-s3 aus PyPI. Mit scipy 1.15.3
  (der neuesten Version für 3.10) ließ sich `scipy.signal` auf diesem macOS nicht laden (Fehler beim Laden einer
  Bibliothek von scipy, nicht unser Code); Solution_92 braucht `scipy.signal.convolve2d`.
- Paketcode und `agents/sherlock` des eingefrorenen Stands sind Byte für Byte gleich.

## Ergebnisse

1. **Nachspielen:** Ein ganzes Spiel Sherlock gegen Sherlock (Seed 4242, 303 Schritte, beide Seiten, wie der
   Kursrunner mit `update()` nach jedem Schritt), aufgezeichnet unter 3.14 und unter 3.10 nachgespielt: Netze 2,
   eingefroren, **0 abweichende Aktionen**.
2. **Kursrunner unter 3.10** (`scripts/check_candidate_runner.py`, [Protokoll](kursrunner_p9_s10_halter_py310.json)):
   8/8 ganze Spiele (default und Solution, beide Seiten, Seeds 500720/500721, je 303 Schritte). In jeder neuen
   Instanz waren beide Netze und alle Schalter bitgenau wie in der Datei und das Gedächtnis frisch. Ein Zug dauerte
   im Median 5,3–5,7 ms, höchstens 10,1 ms. Geschützte Dateien unverändert.

## Erster Versuch ungültig (offen dokumentiert)

Der erste Lauf um 19:31 ([Protokoll](run_py310_versuch1.log)) war ungültig: `scripts/xversion_replay.py` suchte die
Gewichte nur im Battle-Format (`GRUPPE/agent.pth`), fand sie im Kurspaket-Format (`sherlock/weights/agent.pth`, Pfad in
`paths.csv`) nicht und spielte beide Male still mit zufällig initialisierten Netzen (daher 571 Abweichungen). Behoben
in `8e5e595`: Der Pfad kommt jetzt aus `paths.csv`, und ohne auffindbare Gewichte bricht das Werkzeug ab. Außerdem
scheiterte im ersten Lauf scipy (siehe oben).

## Grenzen

Ein Spiel zum Nachspielen und acht Kursrunner-Spiele auf zwei bekannten Seeds sind eine Integrationsprüfung, keine
Siegquote. Windows wurde nicht geprüft. Das Zeitlimit des Kurses ist unbekannt; gemessen wurden die Zugzeiten.
