"""Replay archived V16 first matches and learn a public predictor of natural first away contact."""
import argparse,base64,gzip,json,sys,zlib
from hashlib import sha256
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];D=HERE.parent
sys.path.insert(0,str(ROOT))
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import Evidence,indices,worlds
from experiments.analysis.relictsuche_20261123.routenlernen.routes import DX,DY,MIRROR_DIR
from experiments.analysis.relictsuche_20261123.vergleich.spielen import PACKAGE,require,write_once,sha
from scripts.r3_package import r3_package_agent
from scripts.experiment import limit_threads
from scripts.scoring import point_tile_map,match_points_after_step
from scripts.xversion_replay import require_clean_policy
from agents.sherlock.features import bfs_maps

ARCH=D/'punktwissen/allgemein_partien.jsonl.gz'
WORK=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/gegnerhaelfte')
FEATURES=['distance','original_heads_toward','turn','energy','sensor','move_cost','away_targets','visible_enemies','enemy_distance','team_margin','dest_energy','dest_fog','nest_distance']


def select():
    with gzip.open(ARCH,'rt') as f:rows=[r for r in map(json.loads,f) if r['version']=='v16' and r['opponent']=='solution92' and r['sensor'] in (2,3,4)]
    idx={(r['seed'],r['team']):r for r in rows};seeds=sorted({a for a,t in idx})[:72]
    assert len(seeds)==72 and all(162860000<=s<=162860159 for s in seeds)
    return [idx[s,i%2] for i,s in enumerate(seeds)]


def world(x,team):return 23-np.asarray(x)[::-1] if team else np.asarray(x)


def offer(sub,o,a,t,seen,proof):
    if not seen or t%4 or t>88 or not proof.positive:return None
    team=sub.team_id;brain=sub._imitation;state=brain.last_fz
    if state is None:return None
    ctx,ids,_,masks,_,_,pos=state;idx=np.asarray(ids,int);ene=ctx['ally_ene'];pos=np.asarray(pos,int)
    bg=brain.belief;geo=(np.asarray(bg.tile_type)>=0)&ctx['passable']
    cost=int(ctx['move_cost']);goals=np.array([world(divmod(k,24),team) for k in indices(worlds(proof.positive))],int).reshape(-1,2)
    goals=goals[(goals.sum(1)>23)&geo[tuple(goals.T)]]
    if not len(goals):return None
    target=np.zeros((24,24),bool);target[tuple(goals.T)]=1
    known=np.asarray(ctx['point_tiles'],bool).copy();known[tuple(goals.T)]=1
    for k in indices(worlds(proof.positive)):known[tuple(world(divmod(k,24),team))]=1
    moves=np.asarray(a)[idx,0];canon=np.where(moves<=4,moves,0);canon=MIRROR_DIR[canon] if team else canon
    planned=(pos+np.column_stack((DX[canon],DY[canon]))).clip(0,23);blocked=~ctx['passable'][tuple(planned.T)];planned[blocked]=pos[blocked]
    dists=bfs_maps(geo,goals);best=None;existing=[]
    for i,u in enumerate(idx):
        if ene[u]<0 or moves[i]>4 or known[tuple(pos[i])] or known[tuple(planned[i])]:continue
        assigned=ctx['assigned'].get(int(u))
        if assigned is not None and known[tuple(assigned)]:continue
        rest=np.arange(len(idx))!=i;rest&=np.asarray(ene)[idx]>=0
        occupied={tuple(q) for q in np.concatenate([pos[rest],planned[rest]])}
        occupied.update(tuple(ctx['assigned'][int(k)]) for k in idx[rest] if ctx['assigned'].get(int(k)) is not None)
        for j,g in enumerate(goals):
            dist=int(dists[j,*pos[i]])
            if not 1<=dist<=12 or ene[u]<dist*cost+10 or tuple(g) in occupied:continue
            for d in range(1,5):
                q=pos[i]+[DX[d],DY[d]]
                if not masks[i,d] or np.any(q<0) or np.any(q>=24) or tuple(q) in occupied or not geo[tuple(q)] or dists[j,*q]!=dist-1:continue
                key=(dist,-int(ene[u]),int(u),int(24*g[0]+g[1]),d)
                if best is None or key<best[0]:best=(key,g,canon[i])
    if best is None:return None
    (dist,neg,u,_,d),g,actual=best;foe=np.asarray(ctx['enemy_coords']).reshape(-1,2)
    enemy_dist=int(np.min(np.abs(foe-g).sum(1))) if len(foe) else 48
    x=[dist,int(d==actual),t,-neg,sub.env_cfg['unit_sensor_range'],cost,len(goals),len(foe),enemy_dist,int(o['team_points'][team]-o['team_points'][1-team]),int(ctx['energy_map'][tuple(g)]),int(ctx['nebula'][tuple(g)]),int(g.sum()-23)]
    return dict(t=t,uid=u,goal=world(g,team).tolist(),dir=int(MIRROR_DIR[d]) if team else d,x=list(map(int,x)))


