"""Project recorded, actually executed R3 or V16 actions onto the released V16 inputs."""
import argparse
from hashlib import sha256
import importlib
import json
from pathlib import Path

import numpy as np
from sammeln import HERE, PACKAGES, ROOT, sample
from verlauf import public_obs
from scripts.imitate import SideRecord
from scripts.r3_package import r3_package_agent


def extract(folder, out, arm, allow_partial):
    release = ROOT / "experiments/releases" / PACKAGES["v16"][0] / "agent.zip"
    if sha256(release.read_bytes()).hexdigest() != PACKAGES["v16"][1]:
        raise ValueError("Different feature generator")
    configs = {m["seed"]: m for m in json.loads((HERE.parent / "kartenparameter/ergebnis.json").read_text())["maps"]}
    out.mkdir(parents=True, exist_ok=True)
    for seat in sample():
        tag = f"{arm}_{seat['seed']}_{seat['side']}"
        receipt = folder / (tag + ".json")
        if allow_partial and not receipt.exists():
            continue
        record = json.loads(receipt.read_text())
        raw = folder / record["filename"]
        done_path = out / (tag + ".json")
        dest = out / (tag + ".npz")
        if done_path.exists():
            previous = json.loads(done_path.read_text())
            if (previous["source_sha256"] != record["sha256"]
                    or previous["sha256"] != sha256(dest.read_bytes()).hexdigest()):
                raise ValueError("Inconsistent cached training game")
            continue
        if sha256(raw.read_bytes()).hexdigest() != record["sha256"] or record["seat"] != seat:
            raise ValueError("Source trajectory mismatch")
        cfg = {k: v for k, v in configs[seat["seed"]].items() if k.startswith("unit_")}
        cfg.update(map_width=24, map_height=24, max_units=16, match_count_per_episode=3,
                   max_steps_in_match=100, num_teams=2)
        player = r3_package_agent(seat["side"], release)
        player.new_game(seat["side"])
        player.set_env_cfg(cfg)
        student = player._imitation
        featurize = importlib.import_module("sherlock.imitation_agent").featurize
        with np.load(raw, allow_pickle=False) as npz:
            arrays = {k: npz[k] for k in npz.files}
        buf = SideRecord()
        for step, commands in enumerate(arrays["commands"]):
            obs = public_obs(arrays, step)
            fz = featurize(student, obs)
            if fz is not None:
                buf.add(fz, commands, student.belief.mirrored)
        meta = dict(seed=seat["seed"], side=seat["side"], opponent="solution92", actor=arm, steps=303,
                    sensor=seat["sensor"], group=seat["group"], source_sha256=record["sha256"],
                    label_source="actual_recorded_action")
        tmp = out / (tag + ".pending.npz")
        n = buf.save(tmp, meta)
        if n <= 0:
            raise ValueError("Empty reference demonstration")
        tmp.replace(dest)
        tmp = done_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(dict(**meta, file=dest.name, sha256=sha256(dest.read_bytes()).hexdigest(),
                                       rows=n), sort_keys=True) + "\n")
        tmp.replace(done_path)
        print(tag, n, flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("folder", type=Path)
    cli.add_argument("out", type=Path)
    cli.add_argument("arm", choices=PACKAGES)
    cli.add_argument("--allow-partial", action="store_true")
    args = cli.parse_args()
    extract(args.folder, args.out, args.arm, args.allow_partial)
