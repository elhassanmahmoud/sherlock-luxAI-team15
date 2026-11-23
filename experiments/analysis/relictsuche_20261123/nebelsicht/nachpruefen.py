"""Independent geometric recount using the original engine's action-independent board evolution."""
from collections import Counter
import gzip
import json

import jax
import jax.numpy as jnp
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from obergrenze import HERE, archived, sha


def write(path, data):
    payload = json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if path.exists(): assert json.loads(path.read_text()) == json.loads(payload)
    else: path.write_text(payload)


def read(p):
    return json.loads(gzip.decompress(p.read_bytes()))


def check_geometric(raw, spec, terrain, live, coords):
    first = 101
    tcoords = np.asarray(coords,int)
    for t in range(1,101):
        team_sensor = int(raw['policy'][t]['visible'],16)
        mark = any(bool(team_sensor>>(int(x)*24+int(y))&1) for x,y in tcoords[live[t-1]])
        if mark:
            first=t; break
    assert first==spec['sight'] and 0<=spec['reduction']<12
    oracle = {(c['t'],c['uid'],c['d']):c for c in spec['choices']}
    found = set()
    nlegal=0
    for t in range(min(100,first-1)):
        p=raw['policy'][t]
        known=int(p['point'],16)
        targets=tcoords[live[t]]
        for uid,origin,old,assigned,legal in p['free']:
            if known>>origin&1 or assigned is not None and known>>assigned&1:continue
            x,y=divmod(origin,24)
            for d,(a,b) in enumerate(((x,y-1),(x+1,y),(x,y+1),(x-1,y)),1):
                if d==old or not 0<=a<24 or not 0<=b<24 or terrain[t,a,b]==2:continue
                nlegal+=1
                possible=[]
                for nx,ny in targets:
                    # Isolated sensor 1 contributes eleven extra units on centre; neighbours receive one.
                    dist=max(abs(a-int(nx)),abs(b-int(ny)))
                    contribution=12 if dist==0 else int(dist==1)
                    damping=spec['reduction'] if terrain[t,nx,ny]==1 else 0
                    if 0<contribution<=damping:possible.append(24*int(nx)+int(ny))
                if possible:
                    key=t,uid,d; found.add(key)
                    assert sorted(possible)==sorted(oracle[key]['nodes'])
    assert nlegal==spec['physically_legal_alternatives'] and found==set(oracle)


def evaluation(geo, results):
    stat=Counter(); matrix={}; totals=Counter()
    for r in results:
        totals.update(r['checks'])
        for f in r['records']:
            key=(r['seed'],r['team'],f['t'],f['uid'],f['d']); assert key not in matrix
            matrix[key]=f
    out=[]
    for r in geo:
        mode={k:[] for k in ('geometry','geometry_mask','fixed_synergy','real_synergy','main','main_precredit')}
        for c in r['choices']:
            f=matrix[r['seed'],r['team'],c['t'],c['uid'],c['d']]
            assert all(f[k]==v for k,v in c.items())
            shape=lambda views: bool(views[0]) and not views[1] and not views[2]
            current=dict(geometry=True, geometry_mask=c['local_mask'],fixed_synergy=shape(f['fixed']),real_synergy=shape(f['actual']))
            current['main']=current['real_synergy'] and f['rest_unchanged'] and f['arrived'] and c['local_mask']
            current['main_precredit']=current['main'] and c['precredit'] and f['branch_points']==0
            for k,ok in current.items():
                if ok:mode[k].append(c['t']+1)
            stat['branch_any_relic']+=bool(f['actual'][0]); stat['branch_alone_relic']+=bool(f['actual'][2])
            stat['branch_others_relic']+=bool(f['actual'][1]); stat['branch_rest_unchanged']+=f['rest_unchanged'];stat['branch_arrived']+=f['arrived']
        out.append(dict(seed=r['seed'],team=r['team'],first=r['sight'],credit_observed=r['credit'],
                        actions={k:len(v) for k,v in mode.items()},earliest={k:min(v) for k,v in mode.items() if v}))
    detail={}
    for name in out[0]['actions']:
        matched=[r for r in out if name in r['earliest']]
        gain=sum(r['first']-r['earliest'][name] for r in matched)
        detail[name]=dict(maps=len({r['seed'] for r in matched}),seats=len(matched),sides=[sum(r['team']==side for r in matched) for side in (0,1)],
                          actions=sum(r['actions'][name] for r in out),max_total_steps=gain,mean_over_all_seats=gain/len(out))
    m=detail['main']; gate=dict(six_maps=m['maps']>=6,eight_seats=m['seats']>=8,two_each=min(m['sides'])>=2,
                               four_precredit_maps=detail['main_precredit']['maps']>=4,half_step=m['mean_over_all_seats']>=.5)
    return dict(games=len(out),maps=len(out)//2,exact_replays=len(results),geometric_actions=sum(r['physically_legal_alternatives'] for r in geo),
                free_decisions=sum(r['free_times'] for r in geo),branch_checks=dict(stat),replay_checks=dict(totals),conditions=detail,
                gates=gate,passed=all(gate.values()),seats=out)


def main():
    env=LuxAIS3GymEnv(numpy_output=True)
    zero={f'player_{i}':jnp.zeros((16,3),dtype=jnp.int16) for i in range(2)}
    @jax.jit
    def trajectory(state,params):
        def step(s, t):
            _,nxt,*_=env.jax_env.step_env(jax.random.key(t),s,zero,params)
            return nxt,(s.map_features.tile_type,nxt.relic_nodes_mask)
        return jax.lax.scan(step,state,jnp.arange(100))[1]
    try:
        for group in ('archiv','frisch'):
            f=HERE/group
            raw=archived(group); geo=read(f/'geometrie.json.gz')
            exact=read(f/'engine_0.json.gz')+read(f/'engine_1.json.gz')
            expected={(r['seed'],r['team']) for r in geo if r['choices']}
            assert expected=={(r['seed'],r['team']) for r in exact} and len(expected)==len(exact)
            previous=None
            for g,spec in zip(raw,geo,strict=True):
                assert (g['seed'],g['team'])==(spec['seed'],spec['team'])
                if spec['seed']!=previous:
                    env.reset(seed=spec['seed']);previous=spec['seed']
                    terrain,live=map(np.asarray,trajectory(env.state,env.env_params)); nodes=np.asarray(env.state.relic_nodes,int)
                check_geometric(g,spec,terrain,live,nodes)
            out=evaluation(geo,exact)
            out.update(group=group, decision_applies=group=='frisch', official_map_frames=100*(len(raw)//2),
                       sources={n:sha(HERE/n) for n in ('PLAN.md','abzweigen.py','obergrenze.py','nachpruefen.py')},
                       data={n:sha(f/n) for n in ('geometrie.json.gz','engine_0.json.gz','engine_1.json.gz')})
            write(f/'ergebnis.json',out)
            print(group,len(raw),'checked',flush=True)
    finally:
        env.close()


if __name__=='__main__':
    main()
