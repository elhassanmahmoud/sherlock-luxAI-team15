# Vorauswahl für zusätzliche Richtungswechsel

Das archivierte [Ergebnis](validation.json) bestand alle Bedingungen des [Versuchsplans](PLAN.md). Für die Vollspiele bleibt exakt der dabei geprüfte R3 mit einer Ansicht und dem zusätzlichen Richtungswechsel im Bereich 0,50 ≤ Konfidenz < 0,70 im Einsatz. Die Netzdatei bleibt das ursprüngliche R3-Einzelnetz.

Vor dem ersten Spiel festgelegt sind 16 bereits bekannte Entwicklungskarten 7170230–7170245 und beide Sitze. Der Kandidat spielt 32 Spiele gegen Solution, 32 gegen den ursprünglichen Kaggle-Gegner und 32 direkt gegen V14. Die bereits vollständigen 64 externen Spiele des originalen R3 und 64 von V14 im [Einzelansicht-Midpoint-Vergleich](../r8_midpoint_20261115/VORAUSWAHL.md) werden unverändert wiederverwendet. Jede Referenzzeile, ihr Quellstand, die Gewichte, Engine und beide Quellenmanifeste werden vor der Übernahme geprüft.

Alle Bedingungen gelten gemeinsam. Der Kandidat muss gegen Solution mindestens ebenso häufig gewinnen wie R3, extern mehr als R3 und wenigstens zwei Spiele mehr als V14 gewinnen, direkt wenigstens 17/32 gewinnen und auf beiden Sitzen tatsächlich zusätzliche Richtungen ausgeführt haben. Jede vollständige Ergebniszeile muss den ganzzahligen Zähler dieser neu ausgeführten Befehle enthalten, auch bei null. Abgewiesene Befehle zählen nicht. Agentenfehler oder unvollständige Partien sind ungültig. Wir zeigen Unterschiede und 95-%-Intervalle je Gegner und gemeinsam über beide Gegner. Je 10.000 Bootstrapziehungen ganzer Karten, beide Sitze gemeinsam, PCG64/2711. Die Zahl der Eingriffe wird je Sitz und Gegner dokumentiert.

Die Referenzergebnisse und Karten waren bei Festlegung bekannt. Eine erfolgreiche Vorauswahl kann daher nur einen später separat festzulegenden Vergleich auf unbenutzten Karten anstoßen. Dieser Lauf löst keine Bestätigung aus.

```bash
M=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15
"$M/.venv/bin/python" -B -m scripts.r3_turn_advice_games check --repo "$M"
"$M/.venv/bin/python" -B -u -m scripts.r3_turn_advice_games play --repo "$M"
"$M/.venv/bin/python" -B -m scripts.r3_turn_advice_games assess --repo "$M"
```

`play --arm external` und `play --arm direct` erlauben je einen getrennten Einsatz der vorhandenen Rechenplätze. Das Ergebnis liegt unter `games/screen/assessment.json` in diesem Studienordner.
