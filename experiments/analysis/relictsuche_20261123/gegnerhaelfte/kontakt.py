"""Predict realized revenue of a free ship's original V16 move onto a pre-proved first enemy-half tile."""
import argparse,base64,gzip,json,zlib
from hashlib import sha256
import numpy as np
import lernen as s
from modell import fit,predict

NAMES=['turn','sensor','since_sight','energy','move_cost','own_points','opp_points','visible_enemy_count','nearby_own','nearby_enemy','tile_energy','fog','distance_behind_center']


def select():
    with gzip.open(s.ARCH,'rt') as f:rows=[r for r in map(json.loads,f) if r['version']=='v16' and r['opponent']=='solution92' and r['sensor'] in (2,3,4)]
    idx={(r['seed'],r['team']):r for r in rows};keys=sorted({k[0] for k in idx})[72:];assert len(keys)==60 and not set(keys).intersection(r['seed'] for r in s.select())
    return [idx[k,i%2] for i,k in enumerate(keys)]


def choices(agent,o,actual,t,view,proof):
    if view is None or t>89 or not proof.positive:return {}
    team=agent.team_id;ctx,ids,_,masks,_,_,positions=agent._imitation.last_fz
    energy=np.asarray(ctx['ally_ene']);ids=np.array(ids,int);pos=np.asarray(positions,int);foes=np.asarray(ctx['enemy_coords']).reshape(-1,2)
    certified=set(s.indices(s.worlds(proof.positive)));known=np.asarray(ctx['point_tiles'],bool)
    out={}
    for i,uid in enumerate(ids):
        d=int(actual[uid,0]);cur=pos[i];world=s.world(cur,team)
        if d not in (1,2,3,4) or int(24*world[0]+world[1]) in certified or known[tuple(cur)]:continue
        d=int(s.MIRROR_DIR[d]) if team else d
        if not masks[i,d]:continue
        dest=cur+[s.DX[d],s.DY[d]]
        if np.any(dest<0) or np.any(dest>=24) or not ctx['passable'][tuple(dest)] or int(dest.sum())<=23:continue
        w=s.world(dest,team);k=int(24*w[0]+w[1]);
        if k not in certified:continue
        alive=(energy[ids]>=0)&(ids!=uid);near=int(np.count_nonzero(np.abs(pos[alive]-dest).max(axis=1)<=3));enear=int(np.count_nonzero(np.max(abs(foes-dest),axis=1)<=3)) if len(foes) else 0
        x=[t,agent.env_cfg['unit_sensor_range'],t-view,energy[uid],ctx['move_cost'],o['team_points'][team],o['team_points'][1-team],len(foes),near,enear,ctx['energy_map'][tuple(dest)],ctx['nebula'][tuple(dest)],dest.sum()-23]
        out[(int(uid),k)]=list(map(float,x))
    return out


def replay(env,r,source):
    tape=np.frombuffer(zlib.decompress(base64.b64decode(r['tape'])),np.int8).reshape(303,2,16,3);assert sha256(tape.astype('<i4').tobytes()).hexdigest()==r['digest']
    tm=r['team'];side=f'player_{tm}';agent=s.r3_package_agent(side,s.PACKAGE);agent.new_game(side);obs,inf=env.reset(seed=r['seed']);agent.set_env_cfg(inf['params']);assert int(inf['params']['unit_sensor_range'])==r['sensor']
    proof=s.Evidence();first=None;event=None;sight=None;ledger=[]
    for t in range(101):
        o=obs[side];a=agent.act(step=t,obs=o);assert np.array_equal(a,tape[t,tm]);vis=bool(np.asarray(o['relic_nodes_mask']).any());
        if vis and sight is None:sight=t
        pos=np.asarray(o['units']['position'][tm]);alive=np.asarray(o['units_mask'][tm],bool)&(np.asarray(o['units']['energy'][tm]).reshape(-1)>=0)
        occ={int(x)*24+int(y) for x,y in pos[alive]};proof.observe(dict(step=t,ms=t,points=int(o['team_points'][tm]),occupied=sorted(occ),epoch_seen=vis))
        offers=choices(agent,o,a,t,sight,proof) if first is None and agent._imitation.last_fz is not None else {}
        out=env.step({f'player_{i}':tape[t,i].astype(np.int32) for i in (0,1)});obs=out[0];st=out[4]['final_state'];pay=s.point_tile_map(st);p=np.asarray(st.units.position)[tm];el=np.asarray(st.units_mask,bool)[tm]&(np.asarray(st.units.energy)[tm,:,0]>=0)
        z={}
        for uid in np.flatnonzero(el):
            x,y=map(int,p[uid]);
            if pay[x,y]:z.setdefault(24*x+y,[]).append(int(uid))
        score=s.match_points_after_step(o,obs[side],out[4]);assert len(z)==int(score[tm])-int(o['team_points'][tm]);away={k:v for k,v in z.items() if sum(divmod(k,24))<23} if tm else {k:v for k,v in z.items() if sum(divmod(k,24))>23}
        if first is None and away:
            first=t;candidates=sorted((v[0],k) for k,v in away.items() if len(v)==1 and (v[0],k) in offers)
            if candidates:
                u,g=candidates[0];event=dict(t=t,uid=u,world=g,x=offers[u,g])
        ledger.append(away)
    s.require_clean_policy(agent,side);assert score[[tm,1-tm]].tolist()==r['matches'][0]['points'] and (101 if sight is None else sight)==r['sight']
    if event:
        u,g,t=event['uid'],event['world'],event['t'];event['y']=sum(v.get(g)==[u] for v in ledger[t:t+12]);assert 1<=event['y']<=12 and t<=89
    return dict(seed=r['seed'],team=tm,sensor=r['sensor'],source=source,archive_digest=r['digest'],first_view=sight,first_away=first,event=event)


