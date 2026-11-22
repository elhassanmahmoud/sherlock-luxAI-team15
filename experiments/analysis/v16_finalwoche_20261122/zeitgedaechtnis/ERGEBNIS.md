# Frühere Beobachtungen verbessern die Wahrscheinlichkeiten, aber nicht die gewählte Aktion

Zwei gleich große Zusatznetze lernten auf 530.487 Lehrerentscheidungen. Ein Netz erhielt die augenblickliche Lage. Das andere sah außerdem, wie sich 21 Merkmale des Schiffs seit einem, zwei, vier und acht Zügen verändert hatten. Geprüft wurde auf 24 eigens gesammelten neuen V16-Partien, die beim Training und bei der vorangegangenen Netzgewichtung nicht verwendet wurden.

| Modell | Richtige Aktionen / 80.621 | Richtige Aktionen bei Netzuneinigkeit / 7.449 | Kreuzentropie |
|---|---:|---:|---:|
| Original V16 | 68.035 | 3.673 | 0,4999 |
| Zusatznetz mit aktuellem Zustand | 67.958 | 3.636 | 0,4806 |
| Zusatznetz mit Historie | 67.944 | 3.658 | 0,4731 |

Die Historie senkte den mittleren logarithmischen Vorhersagefehler. Beim tatsächlich an erster Stelle stehenden Befehl fehlten jedoch 91 Treffer gegenüber dem Original und 14 gegenüber der Kontrolle mit nur dem aktuellen Zustand. Im Spiel fällt die Auswahl anhand dieser Rangfolge. Die zuvor festgelegten Bedingungen für ganze Vergleichsspiele wurden verfehlt. Das Ergebnis betrifft diese Ausgestaltung und Trainingsdaten. [Prüfung nach Spiel](offline.json) · [Trainingsdaten und Modell-Hashes](trainiert.json) · [Versuchsplan](PLAN.md)
