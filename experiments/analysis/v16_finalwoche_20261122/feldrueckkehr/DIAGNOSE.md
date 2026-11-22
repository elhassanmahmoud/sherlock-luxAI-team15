# Was passiert nach dem Verlust eines Punktefelds?

In acht vollständigen V16-Partien gegen den Kaggle-Dritten verloren wir 176-mal die Besetzung eines früher im Match genutzten Punktefeldes. Nach 118 dieser Verluste besetzte V16 das Feld bis Matchende erneut. **Nach einem Ausfall unter gegnerischem Beschuss blieb das Feld im Schnitt deutlich länger leer als nach dem Wegziehen eines überlebenden Halters.** Die vier vollständigen Karten wurden auf beiden Sitzen gespielt. Der Sitzwechsel erzeugte in diesen Beispielen spiegelgleiche Abläufe. Für die Übertragbarkeit zählen deshalb vier Karten.

| Beobachteter Übergang | Verlustepisoden | Leere Feldzüge bis Rückkehr oder Matchende | Davon mit Rückkehr |
|---|---:|---:|---:|
| Ausfall mit gegnerischem Schussschaden | 88 | 666 | 54 |
| Halter zieht und überlebt | 62 | 282 | 50 |
| Ausfall mit gegnerischem Energieentzug durch Nachbareinheiten | 14 | 70 | 4 |
| Zusammenstoß | 4 | 8 | 2 |
| Mehrere Halter mit unterschiedlichen Übergängen | 8 | 12 | 8 |

Gezählt wurden früher bis Zug 70 tatsächlich bepunktete Felder, die V16 ab Zug 70 in einem Schritt räumte. Die Nachrechnung ordnet Schuss- und Sogschaden zu. Ein beteiligter Schuss ist kein Nachweis, dass er ohne andere Energiekosten allein tödlich gewesen wäre. Bei Matchende noch offene Rückkehrzeiten sind dort abgeschnitten.

**Was ein Ersatzschiff wirklich tun könnte.** Für die letzten sechs der acht Spiele wurde zusätzlich je Feld und Zug erfasst, warum eine umgehende Rückkehr ausfällt. Von 604 freien Feldzügen in Zug 71–94 war 218-mal keine eigene Nachbareinheit da, 136-mal lag das Feld außerhalb der aktuellen Sicht und 126-mal hielten die Nachbarn schon ein Punktefeld, bewegten sich auf ein anderes Punktefeld oder sollten schießen. In 84 Fällen bewegte V16 ohnehin schon jemanden auf das Feld. Ein Entsenden in jedem solchen Fall wäre also kein sinnvoller Eingriff. Die Zusatzmessung fehlte auf den beiden Sitzen der ersten Karte. Ein Feld kann mehrere Züge hintereinander gezählt werden.

## Ein Zug an derselben Stelle

Der Prototyp greift nur ein, wenn eine freie, ausreichend starke Nachbareinheit ein kürzlich gehaltenes, weiterhin bekanntes und aktuell sichtbares Punktefeld mit einem vom Netz plausibel bewerteten Schritt erreichen kann. Für keine der acht Änderungen musste Sherlock einen anderen Punkt oder einen Schuss aufgeben. Die Schattenempfehlung des Lehrers stimmte auf zwei Karten mit der Rückkehr und auf den anderen zwei mit dem bisherigen Befehl überein.

Pro Match war vorab nur der erste geeignete Moment vorgesehen. Hier gab es auf jeder Karte je Sitz genau einen. Das Originalspiel wurde erneut vom Start aus ausgeführt, diesmal ohne Schattenlehrer. Zum Eingriff stimmten der vollständige Enginezustand, die bisherigen Befehle beider Spieler, V16s Originalempfehlung und der angezeigte Alternativzug überein. Im zweiten Verlauf änderte sich einmal genau ein Befehl. Ab dem nächsten Zug spielten beide Seiten wieder mit ihren normalen Agenten.

| Karte | Match / Zug | Eigene Punkte zusätzlich | Veränderung der Gegnerpunkte | Änderung des Punktabstands | Weitere eigene Züge auf dem gezielten Feld |
|---|---|---:|---:|---:|---:|
| 160347000 | 2 / 76 | +2 | 0 | +2 | +1 |
| 160347001 | 3 / 77 | +4 | 0 | +4 | +3 |
| 160347002 | 3 / 81 | +2 | −4 | +6 | +2 |
| 160347003 | 2 / 69 | +1 | 0 | +1 | +1 |

Auf Karte 160347002 stand Einheit 13 von Spieler 0 in Zug 81 auf (13, 2). V16 und der Schattenlehrer wählten rechts. Als wir nur diesen Befehl durch einen Schritt nach links auf das gerade frei gewordene Punktefeld (12, 2) ersetzten, besetzte Sherlock es in sieben der nächsten acht Schritte, im Original in fünf. Insgesamt erzielten beide Teams in diesen acht Schritten 7:23 statt 5:27 Punkten. Der Punktabstand verbesserte sich um sechs. Aus dem Paar allein folgt keine Einzelursache für die vier fehlenden Gegnerpunkte.

Die Tabelle zeigt jeweils die acht Wertungszüge ab dem Eingriff. Sie gilt identisch auf beiden Sitzen. Mittlerer Effekt über die Karten: **+2,25 eigene Punkte, −1,00 Gegnerpunkte, +3,25 Punktedifferenz**. Auf allen vier Karten verbessert sich die lokale Punktedifferenz. Keine der ausgewählten Situationen lag am abgeschnittenen Matchrand. Die Spielausgänge der acht Originalpartien waren zwei Siege und sechs Niederlagen für V16; die kurzen alternativen Verläufe enden bewusst nach acht Zügen. Sie beantworten keine Frage über ganze Spiele.

Die Regel hat damit den vorab vereinbarten Wirkungstest bestanden. Der nächste Vergleich verwendet separat festgelegte 20 Karten mit ganzen Spielen gegen Solution, Kaggle und V16. [Versuchsplan](PLAN.md) · [Gemessene Verlustursachen und alle Einzelfalleffekte](diagnose_ergebnis.json) · [Originalverläufe und Verzweigungen](diagnose/) · [Quellen und Eingriffe in die Messung](herkunft.json).
