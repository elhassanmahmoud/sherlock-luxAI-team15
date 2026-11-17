# Tagesbericht 17.11.2026: Ein Schüler-Agent schlägt R3 in zwei frischen Bestätigungen

**Entschieden am Abend (23:24):** Mahmoud und Moayed haben zugestimmt, R3 durch den reinen Schüler v9 mit Stay-Bias 1,0
und Halter-Regel zu ersetzen. Der Agent heißt weiter Sherlock. Die Prüfung unter Python 3.10 ist bestanden
([3.10-Prüfung](../experiments/analysis/deve_20261117/PY310_ERGEBNIS.md)), `dist/agent.zip` ist neu gebaut und geprüft
([Release](../experiments/releases/20261117_sherlock_schueler/README.md)).

## Das Wichtigste in Zahlen

| Auf 400 frischen Karten (7261000–7261399) | R3 (Abgabe) | empfohlener Schüler |
|---|---:|---:|
| gewonnene Spiele gegen Solution | 787/800 | **787/800** |
| gewonnene Spiele gegen Kaggle | 10/800 | **20/800** |
| gewonnene Matches gegen Kaggle | 76/2.400 | **216/2.400** |
| Punkteanteil gegen Kaggle | 33,4 % | **39,3 %** |
| direkt gegen R3 | – | 194/200 |

Gepaart gegen R3: Punkteanteil gegen Kaggle +5,51 [+4,66; +6,34] Prozentpunkte, Spiele gegen beide Gegner zusammen
+0,62 [−0,38; +1,62]. Paket: `experiments/candidates/devf_20261117/agent_p9_s10_halter.zip` (SHA-256 `0c59706b…6099`,
9,5 MB, Format wie R3, Ladeprüfung des Kursrunners bestanden). [Ergebnis](../experiments/analysis/devf_20261117/BESTAETIGUNG3_ERGEBNIS.md)
· [Wechselanleitung mit Rückweg](../experiments/analysis/deve_20261117/WECHSEL_ANLEITUNG.md).

## Wie wir dorthin kamen

1. **Vormittag: Taktiken und R3 + Schüler.** Eine engine-genaue Analyse zeigte, dass R3 gegen Kaggle den Energiekrieg
   verliert (24 eigene Tode je Match gegen 3). Die gewünschten Handregeln (Granaten, Nebel-Schüsse, Erobern, Ausweichen,
   Sparen, Halterwechsel, Tanken) brachten einzeln höchstens +0,8 Prozentpunkte. R3 mit eingebautem Imitations-Schüler
   brachte +4, verfehlte die erste frische Bestätigung (7159000–7159399) aber um ein einziges Spiel
   ([Ergebnis](../experiments/analysis/r3t_20261117/BESTAETIGUNG_ERGEBNIS.md)).
2. **Mittag: Diagnose und Dev E.** Der reine Schüler (alle Units spielen das Netz) kämpfte gegen Kaggle am stärksten.
   Auf Dev E (7258000–7258199) war der reine Schüler v9 der beste von sechs Agenten: Kaggle 22/400 statt 2/400
   ([Ergebnis](../experiments/analysis/deve_20261117/ERGEBNIS.md)).
3. **Zweite frische Bestätigung bestanden** (7260000–7260399): reiner Schüler v9, Kaggle 28/800 statt 16/800,
   Solution 789/800 statt 787/800 ([Ergebnis](../experiments/analysis/deve_20261117/BESTAETIGUNG_ERGEBNIS.md)).
4. **Dev F** (7259000–7259199): Eine schwächere Strafe fürs Stehenbleiben (1,0 statt 1,5) zusammen mit der neuen
   Halter-Regel war besser; gezieltes Besetzen freier Punktefelder schadete
   ([Ergebnis](../experiments/analysis/devf_20261117/ERGEBNIS.md)).
5. **Dritte frische Bestätigung bestanden** (7261000–7261399): die Variante aus Dev F, auf denselben Karten auch
   +1,64 Prozentpunkte Punkteanteil vor dem Schüler aus Schritt 3.
6. **Robustheit:** Gegen default, Zufall, Rush, eine Solution-Variante und das DQN der Vorlage alle 50 Spiele
   gewonnen wie R3, gegen V14 48/50 (R3 34/50) ([Ergebnis](../experiments/analysis/robust_p9_20261117/ERGEBNIS.md)).

Alle Vergleiche waren vor dem ersten Spiel festgelegt (Pläne mit Commit), liefen aus eingefrorenen Quellständen und
werden gepaart nach Karte ausgewertet. Die Spielbedingung der Bestätigungen erlaubt seit Mittag eine Toleranz von einem
halben Prozentpunkt, weil die Siege gegen beide Gegner fast ausgereizt sind; **beide bestandenen Bestätigungen hätten
auch die alte, strengere Regel erfüllt.**

## Was der neue Agent ist

Ein Ensemble aus zwei CNNs, das durch Nachahmung und sechs DAgger-Runden vom öffentlich freigegebenen
Kaggle-Drittplatzierten gelernt hat (bis zu 19 Mio. Entscheidungen). Fest eingestellt sind nur drei Spielschalter:
weniger Stehenbleiben (Stay-Bias 1,0), höchstens eine stehende Unit je Feld, keine Strafe für Halter auf Punktefeldern.
Der Kaggle-Code ist nicht im Paket. In der Präsentation offenlegen, von wem das Netz gelernt hat.

## Abend: „Beast“-Test und Bestätigung 5

Auf Mahmouds Wunsch („alles Mögliche eingebaut“) liefen auf Dev H (7266000–7266199) 17 Varianten des empfohlenen
Schülers: alle Taktiken, ein Matchende-Sturm in drei Versionen, vier nie gemessene Schüler-Schalter und der Schüler ohne
Sicherheitsmasken. Keine Handregel half belastbar, die meisten kosteten 0,4–0,7 Prozentpunkte, **alle zusammen −1,64**
(Kaggle-Siege 7 statt 24 von 400). Nur „öfter schießen“ erreichte knapp die Schwelle und fiel in der frischen
Bestätigung 5 (7267000–7267399) durch (+0,13 gegenüber K). Dort lag K erneut +4,49 Prozentpunkte vor R3 (238 statt 98
Matches gegen Kaggle; gegen Solution 778 statt 789/800) ([Dev H und Bestätigung 5](../experiments/analysis/devh_20261117/ERGEBNIS.md)).

## Offen

- Erledigt: Ja von Mahmoud und Moayed, Release `experiments/releases/20261117_sherlock_schueler/`, `dist/agent.zip`
  neu gebaut und geprüft; Python 3.10 bestanden (0 abweichende Aktionen, 8/8 Kursrunner-Spiele).
- Abgeschlossen am Nachmittag: DAgger-Runde 7 → Schüler v10 → vorab festgelegter Vergleich Dev G (7264000–7264199).
  Keine neue Variante war besser als der empfohlene Kandidat (v10 +0,47, Dreier-Ensemble +0,18, Stay-Bias 0,5 +0,37;
  verlangt +1,0), der dort erneut +5,0 Prozentpunkte vor R3 lag
  ([Ergebnis](../experiments/analysis/devg_20261117/ERGEBNIS.md)). DAgger und Schalter sind damit weitgehend
  ausgereizt.
- Präsentation (27.11., Upload bis 23.11.): Mahmouds Folien auf den neuen Agenten umstellen, falls gewechselt wird.
