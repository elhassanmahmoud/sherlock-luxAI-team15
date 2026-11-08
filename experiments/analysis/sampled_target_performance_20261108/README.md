# Fester Folgeaktions-Leistungsvergleich

**Fester Vergleich tatsächlich gestartet; noch kein vollständiges Leistungsresultat.**

Studienkopie: `sherlock-student-20261104/sherlock-luxAI-team15`, Quelle/HEAD `153d2af974d7fa4ce1a9dbc318b1cb2dade5be2b`, Laufzustand `performance_v1/state.json`. Nicht duplizieren oder während des laufenden Vergleichs Quellen/Gewichte ändern. Vier finale Einzelnetze, zwei feste Trainingsstarts. Je Rolle40 Spiele gegen Solution92 und40 gegen sol92_sq, plus je40 direkte Spiele Sampled gegen seine passende Kontrolle: **400 insgesamt**,20 Karten pro separater Panel-/Direktliste und beide Seiten.

[Trainingsabnahme](../sampled_target_20261108/TRAININGSERGEBNIS.md), [tatsächliche Werkzeugprüfung](../sampled_target_20261108/operations/task4-integration.md), [fester Jobplan](plans/jobs.json), [Inferenzkopien](../../candidates/sampled_target_20261108/admission.json).

Alle vier Netze verwenden identische Inferenzkonfigurationen. Keine einseitigen Overrides im Direktduell. Gewertet wird Sieg +0,5×Remis, strikte Siege separat. Das vorab festgelegte Methodensignal verlangt beide positiven Panelkontraste, mittleren Gewinn≥5 Prozentpunkte und direkte Scores je≥50 %, zusammen>50 %. Ergebnisse und Unsicherheit für beide Starts vollständig berichten; kein Nachschlag oder V14-Ersatz aus diesem Pilot.

Der vollständige historische Aufnahmeweg benötigt zusätzlich die lokal erhaltenen Replay-NPZs; [Dateiindex](../sampled_target_20261108/operations/local-replay-files.json). Git allein enthält diese großen Puffer nicht.
