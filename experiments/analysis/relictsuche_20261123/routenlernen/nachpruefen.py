"""Independent data, archive and executable-command audit using stored artifacts."""
import gzip
from hashlib import sha256
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/routenlernen")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify():
    training = json.loads((HERE / "training.json").read_text())
    held = json.loads((HERE / "offline.json").read_text())
    stored = json.loads((HERE / "routengewichte.json").read_text())
    model = {k: np.asarray(stored[k], np.float32) for k in ("mean", "scale", "w1", "b1", "w2", "b2")}
    if model["w1"].shape != (48, 32) or model["w2"].shape != (32, 1):
        raise ValueError("Not the expected trained parameter count")
    all_seeds = set()
    total_hashes = 0
    for part, report in (("train", training), ("valid", held)):
        groups = paths = 0
        board_mean = []
        for r in report["input_files"]:
            seed = r["seed"]
            if seed in all_seeds:
                raise ValueError("Overlapping data")
            all_seeds.add(seed)
            file = OUT / ("direction_" + part) / f"{seed}.npz"
            if digest(file) != r["sha256"]:
                raise ValueError("Raw sample hash mismatch")
            total_hashes += 1
            gain = []
            with np.load(file, allow_pickle=False) as raw:
                x, y, indexes, cuts = (raw[key] for key in ("x", "y", "selections", "offsets"))
                if int(raw["team"]) != r["team"] or not (len(x) == len(y) == len(indexes) == cuts[-1]):
                    raise ValueError("Raw shape/seat mismatch")
                for a, b in zip(cuts[:-1], cuts[1:], strict=True):
                    if indexes[a] != 0:
                        continue
                    groups += 1
                    paths += int(b - a)
                    if part == "valid":
                        inp = (x[a:b] - model["mean"]) / model["scale"]
                        pred = (np.maximum(inp @ model["w1"] + model["b1"], 0) @ model["w2"]).ravel() + model["b2"][0]
                        # Independently locate the baseline by feature name, with a handwritten
                        # decode of the 44 moving templates: straight, then 5 bends each way.
                        favor = x[a:b, stored["features"].index("original_first_move")]
                        winner = int(np.argmax(pred + .15 * favor))
                        if pred[winner] < pred[0] + .35:
                            winner = 0
                        # Same baseline used in the published table: fewest off-axis steps.
                        offaxis = (0, 6, 4, 2, 4, 2, 6, 4, 2, 4, 2)
                        turns = np.asarray([0 if k == 0 else offaxis[(int(k) - 1) % 11] for k in indexes[a:b]])
                        candidates = np.flatnonzero(favor)
                        original = candidates[np.argmin(turns[candidates])] if len(candidates) else 0
                        gain.append(float(y[a + winner] - y[a + original]))
            if gain:
                board_mean.append(float(np.mean(gain)))
        expected = training if part == "train" else held["measured"]
        if groups != expected["groups"] or paths != expected["paths"]:
            raise ValueError("Different count of scored groups/routes")
        if part == "valid" and abs(np.mean(board_mean) - expected["vs_original_direction"]["mean"]) > 1e-7:
            raise ValueError("Different action choice or reference computation")
    manifest = json.loads((HERE / "paket.json").read_text())
    if any(digest(HERE / n) != h for n, h in manifest["source"].items()):
        raise ValueError("Freeze digest differs")
    package = Path(manifest["candidate"])
    released = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
    if digest(package) != manifest["sha256"] or digest(released) != manifest["original_sha256"]:
        raise ValueError("Package hash differs")
    with ZipFile(package) as receive, ZipFile(released) as old:
        if (receive.testzip() or receive.read("sherlock/weights/agent.pth") != old.read("sherlock/weights/agent.pth")
                or receive.read("sherlock/routengewichte.json") != (HERE / "routengewichte.json").read_bytes()):
            raise ValueError("Weights differ between archives and study")
    replays = [json.loads(r) for r in gzip.decompress((HERE / "eroeffnungen.jsonl.gz").read_bytes()).splitlines()]
    if all_seeds.intersection({r["seed"] for r in replays}) or len(replays) != 128:
        raise ValueError("Replays duplicate training or validation")
    for r in replays:
        for t, uid, old, new in r["events"]:
            if (t >= r["first"] or t > r["first_credit"] or not 10 <= t <= 90 or not 0 <= old <= 4
                    or not 1 <= new <= 4 or old == new or not 0 <= uid < 16):
                raise ValueError("A recorded intervention violates the active window")
    output = dict(archives_checked=2, raw_maps_checked=total_hashes,
                  heldout_learned_gain_recomputed=float(np.mean(board_mean)),
                  opening_records_checked=len(replays), frozen_files_checked=len(manifest["source"]))
    (HERE / "nachpruefung.json").write_text(json.dumps(output, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    verify()
