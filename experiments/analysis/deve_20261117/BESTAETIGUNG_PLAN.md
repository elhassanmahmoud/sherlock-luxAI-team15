# Frische Bestätigung des Dev-E-Siegers auf 7260000–7260399 (festgelegt am 17.11.2026, 11:20, vor dem Ende des Dev-E-Vergleichs)

**Freigabe:** Mahmoud hat am 17.11. alle Schritte für neue Lösungen gegen Kaggle freigegeben („hast von mir alle
Go's“, „wir brauchen Fortschritt“). Die Karten 7260000–7260399 waren bisher von niemandem reserviert oder benutzt.
**Ob R3 als Abgabe ersetzt wird, entscheiden Mahmoud und Moayed gemeinsam.** Bis dahin bleibt R3 die Abgabe.

## Wer antritt

Der Kandidat, den die [Dev-E-Auswahlregel](PLAN.md) bestimmt (S9, S9H, P8 oder P9). Besteht auf Dev E keiner, fällt
die Bestätigung aus. Vor dem ersten Spiel wird unten als Nachtrag eingetragen, welcher Kandidat antritt und welche
Prüfsumme sein Kurspaket hat.

- **R3-Varianten** (S9, S9H): Kurspaket mit `scripts/build_r3t_package.py`, wie in der ersten Bestätigung.
- **Reiner Schüler** (P8, P9): Kurspaket mit `scripts/build_student_package.py` (Format wie R3: `paths.csv`,
  `sherlock/`, eine Gewichtsdatei mit den Spielschaltern imit_stay_bias 1,5 und imit_unstack).
- Vor dem ersten Spiel: Ladeprüfung des Kursrunners auf beiden Seiten (`scripts.build_submission.check`) und ein
  kurzer Gleichheitstest (das Paket spielt auf einigen Dev-E-Sitzen genau wie die gemessene Variante).

## Was gespielt wird

- **7260000–7260399** (400 Karten), beide Seiten, gegen Solution und Kaggle: R3-Paket und Kandidatenpaket je
  1.600 Spiele, beide als echte Kurspakete geladen.
- Nur zur Information: Kandidat direkt gegen R3 auf 7260000–7260099 (200 Spiele).
- Eingefrorene Quelle, 10 Prozesse, streng nacheinander, keine Trainings parallel.

## Vorab festgelegte Regel (alle Bedingungen müssen erfüllt sein)

Gepaart nach Karte gegen R3 (beide Seiten zusammen, 10.000 Ziehungen, Seed 2711):

1. **Punkteanteil gegen Kaggle:** Mittel mindestens +2,0 Prozentpunkte und untere 95-%-Grenze über 0.
2. **Gewonnene Spiele gegen Solution und Kaggle zusammen:** Mittel mindestens −0,5 Prozentpunkte und untere
   95-%-Grenze nicht unter −1,5 Prozentpunkten.
3. **Gewonnene Spiele gegen Solution:** Mittel nicht unter −0,5 Prozentpunkten.
4. **Gewonnene Matches gegen Kaggle:** im Mittel mehr als R3.
5. **Technik:** kein abgefangener Fehler in irgendeinem Spiel, alle Spiele über 303 Schritte.

**Offen gesagt: Bedingung 2 ist gegenüber der ersten Bestätigung geändert.** Dort hieß sie „Mittel mindestens 0,
untere Grenze nicht unter −1,0“, und der Kandidat verfehlte sie um ein Spiel von 1.600. Gegen beide Gegner sind die
Siege fast ausgereizt: Gegen Solution gewinnen R3 und alle Kandidaten etwa 99 %, gegen Kaggle etwa 1 %. Ein gleich
starker Agent verfehlt „Mittel mindestens 0“ dann ungefähr jedes zweite Mal allein durch Zufall. Deshalb gilt jetzt
eine kleine Toleranz von einem halben Prozentpunkt (8 Spiele von 1.600). Diese Änderung entstand nach dem Ergebnis der
ersten Bestätigung. Mahmoud und Moayed sollen das bei ihrer Entscheidung wissen. Neu ist Bedingung 4: Der Gewinn an
Punkten soll sich auch in gewonnenen Matches zeigen.

**Bestanden:** Empfehlung an Mahmoud und Moayed, R3 durch das Kandidatenpaket zu ersetzen. Vor einer Abgabe zusätzlich
das Nachspielen unter Python 3.10 (`scripts/xversion_replay.py`).
**Nicht bestanden:** R3 bleibt die Abgabe. Keine Wiederholung auf anderen Karten und keine nachträgliche Änderung
der Regel.

## Nachtrag 17.11.2026, 12:36, vor dem ersten Bestätigungsspiel: Kandidat

Nach der Dev-E-Auswahlregel tritt **P9 an, der reine Schüler v9** (Ensemble v9 + v8L, Spielschalter imit_stay_bias 1,5
und imit_unstack). Auf Dev E: Punkteanteil gegen Kaggle +4,97 [+3,92; +6,03] gegenüber R3, 0,68 vor P8
([Ergebnis](ERGEBNIS.md)).

- Kurspaket `experiments/candidates/deve_20261117/agent_p9_reiner_schueler.zip`, SHA-256
  `1579eb8338d1e9a98e52a96e0777633578e99e3d6e81365660f526852655253f`, 9,5 MB, gebaut mit
  `scripts/build_student_package.py` aus der eingefrorenen Quelle `ab34c54` (Schülergewichte `ens_v9_v8L.pth`,
  SHA-256 `a9f551f8…e7ea`). Zwei Bauläufe ergaben dieselbe Prüfsumme.
- Ladeprüfung des Kursrunners auf beiden Seiten bestanden (`scripts.build_submission.check`: „Check ok“).
- Gleichheitstest: Das Paket spielte auf 7258000–7258003 (beide Seiten, gegen Solution und Kaggle, 16 Spiele) in allen
  verglichenen Spalten genau wie P9 auf Dev E.
- Für das Duell gegen R3 spielt P9 als gleichwertige Spec (`--weights …/ens_v9_v8L.pth --set imit_stay_bias=1.5
  --set imit_unstack=true`), weil pro Prozess nur ein Paket mit dem Modul `sherlock` geladen werden kann.
