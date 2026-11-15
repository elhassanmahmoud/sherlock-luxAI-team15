# Unabhängige Prüfung der Richtungswechsel

Startvoraussetzung ist die vollständige, erneut geprüfte positive [Vorauswahl](games/screen/assessment.json). Fest stehen der ursprüngliche R3, sein zusätzliches Fenster 0,50 ≤ Konfidenz < 0,70 und die unveränderten Originalgegner. Die ersten vorgeschlagenen Kartennummern 7170500–7170539 und 7170600–7170639 sind schon für die [Kontaktstudie](../r3_v4_contact_20261115/BESTAETIGUNGSPLAN.md) registriert. Die folgenden Blöcke schließen an deren exklusive Obergrenzen an.

| Ausführung | Neue Karten | Gegner und Sitze | Spiele |
|---|---|---|---:|
| Richtungswechsel | 7170560–7170599 | Solution und Kaggle, jeweils beide Sitze | 160 |
| V14-Kontrolle | dieselben 40 externen Karten | Solution und Kaggle, jeweils beide Sitze | 160 |
| Ursprünglicher R3 | dieselben 40 externen Karten | ausschließlich Solution, beide Sitze | 80 |
| Richtungswechsel direkt gegen V14 | 7170660–7170699 | beide Sitze | 80 |

Alle fünf primären Bedingungen gelten gemeinsam. Gegen Solution muss der Kandidat mindestens V14s Anzahl ganzer Siege erreichen. Die untere Grenze des gepaarten 95-%-Intervalls der gepoolten externen Siegquotendifferenz muss strikt über null liegen. Die untere 95-%-Grenze der direkten Siegquote gegen V14 muss strikt über 50 % liegen. Auf beiden Sitzen müssen tatsächlich zusätzliche Richtungswechsel ausgeführt worden sein. Der Originalmechanismus zählt sie nach physischer Ausführung, der Runner speichert den Zähler für jede einzelne Kandidatenpartie einschließlich null. Agentenfehler, fehlende Sitze, veränderte Quellen oder unvollständige Spiele erlauben keine Auswertung.

Wie viele Siege sind speziell der neuen Richtungsregel zuzuschreiben? Dazu wird der Kandidat auf den 80 identischen Solution-Sitzen mit dem ursprünglichen R3 verglichen. Die Formulierung „gegen Solution nachgewiesen besser als der ursprüngliche R3“ setzt eine strikt positive untere Grenze dieses gesonderten, kartengepaarten 95-%-Intervalls voraus. Das Ergebnis beeinflusst die primäre Prüfung gegen V14 nicht. Wir berichten die einzelnen externen Gegner, die Siege, gewechselten Ausgänge und die zusätzlichen Befehle je Sitz. Für alle Intervalle werden 10.000-mal ganze Karten gezogen, PCG64/2711. Die beiden Sitze bleiben zusammen, extern zusätzlich die beiden Gegner. Eine Erfolgsserie ist keine Garantie für perfekte Ergebnisse auf allen Karten. Eine Veröffentlichung als Kursagent bedürfte der gesonderten Prüfung und Sicherung.

```bash
M=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15
"$M/.venv/bin/python" -B -m scripts.r3_turn_advice_confirm check --repo "$M"
"$M/.venv/bin/python" -B -u -m scripts.r3_turn_advice_confirm play --repo "$M"
"$M/.venv/bin/python" -B -m scripts.r3_turn_advice_confirm assess --repo "$M"
```

`--arm turn_external`, `--arm v14_external`, `--arm r3_solution` und `--arm direct` sind einzeln ausführbar. Jeder Arm sperrt sein Ergebnisverzeichnis. Unterbrechungen setzen mit den übrigen Sitzen desselben Arms fort. Erst alle vier vollständigen Arme erlauben den Abschlussbericht.
