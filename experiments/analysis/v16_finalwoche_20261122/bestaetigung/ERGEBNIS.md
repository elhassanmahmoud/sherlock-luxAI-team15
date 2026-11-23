# Feinanpassung des V16-Aktionskopfs

Der nachtrainierte Aktionskopf gewinnt gegen Solution 390 von 400 Spielen. Das eingereichte V16 gewinnt auf denselben Startplätzen 394. Gegen Kaggle gewinnt der Kandidat zwei Spiele mehr, im direkten Duell verliert er 58 von 100. Eine von fünf vorab festgelegten Bedingungen ist erfüllt. Die Abschlusspräsentation und das Turnierpaket verwenden weiterhin V16. [Vorab festgelegte Bedingungen](PLAN.md)

| Gegner | V16, gewonnene Spiele | Kontrollkopf, gewonnene Spiele | V16, gewonnene Matches | Kontrollkopf, gewonnene Matches |
|---|---:|---:|---:|---:|
| Solution 92 | 394/400 | 390/400 | 1.148/1.200 | 1.140/1.200 |
| Kaggle-Dritter | 14/400 | 16/400 | 104/1.200 | 98/1.200 |
| Direkt gegeneinander | 58/100 | 42/100 | 162/300 | 138/300 |

Die primäre Messgröße war der durchschnittliche Anteil an den erzielten Punkten pro Kaggle-Spiel. Er stieg von 32,57 % auf 32,88 %. Der Unterschied beträgt **+0,31 Prozentpunkte** mit einem 95-%-Kartenintervall von **−0,98 bis +1,68**. Verlangt waren mindestens +1,00 Prozentpunkte und eine positive Intervalluntergrenze. Die ganze Kaggle-Siegzahl erreichte die Mindestanforderung. Die Mindestzahlen gegen Solution und im direkten Duell wurden verfehlt. Das 95-%-Intervall der direkten Siegquote reicht von 28 % bis 56 %. [Alle Messgrößen und Entscheidungen](ergebnis.json)

Auf identischen Startplätzen gewann der Kontrollkopf gegen Kaggle zehn Spiele, die V16 verlor, und verlor acht vorherige V16-Siege. Gegen Solution wurden zwei Niederlagen gedreht und sechs Siege abgegeben. Diese Verschiebungen erklären, weshalb die beiden zusätzlichen Kaggle-Siege allein kein allgemeines Stärkeplus belegen.

## Was geprüft wurde

V16 und Kandidat verwenden die gleichen beiden Netze, Regeln und den gleichen Ladeweg. Am Kandidaten waren ausschließlich Gewichtsmatrix und Bias der letzten Aktionsschicht von v9 nachtrainiert. Der Kopf stammt aus dem ungewichteten Kontrollarm der Feldgewichtungsstudie und war vor dieser Prüfung vollständig eingefroren. Nach seiner nachträglichen Auswahl als Entwicklungskandidat hatte er im ersten separaten Vergleich auf 20 Karten 22/40 direkte Spiele gewonnen. Ein ebenfalls geprüfter Kundschafter verfehlte seine Eintrittsbedingungen. Deshalb wurde genau dieser unveränderte Kontrollkopf für die breite Bestätigung ausgewählt. [Auswahlbeleg](auswahl.json) · [Entwicklungsvergleich](../kontrollkopf/ERGEBNIS.md)

Die 200 zuvor festgelegten frischen Karten 160337000–160337199 wurden jeweils mit beiden Startseiten gegen beide externen Gegner gespielt. Die ersten 50 Karten ergaben zusätzlich 100 direkte Spiele. Zu jeder Karte blieben die Startseiten und Vergleichsarme bei der Unsicherheitsberechnung zusammen. Gezählt wurden 1.700 vollständige Spiele mit je 303 Schritten und drei Matches. Die Abschlussaufsicht meldete keine Ereignisse, eine getrennte Rechnung aus dem komprimierten Archiv bestätigte Prüfsummen, Sitzabdeckung, Sieg- und Matchzahlen, die primäre Unsicherheit und sämtliche Bedingungen. [Quellen](quellen.json) · [Rohpartien](partien.jsonl.gz) · [Abschlussbeleg](ende.json) · [Gegenrechnung](gegenrechnung.json)

Die Rohpartien lassen sich mit der Projekt-Python-Umgebung aus dem Repo-Stamm ohne weitere Spiele überprüfen.

```sh
ordner=experiments/analysis/v16_finalwoche_20261122/bestaetigung
python "$ordner/gegenrechnung.py" "$ordner"
```
