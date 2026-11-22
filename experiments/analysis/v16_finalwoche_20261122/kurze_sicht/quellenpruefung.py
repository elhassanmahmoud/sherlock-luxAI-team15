"""Replay both seats' original observations and verify every V16 command and early learning input."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from sammeln import HERE, PACKAGES, ROOT, sample
from verlauf import public_obs
from scripts.imitate import PLANE_SCALE, SideRecord
from scripts.r3_package import r3_package_agent


def verify(raw_dir, teach_dir, output):
    selected = [next(r for r in sample() if r["side"] == s) for s in ("player_0", "player_1")]
    cfgs = {r["seed"]: r for r in json.loads((HERE.parent / "kartenparameter/ergebnis.json").read_text())["maps"]}
    rel, sha = PACKAGES["v16"]
    release = ROOT / "experiments/releases" / rel / "agent.zip"
    if sha256(release.read_bytes()).hexdigest() != sha:
        raise ValueError("Unexpected original V16")
    reports = []
    for row in selected:
        tag = f"v16_{row['seed']}_{row['side']}"
        receipt = json.loads((raw_dir / (tag + ".json")).read_text())
        raw = raw_dir / receipt["filename"]
        if sha256(raw.read_bytes()).hexdigest() != receipt["sha256"]:
            raise ValueError("Raw trajectory changed")
        with np.load(raw, allow_pickle=False) as z:
            hist = {k: z[k] for k in z.files}
        cfg = {k: v for k, v in cfgs[row["seed"]].items() if k.startswith("unit_")}
        cfg.update(map_width=24, map_height=24, max_units=16, match_count_per_episode=3,
                   max_steps_in_match=100, num_teams=2)
        actor = r3_package_agent(row["side"], release)
        actor.new_game(row["side"])
        actor.set_env_cfg(cfg)
        b = SideRecord()
        for i in range(303):
            original = actor.act(i, public_obs(hist, i))
            if not np.array_equal(original, hist["commands"][i]):
                raise ValueError(f"Action mismatch at {tag}, turn {i}")
            policy = actor._imitation
            if policy.last_fz is not None:
                b.add(policy.last_fz, original, policy.belief.mirrored)
        ffile = teach_dir / (tag + ".npz")
        with np.load(ffile, allow_pickle=False) as z:
            for field in ("planes", "act", "pos", "feats", "mask", "step", "uid", "sdx", "sdy", "mstep"):
                expected = np.asarray(getattr(b, field), dtype=z[field].dtype)
                if not np.array_equal(expected, z[field]):
                    raise ValueError(f"Different teacher feature {tag}, {field}")
        reports.append(dict(seed=row["seed"], side=row["side"], actions=303*16,
                            features=len(b.act), raw_sha=receipt["sha256"], teacher_sha=sha256(ffile.read_bytes()).hexdigest()))
    output.write_text(json.dumps(dict(package=sha, identical=reports), indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "teach", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    verify(args.raw, args.teach, args.output)
