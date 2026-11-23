"""Force the two ends of the gated policy on recorded positive cases and verify both complete game action streams."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.netzvertrauen.kandidat import ScoutVote
from experiments.analysis.relictsuche_20261123.netzvertrauen.erheben import HERE,PACKAGE
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,write_once
from scripts.common import make_opponent,play_game
from scripts.r3_package import r3_package_agent
from scripts.par_eval import require_no_agent_errors
from scripts.experiment import limit_threads


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    a=p.parse_args()
    rows=[r for f in sorted((a.folder/"karten").glob("*.json")) for r in json.loads(f.read_text())["comparisons"]]
    # Use equality checks only. No win or net-score values enter the selection.
    cases=[next(r for r in rows if r["team"]==s and r["opponent"]==o and r["event"])
           for s in (0,1) for o in ("solution92","v16")]
    env=LuxAIS3GymEnv(numpy_output=True)
    checked=[]
    limit_threads()
    try:
        for r in cases:
            side=f"player_{r['team']}"
            opp=f"player_{1-r['team']}"
            for allow in (False,True):
                torch.manual_seed(r["seed"])
                actor=ScoutVote(side,allow)
                rival=make_opponent("solution92",opp) if r["opponent"]=="solution92" else r3_package_agent(opp,PACKAGE)
                monitor=Monitor(env,r["team"],"discovery")
                raw=play_game(monitor,actor,rival,r["seed"],side,False)
                require_no_agent_errors(actor.base,rival)
                assert actor.decision is allow and actor.at==r["event"][0][0]
                assert np.allclose(actor.features,r["features"],atol=1e-7,rtol=1e-7)
                ref=r["candidate"] if allow else r["base"]
                assert raw["game_win"]==ref["win"] and monitor.matches==ref["matches"] and monitor.digest.hexdigest()==ref["action_hash"]
                checked.append(dict(seed=r["seed"],team=r["team"],opponent=r["opponent"],allow=allow,
                                    t=actor.at,hash=ref["action_hash"],turns=monitor.turn))
    finally:
        env.close()
    write_once(HERE/"technik.json",checked)


if __name__=="__main__":
    main()
