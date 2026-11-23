"""One legally reachable uncertain field chosen from public evidence; V16 controls all remaining actions."""
from functools import lru_cache
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.feldprobe.signalmodell import Evidence,DELTA,options,parameters,pick
from scripts.r3_package import r3_package_agent

PACKAGE=Path(__file__).resolve().parents[4]/"experiments/releases/20261117_sherlock_v16/agent.zip"
MIRROR=np.array([0,2,1,4,3])


@lru_cache(maxsize=1)
def columns():
    from sherlock.features import FEATURE_NAMES
    return [FEATURE_NAMES.index(n+"_point") for n in "curdl"],FEATURE_NAMES.index("enemies_in_sap")


class Probe:
    def __init__(self,base):
        self.base=base
        self.model=parameters()
        self.start()

    def __getattr__(self,key):
        return getattr(self.base,key)

    def start(self):
        self.history=Evidence()
        self.last_score=0
        self.event=None
        self.changes=0

    def new_game(self,player=None):
        self.base.new_game(player)
        self.start()

    def set_env_cfg(self,cfg):
        self.base.set_env_cfg(cfg)

    def act(self,step,obs):
        original=self.base.act(step,obs)
        if self.changes or int(self.base.env_cfg["unit_sensor_range"])!=1:
            return original
        team=self.base.team_id
        match,turn=divmod(step,101)
        board=self.base._imitation
        b=board.belief
        known=b.point_tiles[::-1,::-1].T if team else b.point_tiles
        tile=b.tile_type[::-1,::-1].T if team else b.tile_type
        loc=np.asarray(obs["units"]["position"][team])
        ene=np.asarray(obs["units"]["energy"][team]).reshape(-1)
        alive=np.asarray(obs["units_mask"][team],bool)&(ene>=0)
        score=int(obs["team_points"][team])
        self.history.relics(np.asarray(obs["relic_nodes"])[np.asarray(obs["relic_nodes_mask"],bool)])
        self.history.observe(turn,loc[alive],score-self.last_score if turn else 0,known)
        self.last_score=score
        if board.last_fz is None or not(8<=turn<=84 and turn%4==0):
            return original
        _,ids,feat,masks,_,_,_=board.last_fz
        ids=np.asarray(ids,int)
        permitted=np.zeros((16,5),bool)
        busy=np.ones(16,bool)
        permitted[ids]=masks[:,:5][:,MIRROR] if team else masks[:,:5]
        pts,sap=columns()
        busy[ids]=(feat[:,pts].max(axis=1)>0)|(feat[:,sap]>0)
        choices=options(self.history,turn,match+1,team,loc,ene,alive,known,tile,original,permitted,busy,self.base.env_cfg["unit_move_cost"])
        index=pick(choices,self.model)
        if index is None:
            return original
        u,d,xy,ref,_,_=choices[index]
        self.event=dict(t=int(step),u=u,d=d,xy=list(xy),ref=list(ref),old=int(original[u,0]),
                        known_empty=bool(b.dead_tiles[23-xy[1],23-xy[0]] if team else b.dead_tiles[xy]))
        out=original.copy()
        out[u]=[d,0,0]
        board._prev_actions[u]=int(MIRROR[d]) if team else d
        board._sap_hits.pop(u,None)
        board.param_est.record_played_actions(out)
        self.changes=1
        return out


def create(side):
    return Probe(r3_package_agent(side,PACKAGE))
