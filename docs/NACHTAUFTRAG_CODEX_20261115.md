# Nachtauftrag für Codex (Nacht 15./16.11.2026)

Vorgeschlagen von Claude Code auf Mahmouds Wunsch (15.11., abends). **Starten nur durch Moayed.** Ziel: Mahmoud findet
am Morgen Prüfungen, Robustheitsdaten und Präsentationsmaterial zum V15-Kandidaten vor, ohne dass die Abgabe
verändert wird.

## Ausgangslage

- V15-Kandidat = Hybrid v4 mixed: V14 hält Punktefelder; Units mit sichtbarem Gegner im Umkreis 5 und alle übrigen
  Units spielen den Imitations-Schüler v4 (vom Kaggle-Platz-3-Agenten gelernt, zwei DAgger-Runden) mit Stay-Bias 1,5
  und Entstapeln. Bestätigung auf 400 Karten: direkt gegen V14 91,25 %, Solution 95,5 % (V14 95,9), default 100 %,
  kaggle3 1,5 % wie V14 ([Entscheidungsvorlage](../experiments/analysis/umbau_20261115/V15_ENTSCHEIDUNG.md),
  [Bericht](../experiments/analysis/umbau_20261115/README.md)).
- **Mahmoud entscheidet morgen über die Übernahme.** Bis dahin bleibt V14 die Abgabe.
- Mahmoud startet morgen auf dem M5 selbst DAgger-Runde 3 → v5 → Test gegen V15. Diesen Lauf nicht duplizieren.

## Rahmen

- **Nicht ändern:** `agents/sherlock/weights/*`, `Gruppe15.zip`; keine V15-Installation, kein Übernahmebericht.
- **M3/8 GB:** höchstens 2 Spielprozesse; kein Training mit vielen Millionen Entscheidungen (falls überhaupt, nur
  `--low-memory`).
- **Karten nur aus 7170000–7173999** (am 15.11. geprüft unbenutzt): 7170000–7170099 Robustheit, 7171000–7171099
  Replays, 7172000ff. optionale DAgger-Daten. Alle übrigen Bereiche sind vergeben (Training ab 7200000, DAgger ab
  7250000/7251000/7252000, Dev A 7150000, Dev B 7151000, Bestätigung 7158000–7158399).
- `scripts/imitate.py`, `agents/sherlock/imitation_agent.py`, `agents/sherlock/hybrid_agent.py` und
  `experiments/analysis/umbau_20261115/tools/gates.py` nur abwärtskompatibel ändern: Mahmouds Lauf morgen nutzt sie.
  Jede Änderung braucht Tests; bei Änderungen unter `agents/sherlock/` V14-Gleichheit mit `scripts/xversion_replay.py`
  nachweisen.
- Vor jedem Push `git pull --rebase`; Ergebnisse getrennt von Code committen; Einträge im Arbeitsstand ergänzen.

## Vorbereitung

```sh
python -m scripts.fetch_kaggle3                      # Lehrer/Testgegner mit festen Prüfsummen (nie committen)
# Schüler v4 liegt im Repo: experiments/candidates/umbau_20261115/student_v4.pth (SHA-256 0e8b280c…7b7f)
python -m scripts.imitate pack-hybrid --student experiments/candidates/umbau_20261115/student_v4.pth \
    --mode mixed --combat-radius 5 --set imit_stay_bias=1.5 --set imit_unstack=true \
    --out experiments/imitation/releases/v15_codex/weights/agent.pth
```

Die gepackte Datei kann sich in den Bytes von Mahmouds Datei (`28933a3b…`) unterscheiden (Serialisierung). Inhalt und
Verhalten sind gleich: dieselben V14-Gewichte, derselbe Schüler und dieselben Schalter.

## Aufgaben (in dieser Reihenfolge)

1. **Python-3.10-Prüfung der V15-Zip** (der Prof spielt mit Python 3.10 oder neuer; auf Mahmouds Mac gibt es nur 3.14):
   `python -m scripts.build_submission --battle --from-run experiments/imitation/releases/v15_codex --out <Ordner>/Gruppe15_V15.zip`,
   dann `scripts/xversion_replay.py record` in der Hauptumgebung und `replay` unter Python 3.10 mit möglichst zwei
   torch/numpy-Ständen; Ziel 0 abweichende Aktionen. Zusätzlich `python -m scripts.check_candidate_runner` unter 3.10.
   Ergebnis nach `experiments/analysis/umbau_20261115/py310/`.
2. **Unabhängige Prüfung der V15-Bestätigung:** `gates.py` auf `confirm/*.csv` nachrechnen; Trennung der Kartenbereiche
   prüfen; Code-Review von Imitation, Hybrid, `pack-hybrid` und der `Agent_x`-Delegation (Spiegelung, Masken,
   Eigenfeld-Schüsse, Zustandsbuchhaltung, Absturzschutz). Befunde als Datei; Korrekturen nur mit Test und klarer
   Kennzeichnung.
3. **Robustheit gegen weitere Gegner** (7170000–7170099, beide Seiten): V15 und V14 jeweils gegen `sol92_sq`, `rush`,
   `dqn`, `random` und Moayeds aktuelle Kandidaten (z. B. Bewegungs-Schüler, FT18). Frage: Ist V15 gegen irgendeinen
   Gegnertyp schlechter als V14? Gepaart auswerten mit `scripts/variant_compare.py`.
4. **Replays für die Präsentation** (7171000ff., Kurs-Runner mit `train=False`): einige Spiele V15 gegen V14, gegen
   Solution_92 und gegen den Kaggle-Agenten; je 2–3 Sätze, was man sieht (z. B. koordinierter Angriff, Halten der
   Punktefelder, Schüsse in den Nebel, wo V15 verliert).
5. **Präsentationsvorschlag:** Abschnitt „Umbau“ als Ergänzung in `docs/presentation/finale_2711/`. Die Geschichte:
   Messung gegen einen Spitzenagenten (V14 gewinnt 1,5–4 %), 17 Handregeln und das Orakel helfen nicht,
   Imitation Learning mit DAgger und der Hybrid bringen 91 % gegen V14, offen bleibt die Kaggle-Lücke. Dazu die
   Offenlegung, dass das Netz vom Kaggle-Agenten gelernt hat. Zahlen nur aus den verlinkten Berichten. Bestehende
   Folien nicht umbauen, Vorschläge kennzeichnen.
6. *Optional, nur wenn 1–5 erledigt sind:* DAgger-Zusatzdaten mit Schüler v4 und Schaltern auf 7172000ff. sammeln
   (bis 400 Spiele, 2 Prozesse), nur sammeln, nicht trainieren. Die Daten bleiben lokal; die Übergabe klärt Mahmoud.

## Nicht tun

Keine Übernahme oder Änderung der Abgabe, keine Wiederholung bereits abgeschlossener Studien, kein Start von
Mahmouds DAgger-3/v5-Lauf, keine Nutzung der oben vergebenen Kartenbereiche.