def run(lane):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    rows=select();s.limit_threads();env=LuxAIS3GymEnv(numpy_output=True);sign=s.sha(s.HERE/'KONTAKTPLAN.md')+s.sha(s.HERE/'kontakt.py')+s.sha(s.ARCH)
    try:
        for i in range(lane,60,2):
            p=s.WORK/'natuerlich'/f'{i:02d}.json';r=json.loads(p.read_bytes()) if p.exists() else replay(env,rows[i],sign);assert r['source']==sign;s.write_once(p,r);print(i,r['seed'],bool(r['event']),flush=True)
    finally:env.close()


def evaluate():
    rows=[json.loads((s.WORK/'natuerlich'/f'{i:02d}.json').read_bytes()) for i in range(60)];assert len({r['source'] for r in rows})==1
    tr,te=rows[:36],rows[36:];models={};scores={};errors={}
    def data(rr):
        e=[r['event'] for r in rr if r['event']];return np.array([v['x'] for v in e],float).reshape(-1,len(NAMES)),np.array([v['y'] for v in e],float)
    x,y=data(tr);xx,yy=data(te);ci=None
    if len(x) and len(xx):
        for n,cols in [('constant',[]),('time_sensor',[0,1]),('model',list(range(len(NAMES))))]:
            m=fit(x,y,np.ones(len(y)),cols);pr=predict(m,xx);models[n]=m;errors[n]=(pr-yy)**2;scores[n]=dict(mse=float(errors[n].mean()),mae=float(abs(pr-yy).mean()),mean=float(pr.mean()))
        baseline=min(('constant','time_sensor'),key=lambda n:scores[n]['mse']);gain=errors[baseline]-errors['model'];draw=np.random.default_rng(231123).integers(0,len(yy),(20000,len(yy)));ci=np.quantile(gain[draw].mean(1),[.025,.975]).tolist()
    summary=dict(maps=[36,24],natural=[sum(r['first_away'] is not None for r in rr) for rr in (tr,te)],supported=[len(y),len(yy)],mean_value=[float(v.mean()) if len(v) else None for v in (y,yy)],models=models,holdout=scores,better_mse_ci95=ci,
                 offers=[r['seed'] for r in rows if r['event']],accepted=bool(ci and ci[0]>0 and len(y)>=8 and len(yy)>=8),features=NAMES,train=[r['seed'] for r in tr],test=[r['seed'] for r in te])
    (s.HERE/'kontaktmodell.json').write_text(json.dumps(summary,indent=2)+'\n');(s.HERE/'kontakte.jsonl.gz').write_bytes(gzip.compress(b''.join(json.dumps(r,separators=(',',':')).encode()+b'\n' for r in rows),mtime=0));print({k:v for k,v in summary.items() if k in ('supported','natural','mean_value','holdout','better_mse_ci95','accepted')})


if __name__=='__main__':
    pa=argparse.ArgumentParser();pa.add_argument('mode',choices=('0','1','fit'));a=pa.parse_args();evaluate() if a.mode=='fit' else run(int(a.mode))
