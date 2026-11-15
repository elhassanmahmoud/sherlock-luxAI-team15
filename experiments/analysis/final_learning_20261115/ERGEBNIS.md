# Scout-Energie verbessert den Spielevergleich nicht

Stand 15. November. Acht Lernkarten auf beiden Seiten gegen den nativen Kaggle-Gegner lieferten 1.025 randomisierte Entscheidungen, darunter 140 mit Tod bzw. verlorenem Einheitenslot. Ein lineares Modell schätzte die Energieänderung nach vier Zügen. Vier weitere Karten auf beiden Seiten lieferten 530 zufällig ausgeführte Aktionen für die Diagnose. Modell und Zufallsdaten liegen zusammen mit ihrer Herkunft in diesem Ordner.

Bei 392 der 530 Gelegenheiten hätte das Modell eine andere Bewegung als V14 gewählt. Davon wurden im Zufallsversuch 82-mal der Modellvorschlag, 97-mal der Originalzug von V14 und 213-mal eine dritte Aktion tatsächlich gespielt. Der modellgestützte Vergleich schätzt über die vier Karten einen mittleren Vorteil von 8,70 Energieeinheiten pro Gelegenheit. Die vier Kartenmittel sind −0,57, +24,88, +9,63 und +0,86. Das ist eine kurzfristige Schätzung auf vier Karten, keine Messung zweier gleichzeitig möglicher Züge derselben Einheit.

Auf zwölf frischen Karten, jeweils beide Seiten, gewinnt der gelernte Kandidat gegen Kaggle 2/24 Spiele und gegen Solution_92 23/24. V14 gewinnt 2/24 bzw. 24/24. Damit ist die vorab definierte Auswahlbedingung für diesen Kandidaten verfehlt. V14 bleibt die Abgabe. Der gemessene Energievorteil hat hier keinen Zuwachs an ganzen Siegen ergeben.

[Festlegung](PROTOKOLL.md) · [Modell](model.json) · [Diagnose](diagnosis.json) · [Ganze Spiele](../finale_20261115/selection/learned/games.jsonl) · [V14 auf denselben Karten](../finale_20261115/selection/v14/games.jsonl).
