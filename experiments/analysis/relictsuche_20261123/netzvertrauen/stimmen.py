"""Read both original V16 network votes on the actual legal scout choices; no second forward pass."""
import numpy as np

MIRROR=(0,2,1,4,3,5)
BASE=("turn","x_plus_y","diagonal","energy","fleet","enemies","move_cost","sap_cost","allies_near","old_stay","toward_far")
VOTES=("logadv_a","logadv_b","adv_gap","orig_a","orig_b","alt_a","alt_b","entropy_a","entropy_b",
       "max_a","max_b","agree","both_prefer_original","both_prefer_route","orig_is_best","route_is_best")
NAMES=BASE+VOTES


class Scores:
    def __init__(self,agent):
        self.player=agent
        self.logits=[None,None]
        core=agent._imitation
        models=[core.net,*core.extra_nets]
        assert len(models)==2
        for i,net in enumerate(models):
            initial=net.forward_all
            def capture(*args,_fn=initial,_i=i,**kw):
                result=_fn(*args,**kw)
                self.logits[_i]=result[0].detach().numpy().copy()
                return result
            net.forward_all=capture

    def values(self,t,world_old,world_new,uid,obs):
        b=self.player._imitation
        ctx,ids,f,mask,_,_,xy=b.last_fz
        k=list(ids).index(uid)
        legal=np.asarray(mask[k],bool).copy()
        if b.has_sap_head:
            legal[5]=ctx["ally_ene"][uid]>=ctx["sap_cost"]
        orig=MIRROR[world_old] if b.belief.mirrored else world_old
        route=MIRROR[world_new] if b.belief.mirrored else world_new
        assert 0<=orig<=4 and 1<=route<=4 and orig!=route and legal[route]
        # V16 may choose a final ruled move. A masked old direction gets the explicit probability zero.
        z=np.stack([log[k] for log in self.logits]).astype(float)
        assert z.shape==(2,6) and len(ids)==self.logits[0].shape[0]==self.logits[1].shape[0]
        z[:,~legal]=-np.inf
        pr=np.exp(z-z.max(axis=1,keepdims=True))
        pr/=pr.sum(axis=1,keepdims=True)
        rank=pr.argmax(1)
        old=pr[:,orig];alt=pr[:,route]
        gap=np.clip(np.log(np.maximum(alt,1e-10))-np.log(np.maximum(old,1e-10)),-10,10)
        h=-(pr*np.log(np.maximum(pr,1e-10))).sum(1)
        x,y=map(int,xy[k])
        distance=np.abs(xy-xy[k]).sum(1)
        ene=ctx["ally_ene"][uid]
        features=[t/100,(x+y)/46,abs(x-y)/23,ene/200,len(ids)/16,
            np.sum(obs["units_mask"][1-self.player.team_id])/16,ctx["move_cost"]/5,ctx["sap_cost"]/50,
            np.sum(distance<=3)/16,orig==0,route in (2,3),*gap,abs(gap[0]-gap[1]),
            *old,*alt,*h,*pr.max(1),rank[0]==rank[1],np.all(old>alt),np.all(alt>old),
            int(np.sum(pr,axis=0).argmax()==orig),int(np.sum(pr,axis=0).argmax()==route)]
        assert len(features)==len(NAMES) and np.isfinite(features).all()
        return list(map(float,features))
