# Bewegungsschüler auf eigenen Spielstellungen

Der erste Bewegungsberater spielte 288 zusätzliche vollständige Partien. Für jede Einheit wurden getrennt V14s ursprünglicher Befehl, der ausgeführte Befehl und der Befehl des beobachtenden Kaggle-Lehrers gespeichert. Dessen Gedächtnis erhielt den ausgeführten Befehl. Die 120 Lernkarten und 24 Diagnosekarten wurden jeweils auf beiden Seiten gegen einen von drei rotierenden Gegnern gespielt. Jeder Gegner ist in jedem Teil gleich häufig vertreten.

| Gemessene Einheitsentscheidungen | Training | Zurückgehaltene Karten |
|---|---:|---:|
| Spiele | 240 | 48 |
| Entscheidungen auf diesen Stellungen | 787.631 | 156.243 |
| Bewegung durch den ersten Schüler geändert | 85.689 | 18.377 |
| Dabei einen zusätzlichen Lehrerzug getroffen | 59.430 | 12.165 |
| Dabei eine ursprüngliche Lehrerübereinstimmung verloren | 16.628 | 3.926 |
| Für den Zusatzverlust nutzbare Lehrerbewertungen | 656.134 | 129.521 |
| Davon mit mindestens zwei legalen Bewegungen | 631.325 | 126.001 |
| Davon mit mindestens 10 % Gewicht auf der zweitbesten Bewegung bei Temperatur 2 | 515.442 | 102.653 |

Alle 288 Archivprüfsummen, Kartenidentitäten, Sitzplätze und Gegner sind im [Datenbericht](corpus.json) aufgeführt. Der Vergleich der ursprünglichen mit den ausgeführten Befehlen fand keine geänderte Schussentscheidung und kein geändertes Schussziel. Gegenüber dem Lehrer gewann der erste Berater auf seinen 24 Diagnosekarten netto 8.239 Übereinstimmungen mit Bewegungsbefehlen. Das misst sein Verhalten auf diesen konkreten Stellungen. Die Stärke eines neu trainierten Beraters wird auf anderen Karten gemessen.

## Nachrechnung und Training

Auf Moayeds Rechner liegen die Rohdaten im Hauptcheckout unter `experiments/imitation/final_20261115_movement_dagger`. Im separaten Studiencheckout lässt sich der [Zähler](summarize_corpus.py) mit dem Pfad zu diesen Archiven ausführen. Der folgende Aufruf verwendet eine neue Ausgabedatei.

```sh
python experiments/analysis/movement_dagger_20261115/summarize_corpus.py \
  experiments/imitation/final_20261115_movement_dagger --out /tmp/sherlock-korpusvergleich.json
```

Für die ursprüngliche Sammlung lief die Fassung `0105658` von `scripts.selective_dagger collect` mit `--raw-teacher`. Der Elterncheckpoint ist der [erste Bewegungsberater](../../candidates/selective_advice_20261115/movement.pth). [Sammlungsprotokoll und Quellprüfsummen](collection_protocol.json) und [Kartenaufteilung und Einsatzbedingungen](../../../docs/superpowers/plans/2026-11-15-bewegung-dagger.md) binden die Daten an diesen Stand.

Der Refit verwendet zusätzlich 32 ursprüngliche V14-Lernkarten und acht V14-Diagnosekarten. Das ergibt 989.063 Lernzeilen, davon 958.870 ausführbare Lehrerbefehle, sowie 207.291 getrennte Diagnosezeilen. Nur die 152 Lernkarten liefern Gradienten.

## Fertiger Refit mit harten Lehrerbefehlen

Die fünf Epochen sind abgeschlossen. Auf den acht ursprünglichen zurückgehaltenen Karten traf R2 68,72 % der Aktionsklassen und 67,64 % der vollständigen Befehle. Der erste Schüler erreichte dort 62,4 % und 61,2 %. Auf den 24 neuen zurückgehaltenen Karten traf R2 68,90 % der Aktionsklassen und 68,11 % der vollständigen Befehle. Bei einem Schuss zählt der vollständige Befehl nur, wenn auch das Zielfeld stimmt. Die [Trainingsausgabe](r2_train.log) enthält alle Epochen und die Nenner.

Der [R2-Checkpoint](../../candidates/movement_dagger_20261115/r2.pth) wiegt rund 693 KiB (SHA-256 `23fa6208d76e81940916388b9ee56c1d290693e8febfa53622442b64b0d33f96`). Im Spiel ergänzt er V14 ausschließlich als Bewegungsberater hinter dessen Entscheidung. Er wird über `scripts.final_battle_compare --candidate selective_movement --model <R2-Checkpoint>` geladen. Der eigenständige v3-Schüler von Mahmoud verwendet andere Daten und einen anderen Einsatzweg.
