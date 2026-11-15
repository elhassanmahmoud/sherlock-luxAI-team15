"""The two existing R3 views can only take over when their best legal classes agree."""
from collections import Counter
from pathlib import Path
import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.cnn_model import map_planes
from agents.sherlock.imitation_agent import sap_legal
from scripts.combat_teacher_counterfactual import native_order,substitute
from scripts.r3_diagonal import ACTIONS,FEATURES,DiagonalAgent,played_action


def scores(net,board,frame,pos,feats):
    normal=net.forward_all(board,frame,pos,feats)[0]
    flipped=net.forward_all(board.transpose(-1,-2).contiguous(),frame,pos[:,[1,0]],feats[:,FEATURES])[0][:,ACTIONS]
    return normal,flipped,(normal+flipped)*.5


def proposals(normal,flipped,mean,mask,base):
    # Each individual view is already back in the same canonical action order.
    choice=lambda logits:logits.masked_fill(~mask,-torch.inf).argmax(1)
    best=choice(mean)
    both=(choice(normal)==best)&(choice(flipped)==best)
    diagonal=played_action(mean,mask,base)
    return diagonal,torch.where(both,diagonal,base),both


class ViewConsensusAgent(DiagonalAgent):
    # Only the passive original observes opportunities without taking them.
    passive=False

    def _reset_episode_state(self):
        super()._reset_episode_state()
        self.consensus_counts=Counter()
        self.first_disagreement=None

    def _advise(self,step,obs,base):
        if self.training or int(obs["match_steps"])==0: return base
        ctx,cached,features,masks,_=self._decide(obs)
        ids=[u for u in cached if ctx["ally_ene"][u]>=0]
        if not ids: return base
        pos=torch.as_tensor(np.asarray(ctx["ally_pos"])[ids],dtype=torch.long)
        mask=sap_legal(np.stack([masks[u] for u in ids]),np.asarray(ctx["ally_ene"])[ids],ctx["sap_cost"])
        world=np.asarray(base)[ids,0].astype(np.int64)
        canon=np.asarray([geo.mirror_dir(d) if self.belief.mirrored and d!=geo.SAP else d for d in world])
        with torch.inference_mode():
            views=scores(self.members[0].net,torch.from_numpy(map_planes(ctx)[None]),
                         torch.zeros(len(ids),dtype=torch.long),pos,torch.from_numpy(np.stack([features[u] for u in ids])))
            parent,child,agree=proposals(*views,torch.from_numpy(mask),torch.from_numpy(canon))
        self.consensus_counts["live_rows"]+=len(ids)
        self.consensus_counts["different_best_views"]+=int((~agree).sum())
        available=torch.from_numpy(canon)!=parent
        veto=(parent!=child).tolist()
        self.consensus_counts["mean_changed_class"]+=int(available.sum())
        local=base.copy()
        for k in torch.where(available)[0].tolist():
            u=ids[k]
            a=int(parent[k])
            direction=geo.mirror_dir(a) if self.belief.mirrored else a
            order=np.array([direction,0,0],dtype=local.dtype)
            if veto[k]:
                self.consensus_counts["would_veto_proposed"]+=1
                actual=native_order(order,obs["units"]["position"][self.team_id][u],
                                    np.asarray(obs["units"]["energy"])[self.team_id].reshape(-1)[u],
                                    self.env_cfg,np.asarray(obs["map_features"]["tile_type"]))
                if actual:
                    self.consensus_counts["would_veto_executable"]+=1
                    if self.first_disagreement is None:
                        self.first_disagreement=dict(step=int(step),match_step=int(obs["match_steps"]),uid=int(u),
                             world_position=np.asarray(obs["units"]["position"])[self.team_id,u].tolist(),
                             v14=base[u].tolist(),diagonal=order.tolist(),legal=mask[k].tolist(),
                             legal_best=[int(x[k].masked_fill(~torch.from_numpy(mask[k]),-torch.inf).argmax()) for x in views])
                if not self.passive: continue
            local[u]=order
        return substitute(self,obs,base,local,"movement",self.selective_counts)


class ObservedDiagonalAgent(ViewConsensusAgent):
    passive=True
