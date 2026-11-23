"""Follow already sealed public routes, then score physical neighbour visibility on archived fleets."""
import argparse
import json
import sys

import jax
import jax.numpy as jnp
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from befund import DATA, DEAD, HERE, PACKAGE, WORK, digest, load, orbits, shadows
from wege import MID, ORB, OTHER, ZONE
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent


@jax.jit
def flags(speed):
    t=jnp.arange(303)
    return ((t-1)*jnp.abs(speed))%1 > (t*jnp.abs(speed))%1


def add(power,cell,amount):
    x,y=cell
    power[max(0,x-1):min(24,x+2),max(0,y-1):min(24,y+2)]+=amount
    power[x,y]+=11*amount


def test(pub,j,hist,meta,old,geometry,reduction,verify):
    team=meta['team'];scoreweights=j['weights'].reshape(-1); active_count=j['active'].sum(1)
    checked=hits=blocked=0
    matches=[]
    for saved in old['matches']:
        m=saved['match'];first=saved['first'];start=m*101
        rec=dict(match=m,first=first,spawn=saved['spawn'],relation=saved['relation'],modes={},any_first={})
        matches.append(rec)
        x,y=map(int,j['centres'][m]);target=int(ORB[24*x+y]); endpoints=[int(MID[target]),int(OTHER[target])]
        for name,order in saved['public_orders'].items():
            depart=order['depart'];path=order['path'];uid=order['uid']
            route=path[1:]+[path[-1]]*(9-len(path));previous=path[0]
            for dt,cell in enumerate(route,1):
                at=depart+dt
                if at>=first:break
                terrain=geometry[at-1]
                alive=pub['units_mask'][at,team]; pos=pub['position'][at,team]
                if not alive[uid] or (cell!=previous and terrain[divmod(cell,24)]==2):
                    blocked+=1;break
                foe=j['real_position'][at,1-team][j['real_live'][at,1-team]]
                if any(int(a)*24+int(b)==cell for a,b in foe):
                    blocked+=1;break
                previous=cell
                power=-(terrain==1).astype(np.int16)*reduction
                for xy in pos[alive]: add(power,xy,1)
                assert np.array_equal(power>0,pub['sensor_mask'][at])
                add(power,pos[uid],-1);add(power,divmod(cell,24),1)
                checked+=1
                if not j['active'][at,m] or not any(power[divmod(k,24)]>0 for k in endpoints):continue
                # Verify the analytic substitution against the original implementation before using its sight.
                simulated=pos.copy();simulated[uid]=divmod(cell,24)
                assert np.array_equal(verify(terrain,simulated,alive),power>0)
                rec['any_first'][name]=at;hits+=1
                if saved.get('already_registered') or saved['relation'] is None or at>first-3:break
                valid=(scoreweights>0)&(scoreweights<=active_count[at])
                bad=valid&ZONE[target]&hist[at,1].reshape(-1)
                if bad.any():
                    threshold=active_count[saved['spawn']-1]
                    rec['modes'][name]=dict(at=at,depart=depart,uid=uid,path=path,pairs=orbits(bad),
                                            new_pairs=orbits(bad&(scoreweights>threshold)))
                break
    return matches,dict(original_sensor_arrays=checked,physical_sights=hits,blocked_routes=blocked)


def run(lane):
    limit_threads()
    templates=[r3_package_agent(f'player_{i}',PACKAGE)._imitation.belief for i in (0,1)]
    env=LuxAIS3GymEnv(numpy_output=True)
    @jax.jit
    def physical(st,p,team,terrain,pos,mask):
        state=st.replace(units=st.units.replace(position=st.units.position.at[team].set(pos)),
                         units_mask=st.units_mask.at[team].set(mask),map_features=st.map_features.replace(tile_type=terrain))
        return env.jax_env.compute_sensor_masks(state,p).sensor_mask[team]
    folder=WORK/'zweiterfund_sicht';folder.mkdir(exist_ok=True)
    try:
        for f in sorted(DATA.glob('*.json'))[lane::2]:
            meta=json.loads(f.read_text());p=WORK/'zweiterfund'/(f.stem+'.json')
            binding=dict(primary=digest(p),implementation=digest(HERE/'sicht.py'),plan=digest(HERE/'SICHTNACHPRUEFUNG.md'))
            dest=folder/(f.stem+'.json')
            if dest.exists():
                assert json.loads(dest.read_text())['source']==binding
                continue
            old=json.loads(p.read_text());pub=load(DATA,meta,'public');j=load(DATA,meta,'private')
            with np.load(DEAD/(f.stem+'.npz')) as z:hist=np.unpackbits(z['bits'],axis=-1,bitorder='little').reshape(303,3,24,24).astype(bool)
            env.reset(seed=meta['seed']);pms=env.env_params;grid=np.asarray(env.state.map_features.tile_type);geometry=[]
            assert np.array_equal(np.asarray(env.state.relic_nodes)[:3],j['centres'])
            sign=int(np.sign(pms.nebula_tile_drift_speed))
            for roll in np.asarray(flags(pms.nebula_tile_drift_speed)):
                geometry.append(grid)
                if roll:grid=np.roll(grid,(sign,-sign),(0,1))
            def check(terrain,pos,mask):return np.asarray(physical(env.state,pms,meta['team'],terrain,pos,mask))
            matches,counts=test(pub,j,hist,meta,old,geometry,int(pms.nebula_tile_vision_reduction),check)
            counts['belief_rows']=shadows(pub,j,hist,meta,matches,templates[meta['team']])
            row=dict(seed=meta['seed'],team=meta['team'],opponent=meta['opponent'],matches=matches,checks=counts,source=binding)
            tmp=dest.with_suffix('.tmp'); tmp.write_text(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n');tmp.replace(dest)
    finally:env.close()
    print(lane,'complete',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('lane',type=int,choices=(0,1));run(parser.parse_args().lane)
