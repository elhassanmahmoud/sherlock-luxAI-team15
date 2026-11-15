# V15-Kandidat: Entscheidungsvorlage (15.11.2026, abends)

**Kandidat:** Hybrid v4 mixed. V14 hält die Punktefelder; Units mit sichtbarem Gegner im Umkreis 5 und alle übrigen
Units spielen den Imitations-Schüler v4 (vom Kaggle-Platz-3-Agenten gelernt, zwei DAgger-Runden) mit Stay-Bias 1,5
und Entstapeln. Gepackte Datei `experiments/imitation/releases/v15_candidate/weights/agent.pth` (lokal, gitignoriert),
SHA-256 `28933a3b7810037b0af37b9ccfbf261c7c9b2b1353c8e0e8ef3b25e2c77cae45`; Schüler v4 SHA-256
`0e8b280cb2173c4efd0d0c94e38119bf2f570dd5af06f52e1b5a7c9743ad7b7f`. Neu erzeugbar mit
`scripts/imitate.py pack-hybrid --student <v4> --mode mixed --combat-radius 5 --set imit_stay_bias=1.5 --set imit_unstack=true`.

**Vorab festgelegt:** [Plan und Hürden](../../../docs/superpowers/plans/2026-11-15-umbau-imitation.md); Kandidat vor dem
ersten Bestätigungsspiel mit Prüfsumme eingetragen (Commit `ddbdb4b`), Auswertung vorab als
[Skript](tools/gates.py) festgelegt (Commit `e57a85f`).

## Bestätigung (7158000–7158399, 400 Karten, beide Seiten, je 800 Spiele, eingefrorene Quelle `ddbdb4b`)

| Hürde | V14 | V15-Kandidat | Ergebnis |
|---|---:|---:|---|
| 1. kaggle3: mehr Spielsiege, untere Grenze > 0 | 1,50 % | 1,50 % (Δ 0,00 pp [−1,50; +1,50]); Matches 3,58 → 4,25 % (+0,67 pp [−0,75; +2,08]) | **verfehlt** |
| 2. solution92: höchstens 3 pp schlechter | 95,88 % | 95,50 % (Δ −0,38 pp [−2,62; +1,75]) | bestanden |
| 3. direkt gegen V14: über 50 %, untere Grenze über 50 % | – | **91,25 % [88,49; 94,00]**, Matches 1976:424 | bestanden |
| 4. default: mindestens 98 % | 100 % | 100 % | bestanden |
| 5. Technik | – | Kurs-Runner 8 Spiele bestanden (beide Seiten, default und Solution_92; Gewichte bitgenau geprüft; 9 ms Median, höchstens 13 ms je Zug); Zip-Kursprüfung in beiden Ordner-Positionen inkl. `train=True` bestanden; isoliertes Nachspielen mit nur torch/numpy 0 abweichende Aktionen | bestanden (Python 3.10 hier nicht verfügbar) |

Rohdaten: [V14-Referenz](confirm/v14_ref.csv), [Kandidat](confirm/v15_candidate.csv), [Kurs-Runner](confirm/runner_v15.json).

## Einordnung

- V15 ist auf frischen Karten gegen Solution_92 und default **gleich stark** wie V14 und schlägt V14 im **direkten
  Duell in 91 % der Spiele**. Gegen lernende Gegner wie V14 ist der Unterschied also sehr groß.
- Gegen den Kaggle-Agenten ist V15 **nicht besser** (je 1,5 % Spielsiege). Die Hürde 1 ist verfehlt; die Lücke zu
  den Spitzenteams des Battles bleibt.
- Die Auswahlwerte (Solution 97 %, kaggle3 9,3 % Matches) haben sich auf den frischen Karten nicht gehalten; das ist
  der erwartete Auswahleffekt.
- Nach dem Plan bleibt V14 die Abgabe, außer Mahmoud entscheidet ausdrücklich anders. **Empfehlung von Claude
  Code:** V15 übernehmen. In keinem gemessenen Gegner ist er schlechter, gegen lernende Agenten ist er klar
  stärker, und Technik und Kursformat sind geprüft. Voraussetzung ist, dass das Team in der Präsentation offen sagt,
  dass das Netz vom Kaggle-Agenten gelernt hat (Lehrer nicht verpackt, eigene Gewichte).

## Bei Übernahme (nur nach ausdrücklichem Ja)

1. Beide V14-Dateien mit Prüfsumme sichern (`experiments/releases/20261115_v14/`).
2. Die gepackte V15-Datei als `agents/sherlock/weights/agent_p0.pth` und `agent_p1.pth` installieren (je 26,8 MB).
3. `scripts.build_submission --battle` baut `Gruppe15.zip` neu (geprüfte Testfassung 24,9 MB); erneut prüfen.
4. Übernahmebericht, README, CLAUDE.md und Arbeitsstand aktualisieren; Rückweg zu V14 dokumentieren.
