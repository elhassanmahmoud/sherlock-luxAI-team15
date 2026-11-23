"""Empirical marginal sight of one scout and joint visibility of a symmetric relic pair."""
import json
from functools import lru_cache
from pathlib import Path
import numpy as np
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import PAIR,XY
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import arrays,OFFSETS
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import COORD,parameters

HERE=Path(__file__).resolve().parent
CELLS=np.arange(576)
MIRROR=24*(23-XY[:,1])+23-XY[:,0]
REP=CELLS[CELLS<=MIRROR]
HEAD=(OFFSETS==0).all(1)
AGE=np.arange(8)
SPAN=np.searchsorted([0,3,9,23],np.abs(XY-XY[MIRROR]).max(1))
DISTINCT=CELLS!=MIRROR


def groups(q,last,fog):
    p=q.ravel()
    b=np.minimum((8*p).astype(int),7)
    pair_id=(np.maximum(b,b[MIRROR])*8+np.minimum(b,b[MIRROR]))*4+SPAN
    pair_prior=np.where(DISTINCT,1-(1-p)*(1-p[MIRROR]),p)
    terrain=np.where(fog.ravel(),2,np.where(last.ravel()>=0,1,0))
    neighbor_id=(AGE[:,None]*3+terrain[None,:])*4+b//2
    prior=np.broadcast_to(np.where(fog.ravel(),.25,1.),(8,576))
    return pair_id,pair_prior,neighbor_id,prior


def estimate(q,last,fog,table):
    gid,old,near,oldnear=groups(q,last,fog)
    new=np.where(DISTINCT,np.clip(old+table['union'][gid],0,1),old)
    return (old,new),(oldnear,table['near'][near])


def scores(q,paths,last,fog,energy,origin,table):
    pairprobs,neighbors=estimate(q,last,fog,table)
    routes=np.vstack((paths,np.full((1,8),origin,int)))
    idx,inside=arrays(routes)
    rows=np.broadcast_to(np.arange(len(routes))[:,None,None],idx.shape)
    cols=PAIR[idx]
    oldseen=np.maximum(last.ravel(),last.ravel()[MIRROR])
    newval=np.where(oldseen<0,1.,.55*np.maximum(0.,1-oldseen/50.))
    prior=np.ones(576);loc,_=parameters();prior[24*COORD[:,0]+COORD[:,1]]=loc/loc.mean()
    cost=.08*np.sum(fog.ravel()[routes],axis=1)+.025*np.maximum(0.,-energy.ravel()[routes]).mean(1)
    output=[]
    banks=[]
    for neighbor in neighbors:
        view=np.where(HEAD[None,None,:],1.,neighbor[AGE[None,:,None],idx])
        view*=inside*(.97**np.arange(1,9))[None,:,None]
        visits=np.zeros((len(routes),576),np.float32)
        np.maximum.at(visits,(rows.ravel(),cols.ravel()),view.ravel())
        banks.append(visits)
    for ne,pa in ((0,0),(0,1),(1,0),(1,1)):
        output.append(banks[ne]@(newval*(1-pairprobs[pa])*prior)-cost)
    return np.stack(output)


@lru_cache(maxsize=1)
def learned():
    with np.load(HERE/'tabellen.npz') as d:return {k:d[k] for k in d.files}
