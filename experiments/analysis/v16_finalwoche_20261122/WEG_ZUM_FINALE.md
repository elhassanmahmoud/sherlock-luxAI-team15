# Sherlock bis zum Finale am 27. November

**Stand am Sonntag, 22. November.** Die Referenz für alle weiteren Vergleiche ist der [freigegebene V16](../../releases/20261117_sherlock_v16/README.md). Mahmoud hat R3 mit zwei durch Nachahmung und sechs DAgger-Runden trainierten CNNs abgelöst. Die Modelle bewerten jede Einheit aus Sherlocks eigener Beobachtung. Als Lehrer und schwerer Prüfgegner diente der öffentliche Kaggle-Drittplatzierte. Gegen andere Kursteams gibt es vor dem Turnier keine gemessene Siegquote.

| Bisher belegter Vergleich | V16 | R3 |
|---|---:|---:|
| Lösung des Kurses, Bestätigung 3 | 787/800 | 787/800 |
| Lösung des Kurses, Bestätigung 5 | 778/800 | 789/800 |
| Kaggle, ganze Spiele in Bestätigung 3 | 20/800 | 10/800 |
| Kaggle, einzelne Matches in Bestätigung 3 | 216/2.400 | 76/2.400 |
| V16 gegen R3, 100 Karten mit Seitentausch | 194/200 | 6/200 |

Die getrennten [Ergebnisse der dritten Bestätigung](../devf_20261117/BESTAETIGUNG3_ERGEBNIS.md) und [die Ergebnisse der fünften Prüfung](../devh_20261117/ERGEBNIS.md) zeigen, weshalb wir Solution und das direkte Duell getrennt beurteilen. Mahmoud hat eine weitere DAgger-Runde, ein drittes Netz und zusätzliche Handregeln bereits getestet. Alle Regeln gemeinsam fielen gegen Kaggle von 24 auf 7 Siege in 400 Entwicklungsspielen.

## Sonntag · Aus den Niederlagen lernen

Auf acht nachgespielten Karten erreichten V16 und Kaggle bis Zug 70 im Mittel 6,46 bzw. 6,83 Punktefelder pro Match. In den letzten 20 Zügen punkteten sie auf diesen früher erreichten Feldern in 38,1 % bzw. 65,2 % der möglichen Feldzüge. Das lässt noch offen, ob Sherlock seine Einheit verliert, freiwillig wegzieht oder nachher keinen Ersatz dorthin schickt. Der [Replaybericht](FELDVERLAUF.md) enthält die Zahlen je Karte und die Kontrolle gegen die acht Originalergebnisse.

Im [Solution-Vergleich](solution/ERGEBNIS.md) sind 31 frühere R3-Siege, die V16 verliert, und 20 Fälle mit umgekehrtem Ausgang als Entwicklungsmaterial markiert. Bei der [gepaarten Replayprüfung](solution/REPLAYS.md) fiel ein anderer Engpass auf. In sieben von acht verlorenen Einzelmatches auf vier ausgewählten Starts lag V16 bei Zug 70 schon zurück. In den letzten zwanzig Zügen holte es insgesamt 179 Punkte auf. Gegen Solution steht daher die Frage im Vordergrund, ob V16 Punktefelder zu spät entdeckt oder bereits bekannte Felder zu spät erreicht.

Der [erste Lernversuch](lernversuch/PLAN.md) trainierte nur die Aktionsausgabe des kleineren V16-Netzes. Beide Trainingsvarianten erhielten dieselben Lehrerbeispiele und Rechenschritte. In einer Variante zählten späte Entscheidungen auf oder neben einem früher besetzten, inzwischen erkannten Punktefeld dreifach. Beide Varianten wählten auf den vier zurückgehaltenen Karten in 622 von 738 solchen Situationen die Lehreraktion. Zwischen den beiden Varianten änderte sich in diesen 738 Situationen kein einziges Aktionsmaximum. Die Zusatzgewichtung verfehlte ihren vorab festgelegten Spieltest. Für die gewöhnliche Trainingsvariante wurde nach dieser Sichtung eine getrennte Prüfung auf neuen Karten vorgesehen.

## Montag bis Mittwoch · Wovon die nächste Entscheidung abhängt

- **Montag, 23.11.** Folien und beide ZIP-Varianten mit der neuen Kursansage abgleichen, wenn sie vorliegt. Für die Folien ist Montag der bisherige Planungstermin. Die [Generalprobe](../../../docs/presentation/finale_2711/GENERALPROBE_2711.md) läuft schon mit der präsentierbaren V16-Fassung.
- **Bei einem positiven Lern- und Spieltest** denselben Kandidaten auf einem vorab festgelegten, vorher unbenutzten Kartensatz bestätigen. Beide Startseiten je Karte, unveränderte Gegner, Direktduell gegen die freigegebene ZIP. Ganze Spiele gegen Solution sind das Maß für das 100-%-Ziel. Beim deutlich stärkeren Kaggle-Gegner zusätzlich Matchsiege und Punkteanteil ausweisen. Die Unsicherheit paarweise nach Karte berechnen. Schwellen und Karten vor dem ersten Bestätigungsspiel in der Studienakte festhalten.
- **Bei einem negativen Test** zuerst in den Replays auflösen, was nach dem Verlust eines Felds passiert. Eine erreichbare freie Wertungsposition mit verfügbarer Ersatzeinheit erfordert eine andere Entscheidung als ein Feld unter Beschuss, zu dem keine überlebensfähige Einheit gelangen kann. Nur Stellungen mit beobachtbarem Handlungsspielraum taugen für eine gezielte Änderung. Die bekannten Verlustkarten dürfen anschließend keine unabhängige Bestätigung mehr liefern.
- **Mittwoch, 25.11.** Als internen Entscheidungstermin einplanen. Die gesicherte V16-Abgabe bleibt verfügbar. Einen nachweislich besseren Kandidaten vor einem gemeinsamen Release im Kursrunner prüfen und archivieren. Für die Folien kommen ausschließlich nachvollziehbar bestätigte Zahlen infrage. Die verbindliche Moodle-Frist hat Vorrang.

Die [Finalfolien](../../../Sherlock_Finale_27-11-2026.pdf) zeigen einen tatsächlich gespielten Zug aus dem veröffentlichten V16. Wenn sich bis zum Turnier kein Kandidat durchsetzt, sind sie fachlich unabhängig von den laufenden Versuchen einsetzbar.
