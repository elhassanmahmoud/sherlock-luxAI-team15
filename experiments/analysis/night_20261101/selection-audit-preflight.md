# Vorbereitete unabhängige Auswahldaten-Abnahme

**Bereitgestellt, noch nicht ausgeführt.** Während der laufenden Auswahl wurden ausschließlich die vorregistrierte Phasendatei, der Freeze, die vorhandenen Statistik-/Runnerquellen und der Nachtplan gelesen. Keine Ergebnis-CSV oder Auswahlergebnisse gelesen, keine Zwischenwahl, keine Tests wiederholt, keine Spiele, Modellimporte oder Supervisoren gestartet. Keine Worktree-Datei verändert.

Prüfer: `/tmp/sherlock-night-20261101/selection-independent-audit.py`.

Der Prüfer importiert nur Standardbibliothek und NumPy. Er verwendet keine Statistikfunktion aus dem Repository, kein pandas, Torch oder LuxAI. Sein einziger Unterprozess liest den Git-HEAD. Alle Berichte bleiben außerhalb des eingefrorenen Worktrees.

## Fest gepinnte Grundlage

- Worktree `/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics`, HEAD `aa0660183cace1e21285fde30ae61e3812136f05`.
- Auswahldatei SHA256 `54c8f8593396fc5ef035c48cd1e2f2899f660a969c2d6bd33f60c453a3b5212c`.
- Freeze-Datei SHA256 `96385f7398bcc531d6983ab7d127df200b74fb4ca54599a8b4ad6e64e51d61ab`.
- Genau sieben Jobs: baseline, overlap, overlap_direct, control, control_direct, discovery, discovery_direct. A/B/C-Reihenfolge bleibt fest.
- Genau 50 Karten831000–831049, beide Seiten, lokales Sechserpanel Solution/Quadrat/V3/V7/V10/V13 plus default. Direktjobs ausschließlich gegen die eingefrorene V14-Referenz.
- Genau3100 Spiele: baseline700, jeder der drei Kandidaten700+100direkt. Keine beliebige Teilmenge akzeptiert.

## Prüfweg bei späterer Ausführung

1. Vor dem ersten Zugriff auf Ergebnis-CSVs: Journal muss `status=complete` aufweisen, alle sieben Jobs mit Exit0 und Ausgabehash enthalten; Phasen-/Freeze-Hashes und Originalphase müssen zur unabhängigen Vorabbindung passen.
2. Exaktes Panel, A/B/C-Reihenfolge, Karten, Gegner und vollständige Job-Commands gegen eine eigene wörtliche Soll-Rezeptur prüfen. Die Rezeptur bindet auch Gewichts- und Ausgabepfade, workers2 und das Fehlen zusätzlicher Overrides. Eingebettete und originale Phase müssen identisch sein.
3. Alle eingefrorenen Quellen, Interpreter, Modellinput-Dateien und Zulassungsbelege gegen ihre Hashes prüfen. Start nach Zulassung und Phasenende vor der Deadline bestätigen.
4. Ausgabehash, vollständiges CSV-Schema, alle erwarteten eindeutigen (seed,side,opponent)-Schlüssel,303Steps/v2, endliche Werte und Ergebnis-/Punktkohärenz aller3100Spiele prüfen. Erst danach Kennzahlen berechnen.
5. Aus den expliziten Schlüsseln selbst dreidimensionale Karten-/Gegner-/Seitenmatrizen aufbauen. Für jedes Gegnerdelta beide Seiten einer Karte gemeinsam mitteln; für Paneldelta zusätzlich alle sechs Gegner derselben Karte gemeinsam mitteln. Remis=0,5.
6. 5000 Resamples ganzer Karten, NumPy-RNG0,2,5/97,5Perzentile. Kein doppelter Bootstrap, keine Zeilen-Pseudoreplikation und kein Mitteln fertiger Gegnerintervalle.
7. Auswahlgates selbst prüfen: Paneldelta≥0,5pp, Solutiondelta≥0, default≥99%, direkt≥50%, Toleranz1e-9. Höchstes Paneldelta; Gleichstand A vor B vor C. Ergebnisse bleiben Auswahl, `promotion_qualified=false`.
8. Optional offiziellen vollständigen Bericht abgleichen: CSV-Hashes, alle Einzelkennzahlen/Intervalle, absolute Siege/Remis/Niederlagen, Gates, Nominee und3100Spiele. Zahlenvergleich mit absoluter Toleranz1e-12; boolesche Gates/Nominee exakt.

## Aufruf erst nach Roots Ende-Meldung

```sh
/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B \
  /tmp/sherlock-night-20261101/selection-independent-audit.py \
  --out /tmp/sherlock-night-20261101/selection-independent-audit.json \
  --compare-summary /Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics/experiments/analysis/night_20261101/selection_summary.json
```

Ohne `--compare-summary` kann der unabhängige Bericht vor der offiziellen Rechnung erstellt werden. Teilphasen führen vor Kennzahlenberechnung zum Abbruch. Der Prüfer überschreibt keine vorhandene Berichtdatei und führt weder neue Messungen noch eine Abgabeübernahme aus.

Die Implementierung wurde jetzt nur erstellt und gelesen, nicht ausgeführt. Ihre tatsächliche Anwendung samt Ergebnis erfolgt nach vollständiger Auswahl und Roots Freigabe; bis dahin gibt es keine Nominierung aus diesem Audit.
