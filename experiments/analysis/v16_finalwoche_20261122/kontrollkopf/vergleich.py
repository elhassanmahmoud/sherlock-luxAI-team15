"""Predeclared 200 games of fixed unweighted training control versus the V16 release."""
import argparse
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import random
import sys
import zipfile

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0,str(ROOT))
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import TARGET, verify
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import _module_for, r3_package_agent

RELEASE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
RELEASE_HASH = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
WEIGHT_HASH = "5b200d5a7fadfffb86ccb6c3e74324e49fe4c1e27510581ae810e6a452b2a67b"


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def same(a,b):
    if torch.is_tensor(a):
        return torch.is_tensor(b) and torch.equal(a,b)
    if isinstance(a,dict):
        return a.keys()==b.keys() and all(same(v,b[k]) for k,v in a.items())
    if isinstance(a,list):
        return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b


def verify_inputs(weight):
    if sha(RELEASE)!=RELEASE_HASH or sha(weight)!=WEIGHT_HASH or not verify():
        raise ValueError("Model or Kaggle source digest mismatch")
    with zipfile.ZipFile(RELEASE) as z:
        base = torch.load(io.BytesIO(z.read("sherlock/weights/agent.pth")),weights_only=False,map_location="cpu")
    candidate = torch.load(weight,weights_only=False,map_location="cpu")
    changed = sorted(k for k in base["policy"] if not torch.equal(base["policy"][k],candidate["policy"][k]))
    if changed!=["pi.bias","pi.weight"] or candidate["policy"].keys()!=base["policy"].keys():
        raise ValueError("Unexpected primary tensors")
    if base.keys()!=candidate.keys() or not all(same(base[k],candidate[k]) for k in base if k!="policy"):
        raise ValueError("Wrong settings or additional network changes")
    import importlib.util
    engine = Path(importlib.util.find_spec("luxai_s3").origin).parent
    return dict(zip_sha256=RELEASE_HASH,candidate_sha256=WEIGHT_HASH,changed=changed,
                engine={f:sha(engine/f) for f in ("env.py","wrappers.py","params.py")},
                evaluator=sha(Path(__file__)),plan=sha(HERE/"PLAN.md"), hash_seed=os.environ["PYTHONHASHSEED"],
                script_sources={s:sha(ROOT/"scripts"/s) for s in ("common.py","par_eval.py","experiment.py",
                                       "scoring.py","metrics.py","r3_package.py","kaggle3_opponent.py")},
                opponents={str(p.relative_to(ROOT)):sha(p) for root in (TARGET,ROOT/"agents/Solution_92_Kaggle")
                           for p in sorted(root.rglob("*")) if p.suffix in (".py",".pth")})


def game_keys():
    return [(seed, side, opponent, arm) for seed in range(19377000,19377020)
            for side in ("player_0","player_1") for opponent in ("solution92","kaggle3","v16")
            for arm in (("kontrolle",) if opponent=="v16" else ("original","kontrolle"))]


def key(r):
    return tuple(r[k] for k in ("seed","side","opponent","arm"))


def validate(r):
    if (r["steps"]!=303 or r["point_counting_version"]!=2 or r["our_wins"]+r["opp_wins"]!=3
            or r["game_win"] != int(r["our_wins"]>=2)):
        raise ValueError(f"Invalid game row {key(r)}")


def run(weight,out):
    import fcntl
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    out.mkdir(parents=True,exist_ok=True)
    lock = (out/"lauf.lock").open("a")
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    contract = verify_inputs(weight)
    record = out/"auftrag.json"
    if record.exists() and json.loads(record.read_text())!=contract:
        raise ValueError("Inputs changed")
    if not record.exists():
        record.write_text(json.dumps(contract,indent=2)+"\n")
    _, release_source = _module_for(RELEASE.resolve())
    seats = game_keys()
    log = out/"partien.jsonl"
    old = [json.loads(s) for s in log.read_text().splitlines()] if log.exists() else []
    for row in old:
        validate(row)
    if [key(r) for r in old] != seats[:len(old)]:
        raise ValueError("Duplicate, out-of-order or unexpected game")
    env = LuxAIS3GymEnv(numpy_output=True)
    with log.open("a") as stream:
        for seed,side,opp,arm in seats[len(old):]:
            other = "player_1" if side=="player_0" else "player_0"
            random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
            if arm=="original":
                player = r3_package_agent(side,RELEASE)
            else:
                player = release_source.Agent_x(side,agent_path=str(weight))
                player.set_to_eval_mode()
            rival = r3_package_agent(other,RELEASE) if opp=="v16" else make_opponent(opp,other)
            row = play_game(env,player,rival,seed,side,train=False)
            require_no_agent_errors(player,rival)
            detail = {k: row[k] for k in ("seed","side","game_win","steps","our_wins","opp_wins",
                                           "our_points","opp_points","point_counting_version")}
            detail.update(opponent=opp,arm=arm)
            validate(detail)
            stream.write(json.dumps(detail)+"\n"); stream.flush()
            print(seed,side,opp,arm,detail["game_win"],flush=True)
    env.close()
    if verify_inputs(weight)!=contract:
        raise ValueError("Source changed during run")
    if len(log.read_text().splitlines())!=200:
        raise ValueError("Incomplete panel")


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("checkpoint",type=Path)
    p.add_argument("out",type=Path)
    args = p.parse_args()
    run(args.checkpoint,args.out)
