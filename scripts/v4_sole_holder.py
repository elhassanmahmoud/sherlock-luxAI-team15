"""Narrow post-routing experiment for the original v4 mixed hybrid, using public information only."""
from collections import Counter
import numpy as np

from agents.sherlock.geometry import mirror_xy
from agents.sherlock.hybrid_agent import HybridAgent
from scripts.r3_solution_retrace import endpoint


def occupancy(obs,team):
    pos=np.asarray(obs["units"]["position"])[team]
    energy=np.asarray(obs["units"]["energy"])[team].reshape(-1)
    ids=np.flatnonzero(np.asarray(obs["units_mask"])[team] & (energy>=0)).tolist()
    return pos,energy,ids


def choose(obs,team,ctx,known,routed,v14,student,baseline,cost,guard):
    """Final commands and observations of possible point-holder handovers; all endpoints are world coordinates."""
    pos,energy,ids=occupancy(obs,team)
    tiles=np.asarray(obs["map_features"]["tile_type"])
    current=Counter(tuple(map(int,pos[u])) for u in ids)
    def dest(uid,command):
        return endpoint(command,pos[uid],energy[uid],cost,tiles)
    ends={u:dest(u,baseline[u]) for u in ids}
    projected=Counter(ends.values())
    enemies=np.asarray(ctx["enemy_coords"]).reshape(-1,2)
    records=[]
    candidates={}
    for u in ids:
        here=tuple(map(int,pos[u]))
        canon=tuple(map(int,ctx["ally_pos"][u]))
        if canon!=(mirror_xy(*here,*tiles.shape) if team else here):
            raise ValueError("Hybrid/public unit coordinate mismatch")
        if not known[canon] or ctx["first_on_tile"].get(canon)!=u:
            continue
        near=bool(len(enemies) and (np.abs(enemies-np.asarray(canon)).max(axis=1)<=5).any())
        ve,se=dest(u,v14[u]),dest(u,student[u])
        if not near or np.array_equal(v14[u],student[u]):
            continue
        alone=current[here]==1
        possible=alone and routed[u] and ve==here and se!=here and ends[u]==se
        rec=dict(uid=u,world=list(here),canonical=list(canon),occupants=current[here],v14=v14[u].tolist(),
                 student=student[u].tolist(),v14_end=list(ve),student_end=list(se),student_chosen=bool(routed[u]),
                 other_planned_before=projected[here]-int(ends[u]==here),can_hold=possible,eligible=False,
                 restored=False,energy=int(energy[u]),tile_confirmed=True,enemy_within_five=True)
        records.append(rec)
        if possible:
            candidates[u]=rec
    # Start with all mixed destinations. Reclaim only uncovered original tiles. A newly
    # retained unit can cease to be the projected replacement on another original tile.
    result=baseline.copy()
    while candidates:
        found=False
        for u,rec in list(candidates.items()):
            here=tuple(rec["world"])
            if projected[here]:
                continue
            rec["eligible"]=True
            del candidates[u]
            if guard:
                projected[ends[u]]-=1
                projected[here]+=1
                ends[u]=here
                result[u]=v14[u]
                rec["restored"]=True
                found=True
        if not found:
            break
    for r in records:
        u=r["uid"]
        origin=tuple(r["world"])
        r.update(final=result[u].tolist(),planned_end=list(ends[u]),
                 other_planned_final=projected[origin]-int(ends[u]==origin))
        if r["restored"] and r["other_planned_final"]!=0:
            raise AssertionError("Unexpected replacement at retained holder tile")
    return result,records


class ObservedHybrid(HybridAgent):
    """The baseline first executes the unmodified parent's act; taps only copy already returned tensors."""
    def __init__(self,*args,guard=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.guard=guard
        self.raw={}
        for label,actor in (("v14",self.v14),("student",self.student)):
            original=actor.act
            def record(*arg,_fn=original,_name=label,**kw):
                out=_fn(*arg,**kw)
                self.raw[_name]=np.array(out,copy=True)
                return out
            actor.act=record

    def _use_student(self,ctx,belief,uid,student_action):
        picked=super()._use_student(ctx,belief,uid,student_action)
        self.routing[uid]=picked
        return picked

    def act(self,step,obs):
        self.routing={}
        out=super().act(step,obs)
        self.events=[]
        ctx=self.v14._prev_ctx
        if ctx is not None:
            final,self.events=choose(obs,self.v14.team_id,ctx,self.v14.belief.point_tiles,self.routing,
                                     self.raw["v14"],self.raw["student"],out,self.v14.env_cfg["unit_move_cost"],self.guard)
            if self.guard and any(r["restored"] for r in self.events):
                self.v14.param_est.record_played_actions(final)
                return final
        return out
