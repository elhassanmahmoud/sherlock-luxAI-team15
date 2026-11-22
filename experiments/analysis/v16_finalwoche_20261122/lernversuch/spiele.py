"""Play the fixed fresh candidate screen using the unmodified release source for all three policies."""
import argparse
import json
from pathlib import Path
import random

import numpy as np
import torch

from sammlung import RELEASE, ZIP_SHA, sha
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import _module_for, r3_package_agent


def run(directory):
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.fetch_kaggle3 import verify
    offline = json.loads((directory / "offline.json").read_text())
    if not offline["gate"] or sha(RELEASE) != ZIP_SHA or not verify():
        raise ValueError("Offline comparison or package verification failed")
    for arm, entry in offline["arms"].items():
        if sha(directory / f"{arm}.pth") != entry["sha256"]:
            raise ValueError(f"Changed {arm} checkpoint")
    _, source = _module_for(RELEASE.resolve())
    env = LuxAIS3GymEnv(numpy_output=True)
    raw = directory / "spiele.jsonl"
    total = {}
    with raw.open("x") as stream:
        for seed in range(19376300,19376308):
            for side in ("player_0","player_1"):
                other = "player_1" if side == "player_0" else "player_0"
                for opponent in ("solution92","kaggle3","v16"):
                    for arm in (("behandlung",) if opponent == "v16" else ("original","kontrolle","behandlung")):
                        random.seed(seed)
                        np.random.seed(seed)
                        torch.manual_seed(seed)
                        player = (r3_package_agent(side,RELEASE) if arm=="original" else
                                  source.Agent_x(side,agent_path=str(directory/f"{arm}.pth")))
                        player.set_to_eval_mode()
                        rival = r3_package_agent(other,RELEASE) if opponent=="v16" else make_opponent(opponent,other)
                        r = play_game(env,player,rival,seed,side,train=False)
                        require_no_agent_errors(player,rival)
                        if r["steps"]!=303 or r["our_wins"]+r["opp_wins"]!=3 or r["result"]!=int(r["our_wins"]>=2):
                            raise ValueError("Incomplete course game")
                        row = dict(seed=seed,side=side,opponent=opponent,arm=arm,**{k:r[k] for k in
                                   ("steps","result","our_wins","opp_wins","our_points","opp_points")})
                        stream.write(json.dumps(row)+"\n"); stream.flush()
                        d = total.setdefault(opponent,{}).setdefault(arm,dict(n=0,wins=0,matches=0))
                        d["n"] += 1
                        d["wins"] += r["result"]
                        d["matches"] += r["our_wins"]
                        print(seed,side,opponent,arm,r["result"],flush=True)
    env.close()
    if any(v["n"]!=16 for group in total.values() for v in group.values()):
        raise ValueError("Incomplete candidate panel")
    qualified = (all(total[o]["behandlung"]["wins"] >= max(total[o][a]["wins"] for a in ("original","kontrolle"))
                     for o in ("kaggle3","solution92"))
                 and total["kaggle3"]["behandlung"]["matches"] > total["kaggle3"]["original"]["matches"]
                 and total["v16"]["behandlung"]["wins"]>8)
    (directory/"spielergebnis.json").write_text(json.dumps(dict(counts=total,gate=qualified,rows_sha256=sha(raw)),indent=2)+"\n")


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory",type=Path)
    run(p.parse_args().directory)
