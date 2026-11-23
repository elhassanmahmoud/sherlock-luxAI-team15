"""Independent recomputation of full-game gates and random exact-matching checks using SciPy."""
import argparse
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching

from ort import HERE, enough,bitmask

def matching_test():
    rng=np.random.default_rng(7781);cases=0
    for n in range(1,17):
        for m in (1,3,10,24,60):
            for density in (.03,.17,.5,.97):
                mat=rng.random((n,m))<density
                truth=int((maximum_bipartite_matching(csr_matrix(mat),perm_type='column')>=0).sum())
                masks=[bitmask(row) for row in mat]
                for required in range(0,min(n,m)+2):
                    if enough(masks,required)!=(truth>=required):raise ValueError('Distinct score capacity differs from SciPy matching')
                    cases+=1
    return cases

def main():
    c=matching_test();print('Matching test cases',c,flush=True)
    archive=HERE/'partien.jsonl.gz';result=json.loads((HERE/'ergebnis.json').read_bytes());cards=json.loads((HERE/'karten.json').read_bytes())['performance']
    rows=[json.loads(x) for x in gzip.decompress(archive.read_bytes()).splitlines()];by={tuple(r['key']):r for r in rows}
    if len(rows)!=len(by) or len(rows)!=288 or len(set(r['source'] for r in rows))!=1:raise ValueError('Wrong game inventory')
    raw=Counter();maps=set();gain=[];direct=[];dif=[];later=earlier=0
    for s in cards:
        dg=[];dd=[];dw=[]
        for team in (0,1):
            ref=by[s,team,'reference','solution92'];cand=by[s,team,'candidate','solution92'];duel=by[s,team,'candidate','v16']
            def resultwin(r):
                wins=sum(x['win'] for x in r['matches']);p=[sum(x['points'][k] for x in r['matches']) for k in (0,1)]
                if p!=r['points'] or r['win']!=int(wins>1) or wins not in range(4):raise ValueError('Invalid game result')
                return int(wins>1)
            rw,cw,dwone=[resultwin(r) for r in (ref,cand,duel)]
            raw.update(reference_win=rw,candidate_win=cw,direct_win=dwone)
            dd.append(dwone);dw.append(cw-rw)
            if cand['events']:maps.add(s)
            base=ref['anchor'];adv=0
            if base:
                raw['alert']+=1;cutoff=(base['t']//101+1)*101
                def absolute(row):
                    observations=[a for slot,a in row['firsts'].items() if int(slot) in base['ids'] and base['t']<=a<cutoff]
                    return min(observations,default=cutoff)
                adv=absolute(ref)-absolute(cand)
            raw['gain']+=adv;dg.append(adv);earlier+=int(adv>0);later+=int(adv<0)
        gain.append(np.mean(dg));direct.append(np.mean(dd));dif.append(np.mean(dw))
    for k,v in raw.items():
        if result['stats']['all'][k]!=v:raise ValueError(k)
    if (len(maps),earlier,later)!=(result['changed_maps'],result['stats']['all']['earlier'],result['stats']['all']['later']):raise ValueError('Paired comparison changed')
    flags=[raw['candidate_win']>=raw['reference_win'], raw['direct_win']>=48,raw['gain']>=48,earlier>later,len(maps)>=4]
    if list(result['gates'][k] for k in ('wins_vs_solution','direct','sighting','more_earlier','four_maps'))!=flags or result['passed']!=all(flags):raise ValueError('Gate recomputation changed')
    draws=np.random.default_rng(842317).integers(len(cards),size=(20000,len(cards)))
    for name,vals in [('sight_gain',gain),('direct',direct),('game_difference',dif)]:
        ci=np.quantile(np.asarray(vals)[draws].mean(1),[.025,.975]);point=np.mean(vals)
        if not np.allclose(ci,result['intervals'][name]['ci95']) or not np.isclose(point,result['intervals'][name]['mean']):raise ValueError('Card interval recomputation changed')
    out=dict(matching_cases=c,verified_games=len(rows),unique_maps=len(cards),changed_maps=len(maps),earlier=earlier,later=later,stats=dict(raw),gates=flags,passed=all(flags),archive_sha=sha256(archive.read_bytes()).hexdigest())
    (HERE/'gegenpruefung.json').write_text(json.dumps(out,indent=2)+'\n');print(out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--matching',action='store_true');a=p.parse_args();print(matching_test()) if a.matching else main()
