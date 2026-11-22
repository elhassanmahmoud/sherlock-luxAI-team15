"""Freeze the exact historical Dev H Python sources next to the verified release and opponents."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from shutil import copy2
import subprocess
import sys
import tarfile
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
HISTORICAL="0cd2ce37bf5c9dec21ac976c549c9c7f616ac614"
REF="experiments/releases/20261117_sherlock_v16/agent.zip"


def freeze(out):
    out.mkdir(parents=True,exist_ok=False)
    tree=subprocess.check_output(["git","-C",str(ROOT),"ls-tree","-r","--name-only",HISTORICAL,"scripts","agents","lux"],text=True)
    names=[p for p in tree.splitlines() if p.endswith(".py")]
    payload=subprocess.check_output(["git","-C",str(ROOT),"archive",HISTORICAL,*names])
    with tarfile.open(fileobj=BytesIO(payload)) as t:t.extractall(out,filter="data")
    extra=ROOT/"experiments/opponents/kaggle3_lux3_048fn"
    paths=[p for p in extra.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    paths += [ROOT/REF,HERE/"PLAN.md",HERE/"spielen.py",HERE/"archiv.py"]
    paths += [ROOT/f"experiments/analysis/devh_20261117/{name}_devH.csv" for name in ("k","wechsel")]
    for p in paths:
        q=out/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);copy2(p,q)
    with zipfile.ZipFile(out/REF) as z:
        ck=z.read("sherlock/weights/agent.pth")
    if sha256(ck).hexdigest()!="8ed7412856d6176b81e257360c8eac4a41b844fec935db33aff9e19221d86495":
        raise ValueError("Unexpected V16 checkpoint")
    (out/"v16.pth").write_bytes(ck)


if __name__=="__main__":freeze(Path(sys.argv[1]))
