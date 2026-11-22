"""Druckt vorab definierte Fälle mit umgekippten Einzelmatches als Häufigkeitentabelle."""
from collections import Counter
import json
from pathlib import Path

games = json.loads(Path(__file__).with_name("daten.json").read_text())["arms"]
for group in ("r3_only", "v16_only"):
    for arm, other in (("v16", "r3"), ("r3", "v16")):
        winner = int((group == "r3_only") == (arm == "r3"))
        totals = [Counter() for _ in range(3)]
        for own, rival in zip(games[arm], games[other], strict=True):
            if (own["seed"], own["side"], own["group"]) != (rival["seed"], rival["side"], rival["group"]):
                raise ValueError("Ungepaarte Spiele")
            if own["group"] != group:
                continue
            for i, (x, y) in enumerate(zip(own["win"], rival["win"], strict=True)):
                if x == winner and x != y:
                    for dest, block in zip(totals, own["match_blocks"][i], strict=True):
                        dest.update(block)
        for phase, counts in zip(("1–30", "31–50", "51–70", "1–70"), [*totals, sum(totals, Counter())], strict=True):
            print(group, arm, phase, json.dumps(dict(sorted(counts.items())), ensure_ascii=False))
