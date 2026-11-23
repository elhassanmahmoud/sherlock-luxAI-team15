"""Record both active seats from the completed pilot and reuse the two verified normal controls."""
import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import random
import shutil

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor, require
from experiments.analysis.relictsuche_20261123.flottenblick.kandidat import create
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent


class Recorder:
    def __init__(self,agent):
        self.agent=agent
        self.rows=defaultdict(list)

    def __getattr__(self,name):
        return getattr(self.agent,name)

    def act(self,step,obs):
        result=self.agent.act(step,obs)
        assert len(self.rows["commands"])==step
        self.rows["commands"].append(np.asarray(result).copy())
        for k,v in obs.items():
            if isinstance(v,dict):
                for leaf,a in v.items():
                    self.rows[k+"/"+leaf].append(np.asarray(a).copy())
            else:
                self.rows[k].append(np.asarray(v).copy())
        return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("study_data",type=Path)
    folder=p.parse_args().study_data
    out=folder/"flottenkurs/tapes"
    out.mkdir(parents=True,exist_ok=True)
    limit_threads()
    with gzip.open(STUDY/"flottenblick/ganzspiel/partien.jsonl.gz","rt") as f:
        old={r["team"]:r for line in f if (r:=json.loads(line))["seed"]==161620000 and r["id"]=="flotte" and r["opponent"]=="solution92"}
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for t in (0,1):
            side=f"player_{t}"
            normal=folder/"routenlernen/tapes"/f"161050000_{side}.npz"
            spec=json.loads((STUDY/"flottenblick/normalsicht.json").read_text())["seats"][t]
            from hashlib import sha256
            require(sha256(normal.read_bytes()).hexdigest()==spec["source_sha256"], "Unverified normal control")
            shutil.copy2(normal,out/normal.name)
            seed=161620000
            random.seed(seed)
            torch.manual_seed(seed)
            np.random.seed(seed)
            actor=create(side)
            record=Recorder(actor)
            rival=make_opponent("solution92",f"player_{1-t}")
            monitor=Monitor(env,t,"discovery",actor)
            game=play_game(monitor,record,rival,seed,side,False)
            require_no_agent_errors(actor.base,rival)
            require(monitor.digest.hexdigest()==old[t]["action_hash"] and monitor.events==old[t]["events"]
                    and monitor.matches==old[t]["matches"] and game["steps"]==303, "Unreproduced pilot game")
            meta=dict(seed=seed,side=side,opponent="solution92",changes=actor.changes,cfg=actor.base.env_cfg)
            np.savez_compressed(out/f"{seed}_{side}.npz", metadata=np.array(json.dumps(meta)),
                                **{k:np.stack(a) for k,a in record.rows.items()})
            print(side,actor.changes,flush=True)
    finally:
        env.close()


if __name__=="__main__":
    main()
