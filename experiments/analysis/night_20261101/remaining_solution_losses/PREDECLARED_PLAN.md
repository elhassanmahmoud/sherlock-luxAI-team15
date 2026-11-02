# Kleiner Diagnoseablauf für verbleibende Solution-Niederlagen

**Nur Vorschlag, noch nichts gestartet.** Erst nach vollständig abgeschlossener Bestätigung, Entscheidung und Abgabe-/Paketprüfung; Root muss separat freigeben. Nur beginnen, wenn der gesamte Ablauf vor 05:00 Berlin mit Schlussreserve sicher passt. Keine neue Kandidatenwahl, kein Tuning, keine Gaußstudie, keine Produktionsänderung und keine frischen Karten.

## Ein Ablauf: dieselben Verlustschlüssel zweimal komplementär vermessen

Die anschließend tatsächlich beibehaltene Abgabe bestimmt **ein einziges** Gewichts-/CSV-Paar:

| Endstand | Unveränderte Quellgewichte `DIAG_W` | Bereits vollständige Eingabe `DIAG_GAMES` |
|---|---|---|
| CONTROL qualifiziert und übernommen | `experiments/ensembles/night_20261101_control.pth` | `experiments/analysis/night_20261101/selection_control.csv` |
| V14 bleibt | `experiments/releases/20261101_v14_baseline/agent_p0.pth` | `experiments/analysis/night_20261101/selection_baseline.csv` |

Das ist keine erneute Auswahl zwischen den beiden Versionen. Nur die nach der regulären Entscheidung gültige Version wird diagnostiziert. Vor Start Hash-/Configzuordnung zur endgültigen Abgabe prüfen; kein Zugriff auf Bestätigungszwischenstände für diese Planung.

Die vorhandene `select_games`-Logik filtert `opponent=solution92`, `result<0.5`, nimmt die vorhandene CSV-Reihenfolge und begrenzt auf acht konkrete **(Seed,Seite)**-Spiele. Beide Werkzeuge verwenden exakt dieselbe Auswahl. Maximal 8+8=**16 vollständige Spiele**, keine zusätzlichen Gegenseiten oder Kontrollkarten.

Aus den jetzt bereits abgeschlossenen Auswahl-CSVs nachgezählt: CONTROL hat fünf solche Spiele, V14 sechs. Der tatsächliche Ablauf umfasst daher aktuell **10 oder 12 Nachspiele**. Sämtliche Seeds liegen im verbrauchten Auswahlblock 831000–831049; es gibt keine neue Reservierung und keine Aussage über repräsentative Verlusthäufigkeiten.

## Vorhandene Befehle, erst nach Freigabe

Aus `sherlock-v10-mechanics` ausführen. `DIAG_W`/`DIAG_GAMES` genau einmal gemäß Endstand oben setzen, keine `--set`-Verhaltensänderungen. `DIAG_DIR` muss ein neuer Diagnoseausgabeordner sein; bestehende Ausgaben keinesfalls überschreiben. Ein Worker, die zwei Schritte nacheinander:

```sh
DIAG_PY=/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python
DIAG_DIR=experiments/analysis/night_20261101/remaining_solution_losses

"$DIAG_PY" -B -m scripts.par_losses \
  --weights "$DIAG_W" --games "$DIAG_GAMES" \
  --opponent solution92 --which lost --limit 8 --workers 1 \
  --out "$DIAG_DIR/matches.csv"

"$DIAG_PY" -B -m scripts.mechanism_probe \
  --weights "$DIAG_W" --games "$DIAG_GAMES" \
  --opponent solution92 --which lost --limit 8 --workers 1 \
  --out "$DIAG_DIR/mechanisms.json"
```

`par_losses` erzeugt je Spiel drei Matches × zwei Teams, `mechanism_probe` je Spiel drei Matchobjekte mit `us`/`opp`. Vor Start Zahl/Schlüssel der gefilterten Eingabe und erwartete 6N CSV-Zeilen/3N Matchobjekte festhalten. Quellen, Gewichte, Gegner und Eingabe-CSV hashen; nachher erneut prüfen. Endsiege aus beiden Nachspielen müssen zu den ursprünglichen CSV-Schlüsseln/Ergebnissen passen. Bei Nichtreproduktion oder unvollständigem Ablauf keine nachträgliche Umdeutung als neue Leistungsbewertung.

