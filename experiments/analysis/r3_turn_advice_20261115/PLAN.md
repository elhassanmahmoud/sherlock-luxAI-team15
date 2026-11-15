# Richtungswechsel unterhalb der bisherigen R3-Schwelle

Der ursprüngliche R3 mit einer Ansicht ersetzt V14s endgültigen Bewegungsbefehl ab 70 % maskierter Softmax-Konfidenz. Der bisherige Kontextselektor nimmt in manchen Situationen bereits angenommene Vorschläge zurück. Frühere Deckungs- und Konsensversuche nutzen ebenfalls die ursprüngliche 70-%-Grenze. Die 50-%-Grenze im früheren Kampfmodus betrifft die Wahl eines Schussziels. Im geprüften Studienbestand fand sich kein Versuch mit der folgenden einzelnen Ausnahme.

**Fester Eingriff vor der ersten Inferenz.** Bei mindestens 50 % und weniger als 70 % darf der ursprüngliche R3 (`99b07775…`) seine beste zulässige Aktion übernehmen, wenn er und V14 unterschiedliche Bewegungsrichtungen 1–4 wählen. Ein bereits finalisierter V14-Befehl wird nach seiner tatsächlichen Richtung verglichen. Für R3 zählt die beste Klasse unter der regulären Maske einschließlich des Schussplatzes. V14s Halten, R3s Halten und alle Schüsse bleiben im Zusatzbereich unberührt. Ab 70 % gilt der vollständige bisherige Mechanismus und unter 50 % V14. Konfidenz ist der Ausgabewert des Netzes, keine geschätzte Siegchance. Kein Nachtraining, keine weitere Schwelle oder Kartenauswahl.

Die 24 alten Diagnosekarten 7272200–7272223 und 24 R3-On-Policy-Karten 7287100–7287123 werden je auf beiden Sitzen nachgerechnet. Jeder Satz umfasst acht verschiedene Karten pro Gegner (Solution, Kaggle, V14). Alle 96 Sitzarchive, Datenprotokolle und die publizierten 70-%-Kontrollen sind über SHA-256 gebunden. Beide Verfahren sehen exakt dieselben komprimierten Einheitsstellungen. Der ursprüngliche R3 muss seine bekannten genauen Treffer und die von ihm verschlechterten richtigen V14-Aktionen je Sitz reproduzieren. Auf R3-On-Policy-Stellungen werden auch seine tatsächlich ausgeführten Aktionen und die bekannten 164 Rekonstruktionsabweichungen separat geprüft. In den Roharchiven wurden bereits vor neuer Netzberechnung alle 496.267 (alt) und 527.141 (neu) durch die jeweilige Maske erlaubten Bewegungsvorschläge auf Energie, Kartengrenzen und bekannte Asteroiden geprüft. In beiden Sätzen waren alle ausführbar.

**Vorab festgelegte Auswertung.** Gezählt werden tatsächlich zusätzlich ausgegebene Bewegungen, neu mit dem Lehrer übereinstimmende und vorher richtige, jetzt verlorene Endklassen sowie übrige geänderte Befehle. Gegenübergestellt werden die Aktionsklassen auf derselben gespeicherten Stellung. Schussziele werden durch die Regel nicht angefasst. Für jeden Sitz, jede Karte, jeden Gegner und jeden Satz werden die paarweisen Unterschiede ausgewiesen. Der Haupteffekt ist der Saldo neu richtiger minus verlorener früher richtiger Befehle pro 100 **aller** Einheitsentscheidungen des betreffenden Satzes. Pro Satz 10.000 Ziehungen mit Zurücklegen aus seinen 24 ganzen Karten, PCG64/2711, 2,5- und 97,5-%-Quantile. Beide Sitze und deren Zeilengewichte bleiben in jedem gezogenen Kartenblock zusammen. Ebenso werden die Intervalle für jeden Gegner aus dessen acht Karten angegeben.

Die untere 95-%-Grenze muss in **beiden** Sätzen strikt positiv sein. Zusätzlich muss der Saldo in **jeder** der drei Gegnergruppen der neuen R3-Sammlung mindestens null erreichen. Sind alle Bedingungen erfüllt, kommt ein gesondert registrierter kurzer Spielvergleich in Betracht. Andernfalls endet dieser Versuch. Die Archive lassen keine Folgerung über eine tatsächliche Siegquote zu.

```bash
M=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15
"$M/.venv/bin/python" -B -u -m scripts.r3_turn_advice_audit \
  --model "$M/experiments/candidates/movement_dagger_20261115/r3_soft.pth" \
  --old "$M/experiments/imitation/final_20261115_movement_dagger" \
  --new "$M/experiments/imitation/final_20261115_r3_context" \
  --out "$M/experiments/analysis/r3_turn_advice_20261115/validation.json"
```
