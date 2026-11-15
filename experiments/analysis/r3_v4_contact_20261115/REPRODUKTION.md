# Reproduktion der Kontaktstudie

Das Ausführungsverzeichnis enthält den unveränderten Agenten-, Skript- und Lux-Paketstand von b2bd67e, dessen zwei Schülergewichte, die V14-Gewichte, die native Kaggle-Installation sowie die in PLAN.md genannten Dev-A-Ergebnisse. Die neuen Skripte liegen zusätzlich dort. `REPO` bezeichnet die lokale Git-Datenbank mit den beiden festgelegten Commits, `OUT` einen separaten Ausgabeordner, `PY` den Interpreter der Kursumgebung. Im Ausführungsverzeichnis einmal die privaten Importe des historischen R3 erzeugen:

```sh
"$PY" -B -m scripts.r3_v4_parent_source --repo "$REPO"
```

Jede Phase hat einen eigenen Start. Der Prüfer liest nur fertige Spielzeilen. Sein Bericht kann außerhalb der drei Rohdatenordner abgelegt werden.

```sh
"$PY" -B -u -m scripts.r3_v4_contact_study sentinel --repo "$REPO" --out "$OUT"
"$PY" -B -m scripts.r3_v4_contact_assess sentinel --repo "$REPO" --out "$OUT"
"$PY" -B -u -m scripts.r3_v4_contact_study diagnosis --repo "$REPO" --out "$OUT"
"$PY" -B -m scripts.r3_v4_contact_assess diagnosis --repo "$REPO" --out "$OUT"
```

Nur bei einem bestandenen Diagnoseergebnis den separaten Lauf `screen` mit denselben Argumenten starten und anschließend über `r3_v4_contact_assess screen` prüfen. Die Quellen-, Gewichts- und Umgebungsbindungen müssen zwischen Spielerhebung und Prüfung gleich sein. Lokal erzeugte Daten dürfen beim Weitergeben über ihre SHA-256-Prüfsummen an den Bericht gebunden werden.
