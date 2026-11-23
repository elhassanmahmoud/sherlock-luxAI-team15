"""Describe the scout's outcome changes by direction of the first sight or point on disjoint maps."""
from collections import Counter
import gzip
import json
from pathlib import Path

from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha, write_once


HERE = Path(__file__).resolve().parent
PANELS = (
    ("ortundflotte/duelle_karten.jsonl.gz", "reference", "scout", 48),
    ("abschlusspruefung/partien.jsonl.gz", "v16", "ortundflotte", 38),
    ("kundschafter_feldwissen/duelle_partien.jsonl.gz", "v16", "joint", 32),
    ("sicht1_wiederholung/partien.jsonl.gz", "v16", "ortundflotte", 96),
)


def load(panel, original, candidate):
    found = {}
    with gzip.open(HERE.parent / panel, "rt") as stream:
        for row in map(json.loads, stream):
            if "key" in row:
                seed, seat, arm, opponent = row["key"]
            else:
                seed, seat = row["seed"], row["team"]
                arm, opponent = row.get("arm", row.get("id")), row["opponent"]
            if opponent != "solution92" or arm not in (original, candidate) or row.get("sensor", 1) != 1:
                continue
            key = (seed, seat, arm)
            assert key not in found
            assert int(sum(m["win"] for m in row["matches"]) >= 2) == row["win"]
            found[key] = row
    return found


def main():
    counts = Counter()
    seen = set()
    sources = {}
    for panel, original, candidate, size in PANELS:
        rows = load(panel, original, candidate)
        maps = {s for s, _, _ in rows}
        assert len(rows) == 4 * size and len(maps) == size and seen.isdisjoint(maps)
        seen.update(maps)
        sources[panel] = sha(HERE.parent / panel)
        for s in maps:
            for seat in (0, 1):
                base, scout = rows[s, seat, original], rows[s, seat, candidate]
                outcome = {0: "same", 1: "rescued", -1: "lost"}[scout["win"] - base["win"]]
                for indicator in ("sight", "credit"):
                    shift = base[indicator] - scout[indicator]
                    when = "earlier" if shift > 0 else "later" if shift < 0 else "same"
                    counts[indicator, when, outcome] += 1
    table = {indicator: {when: {outcome: counts[indicator, when, outcome] for outcome in ("rescued", "same", "lost")}
                         for when in ("earlier", "same", "later")} for indicator in ("sight", "credit")}
    assert len(seen) == 214 and sum(counts.values()) == 2 * 2 * len(seen)
    write_once(HERE / "zeit_und_siege.json", dict(sources=sources, cards=len(seen), seats=2*len(seen), table=table))


if __name__ == "__main__":
    main()
