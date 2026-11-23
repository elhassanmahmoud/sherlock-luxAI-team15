"""Partially identified historical match order, with exact net contributions for all discordant low-vision seats."""
from collections import Counter
from itertools import product
from pathlib import Path
import gzip
import json
import sys

import numpy as np

HERE=Path(__file__).resolve().parent; STUDY=HERE.parent; ROOT=STUDY.parents[2]
sys.path.insert(0,str(STUDY.parent/'v16_finalwoche_20261122/solution'))
from sitzvergleich import ANALYSIS, SOURCES, solution_rows
from originale import HASHES, digest

TAPES=Path.home()/'Desktop/KI/sherlock-luxAI-team15/experiments/imitation/finalwoche_20261122/kurze_sicht/spiele'
SEQUENCES=tuple(product((0,1), repeat=3))
STRATA={'v16_m1_win':lambda a,b:a[0], 'v16_m1_loss':lambda a,b:not a[0], 'both_m1_win':lambda a,b:a[0] and b[0],
        'both_m1_loss':lambda a,b:not a[0] and not b[0], 'r3_only_m1':lambda a,b:not a[0] and b[0], 'v16_only_m1':lambda a,b:a[0] and not b[0]}


def save(path,data):
    content=json.dumps(data,sort_keys=True,indent=2,allow_nan=False)+'\n'
    if path.exists():assert json.loads(path.read_text())==json.loads(content)
    else:path.write_text(content)


def compressed(path,rows):
    txt=''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in rows).encode()
    if path.exists():assert gzip.decompress(path.read_bytes())==txt
    else:path.write_bytes(gzip.compress(txt,mtime=0))


def collect():
    mp=json.loads((STUDY.parent/'v16_finalwoche_20261122/kartenparameter/ergebnis.json').read_text())['maps']
    sight={r['seed']:r['unit_sensor_range'] for r in mp};rows=[]
    for panel,(first,arms) in SOURCES.items():
        data={a:solution_rows(ANALYSIS/file,sha,first) for a,(file,sha) in arms.items()}
        for key in sorted(data['v16']):
            seed,side=key;team=int(side[-1]);row=dict(seed=seed,side=team,sensor=sight[seed],panel=panel)
            for name in ('v16','r3'):
                original=data[name][key];n=original['matches'];order=None;source='aggregate'
                tap=TAPES/f'{name}_{seed}_{side}.json'
                if tap.exists():
                    receipt=json.loads(tap.read_text());npz=TAPES/receipt['filename']
                    assert receipt['actual']==original==receipt['seat']['expected'][name] and digest(npz)==receipt['sha256']
                    assert receipt['package']==HASHES[name] and receipt['seat']['seed']==seed and receipt['seat']['side']==side
                    with np.load(npz,allow_pickle=False) as z:
                        w=z['team_wins'][:,team]; assert len(w)==303 and w[0]==0
                        assert np.array_equal(w[:101],np.zeros(101)) and (w[101:202]==w[101]).all() and (w[202:]==w[202]).all()
                        order=[int(w[101]),int(w[202]-w[101]),int(n-w[202])]
                    assert sum(order)==n and set(order)<={0,1};source='public_tape'
                elif n in (0,3):order=[int(n==3)]*3;source='unique_aggregate'
                row[name]=dict(**original,order=order,source=source)
            rows.append(row)
    assert len(rows)==1600 and len({(r['seed'],r['side']) for r in rows})==1600
    return rows


def scores(r,stratum):
    def options(name):
        a=r[name];return [tuple(a['order'])] if a['order'] is not None else [s for s in SEQUENCES if sum(s)==a['matches']]
    delta=r['r3']['win']-r['v16']['win']; nums=[]
    for a,b in product(options('v16'),options('r3')):
        yes=int(bool(STRATA[stratum](a,b)))
        nums.append([yes,delta*yes,yes*(b[1]-a[1]),yes*(b[2]-a[2]),yes*((b[1]+b[2])-(a[1]+a[2])),
                     yes*int(delta>0),yes*int(delta<0),yes*int(delta>0 and b[1]>a[1])])
    x=np.array(nums,dtype=int)
    return x.min(axis=0),x.max(axis=0)


def summarize(rows):
    summary={}; labels=('seats','whole_delta','m2_delta','m3_delta','m23_delta','whole_rescues','whole_lost','rescued_with_m2')
    ordered=sorted(rows,key=lambda r:(r['seed'],r['side']));n=len(ordered)//2
    for name in STRATA:
        a,b=map(np.asarray,zip(*(scores(r,name) for r in ordered)))
        low=a.sum(0);high=b.sum(0)
        record={k:[int(lo),int(hi)] for k,lo,hi in zip(labels,low,high,strict=True)}
        record['confirmed_rescue_maps']=sorted({r['seed'] for r,l in zip(ordered,a,strict=True) if l[5]})
        record['confirmed_harm_maps']=sorted({r['seed'] for r,l in zip(ordered,a,strict=True) if l[6]})
        if np.array_equal(a[:,1],b[:,1]):
            effect=a[:,1].reshape(-1,2).mean(axis=1)
            rng=np.random.default_rng(163400); estimates=[]
            for _ in range(40): estimates.extend(effect[rng.integers(0,n,(500,n))].mean(axis=1).tolist())
            record['whole_contribution_pp']=float(100*effect.mean());record['map_ci95_pp']=(100*np.percentile(estimates,[2.5,97.5])).tolist()
        summary[name]=record
    return dict(seats=len(rows),maps=n,known_orders={name:dict(Counter(r[name]['source'] for r in rows)) for name in ('v16','r3')},
                discordant_all=sum(r['v16']['win']!=r['r3']['win'] for r in rows),
                discordant_with_both_orders=sum(r['v16']['win']!=r['r3']['win'] and all(r[z]['order'] is not None for z in ('r3','v16')) for r in rows),
                strata=summary)


def main():
    rows=collect();out=HERE/'archiv';out.mkdir(exist_ok=True)
    result={}
    select={'low':lambda r:r['sensor']<=2,'range1':lambda r:r['sensor']==1,'wide':lambda r:r['sensor']>=3,'all':lambda r:True,
            'low_panel3':lambda r:r['sensor']<=2 and r['panel']==3,'low_panel5':lambda r:r['sensor']<=2 and r['panel']==5}
    for key,predicate in select.items():result[key]=summarize([r for r in rows if predicate(r)])
    lo=result['low']; c=lo['strata']['both_m1_win']
    assert lo['seats']==786 and lo['discordant_all']==lo['discordant_with_both_orders']==30
    result['historical_gates']=dict(four_rescue_maps=len(c['confirmed_rescue_maps'])>=4,net_two=c['whole_delta'][0]>=2,
                  two_m2_rescues=c['rescued_with_m2'][0]>=2,panels_nonnegative=all(result[k]['strata']['both_m1_win']['whole_delta'][0]>=0 for k in ('low_panel3','low_panel5')))
    compressed(out/'sitze.jsonl.gz',rows);result['source_tables']=SOURCES;result['data_sha']=digest(out/'sitze.jsonl.gz')
    save(out/'ergebnis.json',result);print('All 1600 matched seats verified',flush=True)


if __name__=='__main__':main()
