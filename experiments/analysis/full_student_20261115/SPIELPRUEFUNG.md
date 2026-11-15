# Prüfung der trainierten Vollschüler

Der Vergleich verwendet die beiden Checkpoints der fünften Epoche und die vom Trainer eingefrorene Datei `corpus.json`. Jeder Arm speichert im Checkpoint die genaue Zahl der Diagnosezeilen und den ungerundeten Quotienten aus vollständig richtigen Befehlen und Zeilen. Das Prüfwerkzeug rekonstruiert daraus die ganzzahlige Trefferzahl und prüft, dass ihre Division exakt denselben Quotienten ergibt. Beim Schuss zählen nur der richtige Aktionstyp und das exakte legale Zielfeld zusammen als Treffer. Unausführbare Lehrerbefehle bleiben im gemeinsamen Nenner. Beide Arme müssen dieselben Zeilen und dieselben legalen Schusslabels bewertet haben.

Die Kontrolle heißt `historical`, der zusätzlich auf Lehrerpartien trainierte Kandidat `plus_teacher`. Die 24 eigenen Diagnosekarten erlauben Gleichstand. Auf den 24 Lehrerkarten muss der Kandidat mehr vollständige Befehle treffen. Die älteren acht Diagnosekarten werden ausgewiesen. Das Werkzeug prüft den Kartensplit, die beiden Modellidentitäten, die Herkunft der Trainingsquellen und die Einstellungen beider Arme. Die Prognosen müssen für diese Entscheidung nicht nochmals berechnet werden.

Nach dem Training im selben Versionsstand im Repository-Stamm ausführen. `P` bezeichnet das Studienverzeichnis, `M` den Ordner der zwei trainierten Checkpoints und `PY` den Python-Interpreter des Projekts. Für die Spielserien eine feste Arbeitskopie mit denselben Agent- und Gegnerquellen benutzen.

```bash
A=(--corpus "$P/corpus.json" --models "$M" --out "$P/evaluation")
"$PY" -m scripts.full_student_gate "${A[@]}" offline
```

`evaluation/offline.json` enthält pro Kohorte beide Ganzzahlzähler, die gemeinsamen Zeilen und Schusszahlen sowie beide Checkpoint-Prüfsummen. Nach bestandener Offline-Prüfung die drei Auswahlserien starten. Zusammen ergeben sich 224 vollständige Spiele. Alle Arme spielen auf beiden Seiten derselben 16 Karten gegen Solution und den nativen Kaggle-Agenten. Nur der Kandidat spielt zusätzlich direkt gegen V14. Unter Ressourcenbegrenzung seriell mit jeweils einem Worker ausführen.

```bash
for arm in v14 historical plus_teacher; do
  "$PY" -m scripts.full_student_gate "${A[@]}" play screen "$arm" || exit 1
done
"$PY" -m scripts.full_student_gate "${A[@]}" assess screen
```

Für `screen/assessment.json` werden die vollständigen Spielzeilen, beidseitigen Kartenpaare, Endstände und Quellenprüfsummen überprüft. Der Vergleich mit der historischen Kontrolle zählt als vierte Bedingung. Bei bestandener Auswahl folgen die im [Plan](PLAN.md) festgelegten unabhängigen Karten. Jede neue Serie verlangt wieder die tatsächlich bestandene Auswahl.

```bash
"$PY" -m scripts.full_student_gate "${A[@]}" play confirm v14 &&
"$PY" -m scripts.full_student_gate "${A[@]}" play confirm plus_teacher &&
"$PY" -m scripts.full_student_gate "${A[@]}" play direct plus_teacher &&
"$PY" -m scripts.full_student_gate "${A[@]}" assess confirm
```

Die Gegenüberstellung in `confirm/assessment.json` umfasst 600 Ausführungen. Pro Bootstrap-Ziehung bleiben die beiden Sitze und extern auch beide Gegner einer Karte zusammen. Die Ergebnisse beschreiben Spielstärke auf diesen Karten. Vor einem Austausch der Abgabe gelten zusätzlich die im Plan genannten technischen Prüfungen. [Auswahl, Bootstrap und Provenienz](../../../scripts/full_student_gate.py).
