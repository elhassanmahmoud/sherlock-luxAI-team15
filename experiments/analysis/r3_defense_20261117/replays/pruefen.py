"""Verify all serialized scoring transitions, commands, matches and source benchmarks."""
import gzip
from hashlib import sha256
import json
from pathlib import Path
import struct

from aufnehmen import HERE, UNIT, BLEND, originals, spiele


def verify():
    _, originals_by_seat = originals(spiele.ROOT)
    cases = json.loads((UNIT / "archiv.json").read_bytes())["vs_v15"]["lost"]
    bench = {(r["seed"], r["seat"]): r for r in map(json.loads, (UNIT/"archiv/games.jsonl").read_bytes().splitlines())}
    hashes = json.loads((HERE / "roh/sha256.json").read_bytes())
    if set(hashes) != {f"{arm}-{s}-{p}.json.gz" for s,p in cases for arm in ("v15", "unit", "r3")}:
        raise ValueError("Missing or unexpected games")
    historical = 0
    for name, h in sorted(hashes.items()):
        raw = (HERE / "roh" / name).read_bytes()
        if sha256(raw).hexdigest() != h:
            raise ValueError(name)
        data = json.loads(gzip.decompress(raw))
        arm, seed, side = data["arm"], data["seed"], data["seat"]
        if name != f"{arm}-{seed}-{side}.json.gz":
            raise ValueError("Wrong name")
        other = "player_" + str(1-int(side[-1]))
        commands = {side:sha256(), other:sha256()}
        frames = data["frames"]
        archived = BLEND / "diagnose/roh" / name
        if archived.exists():
            old = json.loads(gzip.decompress(archived.read_bytes()))
            if not all(all(f[key] == frame[key] for key in f)
                       for f,frame in zip(old["frames"], frames, strict=True)):
                raise ValueError("Historical frame differs")
            historical += 1
        for n, f in enumerate(frames):
            if f["step"] != n:
                raise ValueError("Nonmonotonic step")
            for side_ix, coords in enumerate(f["scored_fields"]):
                if len(set(map(tuple, coords))) != len(coords) or len(coords) != f["after"][side_ix] - f["before"][side_ix]:
                    raise ValueError("Point award mismatch")
            for who, col in ((side, "own_orders"), (other, "opp_orders")):
                commands[who].update(struct.pack("<48q", *(v for command in f[col] for v in command)))
        if len(frames) != 303 or data["command_sha256"] != {s:h.hexdigest() for s,h in commands.items()}:
            raise ValueError("Truncated command stream")
        row = data["actual"]
        matches = [frames[t]["after"] for t in (100,201,302)]
        if [sum(x[i] for x in matches) for i in (0,1)] != [row["our_points"],row["opp_points"]]:
            raise ValueError("Total points mismatch")
        if frames[-1]["next_wins"] != [row["our_wins"],row["opp_wins"]]:
            raise ValueError("Match wins mismatch")
        if arm == "unit":
            if bench[seed,side] != row:
                raise ValueError("Unit benchmark mismatch")
        elif [row[k] for k in spiele.GAME] != originals_by_seat[arm][seed,side]:
            raise ValueError("Original benchmark mismatch")
    print(f"{len(hashes)} full games, {303*len(hashes)} scoring transitions, {historical} archived public traces verified")


if __name__ == "__main__":
    verify()
