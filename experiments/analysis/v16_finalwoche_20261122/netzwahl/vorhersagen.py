"""Cache each frozen net's legal action scores for the fixed teaching games."""
import argparse
from hashlib import sha256
import importlib
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from agents.sherlock.features import FEATURE_NAMES
from scripts.imitate import PLANE_SCALE, prepare_labels, prev_move_columns
from scripts.r3_package import _module_for

FEATURES = ("self_energy", "match_step_frac", "match_idx_frac", "on_point", "redundant_here",
            "enemies_in_sap", "enemies_visible", "explored_frac", "known_points")
RELEASE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
V16 = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"


def input_files(base, archive_only):
    index = ROOT / "experiments/analysis/umbau_20261115/dagger_zusatz/index-400.json"
    archive = base.parents[1] / "k3_v4_extra_7172000/data"
    items = []
    for row in sorted(json.loads(index.read_text())["files"], key=lambda r: r["seed"])[:120]:
        filename = f"g{row['seed']}_{row['side']}_{row['opponent']}_dagger.npz"
        items.append((row, archive / filename, "old"))
    previous = base.parent / "frisch"
    for row in json.loads((previous / "sammlung.json").read_text()):
        if row["split"] == "train":
            items.append((row, previous / row["file"], "new"))
    if not archive_only:
        for seed in [*range(160345000, 160345032), *range(160345100, 160345124)]:
            row = json.loads((base / "frisch" / f"{seed}.json").read_text())
            items.append((row, base / "frisch" / row["file"], "new" if row["split"] == "train" else "valid"))
    return items


def networks(device):
    if sha256(RELEASE.read_bytes()).hexdigest() != V16:
        raise ValueError("Different released student")
    _module_for(RELEASE.resolve())
    net_class = importlib.import_module("sherlock.imitation_net").ImitationNet
    with zipfile.ZipFile(RELEASE) as package:
        weights = torch.load(io.BytesIO(package.read("sherlock/weights/agent.pth")),
                             map_location="cpu", weights_only=False)
    if weights["members"] != ["v9_from_v8.pth", "v8L_from_v7L.pth"]:
        raise ValueError("Unexpected ensemble order")
    models = []
    for member in (weights, weights["imitation_ensemble"][0]):
        model = net_class(**member["arch"]).eval()
        model.load_state_dict(member["policy"])
        models.append(model.to(device))
    return models


def predict(row, path, split, models, device, out):
    digest = sha256(path.read_bytes()).hexdigest()
    if digest != row["sha256"]:
        raise ValueError(f"Archive checksum changed on {row['seed']}")
    with np.load(path, allow_pickle=False) as archive:
        frame = {key: archive[key] for key in archive.files if key != "meta"}
        meta = json.loads(str(archive["meta"]))
    if (any(meta[k] != row[k] for k in ("seed", "side", "opponent")) or meta["steps"] != 303
            or meta["teacher_history"] != "played_student_actions"
            or (split != "old" and meta["student"] != V16)):
        raise ValueError(f"Data identity mismatch on {row['seed']}")
    previous = prev_move_columns(frame)
    feats = torch.from_numpy(np.concatenate((frame["feats"], previous), axis=1)).float()
    rows = {k: torch.from_numpy(frame[k]) for k in ("pos", "feats", "mask", "act", "sdx", "sdy")}
    prepare_labels(rows, *frame["planes"].shape[-2:])
    all_logits = [[], []]
    with torch.inference_mode():
        for start in range(0, len(frame["planes"]), 16):
            stop = min(start + 16, len(frame["planes"]))
            a, b = np.searchsorted(frame["step"], (start, stop))
            boards = torch.from_numpy(frame["planes"][start:stop]).to(device, dtype=torch.float32) / PLANE_SCALE
            step = torch.from_numpy(frame["step"][a:b].astype(np.int64) - start).to(device)
            pos = rows["pos"][a:b].to(device, dtype=torch.long)
            units = feats[a:b].to(device)
            for index, model in enumerate(models):
                logits = model.forward_all(boards, step, pos, units)[0].cpu()
                all_logits[index].append(logits)
    eligible = rows["admitted"]
    if len(eligible) != row["rows"] or not eligible.any():
        raise ValueError("Wrong number of unit observations")
    path_out = out / f"{split}_{row['seed']}.npz"
    temporary = out / f"{split}_{row['seed']}.pending.npz"
    np.savez_compressed(temporary, a=torch.cat(all_logits[0])[eligible].numpy(),
                        b=torch.cat(all_logits[1])[eligible].numpy(),
                        legal=rows["mask"][eligible].numpy(), y=rows["act"][eligible].numpy(),
                        x=feats[eligible][:, [FEATURE_NAMES.index(k) for k in FEATURES]].numpy(),
                        origin=digest, model=V16)
    temporary.replace(path_out)


def encode(base, archive_only, device):
    torch.set_num_threads(1)
    models = networks(device)
    out = base / "vorhersagen"
    out.mkdir(exist_ok=True)
    for row, path, split in input_files(base, archive_only):
        cached = out / f"{split}_{row['seed']}.npz"
        if cached.exists():
            with np.load(cached, allow_pickle=False) as cache:
                if str(cache["origin"]) != row["sha256"] or str(cache["model"]) != V16:
                    raise ValueError("Cache provenance mismatch")
            continue
        predict(row, path, split, models, device, out)
        print(split, row["seed"], flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("base", type=Path)
    cli.add_argument("--archive-only", action="store_true")
    cli.add_argument("--device", default="mps", choices=("mps", "cpu"))
    args = cli.parse_args()
    encode(args.base, args.archive_only, args.device)
