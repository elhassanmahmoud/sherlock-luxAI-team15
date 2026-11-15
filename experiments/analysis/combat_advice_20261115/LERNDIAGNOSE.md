# Was lernt der Schusskopf auf V14-Spielzügen?

Auf den 32 Lernkarten mit je zwei Sitzplätzen standen 201.432 Entscheidungen lebender eigener Einheiten und 10.476 legale Lehrer-Schüsse zur Verfügung. Fünf Epochen mit je 640 AdamW-Updates auf dem M3. Der Kopf ist eine eigene Konvolution mit zwei Ausgaben je Einheit: Wahrscheinlichkeit für Schießen und Verteilung über die erreichbaren Zielfelder. Die 36 V14-Netze liefen eingefroren. Modell-SHA-256 `a26c1f98645aeebe12ec7c3850ae2b01632d65adbc660436b09350db13691ddb`.

## Diagnose auf acht anderen Karten

- 51.048 Entscheidungen, darunter 2.716 legale Lehrer-Schüsse. Bei 407 Entscheidungen wollten V14 und Lehrer beide schießen. V14 wählte 187-mal dasselbe Feld wie der Lehrer (45,9 %), die tatsächlich freigegebene Zielkorrektur 206-mal (50,6 %). Ohne Vertrauensschwelle teilte der Kopf bei 220 Entscheidungen die Lehrerwahl.
- Insgesamt 211 geänderte Ziele. 35 vollständige Befehle stimmten danach erstmals mit dem Lehrer überein; 16 zuvor übereinstimmende Befehle wichen anschließend ab. Damit ist die Zielkorrektur für den Spielvergleich zugelassen.
- Die zusätzliche Schussfreigabe schlug bei 39.706 zulässigen Nicht-Schuss-Gelegenheiten kein einziges Mal einen neuen Schuss vor. Dieser Modus scheidet an der vorher definierten Mindestfallzahl aus. Die Freigabeschwellen wurden nach der Diagnose beibehalten.
- Über alle 80 Sammelpartien fielen fünf Schüsse aufs eigene Feld bei 13.192 legalen Lehrer-Schüssen an. 16 dieser Schüsse waren an einem der zehn unvereinbaren Schützenpaare beteiligt. Die Möglichkeit solcher Paare ist ein architektonischer Grund für getrennte Zielbewertungen; die niedrige Häufigkeit erklärt den gemessenen Zielgewinn nicht für sich allein.

Diese Diagnose misst Übereinstimmung mit einem Lehrer in V14-Zuständen. Der folgende Spielvergleich prüft Siege gegen Kaggle3 und Solution_92 auf 16 neuen Karten. Unterschiedlich quantisierte Eingaben zwischen NPZ und Spiel können einzelne Schwellenentscheidungen ändern.

[Validierungszahlen nach Karte und Sitz](validation.json) · [Schussanalyse und Prüfsummen der NPZ-Dateien](v14_advice_audit.json) · [Erhebungsprotokoll](data_protocol.json) · [Eigener Schusskopf](../../candidates/combat_advice_20261115/aim.pth) · [Vorabplan](PLAN.md).
