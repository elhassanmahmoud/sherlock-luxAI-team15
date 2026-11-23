# Kursprüfung des separat verpackten Bewegungsberaters

Das eigenständige Forschungspaket mit SHA-256 `fc4061619542169bd7197bec857ff91408297bcb2c2f2f1151c03b362ba23bfe` enthält die beiden originalen V16-Netze mit bytegleichen Gewichten und die kleinere Wertfunktion daneben. Der [Paketbau](paket.py) prüft die Herkunft aller drei Bausteine. Der Agent lädt die Wertfunktion relativ zur eigenen Datei und V16 aus dem Gewichtspfad des Kursrunners.

Auf Python 3.10.15 und 3.13 war das Paket auf beiden Sitzplätzen über die normale Klassenschnittstelle ladbar. Beim Nachspielen derselben 1.212 echten Züge (vier komplette Spiele, beide Gegner und beide Seiten) entsprachen alle **19.392 Einheitenbefehle pro Python-Version** der tatsächlich gemessenen Forschungsvariante. Die Fälle enthielten jeweils vier bis sechs tatsächliche Änderungen durch den Berater. [Python 3.10](kurs310.json) · [Python 3.13](kurs313.json) · [Aufzeichnung und Vergleich](kursprobe.py)

Anschließend spielten wir mit Python 3.10 zwei dieser Solution-Spiele von vorn im unveränderten Kursrunner. Auf P0 spielte er mit ausgeschaltetem Training. Auf P1 führte der Runner alle 303 Aufrufe von `update` und einen Aufruf von `save_agent` aus. Beide Verläufe reproduzierten sämtliche 4.848 Einheitenbefehle ihres jeweiligen Originals, einschließlich der fünf bzw. vier Änderungen durch den Berater. Die bereitgestellte Gewichtsdatei hatte vor und nach beiden Durchläufen dieselbe Prüfsumme. [Runnerprüfung](kurslauf.py) · [P0](kurslauf_p0.json) · [P1](kurslauf_p1.json)

Die Spielstärke entscheidet der gesonderte Vergleich auf unbenutzten Karten. Das aktive Abgabepaket ist V16.

Auch die gesonderte Battle-ZIP mit dem Ordner `Gruppe15` ist geprüft. In Python 3.10 und 3.13 lud sie sowohl im Projektordner als auch unter `agents/`. Auch mit diesem Layout reproduzierte der unveränderte Kursrunner die beiden vollständigen Solution-Spiele in Python 3.10 bis zum letzten Einheitenbefehl. SHA-256 des Forschungspakets `39a2d30b125ebcde850a6fce23b3b4cb81b105f647b92df10264654bbd5f117d`. [Getrennter Bau](battlepaket.py) · [P0](battle_p0.json) · [P1](battle_p1.json)
