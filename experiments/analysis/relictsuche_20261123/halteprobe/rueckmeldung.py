"""Post-entry score attribution with one public scoring bit per mirror orbit and distinct physical occupations."""
from collections import Counter
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
XY=np.indices((24,24),dtype=np.int16).reshape(2,-1).T
MIR=(23-XY[:,1])*24+23-XY[:,0];ORB=np.minimum(np.arange(576),MIR);D=np.array([(0,0),(0,-1),(1,0),(0,1),(-1,0)],np.int16)
NEIGH=np.full((576,5),-1,np.int16)
for action,delta in enumerate(D):
    p=XY+delta;valid=(p>=0).all(1)&(p<24).all(1);NEIGH[valid,action]=p[valid,0]*24+p[valid,1]
STATIC=('target_known_zone','target_overlap','alternative_known_zone','alternative_overlap','target_center_distance','alternative_center_distance','target_last_fraction','alt_last_fraction','target_prior_observations','alt_prior_observations','target_axis','target_home_distance','target_nebula','alternative_nebula','phase','clock','energy','alternative_already_covered','study_target_multiplicity')
FEEDBACK=('gain','previous_gain','residual','unknown_count','residual_fraction','delta_gain','delta_residual','new_unknown_orbits','departed_unknown_orbits','one_eq_target','joint_target','joint_alt','joint_advantage','certain_now','ruled_out_now','using_previous','gain_consistent')

def world(board,team):return np.asarray(board[::-1,::-1].T if team else board)
def flat(xy):return int(xy[0]*24+xy[1])

def weights(cells,known):
    own=np.unique(cells); fixed=known[own];ids,cnt=np.unique(ORB[own[~fixed]],return_counts=True)
    return dict(zip(map(int,ids),map(int,cnt),strict=True)),int(fixed.sum())

def conditional(prev,now,gprev,gcurrent,targets):
    """Joint score likelihood under a fixed 20-percent prior. Impossible soft assumptions trigger a marginal fallback."""
    prior=.2;chosen=list(dict.fromkeys(targets));out={}
    if min(gprev,gcurrent)<0 or gprev>sum(prev.values()) or gcurrent>sum(now.values()):return {k:prior for k in chosen},False
    vars=set(prev)|set(now)
    for key in chosen:
        if key not in vars:out[key]=prior;continue
        dp=np.zeros((gprev+1,gcurrent+1),float);dp[0,0]=1.
        for q in vars-{key}:
            a=prev.get(q,0);b=now.get(q,0);shift=dp[:gprev-a+1,:gcurrent-b+1]*prior if a<=gprev and b<=gcurrent else None
            dp*=1-prior
            if shift is not None:dp[a:,b:]+=shift
        w0=(1-prior)*dp[gprev,gcurrent];a=prev.get(key,0);b=now.get(key,0)
        w1=prior*dp[gprev-a,gcurrent-b] if a<=gprev and b<=gcurrent else 0.
        if w0+w1<1.e-24:return {k:prior for k in chosen},False
        out[key]=w1/(w0+w1)
    return out,True

