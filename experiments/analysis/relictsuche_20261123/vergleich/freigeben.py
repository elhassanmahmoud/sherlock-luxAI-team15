"""Record the explicit code and weight digests supplied by the candidate owner before playing."""
import argparse
from pathlib import Path
import re

from spielen import SCRATCH, common_source, inputs, require, sha, stamp, write_once


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--id", required=True)
    p.add_argument("--file", nargs=2, action="append", required=True, metavar=("PATH", "SHA256"),
                   help="First file is the candidate module, followed by every extra input")
    p.add_argument("--work", type=Path, default=SCRATCH)
    a = p.parse_args()
    require(a.id != "reference" and re.fullmatch("[a-z][a-z0-9_-]*", a.id), "Invalid candidate id")
    paths = []
    for location, expected in a.file:
        path = Path(location).resolve(strict=True)
        require(sha(path) == expected and re.fullmatch("[0-9a-f]{64}", expected), f"Rejected candidate input: {path.name}")
        paths.append(path)
    common = common_source()
    source = {"common": stamp(common), "id": a.id, "candidate": inputs(paths[0], paths[1:])}
    write_once(a.work / "common.json", common)
    write_once(a.work / "sources" / (a.id + ".json"), source)
    print(f"Released {a.id}, {len(paths)} independently checked input hashes, identity {stamp(source)}")
