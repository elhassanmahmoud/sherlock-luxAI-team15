"""Complete paired accounting on 24 new maps, including the order of all three matches."""
import json
from pathlib import Path

import numpy as np

from archiv import STRATA, compressed, save
from originale import HASHES, HERE, PACKAGE, R3, SCRATCH, STUDY, digest, seeds


def draw(values):
    rng=np.random.default_rng(163400)
    return np.concatenate([values[rng.integers(0,len(values),(500,len(values)))].sum(axis=1) for _ in range(40)])


def summarize(rows,predicate):
    seeds0=sorted({r['seed'] for r in rows})
    group=[r for r in rows if predicate(r['v16']['order'],r['r3']['order'])]
    result={'seats':len(group),'maps':len({r['seed'] for r in group}),'by_policy':{},'paired':{}}
    for name in ('v16','r3'):
        a=[r[name] for r in group]
        result['by_policy'][name]={'match_wins':[sum(r['order'][i] for r in a) for i in range(3)],
            'match_margins':[sum(r['margins'][i] for r in a) for i in range(3)],'whole_wins':sum(r['win'] for r in a)}
    for label in ('m2','m3','m23','whole'):
        def score(a):
            return a['win'] if label=='whole' else sum(a['order'][i] for i in {'m2':[1],'m3':[2],'m23':[1,2]}[label])
        diffs=[score(r['r3'])-score(r['v16']) for r in group]
        table=[[sum(r['seed']==s for r in group),sum(d for r,d in zip(group,diffs,strict=True) if r['seed']==s)] for s in seeds0]
        boot=draw(np.asarray(table));nonempty=boot[:,0]>0
        rate=100*boot[nonempty,1]/boot[nonempty,0]
        result['paired'][label]={'net':sum(diffs),'higher':sum(d>0 for d in diffs),'lower':sum(d<0 for d in diffs),
            'equal':sum(d==0 for d in diffs),'delta_per_100_selected_seats':100*sum(diffs)/len(group) if group else None,
            'map_ci95_per_100_selected_seats':np.percentile(rate,[2.5,97.5]).tolist() if len(rate) else None,
            'nonempty_bootstrap_samples':int(nonempty.sum())}
    return result


def main():
    panel=seeds();rows=[];raw=[]
    files=list((SCRATCH/'originale').glob('*/*.json'));assert len(files)==96
    for seed in panel:
        for team in (0,1):
            result=dict(seed=seed,team=team)
            for name in ('v16','r3'):
                row=json.loads((SCRATCH/'originale'/name/f'{seed}-{team}.json').read_text())
                assert (row['seed'],row['team'],row['id'],row['sensor'])==(seed,team,name,1)
                pkg=PACKAGE if name=='v16' else R3
                assert row['source']=={p.name:digest(p) for p in (pkg,HERE/'PLAN.md',HERE/'originale.py',STUDY/'vergleich/spielen.py')}
                assert digest(pkg)==HASHES[name] and row['agent_errors']==[0,0] and len(row['action_hash'])==64
                order=[m['win'] for m in row['matches']];margins=[m['points'][0]-m['points'][1] for m in row['matches']]
                assert len(order)==3 and set(order)<={0,1} and row['win']==int(sum(order)>=2)
                assert all(m==0 or int(m>0)==w for m,w in zip(margins,order,strict=True))
                result[name]=dict(order=order,margins=margins,win=row['win']);raw.append(row)
            rows.append(result)
    result={k:summarize(rows,p) for k,p in dict(all=lambda a,b: True,**STRATA).items()}
    common=result['both_m1_win']['paired']['m23']
    result['fresh_gate']=(common['net']>=-2)
    out=HERE/'originalpruefung';out.mkdir(exist_ok=True)
    compressed(out/'spiele.jsonl.gz',raw);result['data_sha']=digest(out/'spiele.jsonl.gz')
    save(out/'ergebnis.json',result);print(json.dumps({'complete':96,'fresh_gate':result['fresh_gate'],'common_m1_follow_net':common['net']}),flush=True)


if __name__=='__main__':main()
