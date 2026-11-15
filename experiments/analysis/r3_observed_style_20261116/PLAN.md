# Erkennt Sherlock V14 an öffentlich sichtbarem Spielverhalten?

Vor der Verknüpfung von Beobachtungen und Gegnerlabels ist **ein** Archivversuch festgelegt. Nach dem ersten Match soll ein konservativer Auslöser V14-artiges Verhalten von den beiden geprüften Alternativen unterscheiden. Gedacht ist er für die gesondert zu prüfende Option, V15 ab Match 2 einzusetzen. Hier wird ausschließlich die Erkennbarkeit gemessen. Bisherige Versuche nutzten unter anderem den öffentlichen Matchausgang oder Parameter vor Spielbeginn. Diese Untersuchung nutzt die im Match tatsächlich beobachtete Belegung. [Früherer Matchwechsel](../r3_v4_wl_20261115/PLAN.md)

## Feste Population

- **Fit** mit beiden Sitzen der 120 Karten 7272000–7272119 (240 Sitzarchive). **Schwellenkalibrierung** auf beiden Sitzen von 7272200–7272223 (48 Sitzarchive). Die 288 Partien lief der erste Bewegungsberater R1, SHA-256 `5327d0ff4e2cc4b09bdcb43ae51fbd7dcc9f6d8487f79f4a7cfd1ad176813575`. Diese Daten dienten zum Training von R2. [Sammlung und tatsächlicher Akteur](../movement_dagger_20261115/SAMMLUNG.md) · [Schlüssel und Prüfsummen](../movement_dagger_20261115/corpus.json)
- **Einmalige Endprüfung** auf beiden Sitzen der 48 Karten 7287000–7287047 sowie der 24 Karten 7287100–7287123. Hier spielte der ursprüngliche R3, SHA-256 `99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9`. Insgesamt 144 Sitze, 48 je Gegner, 24 Karten je Gegner. Beide Ursprungsblöcke werden zusätzlich getrennt ausgewiesen. Kein Fit und keine Schwellenauswahl mit R3. Jeder Sitz darf pro Teil genau einmal vorkommen, beide Sitze einer Karte gehören zum selben Teil, alle Einzelarchive müssen mit den vorhandenen Hashregistern übereinstimmen. [R3-Lernblock](../r3_context_selector_20261115/fit/table.json) · [R3-Diagnoseblock](../r3_context_selector_20261115/fit/validation.json)

## Öffentliche Eingabe und Auslöser

Nur die kanonischen, komprimierten Kartenebenen 0 (bereits bestätigte Punkte), 10 (sichtbare gegnerische Einheiten), 11 (deren Energie), 12 (aktuell sichtbare Fläche) und 14 (eigene Kartenhälfte). Die Uhr trennt die Züge 1–50 und 51–100 in Match 1. Verwendet werden alle bereits erfassten Ansichten mit lebender eigener Einheit. Ein fehlender Schritt unterbricht die Berechnung zwischen benachbarten Zügen. Gegnerlabels kommen ausschließlich in Fit, Kalibrierung und Auswertung vor; die Merkmalsberechnung erhält weder Kartennummer, Sitz, Gegnername, private Befehle, Lehrerwerte, Spielparameter, Punkte-/Matchergebnis noch spätere Ansichten. [Kodierung der Ebenen](../../../agents/sherlock/cnn_model.py)

Jede Hälfte liefert genau neun Zahlen. Jeweils über alle verfügbaren Züge bzw. Feldkontakte werden Zähler und Nenner zuerst summiert.

1. Sichtbare Felder geteilt durch alle beobachteten Brettfelder.
2. Anteil der Ansichten mit mindestens einem sichtbaren gegnerischen Feld.
3. Besetzte Gegnerfelder geteilt durch sichtbare Felder.
4. Anteil mehrfach besetzter Gegnerfelder an den besetzten Gegnerfeldern.
5. Sichtbare Einheiten je besetztem Gegnerfeld. Die archivierte Anzahl ist bei vier je Feld gedeckelt.
6. Anteil besetzter Gegnerfelder auf bestätigten Punktfeldern.
7. Anteil besetzter Gegnerfelder in Sherlocks eigener kanonischer Hälfte.
8. Summe der archivierten Gegnerenergie (Einheit 400, gedeckelt je Feld) geteilt durch die gedeckelte Zahl der sichtbaren Einheiten.
9. Beständigkeit der Belegung zwischen zwei direkt benachbarten Zügen derselben Hälfte. Auf Feldern, die beide Male sichtbar waren, wird die Schnittmenge der gegnerischen Belegung durch deren Vereinigung geteilt.

Ein leerer Nenner ergibt null. Die 18 Merkmale werden nur mit Mittelwert und Populationsstandardabweichung aus den 240 Fitsitzen standardisiert; konstante Merkmale erhalten Skala 1. Eine binäre logistische Regression unterscheidet V14 von den beiden anderen. Die nach Klassen ausgeglichenen Gewichte summieren sich auf 240. Zur gewichteten Summe der logistischen Verluste kommt der Term ½‖w‖², der freie Achsenabschnitt ist unbestraft. Es gibt einen Fit und keine Suche über Merkmale, Regularisierung oder Schwellen.

Die Schwelle ist das Maximum aus 0,5 und dem größten V14-Score irgendeines Kaggle- oder Solution-Sitzes in der getrennten Kalibrierung. Ausgelöst wird ausschließlich **streng oberhalb** dieser Schwelle. Die vollständige Regel wird vor dem Öffnen der R3-Beobachtungen festgeschrieben.

## Vorabentscheidung

Auf R3 müssen **mindestens 16/48 V14-Sitze** auslösen, zugleich **höchstens 1/48 Kaggle** und **höchstens 1/48 Solution**. Verfehlt eine Bedingung ihr Ziel, endet der Versuch ohne erneuten Fit, neue Merkmale oder Spielversuch. Berichtet werden die drei tatsächlichen Zähler und betroffenen Karten sowie deskriptive 95-%-Perzentilintervalle durch 10.000 Ziehungen ganzer Karten einschließlich beider Sitze je Gegner (Seed 2711). Bei Erfolg ist zunächst nur ein späterer kausaler Spieltest begründet. Die Archive decken drei konkrete Gegner und zwei Spielverteilungen ab; sie messen keinen Nutzen gegen unbekannte Gegner.
