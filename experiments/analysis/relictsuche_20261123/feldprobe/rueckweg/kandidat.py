"""Fieldprobe with one public veto for reversing the same ship's most recent move."""
import numpy as np

from experiments.analysis.relictsuche_20261123.feldprobe.kandidat import MIRROR, PACKAGE, Probe, columns
from experiments.analysis.relictsuche_20261123.feldprobe.signalmodell import DELTA, NAMES, options, pick
from scripts.r3_package import r3_package_agent

LOWER=[NAMES.index("recent_lower"),NAMES.index("ever_lower")]


def reverse_veto(uid,d,target,features,previous_pos,previous_alive,previous_codes,position,alive):
    if previous_pos is None or not(previous_alive[uid] and alive[uid]):
        return False
    old=int(previous_codes[uid])
    if not 1<=old<=4 or any(features[i]>0 for i in LOWER):
        return False
    return (tuple(previous_pos[uid])==tuple(target) and
            np.array_equal(previous_pos[uid]+DELTA[old],position[uid]) and
            np.array_equal(DELTA[old]+DELTA[d],(0,0)))


class ReturnProbe(Probe):
    def start(self):
        super().start()
        self.attempt=None
        self.previous_pos=None
        self.previous_alive=None
        self.previous_codes=None

    def act(self,step,obs):
        original=self.base.act(step,obs)
        if self.attempt is not None or int(self.base.env_cfg["unit_sensor_range"])!=1:
            return original
        team=self.base.team_id
        match,turn=divmod(step,101)
        board=self.base._imitation
        b=board.belief
        known=b.point_tiles[::-1,::-1].T if team else b.point_tiles
        tile=b.tile_type[::-1,::-1].T if team else b.tile_type
        pos=np.asarray(obs["units"]["position"][team])
        ene=np.asarray(obs["units"]["energy"][team]).reshape(-1)
        alive=np.asarray(obs["units_mask"][team],bool)&(ene>=0)
        score=int(obs["team_points"][team])
        self.history.relics(np.asarray(obs["relic_nodes"])[np.asarray(obs["relic_nodes_mask"],bool)])
        self.history.observe(turn,pos[alive],score-self.last_score if turn else 0,known)
        self.last_score=score
        last=(self.previous_pos,self.previous_alive,self.previous_codes)
        self.previous_pos=pos.copy()
        self.previous_alive=alive.copy()
        self.previous_codes=np.asarray(original[:,0]).copy()
        if board.last_fz is None or not(8<=turn<=84 and turn%4==0):
            return original
        _,ids,feat,masks,_,_,_=board.last_fz
        ids=np.asarray(ids,int)
        permitted=np.zeros((16,5),bool)
        busy=np.ones(16,bool)
        permitted[ids]=masks[:,:5][:,MIRROR] if team else masks[:,:5]
        pts,sap=columns()
        busy[ids]=(feat[:,pts].max(axis=1)>0)|(feat[:,sap]>0)
        choices=options(self.history,turn,match+1,team,pos,ene,alive,known,tile,original,permitted,busy,self.base.env_cfg["unit_move_cost"])
        index=pick(choices,self.model)
        if index is None:return original
        u,d,xy,ref,inputs,_=choices[index]
        event=dict(t=int(step),u=u,d=d,xy=list(xy),ref=list(ref),old=int(original[u,0]),
                   known_empty=bool(b.dead_tiles[23-xy[1],23-xy[0]] if team else b.dead_tiles[xy]))
        veto=reverse_veto(u,d,xy,inputs,*last,pos,alive)
        self.attempt=dict(event=event,veto=bool(veto),prior_position=last[0][u].tolist(),current_position=pos[u].tolist(),
                          last_command=int(last[2][u]),last_alive=bool(last[1][u]),bounds=[float(inputs[i]) for i in LOWER])
        if veto:
            return original
        self.event=event
        out=original.copy()
        out[u]=[d,0,0]
        board._prev_actions[u]=int(MIRROR[d]) if team else d
        board._sap_hits.pop(u,None)
        board.param_est.record_played_actions(out)
        self.changes=1
        return out


def create(side):
    return ReturnProbe(r3_package_agent(side,PACKAGE))
