# Dev H: „Beast“ – alle Taktiken und ein Matchende-Sturm auf dem empfohlenen Schüler (festgelegt am 17.11.2026, 19:41, vor dem ersten Spiel)

**Auftrag:** Mahmoud, 17.11., abends: „ja los gehts, ich will den beast agent sherlock all in all alles mögliche
eingebaut“. R3 bleibt die Abgabe, bis Mahmoud und Moayed gemeinsam anders entscheiden. Empfohlen ist bisher **K**,
der reine Schüler v9 mit Stay-Bias 1,0, Entstapeln und Halter-Regel (`experiments/candidates/devf_20261117/agent_p9_s10_halter.zip`).

## Warum

- K holt gegen Kaggle rund 190 Punkte je Match, Kaggle 303. In den letzten 10 Schritten eines Matches besetzt Kaggle
  8 Punktefelder, wir 3, und 5,2 uns bekannte Felder bleiben leer
  ([Diagnose](../deve_20261117/DIAGNOSE.md), [Punktefelder](../deve_20261117/PUNKTEFELDER.md)).
- K verliert je Match etwa 17 Units, Kaggle 8.
- Die Taktiken (Granaten, Nebel-Schüsse, Ausweichen vor Sog, Sparen, Halterwechsel, Erobern, Tanken) wurden bisher
  nur über R3 gemessen (einzeln höchstens +0,8 Prozentpunkte), nie über dem reinen Schüler. Vier Schüler-Schalter vom
  15.11. (`end_sap`, `focus_sap`, `imit_cover`, `imit_sap_bias`) wurden noch nie gemessen.
- **Neu: Matchende-Sturm** `imit_end_fill` (agents/sherlock/imitation_agent.py, Commit `d2f1177`): In den letzten N
  punktenden Schritten eines Matches bleiben Halter auf ihrem Feld, und jedes bekannte freie Punktefeld bekommt die
  nächste eigene Unit, die es vor dem Matchende noch erreicht. Die Engine entfernt am Matchende alle Units, Überleben
  zählt dann nicht mehr.
- Die Taktiken liegen jetzt als `imit_tactics` hinter der Policy des Schülers (agents/sherlock/tactics_layer.py), damit
  sie auch im Kurspaket des Schülers stecken können. Mit allen neuen Schaltern aus spielt der Schüler nachweislich
  unverändert (Test mit 120 Schritten, alle Aktionen gleich).

## Wer antritt

Alle Agenten sind K (Ensemble v9 + v8L, `imit_stay_bias=1.0`, `imit_unstack=true`, `imit_hold_points=true`) plus:

| Name | zusätzlich |
|---|---|
| K | nichts (Kontrolle) |
| ENDE10 | `imit_end_fill=10` |
| ENDE20 | `imit_end_fill=20` |
| ALLE | alles gleichzeitig: `imit_tactics=granate+nebel+sog+sparen+wechsel+erobern+tanken`, `imit_end_fill=10`, `end_sap=10`, `focus_sap=true`, `imit_cover=0.5`, `imit_sap_bias=0.5` |
| ENDSAP | `end_sap=10` (in den letzten Schritten Restenergie verschießen) |
| GRANATE | `imit_tactics=granate` |
| NEBEL | `imit_tactics=granate+nebel` |
| SOG | `imit_tactics=sog` |
| FOCUS | `focus_sap=true` (gemeinsame sichere Abschüsse) |
| SPAREN | `imit_tactics=sparen` |
| WECHSEL | `imit_tactics=wechsel` |
| EROBERN | `imit_tactics=erobern` |
| TANKEN | `imit_tactics=tanken` |
| COVER | `imit_cover=0.5` (Tarnung) |
| SAPBIAS | `imit_sap_bias=0.5` (öfter schießen) |

Ein Probelauf vor dem Plan (Analysekarten 7256000–7256001, je 8 Spiele) lief für K und ALLE fehlerfrei und gleich
schnell. Er ist zu klein für eine Aussage und zählt nicht.

## Was gespielt wird

- **Dev H: 7266000–7266199** (200 Karten, bisher von niemandem benutzt), beide Seiten, gegen Solution und Kaggle:
  je Agent 800 Spiele, zusammen 12.000.
- Eingefrorene Quelle (dieser Plan-Commit), 10 Prozesse, streng nacheinander in der Reihenfolge der Tabelle, keine
  Trainings parallel.

## Vorab festgelegte Regel

Gepaart nach Karte gegen K (beide Seiten zusammen, 10.000 Ziehungen, Seed 2711).

**Ein Modul hilft**, wenn alle Bedingungen gelten:

1. Punkteanteil gegen Kaggle im Mittel mindestens +0,5 Prozentpunkte,
2. gewonnene Spiele gegen Solution im Mittel nicht unter −1,0 Prozentpunkt,
3. gewonnene Spiele gegen Solution und Kaggle zusammen im Mittel nicht unter −0,5 Prozentpunkten,
4. kein abgefangener Fehler, alle Spiele über 303 Schritte.

Die Schwelle ist bewusst niedrig: Dev H sucht Bausteine. Ob die Kombination wirklich besser ist, entscheidet erst die
frische Bestätigung.

