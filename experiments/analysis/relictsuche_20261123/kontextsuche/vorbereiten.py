"""Freeze the preexisting reduced ridge and replay an acceptance and refusal against both genuine opponents."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import torch

from experiments.analysis.relictsuche_20261123.kontextsuche.kandidat import HERE,create
from experiments.analysis.relictsuche_20261123.netzvertrauen.lernen import fit,predict
from experiments.analysis.relictsuche_20261123.netzvertrauen.stimmen import BASE
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,PACKAGE,sha,write_once
from scripts.common import play_game,make_opponent
from scripts.r3_package import r3_package_agent
from scripts.par_eval import require_no_agent_errors
from scripts.experiment import limit_threads


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    archive=HERE.parent/"netzvertrauen/lernspiele.jsonl.gz"
    with gzip.open(archive,"rt") as f:rows=list(map(json.loads,f))
    assert len(rows)==640
    trained=fit(rows,len(BASE))
    write_once(HERE/"modell.json",dict(features=BASE,model=trained,threshold=.20,train_hash=sha(archive)))
    env=LuxAIS3GymEnv(numpy_output=True)
    limit_threads()
    result=[]
    try:
        for opp in ("solution92","v16"):
            for choice in (False,True):
                r=next(q for q in rows if q["opponent"]==opp and q["features"] is not None and
                       (predict(q["features"],trained)>=.20)==choice)
                seed,team=r["seed"],r["team"]
                torch.manual_seed(seed)
                side=f"player_{team}";other=f"player_{1-team}"
                actor=create(side)
                rival=r3_package_agent(other,PACKAGE) if opp=="v16" else make_opponent(opp,other)
                mon=Monitor(env,team,"discovery",actor)
                real=play_game(mon,actor,rival,seed,side,False)
                require_no_agent_errors(actor.base,rival)
                ref=r["candidate"] if choice else r["base"]
                assert actor.decision is choice and np.allclose(actor.features[:len(BASE)],r["features"][:len(BASE)],atol=1e-8)
                assert mon.digest.hexdigest()==ref["action_hash"] and mon.matches==ref["matches"] and real["game_win"]==ref["win"]
                result.append(dict(seed=seed,team=team,opponent=opp,chosen=choice,turn=actor.at,hash=mon.digest.hexdigest(),steps=mon.turn))
    finally:env.close()
    write_once(HERE/"technik.json",dict(model_sha=sha(HERE/"modell.json"),cases=result))
    print(result)


if __name__=="__main__":main()
