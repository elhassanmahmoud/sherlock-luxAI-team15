# Sherlock V16 für das Finale am 27. November

**Seit dem 17.11.2026 ist Sherlock V16 die Abschlussabgabe von Team 15.** Der Agent heißt weiter Sherlock (Ordner
`sherlock/`, Klasse `agents.sherlock.main.Agent_x`); in den Messungen heißt die Version intern „K“. V16 ist ein Ensemble
aus zwei CNNs, die vom Kaggle-Drittplatzierten gelernt haben, mit drei festen Spielschaltern, und ersetzt R3. Mahmoud und Moayed haben dem Wechsel am Abend des 17.11. zugestimmt.
Das fertige [agent.zip](agent.zip) ist die bytegleiche Kopie des geprüften Kandidatenpakets
`experiments/candidates/devf_20261117/agent_p9_s10_halter.zip` und hat die SHA-256-Prüfsumme
`0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099`.

| Angabe für den Kursrunner | Wert |
|---|---|
| Gruppe | 15 |
| Agentenklasse | `agents.sherlock.main.Agent_x` |
| Gewichte für beide Spieler | `agents/sherlock/weights/agent.pth` (SHA-256 `8ed74128…6495`) |
| Größe | 9,5 MB |

## Was in dieser Version steckt

- **Netze:** zwei CNNs (v9 und v8L), deren Bewertungen gemittelt werden. Sie sehen die ganze Karte als 16
  Ebenen aus Sherlocks Gedächtnis, je Unit 79 Merkmale und die letzten eigenen Bewegungen. Ein eigener Zielkopf wählt
  das Feld für jeden Schuss.
- **Gelernt** durch Nachahmung und sechs DAgger-Runden vom öffentlich freigegebenen Kaggle-Drittplatzierten (lux3-bot,
  Apache-2.0), bis zu 19 Millionen Entscheidungen. Der Kaggle-Code ist nicht im Paket. In der Präsentation offenlegen,
  von wem das Netz gelernt hat.
- **Von Sherlock übernommen:** das Gedächtnis (Relikte, Punktefelder, Symmetrie, Nebel, Asteroiden, Energiefeld), die
  Aktionsmasken (`safe_moves`, `collision_guard`) und der Absturzschutz.
- **Feste Schalter:** `imit_stay_bias=1.0` (weniger stehen bleiben), `imit_unstack=true` (höchstens eine stehende Unit je
  Feld), `imit_hold_points=true` (Halter auf Punktefeldern nicht bestrafen). Alle übrigen Taktikschalter sind aus; sie
  halfen in Dev H nicht oder schadeten ([Dev H](../../analysis/devh_20261117/ERGEBNIS.md)).

## Warum K?

Auf 400 frischen Karten (7261000–7261399, dritte Bestätigung, vorab festgelegte Regel) gegen R3:

| | R3 | K |
|---|---:|---:|
| gewonnene Spiele gegen Solution | 787/800 | 787/800 |
| gewonnene Spiele gegen Kaggle | 10/800 | **20/800** |
| gewonnene Matches gegen Kaggle | 76/2.400 | **216/2.400** |
| Punkteanteil gegen Kaggle | 33,4 % | **39,3 %** |
| direkt gegen R3 | – | **194/200** |

Gepaart: Punkteanteil gegen Kaggle +5,51 [+4,66; +6,34] Prozentpunkte, Spiele gegen beide Gegner +0,62 [−0,38; +1,62]
([Ergebnis](../../analysis/devf_20261117/BESTAETIGUNG3_ERGEBNIS.md)). Dasselbe Netz mit Stay-Bias 1,5 hatte schon die
zweite Bestätigung auf 7260000–7260399 bestanden ([Ergebnis](../../analysis/deve_20261117/BESTAETIGUNG_ERGEBNIS.md)). Auf
dem unbenutzten Kartensatz Dev G lag K erneut +5,0 Prozentpunkte vor R3, in der Bestätigung 5 (7267000–7267399,
zur Information) +4,49 [+3,66; +5,34] bei 238 statt 98 gewonnenen Matches gegen Kaggle; gegen Solution gewann K dort
778/800, R3 789/800. Gegen default, Zufall, Rush, eine
Solution-Variante und das DQN der Vorlage gewann das Netz alle 50 Spiele, gegen V14 48/50 (R3 34/50)
([Robustheit](../../analysis/robust_p9_20261117/ERGEBNIS.md)). Gegen den Kaggle-Dritten verliert auch K weiterhin die
meisten Spiele.

## Ausliefern und prüfen

- Im unveränderten Kursrunner 8/8 ganze Spiele unter Python 3.14 und unter Python 3.10, Netze und Schalter in jeder
  Instanz bitgenau geprüft, ein Zug im Median 5–6 ms ([3.14](../../analysis/devf_20261117/kursrunner_p9_s10_halter.json),
  [3.10](../../analysis/deve_20261117/kursrunner_p9_s10_halter_py310.json)).
- Ein unter Python 3.14 aufgezeichnetes ganzes Spiel spielt unter Python 3.10 Zug für Zug gleich (0 abweichende Aktionen)
  ([3.10-Prüfung](../../analysis/deve_20261117/PY310_ERGEBNIS.md)).

Vom Projektordner aus erstellt der Standardaufruf die Ausgabedatei und prüft beide Sitze im Kursrunner:

```sh
python -m scripts.build_submission
shasum -a 256 dist/agent.zip   # 0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099
```

## Rückweg zu R3

Das R3-Release bleibt unverändert unter [`../20261116_r3_finale/`](../20261116_r3_finale/README.md) (SHA-256
`8aabdc73…a64d`). Für den Rückweg in `scripts/build_submission.py` `FINAL_RELEASE` und `FINAL_ZIP_SHA256` wieder auf
das R3-Release setzen (beide Werte stehen dort als `R3_RELEASE` und `R3_ZIP_SHA256`) und `dist/agent.zip` neu bauen.
Die V14-Gewichte unter `agents/sherlock/weights/` bleiben unverändert.
