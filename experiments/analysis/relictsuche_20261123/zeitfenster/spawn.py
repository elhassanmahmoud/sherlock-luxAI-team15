"""Hold one departing sensor on its current site for up to three turns in the original fleet."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import jax
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from halten import HERE, OLD, STUDY, choose, free
sys.path.insert(0,str(STUDY/'zweiterfund'))
from experiments.analysis.relictsuche_20261123.zweiterfund.befund import WORK, digest, load
from experiments.analysis.relictsuche_20261123.zweiterfund.sicht import add, flags
from scripts.experiment import limit_threads


def contribution(pos, cell):
    d=max(abs(int(pos[0])-cell//24),abs(int(pos[1])-cell%24))
    return 12 if d==0 else int(d==1)


def collect(pub,j,meta,order,terrain,reduction,engine):
    team=meta['team']; move=meta['cfg']['unit_move_cost'];x,y=map(int,j['centres'][0]);ends=sorted({24*x+y,24*(23-y)+23-x})
    active=np.flatnonzero(j['active'][:101,0]);assert len(active)
    spawn=int(active[0]); actual_views=[]; originals=[]; checks=Counter()
    for t in range(101):
        vis=pub['sensor_mask'][t].ravel()
        on={c for c in ends if vis[c]};actual_views.append(on)
        assert (bool(on) and t>=spawn)==bool(pub['relic_nodes_mask'][t,[0,3]].any())
        if t==0:
            originals.append(None);continue
        field=-(terrain[t-1]==1).astype(np.int16)*reduction
        for p in pub['position'][t,team,pub['units_mask'][t,team]]:add(field,p,1)
        assert np.array_equal(field>0,pub['sensor_mask'][t]);checks['original_full_masks']+=1
        originals.append(field)
    first=next((t for t in range(spawn,101) if actual_views[t]),101)
    prior=[t for t in range(spawn) if actual_views[t]]
    def held(t,uid,oracle):
        origin=pub['position'][t,team,uid]; cell=int(origin[0])*24+int(origin[1]); first_orig=pub['position'][t+1,team,uid]
        moved=bool(pub['units_mask'][t+1,team,uid] and not np.array_equal(first_orig,origin))
        departing={c for c in actual_views[t] if contribution(origin,c)>contribution(first_orig,c)} if moved else set()
        if oracle and not departing:return None
        observations=[];safe=True
        for dt in (1,2,3):
            a=t+dt;alive=pub['units_mask'][a,team].copy();pos=pub['position'][a,team].copy()
            power=originals[a].copy()
            if alive[uid]:add(power,pos[uid],-1)
            add(power,origin,1);pos[uid]=origin;alive[uid]=True
            foes=j['real_position'][a,1-team][j['real_live'][a,1-team]]
            safe &= bool(pub['units_mask'][a,team,uid] and not np.any(np.all(foes==origin,axis=1)))
            seen={c for c in ends if power[divmod(c,24)]>0}
            # All actual candidate and public-policy windows, including negative alternatives, are checked against the engine.
            assert np.array_equal(engine(terrain[a-1],pos,alive),power>0);checks['held_engine_masks']+=1
            observations.append(dict(at=a,seen=sorted(seen),safe=safe))
        eligible=[v for v in observations if spawn<=v['at']<first and set(v['seen'])&departing]
        gains=[v for v in eligible if v['safe']]
        first_hold=next((v['at'] for v in observations if v['safe'] and v['at']>=spawn and v['seen']),None)
        return dict(t=t,uid=uid,origin=cell,executed_departure=moved,departing=sorted(departing),
                    leaves_team_view=bool(departing-actual_views[t+1]),
                    only_by_ship=sorted(c for c in departing if originals[t][divmod(c,24)]-contribution(origin,c)<=0),
                    steps=observations, earliest_optimistic=eligible[0]['at'] if eligible else None,
                    earliest=gains[0]['at'] if gains else None,
                    leading=first_hold if first_hold is not None and first_hold<first else None,
                    loses_original=bool(t<first<=t+3 and (first_hold is None or first_hold>first)),
                    first_hold=first_hold)
    oracle=[]
    for t in range(max(1,spawn-3),spawn):
        if not actual_views[t]:continue
        for uid in free(pub,team,t,move):
            row=held(t,int(uid),True)
            if row is not None:oracle.append(row)
    applied=held(order['t'],order['uid'],False) if order is not None else None
    return dict(seed=meta['seed'],team=team,opponent=meta['opponent'],spawn=spawn,first=first,ends=ends,
                before=prior,view_at_spawn=bool(actual_views[spawn]),gap_from_last=spawn-prior[-1] if prior else None,
                oracle=oracle,ordered=order,public_result=applied,checks=checks)


def run(split,lane):
    limit_threads();env=LuxAIS3GymEnv(numpy_output=True)
    @jax.jit
    def physical(st,p,team,terrain,pos,alive):
        clone=st.replace(units=st.units.replace(position=st.units.position.at[team].set(pos)),
                         units_mask=st.units_mask.at[team].set(alive),map_features=st.map_features.replace(tile_type=terrain))
        return env.jax_env.compute_sensor_masks(clone,p).sensor_mask[team]
    dest=WORK/'zeitfenster'/split;dest.mkdir(parents=True,exist_ok=True)
    data=WORK/'spaetort'/split; files=sorted(data.glob('*.json'));assert len(files)=={'train':160,'valid':48}[split]
    identity={p.name:digest(p) for p in (HERE/'PLAN.md',HERE/'halten.py',Path(__file__),OLD,STUDY/'zweiterfund/sicht.py')}
    try:
        for f in files[lane::2]:
            meta=json.loads(f.read_text());out=dest/(f.stem+'.json');binding={**identity,'public':meta['public_sha'],'referee':meta['private_sha']}
            if out.exists():assert json.loads(out.read_text())['source']==binding;continue
            pub=load(data,meta,'public')
            order=choose(pub,meta)
            j=load(data,meta,'private')
            env.reset(seed=meta['seed']);pars=env.env_params;grid=np.asarray(env.state.map_features.tile_type);boards=[]
            assert np.array_equal(np.asarray(env.state.relic_nodes)[:3],j['centres']);reduction=int(pars.nebula_tile_vision_reduction)
            assert int(pars.unit_sensor_range)==1 and 0<=reduction<12
            schedule=np.asarray(env.state.relic_spawn_schedule)[:3]
            tt=np.arange(1,101)[:,None]-1
            assert np.array_equal((schedule>=0)&(schedule<=tt),j['active'][1:101])
            sign=int(np.sign(pars.nebula_tile_drift_speed))
            for change in np.asarray(flags(pars.nebula_tile_drift_speed))[:100]:
                boards.append(grid)
                if change:grid=np.roll(grid,(sign,-sign),(0,1))
            verify=lambda ter,pos,alive:np.asarray(physical(env.state,pars,meta['team'],ter,pos,alive))
            r=collect(pub,j,meta,order,boards,reduction,verify);r['source']=binding
            tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n');tmp.replace(out)
    finally:env.close()
    print(split,lane,'complete',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('split',choices=('train','valid'));p.add_argument('lane',type=int,choices=(0,1))
    a=p.parse_args();run(a.split,a.lane)