class History:
    def __init__(self,team):
        self.team=team;self.old=None;self.now=None;self.previous_score=0;self.n=np.zeros(576,int);self.total=np.zeros(576,float)
        self.zone=np.zeros(576,int);self.distance=np.full(576,24,int);self.centres=set();self.stable=False
    def update(self,t,o,known):
        ms=t%101; self.old=self.now
        if self.old and self.old['ms']:
            r=self.old['res'];u=sum(self.old['weights'].values())
            if 0<=r<=u and u:
                keys=list(self.old['weights']);self.n[keys]+=1;self.total[keys]+=r/u
        if ms==0:self.stable=False
        for p in np.asarray(o['relic_nodes'])[np.asarray(o['relic_nodes_mask'],bool)]:
            for v in (tuple(map(int,p)),tuple(map(int,23-p[::-1]))):
                if v not in self.centres:
                    self.centres.add(v);dist=np.max(np.abs(XY-v),axis=1);self.distance=np.minimum(self.distance,dist);self.zone+=(dist<=2)
        self.stable|=ms>=50 or bool(np.asarray(o['relic_nodes_mask'])[[t//101,t//101+3]].any())
        pos=np.asarray(o['units']['position'])[self.team];ene=np.asarray(o['units']['energy'])[self.team].reshape(-1);ids=np.flatnonzero(np.asarray(o['units_mask'][self.team],bool)&(ene>=0));cells=24*pos[ids,0]+pos[ids,1]
        board=np.asarray(known,bool).ravel();key,count=weights(cells,board);score=int(o['team_points'][self.team]);gain=score-self.previous_score if ms else 0;self.previous_score=score
        self.now={'t':t,'ms':ms,'gain':gain,'res':gain-count,'weights':key,'own':np.unique(cells),'ids':ids,'pos':pos,'en':ene,'cells':cells,'stable':self.stable,'board':board}
    def features(self,target,alternative,energy,terrain,peer_alternative):
        old,cur=self.old,self.now;t=cur['t'];ct=ORB[target];ca=ORB[alternative];m=cur['weights'];r=cur['res'];u=sum(m.values());prev,past_score=weights(old['own'],cur['board']);r_old=old['gain']-past_score
        one,valid=conditional({},m,0,r,[ct,ca]);joint,ok=(conditional(prev,m,r_old,r,[ct,ca]) if old['stable'] and old['ms'] else (one,False))
        if not ok:joint=one
        prior=lambda k:(self.total[k]+.8)/(self.n[k]+4)
        x,y=XY[target];home=(x+y if self.team==0 else 46-x-y)/46
        tr=np.asarray(terrain).ravel()
        static=[int(self.zone[target]>0),min(3,self.zone[target])/3,int(self.zone[alternative]>0),min(3,self.zone[alternative])/3,
             min(8,self.distance[target])/8,min(8,self.distance[alternative])/8,prior(ct),prior(ca),np.log1p(self.n[ct])/4,np.log1p(self.n[ca])/4,
             abs(int(x+y)-23)/23,home,tr[target]==1,tr[alternative]==1,(t//101)/2,cur['ms']/100,min(300,energy)/200,peer_alternative,m.get(ct,0)/2]
        post=[cur['gain']/12,old['gain']/12,r/8,u/12,r/max(u,1),(cur['gain']-old['gain'])/4,(r-r_old)/4,
             len(m.keys()-prev.keys())/8,len(prev.keys()-m.keys())/8,one[ct],joint[ct],joint[ca],joint[ct]-joint[ca],
             int(valid and joint[ct]>=1-1.e-8),int(valid and joint[ct]<=1.e-8),int(ok),int(valid)]
        return np.asarray(static+post,np.float32)

def frame_now(o,team,known,terrain,cmd,mask,cfg,assigned=None):
    pos=np.asarray(o['units']['position'])[team];energy=np.asarray(o['units']['energy'])[team].reshape(-1);live=np.asarray(o['units_mask'][team],bool)&(energy>=0)
    ids=np.flatnonzero(live);c0=24*pos[ids,0]+pos[ids,1];acts=np.asarray(cmd)[ids,0];base=NEIGH[c0,np.where(acts<=4,acts,0)];tile=np.asarray(terrain).ravel();base=np.where((base<0)|(tile[np.maximum(base,0)]==2),c0,base)
    em=np.asarray(o['units_mask'][1-team],bool);enemy=np.asarray(o['units']['position'])[1-team,em];return {'ids':ids,'cells':c0,'dest':base,'uid_pos':pos,'cmd':np.asarray(cmd)[:,0],'known':np.asarray(known,bool).ravel(),'terrain':tile,'enemy':enemy,'en':energy,'mask':mask,'cfg':cfg,'assigned':assigned or {}}

def eligible(frame,uid,target):
    ids=frame['ids'];k=np.flatnonzero(ids==uid)
    if len(k)!=1:return None
    i=k.item();src=int(frame['cells'][i]);dst=int(frame['dest'][i]);move=int(frame['cmd'][uid]);cfg=frame['cfg'];xy=XY[src];enemy=frame['enemy'];goal=frame['assigned'].get(uid)
    if src!=target or not 1<=move<=4 or src==dst or frame['en'][uid]<max(30,4*int(cfg['unit_move_cost'])) or not frame['mask'][uid,0] or not frame['mask'][uid,move]:return None
    if frame['known'][src] or frame['known'][dst] or src in frame['cells'][ids!=uid] or src in frame['dest'][ids!=uid]:return None
    if len(enemy) and (np.abs(enemy-xy).max(1)<=int(cfg['unit_sap_range'])).any():return None
    if goal is not None and frame['known'][goal] and np.abs(XY[goal]-xy).sum()<=3 and np.abs(XY[goal]-XY[dst]).sum()<np.abs(XY[goal]-xy).sum():return None
    return dst, bool(dst in frame['dest'][ids!=uid])
