"""Public per-player limits on score from known relic areas under fog of war."""
import numpy as np


def occupied(obs, team):
    ids = np.asarray(obs["units_mask"][team],bool) & (np.asarray(obs["units"]["energy"])[team].reshape(-1)>=0)
    pos = np.asarray(obs["units"]["position"])[team,ids]
    visible = np.zeros((24,24),bool)
    if len(pos):
        visible[pos[:,0],pos[:,1]]=True
    return visible, int(ids.sum())


def bounds(obs, team, possible):
    own,_ = occupied(obs,team)
    rival,seen_count = occupied(obs,1-team)
    fog = ~np.asarray(obs["sensor_mask"],bool)
    own_limit=int((own & possible).sum())
    foe_seen=int((rival & possible).sum())
    foe_hidden=min(16-seen_count,int((possible & fog).sum()))
    return own_limit,foe_seen+foe_hidden
