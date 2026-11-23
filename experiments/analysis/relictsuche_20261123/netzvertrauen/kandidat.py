"""Decide once, at the first real scout deviation, between both fully tested command streams."""
from functools import lru_cache
import json
from pathlib import Path
import numpy as np

from experiments.analysis.relictsuche_20261123.flottenblick.kandidat import create as fleet
from experiments.analysis.relictsuche_20261123.netzvertrauen.stimmen import Scores,NAMES

HERE=Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def model():
    spec=json.loads((HERE/"modell.json").read_text())
    assert tuple(spec["features"])==NAMES
    return spec


class ScoutVote:
    def __init__(self,side,forced=None):
        self.scout=fleet(side)
        self.base=self.scout.base
        self.votes=Scores(self.base)
        self.forced=forced
        self.decision=None
        self.at=None
        self.features=None
        act=self.base.act
        def capture(*args,**kwargs):
            original=act(*args,**kwargs)
            if self.decision is None:
                self.raw=original.copy()
                p=self.base._imitation
                self.remembered=dict(p._prev_actions),dict(p._sap_hits)
            return original
        self.base.act=capture

    def __getattr__(self,k):
        return getattr(self.scout,k)

    def new_game(self,player=None):
        self.scout.new_game(player)
        self.decision=None
        self.at=self.features=None

    def act(self,step,obs):
        if self.decision is False:
            return self.base.act(step,obs)
        out=self.scout.act(step,obs)
        if not self.scout.changes or self.decision is not None:
            return out
        delta=np.flatnonzero(np.any(out!=self.raw,axis=1)).tolist()
        assert delta==[self.scout.uid] and self.scout.changes==1
        u=delta[0]
        x=self.votes.values(step,int(self.raw[u,0]),int(out[u,0]),u,obs)
        self.at=step
        self.features=x
        if self.forced is None:
            spec=model()
            w=spec["model"]
            value=((np.array(x)-w["center"])/w["scale"])@w["beta"]+w["bias"]
            self.decision=bool(value>=spec["threshold"])
        else:
            self.decision=bool(self.forced)
        if self.decision:
            return out
        p=self.base._imitation
        p._prev_actions,p._sap_hits=self.remembered
        p.param_est.record_played_actions(self.raw)
        self.scout.changes=0
        self.scout.done=True
        return self.raw


def create(side):
    return ScoutVote(side)
