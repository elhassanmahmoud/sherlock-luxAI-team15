# Artillerie: Trainings- und Spielregel offline vergleichen

Vor der tatsächlichen Auswertung festgelegt. Die Fog-Studien sind geschlossen; ihre Ergebnisse werden nicht nachgetestet. V14 und die ZIP bleiben unverändert.

## Fragestellung

`_artillery_ok` berücksichtigt `art_splash` nur außerhalb des Trainings, auch wenn `rules_in_training_all=True` ist. Der Codeunterschied ist bekannt; seine konkrete Exposition ist noch nicht gemessen. Ein Unterschied ist noch kein Beleg für eine schlechtere Entscheidung oder Spielstärke.

## Vorab geänderter Umfang

Ursprünglich waren zwei bekannte Referenzspiele mit einem beobachtenden Wrapper vorgesehen. Noch vor einer Ausführung zeigte die unabhängige Prüfung, dass die archivierten Targeting-Spuren die nötigen öffentlichen Eingaben und historischen Helper-Rückgaben bereits enthalten. Deshalb **null neue Spiele**, keine Modelle laden oder trainieren, keine erneute Engine-Reproduktion behaupten.

Genau diese beiden vorhandenen Dateien verwenden:

- `experiments/analysis/continuation_20261102/targeting/831006_player_1.jsonl.gz`
- `experiments/analysis/continuation_20261102/targeting/831043_player_0.jsonl.gz`

Keine weiteren Spuren bei Nullbefund. Der gespeicherte Trainings-/Inferenzunterschied wird deskriptiv untersucht; keine Kandidatenauswahl anhand dieser bekannten Fälle.

## Methode und Prüfungen

1. Herkunft und Prüfsummen der Spuren, aufgezeichnete Konfiguration sowie historischen und aktuellen Helper-Code abgleichen. Unterschiede oder fehlende Eingaben offen benennen und bei einer unauflösbaren Voraussetzung abbrechen.
2. Für jeden tatsächlich aufgezeichneten `_artillery_ok`-Aufruf öffentlichen Kontext und Argumente rekonstruieren. Unit-Position, Energie und Ziel gegen die gespeicherten Argumente prüfen. Keine Schätzung fehlender Estimator-Zustände.
3. Nur die aktuelle Trainingsvariante des identischen Helpers auf einem isolierten Minimalobjekt auswerten. `training=True` überspringt den Estimator. Die ursprüngliche Evaluationsantwort stammt aus dem Archiv; sie wird ohne gespeicherten Streufaktor-Posterior ausdrücklich nicht neu berechnet.
4. Konfiguration, Kontext und Belief-Punktekarte vor/nach dem Aufruf unverändert prüfen; temporäre Zustände auch bei Fehlern restaurieren. Ein Fehler führt zum Abbruch, nicht zu einem geratenen Ergebnis. Gezielte Prüfungen für Rückgabe/Restaurierung und Fehlerpfad sowie unabhängiger Code-/Methodenreview vor realer Auswertung.
5. Ereigniszahl, eindeutige Spiel-/Schritt-/Einheit-Kombinationen und die vier Kombinationen historisches Eval-/rekonstruiertes Trainingsverdikt ausgeben. Rechenquelle und Input-Hashes binden, Ausgaben in einem neuen Verzeichnis ablegen, keine historischen Dateien überschreiben.

## Aussagegrenzen und Fortsetzung

Die Spuren sind historisch ausgewählt und korreliert. Helper-Unterschiede bedeuten weder andere endgültige Aktionen noch eine bessere Aktion: aufrufende Bedingungen und nachgelagerte Regeln gelten weiterhin. Keine Siege, Rewards oder Lernwirkung aus dieser Diagnose ableiten. Erst ein relevanter Unterschied rechtfertigt einen getrennten, optionalen Trainingsvergleich; noch keine Produktions- oder Trainingsänderung in diesem Schritt. Keine starke allgemeine Aussage aus einem Nullbefund.

Bestehende Quoten- und Prozessregeln beachten. Resets übernimmt ausschließlich Moayed. Diese kleine Offline-Prüfung startet keine Hintergrundtrainings und benötigt keine neuen Karten.
