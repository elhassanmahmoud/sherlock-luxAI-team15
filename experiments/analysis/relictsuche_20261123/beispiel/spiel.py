"""Reproduce and remove the first additional piece of information in the single newly won pilot seat."""
from collections import Counter
import gzip
import json
from pathlib import Path

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import Knowledge
from experiments.analysis.relictsuche_20261123.punktwissen.spiele import PACKAGE, Tape, decoded, paired
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import MIRROR, indices
from experiments.analysis.relictsuche_20261123.vergleich.spielen import write_once
from scripts.common import make_opponent, play_game
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.experiment import limit_threads
from scripts.scoring import match_points_after_step

HERE=Path(__file__).resolve().parent


class SelectProof(Knowledge):
    def reset(self):
        super().reset()
        self.first=None
        self.public=[]
        self.explanations=[]

    def remember(self,t,obs):
        team=self.base.team_id
        match,turn=divmod(t,101)
        pos=np.asarray(obs["units"]["position"][team])
        live=np.asarray(obs["units_mask"][team],bool)&(np.asarray(obs["units"]["energy"][team]).reshape(-1)>=0)
        obsrow=dict(step=t,ms=turn,points=int(obs["team_points"][team]), occupied=sorted({int(x)*24+int(y) for x,y in pos[live]}),
                    epoch_seen=bool(np.asarray(obs["relic_nodes_mask"])[[match,match+3]].any()))
        self.public.append(obsrow)
        newly=self.proof.observe(obsrow)
        belief=self.base._imitation.belief
        belief.observe(obs)
        accepted=[]
        for world in newly:
            cell=MIRROR[world] if belief.mirrored else world
            if cell in belief._point: continue
            if self.first is None:self.first=world
            if (self.mode=="only_first" and world!=self.first) or (self.mode=="without_first" and world==self.first):
                continue
            accepted.append((world,cell,cell in belief._dead or belief._mirror_idx(cell) in belief._dead))
        if any(was_dead for _,_,was_dead in accepted):belief.records.clear()
        for world,cell,was_dead in accepted:
            belief._mark_point(cell)
            self.events.append(dict(t=t,world=world,was_dead=bool(was_dead)))
            proof=self.proof.proofs[world]
            witnesses=[]
            for tick in (proof["lo"],proof["hi"]):
                if tick is not None:
                    assert self.public[tick]["ms"]
                    q=self.public[tick]
                    witnesses.append(dict(t=tick,income=q["points"]-self.public[tick-1]["points"],occupied=q["occupied"]))
            self.explanations.append(dict(t=t,world=world,mirror=MIRROR[world],witnesses=witnesses,logical_bound=proof))
        if accepted:belief._refresh_candidates()


class Timeline(Tape):
    def __init__(self,env,team,actor):
        super().__init__(env,team,actor)
        self.score=[]
        self.before=[]

    def step(self,cmd):
        before=self.old
        own=self.team
        self.before.append(dict(t=self.turn,pos=np.asarray(before["units"]["position"][own]).tolist()))
        out=super().step(cmd)
        totals=match_points_after_step(before,out[0][self.side],out[4])
        self.score.append([int(totals[own]),int(totals[1-own])])
        return out


def main():
    limit_threads()
    with gzip.open(HERE.parent/"punktwissen/partien.jsonl.gz","rt") as f:
        rx={(r["seed"],r["team"],r["version"]):r for r in map(json.loads,f) if r["opponent"]=="solution92"}
    changes=[(s,t) for s,t,a in rx if a=="neu" and rx[s,t,a]["win"]!=rx[s,t,"v16"]["win"]]
    assert len(changes)==1
    s,team=changes[0]
    base,cand=[rx[s,team,arm] for arm in ("v16","neu")]
    assert cand["win"]-base["win"]==1
    first=paired(base,cand)
    env=LuxAIS3GymEnv(numpy_output=True)
    results={}
    full={}
    try:
        for mode in ("original","all","only_first","without_first"):
            torch.manual_seed(s)
            side=f"player_{team}"; other=f"player_{1-team}"
            rival=make_opponent("solution92",other)
            orig=r3_package_agent(side,PACKAGE)
            if mode=="original":actor=orig
            else:
                actor=SelectProof(orig)
                actor.mode=mode
            tape=Timeline(env,team,actor if mode!="original" else None)
            game=play_game(tape,actor,rival,s,side,False)
            require_no_agent_errors(orig,rival)
            assert tape.turn==303 and game["our_wins"]==sum(m["win"] for m in tape.matches)
            actual=np.asarray(tape.commands)
            if mode in ("original","all"):
                anchor=base if mode=="original" else cand
                assert tape.digest.hexdigest()==anchor["digest"] and tape.matches==anchor["matches"] and np.array_equal(actual,decoded(anchor))
                if mode=="all": assert actor.events==anchor["events"]
            events=[] if mode=="original" else actor.events
            explanations=[] if mode=="original" else actor.explanations
            delta=np.flatnonzero(np.any(actual!=decoded(base),axis=(1,2,3)))
            start=int(delta[0]) if len(delta) else None
            shifted=[]
            if start is not None:
                for uid in np.flatnonzero(np.any(actual[start,team]!=decoded(base)[start,team],axis=1)):
                    shifted.append(dict(uid=int(uid),field=tape.before[start]["pos"][uid],
                        old=decoded(base)[start,team,uid].tolist(),new=actual[start,team,uid].tolist()))
            if mode=="all":assert start==first
            results[mode]=dict(matches=tape.matches,hash=tape.digest.hexdigest(),win=game["game_win"],
                first_changed=start,commands=shifted,events=events,proofs=explanations)
            full[mode]=tape.score
    finally: env.close()
    write_once(HERE/"verlaeufe.json",dict(seed=s,team=team,groups=results,points=full))


if __name__=="__main__":
    main()
