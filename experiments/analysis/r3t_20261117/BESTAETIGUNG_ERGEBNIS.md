# Ergebnis der frischen Bestätigung "R3 + Schüler" (17.11.2026)

**Kurz: Nach der vorab festgelegten Regel nicht bestanden, um ein einziges Spiel.** Das Kurspaket R3 + Schüler
(SHA-256 `23b75afd…500d`) gewann auf 400 frischen Karten gegen Solution und Kaggle zusammen 803 von 1.600 Spielen, R3
804. Bedingung 2 verlangte im Mittel mindestens Gleichstand, gemessen wurden −0,06 Prozentpunkte [−0,94; +0,75].
Die übrigen Bedingungen sind klar erfüllt: Punkteanteil gegen Kaggle +3,53 Prozentpunkte [+2,85; +4,20], gegen
Solution +0,12 Prozentpunkte gewonnene Spiele, keine Fehler. **R3 bleibt nach der Regel die Abgabe.** Eine Übernahme
wäre nur als ausdrückliche Teamentscheidung von Mahmoud und Moayed möglich, wie bei V14 am 01.11.

## Was gelaufen ist

Vorab festgelegt im [Plan](BESTAETIGUNG_PLAN.md) (Commits `149a6f8`, Kandidat `985e523`/`e67699d`), freigegeben von
Mahmoud. Karten 7159000–7159399, beide Seiten, bisher von niemandem benutzt. Eingefrorene Quelle `149a6f8`,
10 Prozesse, von 09:19 bis 10:05 ([Skript](run_bestaetigung.sh), [Protokoll](run_bestaetigung.log)). Gespielt wurden
das unveränderte R3-Paket (`8aabdc73…a64d`) und das echte Kurspaket des Kandidaten, beide als `r3zip:` geladen. Alle
3.400 Spiele liefen über 303 Schritte ohne abgefangenen Fehler. Vorher bestand das Paket die Ladeprüfung des
Kursrunners auf beiden Seiten (`scripts/build_submission.check`).

## Ergebnisse

| | R3 | R3 + Schüler |
|---|---:|---:|
| gewonnene Spiele gegen Solution | 792/800 | 793/800 |
| gewonnene Spiele gegen Kaggle | 12/800 | 10/800 |
| gewonnene Matches gegen Kaggle | 84/2.400 | 124/2.400 |
| Punkteanteil gegen Kaggle | 32,6 % | 36,6 % |
| Punkteanteil gegen Solution | 69,1 % | 70,4 % |
| direkt gegen R3 (7159000–7159099, nur Information) | – | 192/200 Spiele, 545/600 Matches |

**Regel** (gepaart nach Karte, 10.000 Ziehungen, Seed 2711, [Auswertung](analyze.py)):

| Bedingung | verlangt | gemessen | erfüllt |
|---|---|---|---|
| 1. Punkteanteil gegen Kaggle | Mittel ≥ +2,0, untere Grenze > 0 | +3,53 [+2,85; +4,20] | ja |
| 2. Spiele gegen Solution und Kaggle zusammen | Mittel ≥ 0, untere Grenze ≥ −1,0 | −0,06 [−0,94; +0,75] | **nein** (ein Spiel) |
| 3. Spiele gegen Solution | Mittel ≥ −0,5 | +0,12 [−0,75; +1,12] | ja |
| 4. Technik | keine Fehler, 303 Schritte | 3.400 Spiele fehlerfrei | ja |

Zusätzlich (nicht Teil der Regel): gewonnene Matches je Spiel gegen Kaggle +0,050 [0,000; +0,095] (0,155 statt 0,105),
gegen Solution +0,020 [−0,009; +0,049]; Punkteanteil gegen Solution +1,20 [+0,67; +1,72].

## Einordnung

- Bei den **gewonnenen Spielen** sind beide gleich gut. Der Unterschied von einem Spiel liegt weit im Zufall.
- In allen feineren Maßen ist der Kandidat **besser**: mehr Punkte gegen beide Gegner, fast die Hälfte mehr gewonnene
  Matches gegen Kaggle. Das ist das gleiche Bild wie auf Dev D und in der zweiten Prüfung.
- Das direkte Duell (192/200) ist kein Beweis für Stärke gegen andere Gegner (siehe Lehre vom 17.11. nachts).
- Nach der vorab festgelegten Regel bleibt R3. Keine Wiederholung auf anderen Karten und keine nachträgliche Änderung
  der Regel.
- **Für eine Teamentscheidung** (Mahmoud und Moayed): Wer wechseln will, bekommt keinen Nachteil bei den Siegen und
  mehr Punkte gegen starke Gegner. Vor einer Abgabe fehlen dann noch das Nachspielen unter Python 3.10
  (`scripts/xversion_replay.py`) und die Größe: Das Paket ist 39 MB statt 37 MB.

## Dateien

- Rohdaten: `bestaetigung_r3.csv`, `bestaetigung_kandidat.csv`, `bestaetigung_direkt.csv` (je Spiel eine Zeile).
- Kurspaket (lokal): `experiments/candidates/r3t_20261117/agent_r3_schueler_ens8.zip`, SHA-256
  `23b75afd90e639a909555864b68caaee1798b20b3af12c5d8906e03d5b32500d`.
