# Rank-Mean-Runner: enger Abschluss

09.11.2026. Neu geschrieben ausschließlich `scripts/rank_mean_eval.py`, `scripts/rank_mean_owner.py`, `tests/test_rank_mean_screen.py`. Ausgangspunkt ist der abgeschlossene Motion-Runner. Kein Commit, keine Gewichts-/Produktionsänderung, kein Modellload, Spiel oder Training.

Profil/Karten/Factory auf `rank_mean_screen_20261109`, Panel9944000–9944019, Direkt9944100–9944119 und `RankMeanAgent(rank_enabled=...)` umgestellt. Die SAP-spezifische Rekonstruktion ist entfernt. Owner ausschließlich zwei Modulnamen geändert; Startaufnahme, Quellen-/Gewichtsbindung, Quota, Batterieoption, STOP, Ownership, Cleanup, feste Spielzahl, Ganzkartenbootstrap und Gates bleiben erhalten.

Passive Hooks liegen nur an den36 Originalnetzen der jeweiligen Agentinstanz und ON zusätzlich am Aggregatmodul. Sie kopieren echte Inputs/Outputs, prüfen den frischen Cache mit Reihenfolge/Featurepräfixen/Masken und genau einen Forward je Mitglied. Der originale `_act` wird instanzlokal nur gezählt, finaler Befehl gegen Rückgabe und originales Remember geprüft; kein Klassenpatch und kein zweiter Forward. Bei direkten Duellen wird auch die OFF-Gegnerinstanz passiv geprüft. Hooks und Instanzmethoden werden im Finally wiederhergestellt.

ON-Rangmittel werden unabhängig in NumPy rekonstruiert: ganzzahlige Midrankzähler, vektorisierte Vergleiche über alle36Mitglieder, einmalige Division. Das erhält echte Gleichstände. OFF validiert Inputs/Qs/Masken ohne ungenutzte Rangrechnung. Der Rohmittelvergleich berücksichtigt mögliche Float32-Reduktionsunterschiede; der tatsächliche rohe Torch-Mittelwert liefert den Baseline-Argmax, nicht ein neu gerundeter NumPy-Wert. Geprüft werden Aggregatausgabe, Agentdiagnose und kumulative Vorschlagszähler.

Technik protokolliert alle303Frames einschließlich36Member-Qs/Features. OFF muss historische native Befehle, Aktionshash, Siege, Matchdaten und v2-Punkte exakt reproduzieren. ON benötigt sowohl geänderte legale Vorschläge als auch mindestens eine native Streamabweichung gegenüber den zugehörigen historischen Partien. Diese Abweichung ist nach Trajektoriendivergenz kein Frame-für-Frame-Kausalbeleg. Performance speichert geänderte Vorschlagsframes kompakt mit IDs/Masken/Mittelwerten/Greedies/nativeFinal; sämtliche36Outputs werden trotzdem live geprüft. Neue Rowfelder heißen `aggregation` und `observed_proposal_changed_steps`. Exposition behauptet keine durch Regeln erhaltene Endaktionsänderung.

## Tatsächliche synthetische Prüfung

Arbeitsverzeichnis: `/Users/moayedshawesh/.codex/worktrees/sherlock-student-20261104/sherlock-luxAI-team15`.

```sh
env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_rank_mean_screen.py > /tmp/rank-mean-runner/GREEN-final.log 2>&1
```

- `RED.log`: erste21gezielteFälle gegen unveränderte Motion-Ausgangskopie,21FAIL/0,25s/Exit1.
- `GREEN-first.log`: ersteUmsetzung21PASS/0,16s/Exit0.
- `GREEN.log`: zusätzliche echte Mock-Hook-/Restaurierungs-/Remember-Durchläufe,24PASS/0,16s/Exit0.
- `RED-off.log`: gleicherAufruf mit `-k off_never`, vor Root-Effizienzkorrektur1FAIL/24deselected/0,05s/Exit1.
- `GREEN-final.log`: finale25gezielteTestsPASS/0,23s/Exit0.

Dies sind ursprüngliche umgeleitete Prozessausgaben. Keine alte Gesamtsuite wiederholt. Netze/Factory sind synthetisch gemockt; kein Torch-Modell konstruiert oder Tensorcheckpoint geladen. Echte Vier-Spiel-Integration und Startaufnahme bleiben offen.

## Finale SHA-256

| Datei | SHA-256 |
|---|---|
| scripts/rank_mean_eval.py | 8e8a75463384f18cbffc6024f0c5ecfed1f45bd72cc3d21c4d6513754af2fc81 |
| scripts/rank_mean_owner.py | 422f11b5fac1c1d16b683233542ed787e34b1b4a3252959e979bb037fc555ff0 |
| tests/test_rank_mean_screen.py | d28c60a7c7174384f88d65984962a79a1431923bf1328f98d500c3c1b1cff777 |
| GREEN-final.log | eff1947526856f8bfddb482b89fa4241343423f342153b65eb0d1294f8609223 |

Root-CLI bleibt strukturell gleich, jetzt `python -B -m scripts.rank_mean_owner technical|performance --admission ABSOLUTER_PFAD --admission-sha SHA256 --usage-file ABSOLUTER_USAGE_PFAD`. Kein automatischer Phasenwechsel oder Wiederholungsstart. Analyse separat über `scripts.rank_mean_eval analyze` mit den bisherigen Aufnahme-/Owner-State-Argumenten.
