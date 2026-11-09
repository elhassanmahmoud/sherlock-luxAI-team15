# Frühe Punkte: direkter Punktreward noch null, Gesamtreward nahe null

Die konservative Offlineanalyse beider akzeptierter Vorlaufreplays bestätigt Fälle mit positivem öffentlichem Team-Punktzuwachs und noch null bestätigten Punktfeldern. Der direkte `w_point`-Term ist dort null; die gespeicherte Gesamtbelohnung enthält weiterhin alle anderen Terme. **Kein Beweis für die Ursache der Niederlagen oder für den Nutzen einer neuen Rewardvariante.**

| Größe (Einheiten-Transitionen) | on48 | on49 |
|---|---:|---:|
| Alle archivierten Zeilen | 141704 | 141514 |
| Konservativ qualifiziert | 90013 | 89766 |
| Davon positiver Team-Punktzuwachs | 74576 | 72132 |
| Davon noch kein bekanntes Punktfeld | 1082 | 389 |
| Anteil dieser Teilmenge | 1,4509 % | 0,5393 % |
| Mittlerer gespeicherter Gesamt-r in Teilmenge | +0,01774 | −0,003226 |
| Median | +0,04069 | +0,01971 |
| Minimum / Maximum | −2,99137 / +1,77783 | −3,50561 / +2,82277 |
| Negative / null / positive Rewards | 262 / 0 / 820 | 104 / 0 / 285 |

Die übrigen positiven Teamgewinnzeilen mit bereits bekannten Feldern haben mittlere Gesamtbelohnung +0,35742 beziehungsweise +0,35545 (Mediane +0,12367/+0,12167). Das sind unterschiedliche Spielsituationen und keine faire kausale Kontrollgruppe. Aus diesem Unterschied wird keine Größe eines erwarteten Verbesserungsgewinns abgeleitet.

## Was tatsächlich untersucht wurde

Genau die Originaldateien `ensemble_behavior_20261109/training_v1/on48/prefill-replay.npz` und `on49/prefill-replay.npz`, je 40 Vorlaufspiele ohne Gradienten; keine neuen Spiele oder Updates. Keine Vermischung mit dem früheren Evaltrace. `s[i]`, `ns[i]`, `r[i]` und `done[i]` sind bereits derselbe gespeicherte Übergang. Die Auswahl verlangt nichtterminalen Fortschritt innerhalb desselben Matches bei unveränderten Matchsiegen, beide Punktfeatures unter der Deckelung und einen positiven Punktzuwachs. Fehlende bestätigte Felder werden am globalen Folgefeature festgestellt; `on_point=0` zusätzlich geprüft. Die ersten fünf tatsächlichen Zeilen jedes Arms sind im Originalresultat enthalten.

283218 Zeilen geprüft; 30 gezielte synthetische Tests nach echtem Red/Green bestanden. Unabhängige Nachrechnung per zeilenweiser Auswahl und Python-Statistik bestätigt alle Nenner, Rewardstatistiken und zehn Beispiele (309 Prüfungen), Root hat die tatsächlichen Daten/Belege und unveränderten Eingabe-/Schutzdateien geprüft. Herkunft ist an den versiegelten Trainingsabschluss, Originalmetadaten, NPZ-Bytehashes und relevante Originalquellen gebunden. Keine Modellimporte oder Forward-Aufrufe. [Originalresultat](result.json), `operations/` enthält Tests, Code- und Datenaudit sowie Root-Abnahme.

## Grenzen und Folgeentscheidung

Gezählt werden Einheitenübergänge, keine Spiele oder unabhängigen Punktereignisse. Ein Teamgewinn erscheint bei mehreren Einheiten; die einzelnen Verursacher sind daraus nicht bekannt. Die konservativen Ausschlüsse begrenzen die Abdeckung, und die Daten beschreiben die Anfangspolitik ohne Gradienten, nicht spätere Lernphasen. Andere Rewardterme sind überwiegend positiv, ihr Mittel hier jedoch klein. Keine automatische Rewardänderung oder Trainingsfreigabe. Vor einem möglichen Bonus wären individuelle Zuordnung, Doppelzählung bereits bekannter Punkte und Matchreset fest zu lösen; seine Wirkung müsste separat kontrolliert gemessen werden.

V14 und die abgegebene ZIP bleiben bytegleich. Der vorhandene Reward wird durch diese Diagnose nicht verändert. Ein größerer Gegnerwechsel beim Training wird als getrennte alternative Hypothese geprüft, weil zuletzt gute Solution-Werte wiederholt mit schwachen V14-Duellen einhergingen; das ist noch kein gestarteter Versuch.
