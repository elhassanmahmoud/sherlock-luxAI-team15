# Die internen Netzbewertungen verbesserten die Auswahl des Suchwegs nicht

Auf 160 bereits für die Flottensuche bekannten Entwicklungskarten verglichen wir zwei neue Bewerter. Sie entschieden genau beim ersten vorgeschlagenen abweichenden Befehl eines freien Schiffs, ob die gelernte Route erlaubt wird. Als Ziele dienten die Ausgänge echter, auf denselben Karten, Sitzen und Gegnern paarweise verglichener Fortsetzungen. Für jeden Sitz stammt die hier bewertete Vorhersage von einem Modell, das seine Karte beim Trainieren nicht gesehen hatte. Die 640 Sitz-Gegner-Vergleiche dieser Studie sind **Entwicklungsdaten**.

| Freigabe des Suchwegs | Zusätzlicher Nutzen je Sitz | Erster Reliktfund, Züge früher | Gegen Solution | Direkt gegen V16 |
|---|---:|---:|---:|---:|
| Ursprüngliche Route immer zulassen | −0,054 | +1,24 | 308/320 | 151/320 |
| Aus öffentlichen Angaben auswählen | +0,090 | +0,56 | 308/320 | 163/320 |
| Zusätzlich die Bewertungen der beiden V16-Netze verwenden | +0,045 | +0,43 | 307/320 | 162/320 |

Original-V16 gewann gegen Solution 308/320 und im seitenausgeglichenen ursprünglichen Selbstvergleich 160/320. Die interne Zuversicht der Netze lieferte weder gegenüber dem einfacheren Bewerter einen Zusatznutzen noch erhielten sich alle externen Siege. Dieser Kandidat verfehlte zwei der vier Zulassungsbedingungen. Der vollständige technische Vergleich hatte zuvor bei erzwungener Freigabe und erzwungenem Verzicht auf beiden Sitzen gegen beide Gegner sämtliche Befehle über 303 Züge reproduziert. Die einfacher gehaltene Vergleichsversion erhält eine neu vorab festgelegte Untersuchung auf unabhängigen Karten. [Vorhersagen und Intervalle](ergebnis.json) · [Echte Fortsetzungen](lernspiele.jsonl.gz) · [Prüfbedingungen der neuen Studie](../kontextsuche/PLAN.md)
