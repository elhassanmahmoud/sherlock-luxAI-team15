# Morgenbericht 17.11.2026 – Nacht 16./17.11. auf Mahmouds M5 (Claude Code)

**R3 bleibt die Abgabe.** Kein Schüler war gegen Solution und Kaggle sicher besser als R3. Das gilt für die
Entwicklungskarten Dev A und für die neuen Karten Dev C, geprüft nach einer vorab festgelegten Regel. Im direkten Duell
ist der Schüler aber viel stärker geworden: Das **Ensemble aus v7 und v7L schlägt R3 196/200 (Dev A) und 192/200
(Dev C)**, nach DAgger-Runde 5 das Ensemble aus v8 und v8L sogar **198/200** (Dev A). Der beste Hybrid aus Runde 5
lag gegen Solution und Kaggle zusammen auf Dev A +2,25 und auf Dev C +1,75 Prozentpunkte über R3. Das liegt knapp
unter der vorab festgelegten Schwelle von +2. Gegen den Kaggle-Agenten gibt es weiter keinen Durchbruch: 2 bis 10 von
200 Spielen, etwa ein Drittel der Punkte.

## Für Mahmoud zuerst

1. **Abgabedatei prüfen:** Auf deinem Rechner ist `dist/agent.zip` noch die alte Datei vom 12.10. (SHA-256
   `bd94ca73…24cf`), nicht das R3-Paket. Für die Abgabe das geprüfte
   [R3-ZIP](../experiments/releases/20261116_r3_finale/agent.zip) nehmen (SHA-256 `8aabdc73…a64d`), oder vorher
   `python -m scripts.build_submission` ausführen. Ich habe diese Datei absichtlich nicht angefasst.
2. **Präsentation:** Die Schüler-Ergebnisse dieser Nacht eignen sich für deine Folien 4–7. Kernaussage: „Unser Netz
   lernt vom Kaggle-Agenten. Es schlägt unseren eigenen Agenten 192 von 200 Mal, gegen fremde Gegner ist es aber
   nicht besser.“ Das ist eine ehrliche und interessante Erkenntnis.
