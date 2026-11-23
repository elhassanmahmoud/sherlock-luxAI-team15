"""Reproduce two actually changed whole games from the frozen 288-game panel and save public inputs."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import random
import shutil
import sys

import numpy as np
import torch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from experiments.analysis.relictsuche_20261123.flottenkurs.aufnehmen import Recorder
from experiments.analysis.relictsuche_20261123.ortundflotte.kandidat import create
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,PACKAGE,require,write_once
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent

SCRATCH=Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123")
OUT=SCRATCH/"ortflottenkurs/tapes"


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("team",type=int,choices=(0,1));a=p.parse_args()
    t=a.team;side=f"player_{t}";foe="solution92" if t==0 else "v16"
    source=HERE.parent/"ortundflotte/duelle_karten.jsonl.gz"
    with gzip.open(source,"rt") as f:
        eligible=[r for r in map(json.loads,f) if r["id"]=="scout" and r["team"]==t and r["opponent"]==foe and r["events"]]
    selected=min(eligible,key=lambda r:r["seed"])
    seed=selected["seed"]
    OUT.mkdir(parents=True,exist_ok=True)
    normal=SCRATCH/"routenlernen/tapes"/f"161050000_{side}.npz"
    norm=json.loads((HERE.parent/"flottenblick/normalsicht.json").read_bytes())["seats"][t]
    require(sha256(normal.read_bytes()).hexdigest()==norm["source_sha256"],"Normal control not validated")
    if not (OUT/normal.name).exists():shutil.copy2(normal,OUT/normal.name)
    limit_threads();random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        actor=create(side);capture=Recorder(actor)
        enemy=make_opponent("solution92",f"player_{1-t}") if foe=="solution92" else r3_package_agent(f"player_{1-t}",PACKAGE)
        mon=Monitor(env,t,"discovery",actor)
        result=play_game(mon,capture,enemy,seed,side,False)
        require_no_agent_errors(actor.base,enemy)
        require(mon.digest.hexdigest()==selected["action_hash"] and mon.events==selected["events"] and mon.matches==selected["matches"]
                and result["steps"]==303 and result["game_win"]==selected["win"],"Fresh-game archive not reproduced")
        meta=dict(seed=seed,side=side,opponent=foe,changes=actor.changes,cfg=actor.base.env_cfg)
        dest=OUT/f"{seed}_{side}.npz"
        arrays={k:np.stack(z) for k,z in capture.rows.items()}
        if dest.exists():
            with np.load(dest) as past:
                require(json.loads(str(past["metadata"]))==meta and all(np.array_equal(past[k],v) for k,v in arrays.items()),"Existing tape differs")
        else:np.savez_compressed(dest,metadata=np.array(json.dumps(meta)),**arrays)
        write_once(HERE/f"referenz_p{t}.json",dict(seed=seed,side=side,opponent=foe,actual_changes=actor.changes,events=mon.events,
                   archive_world_commands=mon.digest.hexdigest(),tape_sha256=sha256(dest.read_bytes()).hexdigest(),
                   archived_games_sha256=sha256(source.read_bytes()).hexdigest(),matches=mon.matches,win=selected["win"]))
        print(seed,side,foe,actor.changes,flush=True)
    finally:env.close()


if __name__=="__main__":main()
