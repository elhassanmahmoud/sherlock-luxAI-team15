"""Restore the study-only control from 1,542 coefficients and the original release."""
import argparse
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parents[3]/"experiments/releases/20261117_sherlock_v16/agent.zip"
RELEASE_SHA = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
EXPECTED = "5b200d5a7fadfffb86ccb6c3e74324e49fe4c1e27510581ae810e6a452b2a67b"


def restore(directory):
    # torch.save includes the filename stem in its archive member paths.
    # The original tensor ordering matters for byte-identical checks.
    data = RELEASE.read_bytes()
    if sha256(data).hexdigest()!=RELEASE_SHA:
        raise ValueError("Unexpected V16")
    with ZipFile(BytesIO(data)) as release:
        ckpt = torch.load(BytesIO(release.read("sherlock/weights/agent.pth")),weights_only=False,map_location="cpu")
    with np.load(HERE/"kontrollkopf.npz",allow_pickle=False) as head:
        for k in ("pi.weight","pi.bias"):
            value = torch.tensor(head[k])
            if value.dtype!=ckpt["policy"][k].dtype or value.shape!=ckpt["policy"][k].shape:
                raise ValueError("Unexpected action head")
            ckpt["policy"][k] = value
    directory.mkdir(parents=True,exist_ok=False)
    dest = directory/"kontrolle.pth"
    torch.save(ckpt,dest)
    if sha256(dest.read_bytes()).hexdigest()!=EXPECTED:
        raise ValueError("Serialization differs from the evaluated model; use the project Python environment")
    print(dest,EXPECTED)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("new_directory",type=Path)
    restore(p.parse_args().new_directory)
