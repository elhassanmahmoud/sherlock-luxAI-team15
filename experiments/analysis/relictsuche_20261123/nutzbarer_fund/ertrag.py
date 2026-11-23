"""Estimate how much of a prospective first relic pair the current fleet can use."""
from functools import lru_cache
from pathlib import Path
import json
import numpy as np

from experiments.analysis.relictsuche_20261123.zielschaetzer.kandidat import COORD,PAIR_END

HERE=Path(__file__).resolve().parent
XY=np.indices((24,24)).reshape(2,-1).T
# A ship can score near either mirrored centre. Each physical tile enters at most once.
OFFSET=np.maximum(np.abs(PAIR_END[:,:,None,:]-XY[None,None,:,:])-2,0)
DIST=OFFSET.sum(3).min(1)
ZONE=DIST==0


def features(pos,walls,indices=None):
    index=slice(None) if indices is None else np.asarray(indices)
    distance=DIST[index][:,24*pos[:,0]+pos[:,1]]
    sorted_dist=np.sort(np.pad(distance,((0,0),(0,3)),constant_values=48),axis=1)[:,:3]
    zone=ZONE[index]
    return np.column_stack((sorted_dist,*(np.sum(distance<=d,axis=1) for d in (0,2,5,8)),
                            DIST[index,0],(zone@walls.astype(np.int32).ravel())/zone.sum(1)))


def forecast(x,m):
    raw=(np.asarray(x)-m["center"])/m["scale"]@np.asarray(m["weights"])+m["bias"]
    return np.expm1(np.clip(raw,0,np.log1p(16)))


@lru_cache(maxsize=1)
def model():
    return json.loads((HERE/"modell.json").read_bytes())


def value_weights(pos,walls):
    m=model()
    return np.clip((1+forecast(features(pos,walls),m))/(1+m["mean_points"]),.5,1.5)
