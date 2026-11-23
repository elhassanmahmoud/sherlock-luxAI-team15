"""Weight a new view by both first relic frequency and predicted fleet coverage."""
import numpy as np
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import PAIR, XY
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import arrays, OFFSETS
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import parameters, COORD

EXPONENTS = (0.0, 0.5, 1.0)


def score_options(q,paths,last,fog,energy,origin):
    wait=np.full((1,paths.shape[1]),origin,np.int16)
    patterns=np.concatenate((paths,wait))
    idx,inside=arrays(patterns)
    head=np.all(OFFSETS==0,axis=-1)
    w=np.where(fog.ravel()[idx] & ~head[None,None],.25,1)
    w=w*inside*(.97**np.arange(1,paths.shape[1]+1))[None,:,None]
    pairs=np.zeros((len(patterns),576),np.float32)
    rows=np.broadcast_to(np.arange(len(patterns))[:,None,None],idx.shape)
    np.maximum.at(pairs,(rows.ravel(),PAIR[idx].ravel()),w.ravel())
    physical=q.ravel()
    mirror=(23-XY[:,1])*24+23-XY[:,0]
    fleet=np.where(np.arange(576)==mirror,physical,1-(1-physical)*(1-physical[mirror]))
    seen=np.maximum(last.ravel(),last.ravel()[mirror])
    fresh=np.where(seen<0,1.,.55*np.maximum(0,1-seen/50))
    prior,_=parameters()
    factor=np.ones(576)
    factor[COORD[:,0]*24+COORD[:,1]]=prior/np.mean(prior)
    costs=.08*np.sum(fog.ravel()[patterns],axis=1)+.025*np.maximum(0.,-energy.ravel()[patterns]).mean(1)
    return np.stack([pairs@(fresh*(1-fleet)*factor**alpha)-costs for alpha in EXPONENTS])


def take(scores):
    i=int(np.argmax(scores[:-1]))
    return i if scores[i]>=scores[-1]+1.0 else len(scores)-1
