# Gemeinsamer Spielvergleich auf 7170230–7170245

Der Runner akzeptiert ausschließlich die vor den Spielausführungen geprüfte Archiventscheidung mit SHA-256 `65ad72a84559634ab1284ac33a65886bd3ae6c4b775f3ba7cb98c20424877998`. Er summiert die 96 Sitzarchive erneut, vergleicht die Summen mit dem Bericht und überprüft die Dateien, Quellen und Modelle beider ursprünglicher Studien. Die Kernquellen für V14, R3 und die Gegner stammen aus den geprüften Spielkopien. Der Ausführungsmodus, die 70-%-Schwelle und die V14-Schüsse sind für beide Ansichten identisch. Nach den ursprünglichen Plänen werden alle 16 Karten von beiden Sitzen gespielt.

| Rolle | Gegner und Anzahl | Herkunft |
|---|---|---|
| V14, Einzelansicht-R3, Einzelansicht-Midpoint | Je 32 Kaggle und 32 Solution | Drei externe Arme aus dem registrierten Einzelansicht-Versuch, hier nur gelesen |
| Diagonal-R3 | 32 Kaggle, 32 Solution | Verifizierte vollständige Kontrolle desselben Panels wiederverwenden, sonst einmal erzeugen |
| Zwei-Ansichten-Midpoint | 32 Kaggle, 32 Solution, 32 direkt gegen V14 | Zwei eigene Arme |

Beim Bereitstellen war keiner der drei externen Einzelansicht-Arme abgeschlossen oder begonnen. Die 192 zugehörigen Spiele laufen unter der Zuständigkeit des Einzelansicht-Versuchs. Dessen direkte Midpoint-Spiele sind für diesen Vergleich nicht erforderlich. Der neue Runner erteilt ausschließlich Aufträge für maximal 160 Spiele; sein Statusbefehl meldet fehlende, teilweise gespeicherte und vollständige Arme. Den neuen Spielverzeichnissen sind eigene Hash-Manifeste zugeordnet. Ein teilweise vorhandener externer Diagonal-R3-Kontrolllauf wird zuerst mit seinem ursprünglichen Runner vervollständigt. Bereits vollständige native Kontrollläufe werden anhand der Originalquellen, Umgebung, Netzdatei und 303 Spielschritten pro Partie geprüft. Die gepaarten Veränderungen verwenden ganze Karten für die Bootstrap-Intervalle.

Vom eingefrorenen **Spielverzeichnis** aus, mit `PROJECT` als Hauptcheckout und `OUT` als eigenem Verzeichnis für die neue Studie:

```sh
"$PROJECT/.venv/bin/python" -B -m scripts.r8_midpoint_diagonal_games status --repo "$PROJECT" --out "$OUT"
"$PROJECT/.venv/bin/python" -B -m scripts.r8_midpoint_diagonal_games check --repo "$PROJECT" --out "$OUT"
"$PROJECT/.venv/bin/python" -B -u -m scripts.r8_midpoint_diagonal_games play --repo "$PROJECT" --out "$OUT"
"$PROJECT/.venv/bin/python" -B -m scripts.r8_midpoint_diagonal_games assess --repo "$PROJECT" --out "$OUT"
```

Einzelne neue Arme lassen sich über `play --arm diagonal`, `dual_external` oder `dual_direct` starten. Pro Aufruf rechnet ein Worker. Über `--singles` kann der ursprüngliche Ergebnisordner angegeben werden, über `--diagonal-control` eine in anderer Ablage gemessene Kontrolle. Das Verfahren setzt die eingereichte Audit-Quelle unter `offline/` voraus (alternativ `--fit-root`). Die Spielkopie basiert auf der [Single-Midpoint-Anleitung](../r8_midpoint_20261115/SPIELVERGLEICH.md), ergänzt um die veröffentlichten Originaldateien `scripts/r3_diagonal.py` und `scripts/r3_diagonal_games.py`, den neuen Aktor und diesen Runner. Die nachgerechnete Entscheidung für die Auswahl steht in `screen/assessment.json`; eine unabhängige Bestätigung wäre gesondert zu registrieren.