## Konkrete Befundfelder und vorsichtige Zuordnung

Nach `(seed,side,match)` verbinden und für jedes verlorene Match eine kurze Zeile ausgeben:

| Möglicher Engpass | Vorhandene Felder / Befund |
|---|---|
| Anfang zu spät / später Zusammenbruch | `won_match`, eigene/gegnerische `points`, `first_score_step`, `occ_mean`, `occ_mean_late` aus `matches.csv`. `first_score_step=-1` bedeutet nie, 101 den letzten Zählschritt; kein Nullwert-Sentinel erfinden. |
| Relic noch unbekannt | `unknown_own_relic_unseen`, relativ zu `true_pt_own`; hohe unbekannte eigene Punktefeld-Schritte ohne bekanntes Relic sprechen für fehlende Erkundungsinformation. |
| Bekannte Zone nicht erschlossen | `unknown_own_relic_known`, `cls_to_cand_own`, `cls_explore`; trennt die Informationslücke um bekannte Relics vom unbekannten Relic. Das sind aufsummierte Feld-/Unit-Schritte, keine Anzahl verschiedener Felder. |
| Wissen vorhanden, Besetzung fehlt | `belief_known`/`belief_correct`, `occ_own_half`, `free_pt_own`, `untargeted_free_pt_own`, `cls_to_pt_own`, `cls_to_pt_enemy`, `dist_to_pt_*`, `cls_no_target`; Endwissen allein beweist keine frühzeitige Kenntnis. |
| Halter gehen im Kampf verloren | `deaths_on_pt`, `deaths_energy`, `deaths_collision`, `pt_unit_steps_lowE`, `sap_dmg_direct_dealt`, `sap_dmg_adj_dealt`, `void_dealt`, `sap_paid`, `field_gain` jeweils us/opp. Zeigt Begleitbilanz; keine universelle kausale Schuldzuweisung. |
| Redundante Belegung | `pt_stacked_unit_steps`, `productive`, `pt_unit_steps`; auf Unit-/Punktfeld-Schritte normieren, nicht als rohe Matchwerte verschiedener Spieldauern vergleichen. |

Abschluss maximal eine kleine Tabelle der verlorenen Matches und drei Sätze: dominanter beobachteter Engpass, Gegenbeispiele/Unsicherheiten, Erkenntnis für die spätere Erklärung. **Keinen neuen Regelschalter daraus ableiten oder ausprobieren.**

## Warum genau diese Werkzeuge

`scripts/par_losses.py` übernimmt im Gegensatz zu den einfachen `analyze_losses`-/`analyze_timing`-CLIs exakte Verlustschlüssel einschließlich Seite und Limit. Es nutzt bereits `analyze_losses.play_and_measure`. `mechanism_probe` akzeptiert dieselbe `--games/--which/--limit`-Schnittstelle und ergänzt die oben benötigte Trennung unbekanntes Relic / ungeklärte Zone / Besetzung / Kampf. Ein zusätzlicher `analyze_timing`-Lauf würde neue vollständige Nachspiele verbrauchen, weil dessen CLI nur einen zusammenhängenden Seedbereich jeweils auf beiden Seiten kennt; er gehört daher nicht zu diesem kleinen Ablauf.

Die Agenten erhalten ausschließlich öffentliche Beobachtungen/Parameter und handeln regulär mit train=False. Die Wahrheit wird in beiden Werkzeugen nur nachgelagert für Messung/Rekonstruktion verwendet; sie wird nicht in den Agentenbelief eingespeist. `mechanism_probe` liest zusätzliche Engineparameter nur in seine getrennte Ereignissimulation. Deren Schaden-/Todeszuschreibungen sind eine Rekonstruktion, kein zusätzlicher unabhängig validierter Kausalnachweis. Keine Wahrheit für Training oder Produktionsregeln verwenden.

Heute tatsächlich ausgeführt: Quelltexte gelesen und die bereits abgeschlossenen Auswahl-CSVs per Standardbibliothek gezählt. **Keine Bestätigungsdaten, Modelle, Spiele, Tests oder Quelländerungen.**
