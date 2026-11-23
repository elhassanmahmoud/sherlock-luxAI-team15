"""Select a complete native policy once, after the same public V16 opening."""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np

from experiments.analysis.relictsuche_20261123.r3_folge.berater import feedback, r3_player
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import PACKAGE
from scripts.r3_package import r3_package_agent

HERE=Path(__file__).resolve().parent
NAMES=("points_early","other_early","points_mid","other_mid","points_late","other_late","sight","credit",
       "enemy_presence","enemy_stationary","own_energy","other_energy","known_fraction","known_points",
       "move_cost","sap_range","own_count","enemy_count","empty_views","own_late_stays","own_late_shots")


def immutable_observation(raw):
    return {k:({n:np.array(a,copy=True) for n,a in v.items()} if isinstance(v,dict) else np.array(v,copy=True)) for k,v in raw.items()}


@lru_cache(maxsize=1)
def weights():
    spec=json.loads((HERE/"modell.json").read_text())
    assert tuple(spec["names"])==NAMES
    return spec


class Switch:
    def __init__(self,side,forced=None):
        self.base=r3_package_agent(side,PACKAGE)
        self.forced=forced
        self.new_game(side)

    def __getattr__(self,name):
        return getattr(self.base,name)

    def new_game(self,side=None):
        self.side=side or self.side
        self.base.new_game(self.side)
        self.history=[]
        self.r3=None
        self.features=None
        self.chosen=False
        self.original_chronology=None

    def set_env_cfg(self,cfg):
        self.cfg=cfg
        self.base.set_env_cfg(cfg)

    def context(self):
        team=self.base.team_id
        other=1-team
        assert len(self.history)==101
        observations=[r[0] for r in self.history]
        actions=[r[1] for r in self.history]
        points=np.array([p["team_points"] for p in observations])[:,[team,other]]
        gain=np.diff(points,axis=0,prepend=points[:1])
        sight=next((i for i,o in enumerate(observations) if np.asarray(o["relic_nodes_mask"]).any()),101)
        credit=next((int(i) for i in np.flatnonzero(points[:,0]>0)),101)
        # Use only consecutive sightings of the same opponent identity when measuring standstill.
        contacts=moving=seen=hidden=0
        ours=[];theirs=[];own_counts=[];enemy_counts=[]
        waits=shots=active=0
        for t,o in enumerate(observations):
            live=np.asarray(o["units_mask"],bool)&(np.asarray(o["units"]["energy"]).reshape(2,16)>=0)
            seen+=int(live[other].sum())
            hidden+=not live[other].any()
            if t:
                pred=observations[t-1]
                prev=np.asarray(pred["units_mask"],bool)&(np.asarray(pred["units"]["energy"]).reshape(2,16)>=0)
                both=prev[other]&live[other]
                equal=(np.asarray(pred["units"]["position"])[other]==np.asarray(o["units"]["position"])[other]).all(1)
                contacts+=int(both.sum())
                moving+=int((both&equal).sum())
            if t>=65:
                energy=np.asarray(o["units"]["energy"]).reshape(2,16)
                ours.extend(energy[team,live[team]].tolist())
                theirs.extend(energy[other,live[other]].tolist())
                own_counts.append(int(live[team].sum()))
                enemy_counts.append(int(live[other].sum()))
                plays=actions[t][live[team],0]
                waits+=int(np.sum(plays==0));shots+=int(np.sum(plays==5));active+=len(plays)
        b=self.base._imitation.belief
        union=np.logical_or.reduce([o["sensor_mask"] for o in observations])
        values=[*gain[:36].sum(0),*gain[36:71].sum(0),*gain[71:].sum(0),sight,credit,seen/101,moving/max(1,contacts),
            np.mean(ours) if ours else 0,np.mean(theirs) if theirs else 0,union.mean(),b.point_tiles.sum(),
            self.cfg["unit_move_cost"],self.cfg["unit_sap_range"],np.mean(own_counts),np.mean(enemy_counts),hidden/101,
            waits/max(1,active),shots/max(1,active)]
        assert len(values)==len(NAMES) and np.isfinite(values).all()
        return [float(x) for x in values]

    def act(self,step,obs):
        if int(self.cfg["unit_sensor_range"])!=1:
            return self.base.act(step,obs)
        if step<101:
            cmd=self.base.act(step,obs)
            self.history.append((immutable_observation(obs),cmd.copy()))
            return cmd
        if step==101:
            self.features=self.context()
            eligible=bool(obs["team_wins"][self.base.team_id])
            if self.forced is None and eligible:
                model=weights()
                x=(np.array(self.features)-model["center"])/model["scale"]
                allowed=bool(x@model["beta"]+model["bias"]>=model["threshold"])
            else:allowed=bool(self.forced)
            self.chosen=eligible and allowed
            if self.chosen:
                self.r3=r3_player(self.side)
                self.r3.new_game(self.side)
                self.r3.set_env_cfg(self.cfg)
                for t,(original_obs,played) in enumerate(self.history):
                    suggested=self.r3.act(t,original_obs)
                    feedback(self.r3,original_obs,suggested,played)
            self.history.clear()
        return self.r3.act(step,obs) if self.chosen else self.base.act(step,obs)
