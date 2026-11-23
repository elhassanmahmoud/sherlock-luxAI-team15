# Ablösung auf Punktefeldern

Die zusätzliche WECHSEL-Regel gewinnt auf 120 neuen Karten vier der 240 Spiele gegen den Kaggle-Dritten. V16 gewinnt acht. Der Unterschied der Siegquoten beträgt **−1,67 Prozentpunkte**, das gepaarte 95-%-Kartenintervall reicht von **−4,17 bis 0,00**. Für diesen Vergleich war vor dem ersten Spiel eine positive Untergrenze festgelegt. Die Regel verfehlte auch die Bedingungen gegen Solution und im direkten Duell. Der Halterwechsel bleibt deaktiviert. [Vorab festgelegter Vergleich](PLAN.md) · [Vollständige Auswertung](ergebnis.json)

| Gegner | Ganze Spiele V16 | Ganze Spiele WECHSEL | Einzelmatches V16 | Einzelmatches WECHSEL |
|---|---:|---:|---:|---:|
| Kaggle-Dritter | 8/240 | 4/240 | 62/720 | 58/720 |
| Solution 92 | 234/240 | 232/240 | 679/720 | 679/720 |
| Direkt gegeneinander | 134/240 | 106/240 | 395/720 | 325/720 |

Vier frühere Kaggle-Siege gingen verloren, keiner kam hinzu. Diese vier Sitze liegen auf zwei Karten. Gegen Solution gewann die Regel einen zusätzlichen Sitz und verlor drei. Die gesamte Zahl gewonnener Einzelmatches blieb dabei gleich. Im direkten Vergleich gewann WECHSEL 44,17 %, mit einem 95-%-Kartenintervall von 37,08 bis 51,25 %. Für die einfache Direktbedingung waren wenigstens 120 Siege erforderlich.

## Wie oft löste die Regel aus?

WECHSEL soll einen erschöpften Halter eines bekannten Punktfelds durch ein benachbartes energiereiches Schiff ablösen. Als Eingriff zählen einzelne Tauschpaare. Ein Befehl kann bereits dem geplanten Tausch entsprechen, deshalb werden tatsächlich geänderte Einheitsbefehle separat gezählt.

| Gegner | Spiele mit mindestens einem Tausch | Tauschpaare | Geänderte Einheitsbefehle |
|---|---:|---:|---:|
| Kaggle-Dritter | 172/240 (71,7 %) | 740 | 1.214 |
| Solution 92 | 184/240 (76,7 %) | 585 | 1.012 |
| V16 | 209/240 (87,1 %) | 1.143 | 1.918 |

Alle 124 externen Startplatzpaare ohne Tausch ergaben exakt dieselben Punkte, Matchsiege und Spielausgänge für beide Varianten. Die Regel wurde also häufig genug aktiv, um hier ihre Wirkung auf den Spielerfolg beobachten zu können. Über die Ursache einzelner verlorener Punkte geben diese Eingriffszähler allein keine Auskunft.

## Warum unterscheidet sich das vom früheren Ergebnis?

Unter 17 früheren Varianten fiel WECHSEL wegen 36/400 Kaggle-Siegen gegenüber 24/400 für V16 auf. Die zusätzlichen Siege konzentrierten sich auf wenige Karten. Für den neuen Vergleich wurden vorab 120 bisher unbenutzte Karten (160358000–160358119), beide Sitze, die historische Taktikimplementierung, das V16-Gewichtspaket und alle drei Gegner festgelegt. Acht alte Endstände wurden vor dem Versuch exakt reproduziert. Der zweite Datensatz bestätigt den zunächst beobachteten Zuwachs nicht. Die verschiedenen Stichproben werden getrennt berichtet. [Historische Sitzpaare und technische Kontrolle](ARCHIV.md)

Die lokalen Spielprozesse beendeten die beiden Teilaufträge im jeweils ersten Lauf. Die unabhängige Gegenrechnung bestätigt alle 1.200 Sitzkombinationen, den primären Unterschied, sein Intervall und die Entscheidung. Beide Startseiten einer Karte blieben bei allen 20.000 Ziehungen gemeinsam erhalten. [Rohpartien](partien.jsonl.gz) · [Prüfsummen des abgeschlossenen Laufs](abschluss.json) · [Unabhängige Kontrolle](gegenrechnung.json)

```sh
ordner=experiments/analysis/v16_finalwoche_20261122/wechsel
python "$ordner/gegenrechnung.py" "$ordner"
```
