"""Replay the invariant pilot losses and measure specific late alternatives on the original seats."""
import gzip
import json
from pathlib import Path

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.abschlusspruefung.vergleich import Referee, make
from experiments.analysis.relictsuche_20261123.folgewahl.politik import Switch
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import create
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import MIRROR
from experiments.analysis.relictsuche_20261123.vergleich.spielen import write_once
from scripts.common import play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.scoring import point_tile_map

HERE=Path(__file__).resolve().parent


class Timeline(Referee):
    def __init__(self,env,team,actor,kind):
        super().__init__(env,team,actor,kind)
        self.new_points=[]

    def step(self,cmds):
        if self.label=="wissen":
            for e in self.subject.events[len(self.new_points):]:
                truth=point_tile_map(self.env.state)
                assert e["t"]==self.turn and all(truth[divmod(k,24)] for k in (e["world"],MIRROR[e["world"]]))
                self.new_points.append(e)
        return super().step(cmds)


def main():
    limit_threads()
    pilot=HERE.parent/"spielwert"
    cards=json.loads((pilot/"obergrenze.json").read_text())["pilot"]["comparisons"]["solution92"]["invariant_original_losses"]
    with gzip.open(pilot/"pilot_partien.jsonl.gz","rt") as f:
        anchors={r["seed"]:r for r in map(json.loads,f) if r["id"]=="b0" and r["opponent"]=="solution92" and not r["win"]}
    env=LuxAIS3GymEnv(numpy_output=True)
    records=[]
    try:
        for c in cards:
            seed,team=c["seed"],c["team"]
            side=f"player_{team}"
            anchor=anchors[seed]
            assert anchor["team"]==team and [m["win"] for m in anchor["matches"]]==[1,0,0]
            original=None
            for kind in ("v16","wissen","punktgrenzen","fehlmarkierung","wechsel"):
                if kind=="wissen":player=create(side)
                elif kind=="wechsel":player=Switch(side,forced=True)
                else:player=make(kind,side)
                foe=make("solution92",f"player_{1-team}")
                rec=Timeline(env,team,player,kind)
                r=play_game(rec,player,foe,seed,side,False)
                require_no_agent_errors(getattr(player,"base",player),foe)
                assert rec.turn==303 and int(sum(m["win"] for m in rec.matches)>=2)==r["game_win"]
                cmds=np.stack(rec.commands)
                if original is None:
                    assert rec.digest.hexdigest()==anchor["action_hash"] and rec.matches==anchor["matches"]
                    original=cmds.copy()
                diff=np.flatnonzero(np.any(original!=cmds,axis=(1,2,3)))
                events=rec.new_points if kind=="wissen" else rec.evidence
                if kind=="wechsel":
                    require_no_agent_errors(player.r3,foe)
                    assert player.chosen and not np.any(diff<101) and rec.matches[0]==anchor["matches"][0]
                elif kind!="v16" and len(diff):
                    assert events and diff[0]>=events[0]["t"]
                records.append(dict(seed=seed,team=team,kind=kind,first=int(diff[0]) if len(diff) else None,
                    changed=int(len(diff)),matches=rec.matches,win=r["game_win"],sight=rec.first_sight,
                    credit=rec.first_credit,hash=rec.digest.hexdigest(),events=events))
    finally:env.close()
    assert len(records)==10
    write_once(HERE/"ergebnis.json",dict(cards=cards,games=records))


if __name__=="__main__":main()
