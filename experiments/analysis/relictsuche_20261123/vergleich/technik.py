"""Publish independently checkable historical run controls without reading the new series."""
import json

from auswerten import save_archive
from spielen import HIST, HERE, SCRATCH, common_source, require, sha, stamp, validate, write_once

if __name__ == "__main__":
    source = json.loads((SCRATCH / "sources/reference.json").read_text())
    require(source["common"] == stamp(common_source()), "Technical sources changed")
    cards = json.loads((HERE / "karten.json").read_text())["technical"]
    rows = []
    for s in cards:
        for t in (0, 1):
            k = ("technical", s, t, "reference", "solution92")
            r = json.loads((SCRATCH / "technical/reference" / f"{s}_{t}_solution92.json").read_text())
            validate(r, k, stamp(source))
            rows.append(r)
    dest = HERE / "technik"
    dest.mkdir(exist_ok=True)
    archive = dest / "partien.jsonl.gz"
    require(save_archive(rows, archive) == rows, "Technical archive failed readback")
    write_once(dest / "pruefung.json", {"historical_seeds": cards, "games": len(rows), "turns": sum(r["steps"] for r in rows),
               "matching_opening_values": len(rows) * 5, "both_policies_clean": True,
               "historical": {p.name: sha(p) for p in (HIST / "teil_0.jsonl", HIST / "teil_1.jsonl")},
               "archive_sha256": sha(archive), "common": common_source(), "source": source})
    print(f"{len(rows)} verified historical games, {len(rows)*5} opening controls match.")
