"""Fit one fixed ridge on training maps; evaluate the locked decision on new maps."""
import argparse
import gzip
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

from erheben import HERE, MODEL_SHA, NAMES, V16, cases, sha, sources


def records(folder, split):
    out = []
    expected = cases(split)
    if {p.stem for p in folder.glob("*.json")} != {str(c[0]) for c in expected}:
        raise ValueError("Incorrect set of map identities")
    spec = sources()
    for case in expected:
        p = folder / f"{case[0]}.json"
        r = json.loads(p.read_text())
        if r["case"] != list(case) or r["source"] != spec or r["release"] != V16 or r["weights"] != MODEL_SHA:
            raise ValueError("Source, weights or replay identity changed")
        l, a = r["original"], r["alternative"]
        if bool(l) != bool(a) or (l and (l["pivot"] != a["pivot"] or l["event"] != a["event"])):
            raise ValueError("Inconsistent paired continuations")
        item = dict(case=list(case), sha256=sha(p), x=None, delta=None)
        if l:
            delta = np.asarray(a["gains"], dtype=int) - np.asarray(l["gains"], dtype=int)
            x = l["event"]["x"]
            if delta.shape != (3, 2) or len(x) != len(NAMES) or not np.isfinite(x).all():
                raise ValueError("Invalid fifteen-turn case")
            item.update(x=x, delta=delta.tolist(), step=l["event"]["step"],
                        unit=l["event"]["uid"], direction=l["event"]["world"], before=l["pivot"]["before"])
        out.append(item)
    return out


def archive(rows, filename):
    data = b"".join((json.dumps(r, separators=(",", ":"), sort_keys=True)+"\n").encode() for r in rows)
    filename.write_bytes(gzip.compress(data, mtime=0))


def write(path, value):
    contents = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)+"\n"
    if path.exists() and path.read_text() != contents:
        raise ValueError("Refusing to overwrite a different frozen result")
    path.write_text(contents)


def train(folder):
    rows = records(folder, "train")
    real = [r for r in rows if r["x"] is not None]
    if len(real) < 40:
        raise ValueError(f"Too few actual training opportunities: {len(real)}")
    x = np.asarray([r["x"] for r in real], dtype=float)
    target = np.asarray([r["delta"][2][0] - r["delta"][2][1] for r in real], dtype=float)
    y = np.clip(target, -30, 30)
    center, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-7] = 1.
    z = (x - center)/scale
    beta = np.linalg.solve(z.T @ z + 32*np.eye(z.shape[1]), z.T @ (y-y.mean()))
    archive(rows, HERE/"trainingskarten.jsonl.gz")
    result = dict(inputs=NAMES, n_maps=len(rows), n_proposals=len(real), train_data=sha(HERE/"trainingskarten.jsonl.gz"),
                  sources=sources(), fit_code=sha(HERE/"lernen.py"), intercept=float(y.mean()),
                  mean=center.tolist(), scale=scale.tolist(), coefficients=beta.tolist(), lambda_ridge=32,
                  threshold=1, clipped_targets=int(np.count_nonzero(y != target)))
    write(HERE/"folgemodell.json", result)
    print(len(real), "actual training proposals", flush=True)


def evaluate(folder):
    r = json.loads((HERE/"folgemodell.json").read_text())
    if (r["fit_code"] != sha(HERE/"lernen.py") or r["sources"] != sources()
            or r["train_data"] != sha(HERE/"trainingskarten.jsonl.gz") or r["inputs"] != list(NAMES)):
        raise ValueError("Estimator or fitting source differs from training")
    rows = records(folder, "test")
    benefit = []
    accepted, rejected = 0, 0
    for item in rows:
        if item["x"] is None:
            benefit.append((0., 0.))
            continue
        x = ((np.asarray(item["x"]) - r["mean"])/r["scale"])
        value = float(r["intercept"] + x @ r["coefficients"])
        allow = value >= r["threshold"]
        y = int(item["delta"][2][0]) - int(item["delta"][2][1])
        accepted += int(allow)
        rejected += int(not allow)
        item.update(prediction=value, accept=bool(allow))
        benefit.append((y*allow, y*(allow-1)))
    d = np.asarray(benefit)
    indices = np.random.default_rng(231115).integers(0, len(rows), size=(20000,len(rows)))
    interval = np.quantile(d[indices].mean(axis=1), [.025,.975], axis=0)
    gates = dict(training=r["n_proposals"] >= 40, accepted=accepted>=10, rejected=rejected>=10,
                 v16=float(interval[0,0])>0, instant=float(interval[0,1])>0)
    archive(rows, HERE/"pruefkarten.jsonl.gz")
    result = dict(maps=len(rows), proposals=accepted+rejected, accepted=accepted, rejected=rejected,
                  no_proposal=len(rows)-accepted-rejected, gates=gates, eligible=all(gates.values()),
                  gains={name:dict(total=int(d[:,i].sum()), mean=float(d[:,i].mean()), ci95=interval[:,i].tolist())
                         for i,name in enumerate(("versus_v16", "versus_always"))},
                  map_archive=sha(HERE/"pruefkarten.jsonl.gz"), frozen_estimator=sha(HERE/"folgemodell.json"),
                  descriptive_by_opponent={o:d[[item["case"][2]==o for item in rows]].mean(axis=0).tolist()
                                           for o in ("solution92","kaggle3")})
    write(HERE/"pruefung.json", result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["train","test"])
    p.add_argument("folder", type=Path)
    a=p.parse_args()
    (train if a.mode=="train" else evaluate)(a.folder)
