"""Rank first-relic routes by unique chances to see a node and step on a productive square."""
import numpy as np
from experiments.analysis.relictsuche_20261123.ortundflotte.richtung import score_options
from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import COORD,parameters
from experiments.analysis.relictsuche_20261123.nutzbarer_fund.ertrag import ZONE

WEIGHTS=np.array([0.,.5,1.5,3.])


def options(q,paths,last,fog,energy,origin,planned):
    existing=score_options(q,paths,last,fog,energy,origin)[2]
    prior,density=parameters()
    last_pair=np.maximum(last,last[::-1,::-1].T)[COORD[:,0],COORD[:,1]]
    novelty=np.where(last_pair<0,1.,.55*np.maximum(0,1-last_pair/50))
    mass=(prior/prior.mean()*novelty*density)@ZONE
    mass=np.where(planned.ravel(),.25*mass,mass)
    choices=np.vstack((paths,np.full((1,8),origin)))
    touched=np.zeros((len(choices),576))
    np.maximum.at(touched,(np.arange(len(choices))[:,None],choices),np.broadcast_to(.97**np.arange(1,9),choices.shape))
    return existing[None,:]+WEIGHTS[:,None]*(touched@mass)[None,:]
