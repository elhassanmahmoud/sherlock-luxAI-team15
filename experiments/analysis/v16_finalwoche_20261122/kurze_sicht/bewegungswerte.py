"""Record the two released networks' movement scores alongside the actually played action."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "netzwahl"))
from vorhersagen import RELEASE, V16, networks
from scripts.imitate import PLANE_SCALE, prev_move_columns


def encode(source, dest, device):
    torch.set_num_threads(1)
    nets = networks(device)
    dest.mkdir(parents=True, exist_ok=True)
    for manifest in sorted(source.glob("*.json")):
        record = json.loads(manifest.read_text())
        raw = source / record["file"]
        path = dest / (manifest.stem + ".npz")
        if path.exists():
            with np.load(path, allow_pickle=False) as prior:
                if str(prior["sha256"]) != record["sha256"] or str(prior["v16"]) != V16:
                    raise ValueError("Mismatched cache")
            continue
        if sha256(raw.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError(f"Corrupt teaching data: {raw}")
        with np.load(raw, allow_pickle=False) as z:
            data = {k: z[k] for k in z.files if k != "meta"}
        inputs = np.concatenate((data["feats"], prev_move_columns(data)), axis=1)
        scores = []
        with torch.inference_mode():
            for a in range(0, len(data["planes"]), 24):
                b = min(a + 24, len(data["planes"]))
                p, q = np.searchsorted(data["step"], [a, b])
                boards = torch.from_numpy(data["planes"][a:b]).to(device, dtype=torch.float32) / PLANE_SCALE
                steps = torch.from_numpy(data["step"][p:q].astype(np.int64) - a).to(device)
                pos = torch.from_numpy(data["pos"][p:q]).to(device, dtype=torch.long)
                feats = torch.from_numpy(inputs[p:q]).to(device, dtype=torch.float32)
                total = sum(n.forward_all(boards, steps, pos, feats)[0] for n in nets)
                scores.append(total[:, 1:5].cpu().numpy())
        tmp = path.with_suffix(".pending.npz")
        np.savez_compressed(tmp, v16=V16, sha256=record["sha256"], logits=np.concatenate(scores),
                            x=data["feats"], legal=data["mask"][:, 1:5], y=data["act"],
                            step=data["step"], uid=data["uid"], pos=data["pos"])
        tmp.replace(path)
        print(manifest.stem, flush=True)


if __name__ == "__main__":
    cmd = argparse.ArgumentParser(description=__doc__)
    cmd.add_argument("source", type=Path)
    cmd.add_argument("dest", type=Path)
    cmd.add_argument("--device", choices=("cpu", "mps"), default="mps")
    args = cmd.parse_args()
    encode(args.source, args.dest, args.device)
