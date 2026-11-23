"""A scalar referee recount of all original sight windows and held first views."""
import argparse
from collections import Counter
import gzip
import json
import statistics

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from spawn import HERE, WORK, choose, digest, load


def range_power(pos,xy):
    x,y=map(int,pos);a,b=xy
    return 12 if (a,b)==(x,y) else int(abs(a-x)<=1 and abs(b-y)<=1)


def audit(saved,pub,ref,meta,env):
    team=meta['team'];move=meta['cfg']['unit_move_cost']
    env.reset(seed=meta['seed']);pars=env.env_params
    initial=np.asarray(env.state.map_features.tile_type);rate=np.float32(pars.nebula_tile_drift_speed)
    effect=int(pars.nebula_tile_vision_reduction);sign=int(np.sign(rate));scale=np.abs(rate)
    shifts=[0]
    for k in range(99):
        a,b=(np.float32(k-1)*scale)%np.float32(1),(np.float32(k)*scale)%np.float32(1)
        shifts.append(shifts[-1]+int(a>b)*sign)
    cx,cy=map(int,ref['centres'][0]); coordinates={(cx,cy),(23-cy,23-cx)}
    def visible(t,held_uid=None,origin=None):
        if not t:return set()
        positions=pub['position'][t,team];alive=pub['units_mask'][t,team]
        result=set()
        for x,y in coordinates:
            n=shifts[t-1];damping=effect*int(initial[(x-n)%24,(y+n)%24]==1)
            v=sum(range_power(positions[u],(x,y)) for u in np.flatnonzero(alive) if u!=held_uid)
            if held_uid is not None:v+=range_power(origin,(x,y))
            if v>damping:result.add(24*x+y)
        return result
    views=[visible(t) for t in range(101)]
    actual=ref['active'][:101,0]
    sp=int(np.flatnonzero(actual)[0]); seen=next((t for t in range(101) if actual[t] and views[t]),101)
    assert sp==saved['spawn'] and seen==saved['first']
    assert saved['before']==[t for t in range(sp) if views[t]]
    for t,hit in enumerate(views):assert hit=={24*x+y for x,y in coordinates if pub['sensor_mask'][t,x,y]}
    expected=set()
    for t in range(max(1,sp-3),sp):
        for uid in range(16):
            if not pub['units_mask'][t,team,uid] or pub['energy'][t,team,uid].item()<max(30,3*move) or pub['protected'][t,uid]:continue
            d=pub['commands'][t,uid,0]
            if not 1<=d<=4 or not pub['units_mask'][t+1,team,uid]:continue
            pos=pub['position'][t,team,uid];nxt=pub['position'][t+1,team,uid]
            if any(range_power(pos,divmod(c,24))>range_power(nxt,divmod(c,24)) for c in views[t]):expected.add((t,uid))
    assert expected=={(q['t'],q['uid']) for q in saved['oracle']}
    assert choose(pub,meta)==saved['ordered']
    rows=saved['oracle']+([saved['public_result']] if saved['public_result'] else [])
    for q in rows:
        t,uid=q['t'],q['uid'];origin=pub['position'][t,team,uid];safe=True;earliest=None
        for v in q['steps']:
            a=v['at'];assert visible(a,uid,origin)==set(v['seen'])
            foes=ref['real_position'][a,1-team][ref['real_live'][a,1-team]]
            safe &= bool(pub['units_mask'][a,team,uid] and not np.any((foes==origin).all(axis=1)))
            assert safe==v['safe']
            if safe and earliest is None and a>=sp and a<seen and set(q['departing'])&set(v['seen']):earliest=a
        assert q['earliest']==earliest
    return len(rows)*3


