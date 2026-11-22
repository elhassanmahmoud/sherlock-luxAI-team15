# Wann schlägt R3 Solution auf einem Sitz, auf dem V16 verliert?

Stand 22. November 2026. Archivvergleich für die Entwicklung. Jede Zeile der Rohdaten beschreibt ein komplettes Spiel aus drei Matches. Ein Sitz bezeichnet dieselbe Karte (Seed) und dieselbe Spielerposition für beide Agenten gegen Solution_92.

| Archivprüfung | Sitze je Agent | Beide gewinnen | Nur V16 gewinnt | Nur R3 gewinnt | Beide verlieren | V16 gesamt | R3 gesamt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Bestätigung 3 | 800 | 777 | 10 | 10 | 3 | 787 | 787 |
| Bestätigung 5 | 800 | 768 | 10 | 21 | 1 | 778 | 789 |

Trotz gleicher Gesamtzahl in Prüfung 3 haben die Agenten auf 20 Sitzen unterschiedliche Ergebnisse. Prüfung 5 enthält 21 Fälle, in denen R3 einen V16-Verlust gegen Solution vermeidet. Auf zehn anderen Sitzen passiert das Umgekehrte. Ein pauschaler Wechsel auf R3 würde auch diese zehn Siege kosten.

**Ansatz für die Replay-Sichtung.** Auf allen 31 Sitzen, die nur R3 gewinnt, holt V16 genau eines von drei Matches. R3 holt auf 22 dieser Sitze alle drei und auf neun Sitzen zwei Matches. Für einen fairen Vergleich stehen daneben die 20 Sitze, die nur V16 gewinnt. Die CSV enthält pro Agent die Anzahl gewonnener Matches sowie eigene und gegnerische Punkte. Die Verlustursache und der früheste entscheidende Zug erfordern Spielverläufe. Alle aufgeführten Sitze sind nach ihrem bekannten Ergebnis ausgewählt und gelten ab jetzt als Entwicklungsfälle. Eine neue Variante braucht einen Vergleich auf anderen Karten sowie ein direktes Duell mit V16.

## Quellen und Reproduktion

- Prüfung 3, Seeds 7261000–7261399, beide Spielerpositionen. [V16](../../devf_20261117/bestaetigung3_kandidat.csv) und [R3](../../devf_20261117/bestaetigung3_r3.csv)
- Prüfung 5, Seeds 7267000–7267399, beide Spielerpositionen. [V16](../../devh_20261117/bestaetigung5_k.csv) und [R3](../../devh_20261117/bestaetigung5_r3.csv)
- [Sitze mit unterschiedlichen Siegern](unterschiedliche_sitze.csv) und [Zählungen einschließlich Matchverteilung](ergebnis.json)

Aus dem Projektverzeichnis:

```sh
dir=experiments/analysis/v16_finalwoche_20261122/solution
out=$(mktemp -d)
python3 "$dir/sitzvergleich.py" --out "$out"
cmp "$out/ergebnis.json" "$dir/ergebnis.json"
cmp "$out/unterschiedliche_sitze.csv" "$dir/unterschiedliche_sitze.csv"
```

Das Werkzeug prüft die SHA-256-Prüfsummen der vier Archivdateien. Für Solution erwartet es in jeder Datei exakt 400 festgelegte Seeds mit beiden Sitzen, 303 Schritte je Spiel und Punktezählung der Version 2. Es kontrolliert die drei Matchausgänge pro Spiel und vergleicht deren Mehrheit mit dem ausgewiesenen Spielsieger.
