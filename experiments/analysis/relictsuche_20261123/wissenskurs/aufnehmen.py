"""Record the first active game per seat and archive its point proofs and decision tape for both course runtimes."""
import argparse
import gzip
import json
from pathlib import Path
import random
import shutil

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.flottenkurs.aufnehmen import Recorder
from experiments.analysis.relictsuche_20261123.punktwissen.spiele import HERE, Tape, create, decoded, sha
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    a=p.parse_args()
    out=a.root/"wissenskurs/tapes"
    out.mkdir(parents=True, exist_ok=True)
    with gzip.open(HERE/"partien.jsonl.gz","rt") as f:
        rows=sorted(map(json.loads,f),key=lambda r:r["seed"])
    normals=json.loads((HERE.parent/"flottenblick/normalsicht.json").read_text())["seats"]
    limit_threads()
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for team in (0,1):
            side=f"player_{team}"
            normal=a.root/"routenlernen/tapes"/f"161050000_{side}.npz"
            assert sha(normal)==normals[team]["source_sha256"]
            shutil.copyfile(normal,out/normal.name)
            old=next(r for r in rows if r["team"]==team and r["version"]=="neu" and r["opponent"]=="solution92" and r["events"])
            seed=old["seed"]
            random.seed(seed)
            torch.manual_seed(seed)
            np.random.seed(seed)
            player=create(side)
            tape=Recorder(player)
            rival=make_opponent("solution92",f"player_{1-team}")
            mon=Tape(env,team,player)
            game=play_game(mon,tape,rival,seed,side,False)
            require_no_agent_errors(player.base,rival)
            assert game["steps"]==303 and mon.digest.hexdigest()==old["digest"] and mon.matches==old["matches"]
            assert player.events==mon.checked==old["events"]
            assert np.array_equal(decoded(old)[:,team],np.stack(tape.rows["commands"]))
            meta=dict(cfg=player.base.env_cfg,seed=seed,side=side,opponent="solution92",changes=len(player.events))
            np.savez_compressed(out/f"{seed}_{side}.npz",metadata=np.array(json.dumps(meta)),
                                **{k:np.stack(v) for k,v in tape.rows.items()})
    finally:
        env.close()


if __name__=="__main__":
    main()