def replay(env,row,model_id):
    seed,team=row['seed'],row['team'];side=f'player_{team}'
    tape=np.frombuffer(zlib.decompress(base64.b64decode(row['tape'])),np.int8).reshape(303,2,16,3)
    require(sha256(tape.astype('<i4').tobytes()).hexdigest()==row['digest'],'Bad source hash')
    agent=r3_package_agent(side,PACKAGE);agent.new_game(side);obs,info=env.reset(seed=seed);cfg=info['params'];agent.set_env_cfg(cfg)
    require(int(cfg['unit_sensor_range'])==row['sensor'],'Sensor differs');seen=False;proof=Evidence();occupied_away=set();closed=False;offers=[];credits=[];first_view=None
    for t in range(101):
        o=obs[side];a=agent.act(step=t,obs=o);require(np.array_equal(a,tape[t,team]),f'Archived original differs {seed} {t}')
        visible=bool(np.asarray(o['relic_nodes_mask']).any());seen|=visible
        if visible and first_view is None:first_view=t
        pos=np.asarray(o['units']['position'][team]);live=np.asarray(o['units_mask'][team],bool)&(np.asarray(o['units']['energy'][team]).reshape(-1)>=0)
        occ={int(x)*24+int(y) for x,y in pos[live]};proof.observe(dict(step=t,ms=t,points=int(o['team_points'][team]),occupied=sorted(occ),epoch_seen=visible))
        if seen:occupied_away.update(k for k in occ if (sum(divmod(k,24))>23 if team==0 else sum(divmod(k,24))<23))
        certain=set(indices(worlds(proof.positive)));closed|=bool(occupied_away&certain)
        v=offer(agent,o,a,t,seen,proof) if not closed else None
        if v is not None:offers.append(v)
        out=env.step({f'player_{n}':tape[t,n].astype(np.int32) for n in (0,1)});obs=out[0];st=out[4]['final_state'];pay=point_tile_map(st)
        p=np.asarray(st.units.position)[team];alive=np.asarray(st.units_mask,bool)[team]&(np.asarray(st.units.energy)[team,:,0]>=0)
        ledger={}
        for uid in np.flatnonzero(alive):
            xy=p[uid];k=int(xy[0]*24+xy[1]);
            if pay[tuple(xy)]:ledger.setdefault(k,[]).append(int(uid))
        score=match_points_after_step(o,obs[side],out[4]);require(len(ledger)==int(score[team])-int(o['team_points'][team]),'Credit mismatch')
        if v is not None:require(pay[tuple(v['goal'])], 'Publicly confirmed goal was false')
        credits.append({k:uids for k,uids in ledger.items() if (sum(divmod(k,24))>23 if team==0 else sum(divmod(k,24))<23)})
    require_clean_policy(agent,side);require(score[[team,1-team]].tolist()==row['matches'][0]['points'] and (101 if first_view is None else first_view)==row['sight'],'Archived M1 mismatch')
    first=next((i for i,z in enumerate(credits) if z),None)
    for v in offers:
        t,u=v['t'],v['uid'];g=24*v['goal'][0]+v['goal'][1];h=t+12
        at=first is not None and t<=first<h and credits[first].get(g)==[u]
        v['y']=sum(c.get(g)==[u] for c in credits[first:h]) if at else 0
        v['natural_first_within12']=first is not None and t<=first<h;v['already_unrecognized']=first is not None and first<t
    return dict(seed=seed,team=team,sensor=row['sensor'],source=model_id,archive_digest=row['digest'],first_view=first_view,first_away=first,away_points=sum(map(len,credits)),matches=row['matches'][0],offers=offers)


def run(lane):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads();rows=select();sig=sha(Path(__file__))+sha(HERE/'PLAN.md')+sha(ARCH);env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for i in range(lane,len(rows),2):
            r=rows[i];path=WORK/f'{i:02d}.json';res=json.loads(path.read_bytes()) if path.exists() else replay(env,r,sig)
            require(res['source']==sig and res['seed']==r['seed'],'Mixed inputs');write_once(path,res);print(i,r['seed'],len(res['offers']),flush=True)
    finally:env.close()


if __name__=='__main__':
    pa=argparse.ArgumentParser();pa.add_argument('lane',type=int,choices=(0,1));run(pa.parse_args().lane)
