# Wann ist V14s ursprüngliche Bewegung besser?

In 144 vollständigen Partien hat R3 selbst gespielt. Der Kaggle-Lehrer bewertete die Stellungen, in die R3 tatsächlich gelangte. Auf den 48 Lernkarten (96 Sitze) schlugen R3 und V14 in **49.723** Fällen verschiedene, jeweils zulässige Bewegungen vor. Von 36 vorab definierten Situationen traten 32 auf. In keiner stimmte V14 in Summe häufiger mit dem Lehrer überein als R3. Die trainierte Tabelle schaltet deshalb in keiner Situation zu V14 zurück.

Auf 24 getrennten Karten (48 Sitze) gab es **25.556** unterschiedliche Bewegungsentscheidungen. R3 traf die Lehreraktion 21.887-mal (85,6 %), V14 2.165-mal (8,5 %). In 1.504 Fällen wählte der Lehrer eine dritte Aktion. Gegen Solution entfielen 7.063 von 8.388 dieser Entscheidungen auf R3 und 795 auf V14. Diese Zahlen beziehen sich ausschließlich auf die Stellen, an denen sich die beiden Vorschläge unterschieden.

Damit führt die Tabelle dieselben Befehle wie R3 aus. Die bisherige Bewegungsberatung bleibt als Ausgangspunkt erhalten. Die neuen Aufzeichnungen mit den ursprünglichen Bewertungen des Lehrers dienen zusätzlich zum gezielten Nachtraining eines Netzes (R8). Beide Startseiten jeder Karte wurden geprüft, und die 96 Lernarchive und 48 Diagnosearchive sind mit Prüfsummen im Ergebnis gebunden.

[Gelernte Tabelle](fit/table.json) · [Auswertung je Karte](fit/validation.json) · [Durchführung](AUSFUEHRUNG.md) · [R8-Vergleich](../r8_warm_20261115/PLAN.md)
