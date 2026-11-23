"""Bind the complete discovery candidate list before opening any outcome file."""
import argparse
import json

from spielen import HERE, SCRATCH, common_source, require, stamp, write_once

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ids", nargs="+", help="All preregistered candidate ids, once their source files are frozen")
    args = p.parse_args()
    ids = sorted(args.ids)
    require(ids and len(ids) == len(set(ids)) and "reference" not in ids, "Invalid discovery candidate list")
    roster = {}
    for name in ids:
        source = json.loads((SCRATCH / "sources" / (name + ".json")).read_text())
        require(source["common"] == stamp(common_source()) and source["id"] == name, "Source registration mismatch")
        roster[name] = stamp(source)
    write_once(HERE / "kandidaten.json", roster)
    print(f"Registered {len(ids)} locked candidate sources")
