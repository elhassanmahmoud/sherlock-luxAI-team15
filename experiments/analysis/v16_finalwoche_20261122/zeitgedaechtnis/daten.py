"""Reconstruct one training file per map and collect genuinely new evaluation maps."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import numpy as np
import torch

from historie import HERE, WIDTH, archived_inputs
sys.path.insert(0,str(HERE.parent/"netzwahl"))
from vorhersagen import V16, RELEASE, input_files, networks, predict
# Source is imported by explicit path because the two studies both have a daten.py.
import importlib.util
source=importlib.util.spec_from_file_location("collect_fixed_teacher",HERE.parent/"netzwahl/daten.py")
teacher=importlib.util.module_from_spec(source)
source.loader.exec_module(teacher)
from scripts.imitate import prepare_labels


def project(row,raw,cache,output):
    if sha256(raw.read_bytes()).hexdigest()!=row["sha256"]:
        raise ValueError("Teaching rows changed")
    p=output/f"{row['seed']}.npz"
    if p.exists():
        with np.load(p,allow_pickle=False) as z:
            if str(z["source"])!=row["sha256"]: raise ValueError("Inconsistent temporal cache")
        return
    with np.load(raw,allow_pickle=False) as z:
        rows={k:torch.from_numpy(z[k]) for k in ("pos","feats","mask","act","sdx","sdy")}
        prepare_labels(rows,24,24)
        valid=rows["admitted"].numpy()
        x=archived_inputs(z["step"],z["mstep"],z["uid"],z["pos"],z["feats"])[valid]
    with np.load(cache,allow_pickle=False) as z:
        if (str(z["origin"])!=row["sha256"] or str(z["model"])!=V16 or len(x)!=len(z["y"])
                or not np.array_equal(rows["act"].numpy()[valid],z["y"])):
            raise ValueError("Network scores and histories are not aligned")
        tmp=p.with_suffix(".pending.npz")
        np.savez_compressed(tmp,x=x,source=row["sha256"],scores=(z["a"]+z["b"]).astype(np.float32),
                            disagree=(np.where(z["legal"],z["a"],-np.inf).argmax(1)!=np.where(z["legal"],z["b"],-np.inf).argmax(1)),
                            y=z["y"].astype(np.int8),mask=z["legal"])
    tmp.replace(p)


def make(base,out,split):
    torch.set_num_threads(1)
    out.mkdir(parents=True,exist_ok=True)
    if split=="train":
        for row,raw,kind in input_files(base/"netzwahl",False,False):
            cached=base/"netzwahl/vorhersagen"/f"{kind}_{row['seed']}.npz"
            project(row,raw,cached,out)
        return
    if os.getenv("PYTHONHASHSEED")!="0" or sha256(RELEASE.read_bytes()).hexdigest()!=V16 or not teacher.verify():
        raise ValueError("Invalid study identity")
    folder=base/"zeitgedaechtnis/pruefpartien"
    folder.mkdir(exist_ok=True,parents=True)
    env=teacher.LuxAIS3GymEnv(numpy_output=True)
    models=networks("mps")
    try:
        for i in range(24):
            seed=160366000+i
            manifest=folder/f"{seed}.json"
            if manifest.exists():
                row=json.loads(manifest.read_text())
            else:
                row=teacher.record(env,folder,"valid",seed,f"player_{i%2}",("kaggle3","solution92")[i//2%2])
                tmp=manifest.with_suffix(".pending")
                tmp.write_text(json.dumps(row)+"\n")
                tmp.replace(manifest)
            raw=folder/row["file"]
            cache=folder/f"valid_{seed}.npz"
            if not cache.exists():predict(row,raw,"valid",models,"mps",folder)
            project(row,raw,cache,out)
            print(seed,flush=True)
    finally:
        env.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("base",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("split",choices=("train","valid"))
    a=p.parse_args()
    make(a.base,a.output,a.split)
