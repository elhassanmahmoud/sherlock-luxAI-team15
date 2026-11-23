# Suchrichtung bei geringer Sicht

**Arbeitsstand am 23. November, 09:51 Uhr.** Flottenblick hat den ersten vollständigen Vergleich für eine unabhängige Wiederholung bestanden. Die Abgabe ist V16. Ein anderes Modell findet das erste Relikt auf schwierigen Starts ab Zug 55 früher. Die Auswirkung auf ganze Partien wird getrennt geprüft.

## Welche Suchrichtung hilft?

Jede Zeile basiert auf vollständigen Drei-Match-Partien, 40 neuen Karten mit Sichtweite eins und beiden Startseiten. Alle Varianten dürfen in der Eröffnung nur die Bewegung eines freien Schiffes ändern. Die ersten drei Zeilen teilen sich dieselben Karten und dieselbe V16-Kontrolle. Jede weitere Zeile hat eigene Karten. Ein positiver Zeitgewinn heißt, dass Sherlock das Relikt bzw. den ersten Punkt früher erreichte.

| Ansatz | Erstes Relikt, Züge früher | Erster Punkt, Züge früher | Siege gegen Solution | V16 auf denselben Sitzen | Siege direkt gegen V16 |
|---|---:|---:|---:|---:|---:|
| Gelernte Richtungsbewertung | −3,24 | +0,62 | 76/80 | 75/80 | 32/80 |
| Gelernter wahrscheinlicher Reliktort | +2,73 | +4,30 | 72/80 | 75/80 | 28/80 |
| Lernen aus echten Alternativwegen | +0,31 | +0,12 | 75/80 | 75/80 | 36/80 |
| Aufbruch nach Wartezügen | −0,08 | +0,15 | 78/80 | 78/80 | 39/80 |
| Nach dem ersten eigenen Punkt suchen | −0,04 | 0,00 | 78/80 | 79/80 | 38/80 |
| Künftige Sicht der übrigen Flotte | +1,76 | 0,00 | 77/80 | 76/80 | 40/80 |

Beim Flottenblick kann der gemessene Sichtvorteil auf diesen 40 Karten auch durch die Kartenwahl entstanden sein (95-%-Intervall −1,06 bis +5,13 Züge). Der zusätzliche ganze Sieg stammt von einer Karte, Startseite 1. Die eigens gebaute Versuchs-ZIP reproduziert die Befehle im Kursrunner auf zwei Python-Versionen. Die 120 zusätzlichen Sicht-1-Karten der Bestätigung werden vor Abschluss nicht zur Modellwahl oder Zwischenwertung verwendet. [Erste drei Modelle](vergleich/ERGEBNIS.md) · [Aufbruch](standsuche/duelle/ERGEBNIS.md) · [Erster Punkt](punktsicht/ERGEBNIS.md) · [Flottenblick](flottenblick/ganzspiel/ERGEBNIS.md) · [Kursrunner](flottenkurs/ERGEBNIS.md)

## Was aus den Spielzügen folgt

- Auf 28 der 80 Sitze kam der frühe Zielschätzer früher zum ersten Relikt. Elfmal kam die entscheidende Sicht vom umgeleiteten Schiff selbst, 17-mal von einem anderen Schiff. [Sicht in der echten Spielumgebung](fundursache/ERGEBNIS.md)
- Die vier verlorenen früheren Siege des Zielschätzers kippten alle in Match 3. Der größte zusätzliche Punkterückstand entstand jeweils außerhalb der Sherlock damals bekannten Reliktgebiete. Eine eigene passive Untersuchung zeigte, dass sich solche Gebiete teilweise allein aus der öffentlichen Punkteanzeige und der Sicht beweisen lassen. [Vier verlorene Spiele](uebergang/ERGEBNIS.md) · [88 überprüfte Partien](spaetgebiet/ERGEBNIS.md)
- Wenn bis Zug 55 sowohl die erste Sicht als auch die erste eigene Gutschrift fehlen, holte eine späte Richtungswahl beides auf 64 anderen, gezielt schwierigen Karten um gut vier Züge vor. Die Zahl der gewonnenen **ersten Matches** blieb bei 43/64. Die 420 vollständigen Partien prüfen die Spielwirkung auf ungefilterten Starts mit Sichtweite eins. [Unabhängige Prüfung auf schwierigen Starts](spaetsuche/OFFLINE.md)
