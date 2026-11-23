"""Mirrored, named protection and positive controls for the public eligibility rule."""
from types import SimpleNamespace

import numpy as np

from archiv import save
from berater import Advice, flip, world
from originale import HERE, PACKAGE, digest
from scripts.r3_package import _module_for


def scenario(team,condition):
    _module_for(PACKAGE.resolve())
    from sherlock.features import FEATURE_NAMES
    direction=1 if team else 2
    def actual(c):return flip(c) if team else c
    def xy(c):return divmod(actual(c),24)
    origin=4*24+8;goal=6*24+8;middle=5*24+8
    uid=7;base=np.zeros((16,3),np.int16);r3=base.copy();r3[uid,0]=direction
    seen=np.zeros(576,bool);points=seen.copy();prior=seen.copy();seen[actual(goal)]=True
    points[goal]=True;prior[actual(goal)]=True
    terrain=np.zeros(576,int)
    pos=np.full((2,16,2),-1,int);mask=np.zeros((2,16),bool);energy=np.full((2,16,1),-1,int)
    pos[team,uid]=xy(origin);mask[team,uid]=True;energy[team,uid,0]=45
    features=np.zeros((1,len(FEATURE_NAMES)));legal=np.ones((1,6),bool);assigned={}
    if condition=='invisible':seen[actual(goal)]=False
    elif condition=='new_m2_point':prior[actual(goal)]=False
    elif condition=='no_longer_positive':points[goal]=False
    elif condition=='occupied_target':
        pos[team,2]=xy(goal);mask[team,2]=True;energy[team,2,0]=100
    elif condition=='next_ally':
        pos[team,2]=xy(middle);mask[team,2]=True;energy[team,2,0]=100;base[2,0]=direction
    elif condition=='holder':points[origin]=True
    elif condition=='different_assignment':
        alt=3*24+8;points[alt]=True;assigned[uid]=divmod(alt,24)
    elif condition=='sap':base[uid,0]=5
    elif condition=='threat':features[0,FEATURE_NAMES.index('enemies_in_sap')]=0.5
    elif condition=='energy':energy[team,uid,0]=29
    elif condition=='asteroid':terrain[middle]=2
    elif condition=='unknown':terrain[middle]=-1
    elif condition=='illegal':legal[0,2]=False
    elif condition=='original_progress':base[uid,0]=direction
    elif condition=='different_ship':pass
    elif condition=='different_goal':pass
    elif condition!='eligible':raise ValueError(condition)
    b=SimpleNamespace(point_tiles=points.reshape(24,24),tile_type=terrain.reshape(24,24),mirrored=bool(team))
    model=SimpleNamespace(belief=b,last_fz=({'move_cost':4,'assigned':assigned},[uid],features,legal,None,None,None))
    obj=object.__new__(Advice);obj.base=SimpleNamespace(_imitation=model);obj.team=team;obj.prior=prior;obj.first=None
    if condition=='different_ship':obj.first={'uid':uid-1,'goal':actual(goal)}
    if condition=='different_goal':obj.first={'uid':uid,'goal':actual(goal+1)}
    obs={'sensor_mask':seen.reshape(24,24),'units':{'position':pos,'energy':energy},'units_mask':mask}
    options=obj.options(obs,base,r3)
    assert options==([(2,-45,uid,goal,actual(goal),direction)] if condition=='eligible' else []),(team,condition,options)


def main():
    conditions=('eligible','invisible','new_m2_point','no_longer_positive','occupied_target','next_ally','holder','different_assignment','sap','threat',
                'energy','asteroid','unknown','illegal','original_progress','different_ship','different_goal')
    for team in (0,1):
        for c in conditions:scenario(team,c)
    save(HERE/'schutzpruefung.json',dict(seats=[0,1],cases=conditions,count=2*len(conditions),source=digest(HERE/'berater.py')))
    print('All 34 eligibility checks passed')


if __name__=='__main__':main()