3. **Moayed:** Der Codex-Auftrag hat einen [Nachtrag](AUFTRAG_CODEX_20261116.md#nachtrag-17112026-morgens-claude-code-nach-der-nacht-auf-dem-m5).
   Codex hat in der Nacht die Verteidigung von V15 untersucht. Ergebnis: kein bestätigter Vorteil, R3 bleibt
   ([Ergebnis](../experiments/analysis/r3_defense_20261117/ERGEBNIS.md)). Die Aufgaben aus dem Auftrag vom 16.11.
   (R3 gegen weitere Spielweisen, Fragenliste, Code-Review) sind noch offen.

## Was in der Nacht gelaufen ist

Alles streng nacheinander aus eingefrorenen Quellständen (`1c148c3`, ab 23:31 `8324845`), nie Training und viele Spiele
gleichzeitig.

| Zeit | Schritt | Ergebnis |
|---|---|---|
| 22:36–23:31 | DAgger-Runde 3 (600 Spiele) → Schüler v5 → Tests | v5 direkt 180/200 gegen R3, gegen Kaggle nichts ([v5](../experiments/analysis/umbau_20261115/v5/ERGEBNIS.md)) |
| 23:31–00:53 | neue Eingabe „letzte Bewegung“ (v6) gegen gleich lange Kontrolle (v5c) | Nachahmung 82,2 statt 80,2 %, im Spiel kein Unterschied ([v6](../experiments/analysis/umbau_20261115/v6/ERGEBNIS.md)) |
| 00:54–03:10 | DAgger-Runde 4 mit v6 → v7 und größeres Netz v7L → Tests | alle Hybride 1–2 Prozentpunkte über R3, im Rahmen des Zufalls ([v7](../experiments/analysis/umbau_20261115/v7/ERGEBNIS.md)) |
| 03:10–03:37 | frische Prüfspiele für die Nachahmung, Ensemble v7 + v7L | Ensemble rein 196/200 direkt gegen R3 |
| 03:37–04:16 | Gegenprobe auf Dev C nach vorab festgelegter Regel | kein Kandidat besteht ([Dev C](../experiments/analysis/umbau_20261115/devC/ERGEBNIS.md)) |
| 04:16–05:57 | DAgger-Runde 5 mit dem Ensemble → v8, v8L, Ensemble v8 + v8L → Tests | reines Ensemble 198/200 direkt gegen R3, Hybrid +2,25 auf Dev A ([v8](../experiments/analysis/umbau_20261115/v8/ERGEBNIS.md)) |
| 05:58–06:08 | Hybrid Ensemble v8 + v8L auf Dev C, vorher angemeldet | +1,75, Regel knapp verfehlt ([Dev C](../experiments/analysis/umbau_20261115/devC/ERGEBNIS.md)) |
| 06:08–06:14 | Nachahmung von v8, v8L und Ensemble auf den frischen Prüfspielen | Ensemble v8 + v8L 87,2 bzw. 81,9 % gleiche Aktion (Runde 4: 86,9 bzw. 81,4 %) |

## Die wichtigsten Zahlen

Gewonnene Spiele von 200 (100 Karten, beide Seiten). Gepaart = Unterschied zu R3 über Solution und Kaggle zusammen in
Prozentpunkten mit 95-%-Kartenintervall.

| Agent | Dev A Solution | Dev A Kaggle | Dev A direkt gegen R3 | Dev A gepaart | Dev C gepaart |
|---|---:|---:|---:|---:|---:|
| R3 (Abgabe) | 195 | 4 | – | – | – |
| V15 | 194 | 10 | 136 | +1,25 [−0,75; +3,5] | −1,0 [−3,5; +1,25] |
| Hybrid v5 | 193 | 0 | 158 | −1,5 [−4,0; +0,75] | – |
| Hybrid v6 | 195 | 8 | 164 | +1,0 [−2,25; +4,25] | – |
| Hybrid v7 | 198 | 6 | 162 | +1,25 [−1,75; +4,5] | – |
| Hybrid v7L | 196 | 10 | 164 | +1,75 [−0,5; +4,25] | +1,75 [−0,75; +4,5] |
| Hybrid Ensemble v7 + v7L | 200 | 2 | 174 | +0,75 [−0,76; +2,5] | +0,5 [−1,75; +2,75] |
| reiner Schüler v5 | 190 | 4 | 180 | −1,25 [−4,0; +1,5] | – |
| reiner Schüler v7 | 196 | 2 | 176 | −0,25 [−2,75; +2,25] | – |
| **reines Ensemble v7 + v7L** | 197 | 8 | **196** | +1,5 [−1,5; +4,5] | −0,75 [−3,0; +1,5] |
| Hybrid Ensemble v8 + v8L (Runde 5) | 198 | 10 | 174 | +2,25 [−0,75; +5,25] | +1,75 [−0,75; +4,5] |
| **reines Ensemble v8 + v8L (Runde 5)** | 196 | 6 | **198** | +0,75 [−2,0; +3,75] | – |

Auf Dev C gewann R3 197/200 gegen Solution und 4/200 gegen Kaggle, das reine Ensemble v7 + v7L 196/200 und 2/200
sowie **192/200 direkt gegen R3**. Die Regel für eine Bestätigung verlangte auf Dev C mindestens +2 Prozentpunkte.
Am nächsten kamen der Hybrid v7L und der Hybrid Ensemble v8 + v8L mit je +1,75. Der Hybrid Ensemble v8 + v8L
gewann auf Dev C 200/200 gegen Solution und 8/200 gegen Kaggle.

## Was wir gelernt haben

1. **DAgger wirkt, aber nur teilweise.** Jede Runde machte den Schüler gegen Solution und im direkten Duell stärker
   (reiner Schüler gegen Solution: v4 185, v5 190, v7 196 von 200; direkt gegen R3 zuletzt 198/200). Auf frischen
   Spielen ahmt er den Lehrer mit jeder Runde genauer nach, aber mit immer kleineren Schritten (Runde 5: +0,5
   Prozentpunkte). Gegen den Kaggle-Lehrer selbst bleibt er bei wenigen Siegen.
2. **„Letzte Bewegung“ als Eingabe** verbessert die Nachahmung auch auf frischen Spielen um 1,2 bis 2,5
   Prozentpunkte. Dafür wiederholt der Schüler seine Bewegung öfter als der Lehrer (63 statt 58 %). Im Spiel brachte
   das keinen messbaren Gewinn.
3. **Ein fast dreimal so großes Netz** lernt in zwei Epochen nicht mehr als das kleine Netz mit langer
   Trainingskette. Auch nach Runde 5 liegt es knapp darunter.
4. **Ein Ensemble aus zwei Schülern** ahmt kaum genauer nach (+0,3 Prozentpunkte), spielt im direkten Duell aber
   deutlich stärker (+10 Prozentpunkte gegen R3).
5. **Duellstärke ist nicht alles.** Ein Agent, der R3 192 von 200 Mal schlägt, ist gegen Solution und Kaggle nicht
   besser als R3. Für die Abgabe zählen deshalb weiter die externen Gegner.
6. **Vorab festgelegte Regeln schützen vor Selbsttäuschung.** Der beste Wert auf den oft benutzten Karten Dev A
   (+2,25) schrumpfte auf neuen Karten auf +1,75. Ohne die Regel hätten wir den Hybrid vielleicht für besser
   gehalten.

## Was das für das Finale heißt

- R3 bleibt. Die Abgabe sollte bis 23.11. eingefroren werden.
- Nach der vorab festgelegten Regel kommt kein Kandidat für eine frische Bestätigung auf 7159000–7159399 in Frage.
  Am nächsten liegen der Hybrid v7L und der Hybrid Ensemble v8 + v8L mit je +1,75 auf Dev C. Ich empfehle keine
  Bestätigung: Der Vorsprung ist klein, und die frühere Bestätigung eines ähnlichen Hybrids auf 400 Karten war
  negativ. Eine Ausnahme müssten Mahmoud und Moayed gemeinsam entscheiden und vorher festlegen.
- Weitere DAgger-Runden derselben Art bringen kaum noch etwas. Schülerarbeit ist nur sinnvoll, wenn sie gezielt die
  Kaggle-Lücke angeht. Die Kampfdiagnose aus dem Codex-Auftrag (Aufgabe 4) zeigt, wo genau der Schüler gegen Kaggle
  verliert. Sie ist der beste nächste Schritt.
- Deshalb habe ich nach Runde 5 keine weitere Runde gestartet. Für neue Kandidaten gibt es außer der reservierten
  Bestätigung keine unbenutzten Karten mehr, und über die Bestätigung entscheidet ihr.

## Umfang der Nacht

| Teil | Spiele |
|---|---:|
| DAgger-Sammlung (Runden 3, 4, 5 je 600 Spiele, Probelauf 2 Spiele) | 1.802 |
| frische Prüfspiele für die Nachahmung | 120 |
| Leistungsmessungen Dev A | 10.000 |
| Gegenprobe Dev C | 3.400 |

Training: v5 (von Grund auf), v6 und v5c (Fortsetzungen von v5), v7, v7L (größeres Netz von Grund auf), v8, v8L.
Alle Schüler liegen lokal unter `experiments/imitation/students/`. Ihre Prüfsummen stehen in den Ergebnisdateien.
Im Repo liegen `experiments/candidates/umbau_20261116/student_v5.pth` und `student_v6.pth`.

## Eingefroren um FREEZE_ZEIT

- Keine Prozesse mehr auf Mahmouds Rechner (geprüft mit `ps`). Alles committet und gepusht (letzter Commit siehe
  `git log`).
- Unverändert (SHA-256 geprüft): V14-Gewichte `agent_p0.pth` und `agent_p1.pth` (`98a07350…d3d8`), R3-Paket
  `experiments/releases/20261116_r3_finale/agent.zip` (`8aabdc73…a64d`), `dist/agent.zip` (`bd94ca73…24cf`, alt),
  `Gruppe15.zip` (`50c188b1…688a`).
