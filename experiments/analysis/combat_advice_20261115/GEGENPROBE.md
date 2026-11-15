# Welche Art von Lehrerentscheidung hilft V14 im Spiel?

Festlegung vor den zusätzlichen Spieleingriffen am 15. November. Die Diagnose hilft bei der Entscheidung, was Sherlock als Nächstes lernen sollte. Ein Lehrer kann in einzelnen Situationen richtig zielen und als Partner von V14 trotzdem das Punktergebnis verschlechtern. Der folgende Versuch prüft das an ganzen Spielen, unabhängig von der Schussgenauigkeit des kleinen Schülernetzes.

Wir nehmen die ersten zwölf Karten der Sammlung 7271000–7271011, beide Seiten. Vier Karten je Gegner (Kaggle3, Solution_92 und V14) sind eine kleine bekannte Entwicklungsstichprobe. Ein Schattenlehrer sieht pro Schritt die öffentliche Sicht des spielenden Agenten und verfolgt die tatsächlich ausgeführten Züge.

1. Kontrolle: Erneut vollständig gespielt mit V14-Befehlen. Endstände der drei Matches in der Gesamtsumme mit der Aufzeichnung jeder Karte und Seite abgleichen.
2. Kampf: Sobald V14 oder der Lehrer einen Schuss vorschlägt, entscheidet der ausführbare Lehrerzug. Das umfasst die Wahl eines Ziels, einen zusätzlichen Schuss und den Verzicht auf einen von V14 vorgeschlagenen Schuss.
3. Bewegung: Nur wenn beide Vorschläge Bewegung oder Stehenbleiben sind, bekommt der ausführbare Lehrerzug den Vorrang.

Für jeden Arm werden ganze Spiel- und Matchsiege je Gegner, Wechsel einzelner Spielergebnisse und Eingriffszahlen dokumentiert. Nicht reproduzierte Ausgangsspiele zuerst kennzeichnen und prüfen. Eine Kategorisierung nach dem jeweils besuchten Spielzustand ergibt keine additive Aufteilung der Gesamtwirkung. Auch ein Vorteil dieser direkten Lehrerberatung ist noch kein Nachweis, dass ein eigener Schüler ihn erreichen wird.

Bei einem klaren Richtungssignal (mindestens zwei zusätzliche ganze Siege über die drei Gegner und höchstens ein Solution-Sieg weniger) wählen wir den erfolgreicheren Mechanismus als Grundlage eines eigenen Lernversuchs; Rangfolge nach zusätzlichen ganzen Siegen, anschließend Matchsiegen. Andernfalls liefern die konkreten Spielverläufe die nächste Fehlerhypothese. Kein Einsatz des Kaggle-Lehrers als abzugebende Policy. Die frischen Spielblöcke für eine echte Übernahme bleiben von dieser Entwicklungsdiagnose getrennt.