def summarize(rows):
    groups={};checks=Counter()
    def count(name,available):
        groups[name]=dict(maps=len(available),opponents=dict(Counter(r['opponent'] for r in available)),
                          seats=dict(Counter(r['team'] for r in available)))
    for r in rows:checks.update(r['checks'])
    count('preseen',[r for r in rows if r['before']]);count('preseen_and_spawn_visible',[r for r in rows if r['before'] and r['view_at_spawn']]);
    count('preseen_and_spawn_missed',[r for r in rows if r['before'] and not r['view_at_spawn']]);
    count('preseen_in_last_three',[r for r in rows if r['before'] and r['gap_from_last']<=3]);count('departed',[r for r in rows if r['oracle']]);
    oracle=[r for r in rows if any(e['earliest'] is not None for e in r['oracle'])]
    count('optimistic',[r for r in rows if any(e['earliest_optimistic'] is not None for e in r['oracle'])]);count('oracle',oracle)
    count('entire_team_lost',[r for r in oracle if any(e['earliest'] is not None and e['leaves_team_view'] for e in r['oracle'])]);
    count('public_ordered',[r for r in rows if r['ordered']]);count('public_before_spawn',[r for r in rows if r['ordered'] and r['ordered']['t']<r['spawn']]);
    count('public_over_spawn',[r for r in rows if r['ordered'] and r['ordered']['t']<r['spawn']<=r['ordered']['t']+3]);
    public=[r for r in rows if r['public_result'] and r['ordered']['t']<r['spawn'] and r['public_result']['earliest'] is not None]
    count('public_bridge',public);count('public_any_earlier',[r for r in rows if r['public_result'] and r['public_result']['leading'] is not None]);
    lost=[r for r in rows if r['public_result'] and r['public_result']['loses_original']];count('public_lost',lost)
    leads=[r['first']-min(e['earliest'] for e in r['oracle'] if e['earliest'] is not None) for r in oracle]
    med=statistics.median(leads) if leads else 0
    current=groups['oracle']
    if len(rows)==160:
        gates=dict(eight_maps=len(oracle)>=8,three_per_opponent=all(current['opponents'].get(k,0)>=3 for k in ('v16','solution92')),
                   two_per_side=all(current['seats'].get(k,0)>=2 for k in (0,1)),median_three=med>=3,
                   four_public=len(public)>=4,limited_losses=len(lost)<=len(public))
    else:
        gates=dict(three_maps=len(oracle)>=3,one_public=len(public)>=1,limited_losses=len(lost)<=len(public))
    return dict(maps=len(rows),categories=groups,checks=checks,oracle_gains=leads,median_oracle_gain=med,
                total_gain_over_all_maps=sum(leads)/len(rows),gates=gates,passed=all(gates.values()),
                best_examples=[dict(seed=r['seed'],team=r['team'],opponent=r['opponent'],spawn=r['spawn'],first=r['first'],
                                    best=min((q for q in r['oracle'] if q['earliest'] is not None),key=lambda q:(q['earliest'],q['t'],q['uid']))) for r in oracle])


def run(split):
    inp=(WORK/'spaetort'/split); files=sorted(inp.glob('*.json'));dest=WORK/'zeitfenster'/split
    assert len(files)=={'train':160,'valid':48}[split] and {p.name for p in files}=={p.name for p in dest.glob('*.json')}
    env=LuxAIS3GymEnv(numpy_output=True); rows=[];checks=0
    try:
        for f in files:
            m=json.loads(f.read_text());row=json.loads((dest/f.name).read_text());assert row['source']['public']==m['public_sha'] and row['source']['referee']==m['private_sha']
            checks+=audit(row,load(inp,m,'public'),load(inp,m,'private'),m,env);rows.append(row)
    finally:env.close()
    assert len({r['seed'] for r in rows})==len(rows)
    out=HERE/split;out.mkdir(exist_ok=True)
    raw=''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rows).encode();p=out/'fenster.jsonl.gz'
    if p.exists():assert gzip.decompress(p.read_bytes())==raw
    else:p.write_bytes(gzip.compress(raw,mtime=0))
    res=summarize(rows);res['independently_checked_held_frames']=checks;res['archive_sha']=digest(p)
    target=out/'ergebnis.json';data=json.dumps(res,sort_keys=True,indent=2)+'\n'
    if target.exists():assert json.loads(target.read_text())==json.loads(data)
    else:target.write_text(data)
    print(len(rows),'complete original openings audited',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('split',choices=('train','valid'));run(p.parse_args().split)
