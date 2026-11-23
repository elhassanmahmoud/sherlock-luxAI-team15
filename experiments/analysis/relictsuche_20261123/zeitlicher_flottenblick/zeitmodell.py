"""Public cumulative other-fleet sight and expected early relic discovery along one route."""
import numpy as np
from experiments.analysis.relictsuche_20261123.flottenblick.flotte import PAIR,XY
from experiments.analysis.relictsuche_20261123.flottenblick.vorhersage import arrays,OFFSETS
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import COORD,parameters

HORIZON=8
GROUPS=8*6*6
MIRROR=(23-XY[:,1])*24+23-XY[:,0]


def bins(q,dist):
    bucket=np.minimum((8*q).astype(int),7)
    return (bucket*6+np.minimum(dist[0].astype(int),5))*6+np.minimum(dist[1].astype(int),5)


def cumulative(q,dist,table):
    profiles=np.asarray(table)[bins(q,dist)]
    return (profiles*q[...,None]).reshape(576,HORIZON).T


def scores(timewise, paths, last, fog, energy, origin, turn):
    patterns=np.vstack((paths,np.full((1,HORIZON),origin,np.int16)))
    fields,inside=arrays(patterns)
    centre=np.all(OFFSETS==0,axis=1)
    visibility=np.where(fog.ravel()[fields] & ~centre,.25,1.)*inside
    seen=np.maximum(last.ravel(),last.ravel()[MIRROR]).clip(0,50)
    other=1-(1-timewise)*(1-timewise[:,MIRROR])
    on_axis=MIRROR==np.arange(576)
    other[:,on_axis]=timewise[:,on_axis]
    mass=np.zeros(576)
    prior,_=parameters()
    mass[24*COORD[:,0]+COORD[:,1]]=prior/prior.mean()
    covered=np.zeros((len(patterns),576))
    rows=np.arange(len(patterns))[:,None]
    total=np.zeros(len(patterns))
    for j in range(HORIZON):
        code=PAIR[fields[:,j]]
        activation=np.maximum(0,min(50,turn+j+1)-seen[code])/min(50,turn+HORIZON)
        np.maximum.at(covered,(rows,code),visibility[:,j]*activation)
        total+=covered@(mass*(1-other[j]))
    cost=.08*fog.ravel()[patterns].sum(1)+.025*np.maximum(0.,-energy.ravel()[patterns]).mean(1)
    return total/HORIZON-cost
