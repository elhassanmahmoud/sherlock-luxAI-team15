"""Complete the three missing original Feldprobe controls on the existing V16 head-to-head seats."""
import gzip
from hashlib import sha256
import json
import os

import numpy as np
from ganzspiel import HERE, check, course, game, identity
from scripts.experiment import limit_threads


KEYS = [(163500055, 1), (163500081, 0), (163500081, 1)]


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv

    limit_threads()
    check(os.getenv("PYTHONHASHSEED") == "0" and all(os.getenv(k) == "1" for k in course.THREADS),
          "Unexpected runtime settings")
    report = json.loads((HERE / "leistung.json").read_bytes())
    public_archive = HERE / "leistung_partien.jsonl.gz"
    check(course.sha(public_archive) == report["archive_sha"], "Fresh panel archive changed")
    raw = [json.loads(line) for line in gzip.decompress(public_archive.read_bytes()).splitlines()]
    direct = {tuple(r["key"][:2]): r for r in raw if r["key"][2:] == ["hold", "v16"]}
    check(sorted(k for k, r in direct.items() if len(r["events"]) == 2) == KEYS, "Different affected seats")
    check(course.stamp(identity()) == report["source"], "Simulator or model changed")
    source = {"frozen_panel": report["source"], "archive": report["archive_sha"],
              "diagnostic": course.sha(HERE / "direktursache.py"), "keys": [list(k) for k in KEYS]}
    family = course.stamp(source)
    controls = []
    changes = []
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed, side in KEYS:
            ctrl = game(env, (seed, side, "probe", "v16"), family)
            hold = direct[seed, side]
            at = hold["events"][1][0]
            check(ctrl["events"] == hold["events"][:1] and ctrl["prefix"][:at + 1] == hold["prefix"][:at + 1],
                  "Copies diverged before the one permitted follow-up")
            check(ctrl["profile"][:at] == hold["profile"][:at] and ctrl["window"][0] == hold["window"][0],
                  "Different physical arrival or team score before the one added stay")
            diff = np.subtract(hold["profile"], ctrl["profile"])
            changes.append({
                "seed": seed, "side": side, "t": at, "uid": hold["events"][1][1],
                "world_target": list(divmod(hold["follow"]["target"], 24)),
                "entry_point": hold["window"][0]["scoring"] and hold["window"][0]["uid"],
                "hold_match_points": [v["points"] for v in hold["matches"]],
                "control_match_points": [v["points"] for v in ctrl["matches"]],
                "hold_win": hold["win"], "control_win": ctrl["win"],
                "gain_immediate": diff[at].tolist(), "gain_four": diff[at:at + 4].sum(0).tolist(),
                "gain_end": diff.sum(0).tolist(),
            })
            controls.append(ctrl)
    finally:
        env.close()
    archive = HERE / "direktkontrollen.jsonl.gz"
    payload = b"".join((json.dumps(r, separators=(",", ":"), sort_keys=True) + "\n").encode() for r in controls)
    archive.write_bytes(gzip.compress(payload, mtime=0))
    check(gzip.decompress(archive.read_bytes()) == payload, "Incomplete additional control archive")
    inactive = sum(r["win"] for k, r in direct.items() if k not in KEYS)
    result = {"source": source, "direct_seats": len(direct), "extra_controls": len(changes),
              "inactive_wins": inactive, "original_feldprobe_wins": inactive + sum(r["control_win"] for r in changes),
              "halteprobe_wins": inactive + sum(r["hold_win"] for r in changes),
              "archive_sha": sha256(archive.read_bytes()).hexdigest(), "cases": changes}
    course.write_once(HERE / "direktursache.json", result)
    print(result, flush=True)


if __name__ == "__main__":
    main()
