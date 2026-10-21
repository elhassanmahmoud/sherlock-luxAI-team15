"""Schwere Trainingskarten aus der Kartensuche (vorab festgelegt, Plan 2026-10-21-hard-map-training):
Karte zaehlt als schwer, wenn V3 gegen Solution_92 mindestens eine Seite verliert (result < 1).

    python3 experiments/analysis/hard_map_training_20261021/select_hard.py
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent / "compare" / "regeln" / "H21_screen_v3_360000.csv"

res = defaultdict(list)
for r in csv.DictReader(open(SRC, newline="")):
    if r["opponent"] == "solution92":
        res[int(r["seed"])].append(float(r["result"]))
assert len(res) == 2000 and all(len(v) == 2 for v in res.values()), "Kartensuche unvollstaendig"
hard = sorted(s for s, v in res.items() if min(v) < 1.0)
games = sum(len(v) for v in res.values())
wins = sum(sum(v) for v in res.values())
summary = dict(source=str(SRC.relative_to(HERE.parent.parent.parent)), maps=len(res), games=games,
               v3_result_mean=round(wins / games, 4), hard_maps=len(hard),
               both_lost=sum(1 for v in res.values() if max(v) < 1.0),
               rule="V3 verliert mindestens eine Seite (result < 1)")
(HERE / "hard_seeds.json").write_text(json.dumps(hard))
(HERE / "screen_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
