"""Compare the live selector with the independently reconstructed joint plans."""
from collections import defaultdict
import gzip
import json
from pathlib import Path

from feldplan import select

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "r3_field_20261116/diagnose/roh"
expected = defaultdict(list)
events = json.loads((HERE / "replays/gelegenheiten.json").read_bytes())["events"]
for event in events:
    if event["combined"]:
        key = event["seed"], event["side"], event["match"], event["turn"]
        expected[key].append((event["uid"], tuple(event["target"])))

frames = 0
handoffs = 0
for path in sorted(RAW.glob("blend-*.json.gz")):
    game = json.loads(gzip.decompress(path.read_bytes()))
    for f in game["frames"]:
        match, turn = divmod(f["step"], 101)
        if not 1 <= turn <= 99:
            continue
        key = game["seed"], game["seat"], match + 1, turn
        got = select([(u, (x, y), e) for u, x, y, e in f["own"]],
                     {(x, y) for _, x, y, _ in f["visible"]}, set(map(tuple, f["confirmed"])),
                     set(map(tuple, f["known_asteroids"])), game["move_cost"], (24, 24),
                     f["r3_orders"], f["v15_orders"])
        if got != expected.pop(key, []):
            raise ValueError(f"Different joint plan at {key}")
        frames += 1
        handoffs += len(got)
if expected or frames != 1485 or handoffs != 79:
    raise ValueError("Incomplete replay comparison")
print(f"{frames} common states, {handoffs} matching unit handoffs")
