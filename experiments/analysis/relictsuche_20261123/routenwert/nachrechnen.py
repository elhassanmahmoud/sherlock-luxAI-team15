"""Independently reconstruct the selected direction and endpoints from the published raw openings."""
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
def read_raw(label):
    path = HERE / (label+".jsonl.gz")
    with gzip.open(path, "rt") as f:
        rows = [json.loads(line) for line in f]
    return rows, sha256(path.read_bytes()).hexdigest()


def verify():
    m = json.loads((HERE/"modell.json").read_text())
    saved = json.loads((HERE/"offline.json").read_text())
    out = {}
    used = set()
    for label, field in (("training","training"), ("pruefung","held")):
        rows, digest = read_raw(label)
        a = saved[field]
        assert len(rows) == a["cards"] and len(rows) == len({r["seed"] for r in rows})
        assert not used.intersection(r["seed"] for r in rows)
        used.update(r["seed"] for r in rows)
        chosen = []
        for r in rows:
            old = r["original"]
            target = old
            gid = None
            if r["event"]:
                scores = [m["intercept"]+sum(w*(v-mu)/s for w,v,mu,s in zip(m["weights"],x,m["mean"],m["scale"],strict=True))
                          for x in r["event"]["x"]]
                i = max(range(3), key=lambda k:scores[k])
                if scores[i] >= m["threshold"]:
                    target, gid = r["trials"][i], i
            chosen.append(dict(seed=r["seed"], arm=gid, shift=[a-b for a,b in zip(old["y"], target["y"], strict=True)],
                               win=target["win"]-old["win"], actual=int(target["changes"]>0),
                               possible_time=max([0, *[old["y"][0]-t["y"][0] for t in r["trials"]]])))
        d = np.array([x["shift"] + [x["win"]] for x in chosen]) * [1,1,-1,1]
        assert np.allclose(d.mean(0), a["actual"]["gain"])
        assert sum(c["actual"] for c in chosen) == a["changed_cards"]
        draws = np.random.default_rng(231123).integers(len(d), size=(5000,len(d)))
        out[field] = dict(maps=len(rows), openings=sum(1+len(r["trials"]) for r in rows),
                          raw_sha256=digest, eligible=sum(bool(r["event"]) for r in rows),
                          any_earlier=sum(r["possible_time"]>0 for r in chosen),
                          prospectively_earlier=int((d[:,0]>0).sum()), prospectively_later=int((d[:,0]<0).sum()),
                          gain_means=d.mean(0).tolist(), ci95=np.quantile(d[draws].mean(1), [.025,.975],axis=0).tolist())
    return out


if __name__ == "__main__":
    (HERE/"gegenpruefung.json").write_text(json.dumps(verify(), indent=2, allow_nan=False)+"\n")