**Beast-Kandidat:**

- K plus alle helfenden Module zusammen. Von ENDE10 und ENDE20 nur das mit dem höheren Punkteanteil. Helfen GRANATE
  und NEBEL, gilt das mit dem höheren Punkteanteil (NEBEL enthält granate).
- Hilft genau ein Modul, ist es selbst der Kandidat. Helfen mehrere, spielt die Kombination einmal auf Dev H (800
  Spiele). Hilft sie dort nach derselben Regel, ist sie der Kandidat, sonst das einzelne Modul mit dem höchsten
  Punkteanteil.
- Hilft kein einzelnes Modul, aber ALLE, ist ALLE der Kandidat. Hilft nichts, gibt es keine Bestätigung, und K bleibt
  empfohlen.

## Danach: frische Bestätigung 5

- **Karten 7267000–7267399** (400, bisher von niemandem benutzt), beide Seiten, gegen Solution und Kaggle: Kandidat,
  K und R3 je 1.600 Spiele. Direkt Kandidat gegen K auf 7267000–7267099 (200 Spiele, nur zur Information).
- Vorher: Kurspaket des Kandidaten mit `scripts/build_student_package.py` bauen, Ladeprüfung, Gleichheitstest gegen
  die gemessene Variante (16 Spiele).
- **Regel (alle Bedingungen müssen erfüllt sein)**, gepaart nach Karte, 10.000 Ziehungen, Seed 2711:
  1. gegenüber K: Punkteanteil gegen Kaggle im Mittel mindestens +1,0 und untere 95-%-Grenze über 0,
  2. gegenüber K: gewonnene Spiele gegen Solution und Kaggle zusammen im Mittel mindestens −0,5 und untere Grenze
     nicht unter −1,5,
  3. gegenüber K: gewonnene Spiele gegen Solution im Mittel nicht unter −0,5,
  4. gegenüber K: im Mittel mehr gewonnene Matches gegen Kaggle,
  5. gegenüber R3: die Regel aus [BESTAETIGUNG_PLAN.md](../deve_20261117/BESTAETIGUNG_PLAN.md) (Punkteanteil
     mindestens +2,0 und untere Grenze über 0; Spiele gegen beide mindestens −0,5 und untere Grenze nicht unter
     −1,5; Solution nicht unter −0,5; mehr Matches gegen Kaggle als R3),
  6. kein abgefangener Fehler, alle Spiele über 303 Schritte.
- **Bestanden:** Empfehlung, statt K den Kandidaten als R3-Ersatz zu nehmen. Der Wechsel braucht weiter das Ja von
  Mahmoud und Moayed, vorher die 3.10-Prüfung des neuen Pakets.
- **Nicht bestanden:** K bleibt empfohlen. Keine Wiederholung auf anderen Karten und keine nachträgliche Änderung der
  Regel. Dev H und 7267000–7267399 werden danach für keine Auswahl mehr benutzt.

## Nachtrag 17.11.2026, 20:08, nach ENDE10 und vor dem Ergebnis aller übrigen Dev-H-Agenten: ENDE10F

**Anlass, offen gesagt:** ENDE10 brachte auf Dev H nur +0,26 [−0,40; +0,93] Prozentpunkte Punkteanteil gegen Kaggle.
Eine Nachmessung auf den Analysekarten 7256000–7256009 (20 Spiele gegen Kaggle, `punktefelder_ende10.csv`) und ein
protokolliertes Einzelspiel zeigen den Grund: In den letzten 10 Schritten bleiben weiter rund 5 bekannte Punktefelder
leer, obwohl Units in 1–3 Feldern Abstand stehen. Die Sicherheitsmasken des Schülers (`safe_moves`,
`collision_guard`) sperren oft genau den Zug auf das freie Feld, sobald ein Gegner in der Nähe ist. Einzelne Units
pendeln deshalb neben einem freien Feld hin und her.

**Neu:** Schalter `imit_end_force` (nur zusammen mit `imit_end_fill`). In der Endphase darf eine Unit jede begehbare
Annäherung nehmen, wenn das Netz keine erlaubt. Felder mit sichtbarem Gegner zählen als frei, wenn die Unit dort nach
den Zügen mehr Energie hat als alle Gegner darauf (der Zusammenstoß zerstört sie). Ohne den Schalter bleibt
`imit_end_fill` Zeile für Zeile gleich.

| Name | zusätzlich zu K |
|---|---|
| ENDE10F | `imit_end_fill=10`, `imit_end_force=true` |

ENDE10F spielt nach dem letzten Dev-H-Agenten auf denselben Karten 7266000–7266199 (800 Spiele). Die Tests des neuen
Schalters laufen erst nach dem Ende von Dev H (keine Tests während laufender Auswertungen). Es gilt dieselbe Regel
„Ein Modul hilft“. Für den Beast-Kandidaten zählt ENDE10F zur Familie ENDE10/ENDE20: Von den helfenden ENDE-Varianten
kommt nur die mit dem höchsten Punkteanteil hinein. Am Ablauf der Bestätigung 5 ändert sich nichts.
