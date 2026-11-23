"""Score an entire qualified full-game pilot, matching maps and seats across arms."""
import json

import numpy as np

from archiv import compressed, save
from gegenrunde import cards
from originale import HERE, SCRATCH, digest
from spielen import stamp


def main():
    work=SCRATCH/'pilot';queue=cards(163420000,32);raw=[];effects=[];source=stamp(json.loads((work/'quelle.json').read_text()))
    assert len(list(work.glob('*-*-*.json')))==192
    counts={arm:{'wins':0,'rounds':[0,0,0],'activations':0,'changes':0,'by_seat':[0,0]} for arm in ('reference','solution','direct')}
    rescued=[];lost=[]
    for seed in queue:
        for team in (0,1):
            p={}
            for arm in counts:
                row=json.loads((work/f'{seed}-{team}-{arm}.json').read_text());raw.append(row);p[arm]=row
                assert (row['seed'],row['team'],row['arm'],row['source'])==(seed,team,arm,source)
                assert row['engine_actions']==[303,303] and row['errors']==[0,0]
                w=[m['win'] for m in row['matches']];assert row['win']==int(sum(w)>=2)
                stats=counts[arm];stats['wins']+=row['win'];stats['by_seat'][team]+=row['win']
                stats['rounds']=[a+b for a,b in zip(stats['rounds'],w,strict=True)]
                stats['activations']+=int(bool(row['events']));stats['changes']+=len(row['events'])
            native=p['reference'];candidate=p['solution']
            assert native['matches'][0]==candidate['matches'][0] and native['sight']==candidate['sight'] and native['credit']==candidate['credit']
            if not candidate['events']:assert native['trace']==candidate['trace']
            diff=candidate['win']-native['win']
            if diff>0:rescued.append((seed,team))
            if diff<0:lost.append((seed,team))
            effects.append([diff,candidate['matches'][1]['win']-native['matches'][1]['win'],p['direct']['win']])
    arr=np.asarray(effects,dtype=float).reshape(len(queue),2,3).mean(1)
    rng=np.random.default_rng(163420);boot=arr[rng.integers(0,len(arr),(20000,len(arr)))].mean(1)*100
    gates=dict(more_solution_games=counts['solution']['wins']>counts['reference']['wins'],
        m2_nonnegative=counts['solution']['rounds'][1]>=counts['reference']['rounds'][1],direct_more_than_half=counts['direct']['wins']>32)
    result=dict(maps=len(queue),games=len(raw),counts=counts,rescued=rescued,lost=lost,
        ci95_percent={n:np.percentile(boot[:,i],[2.5,97.5]).tolist() for i,n in enumerate(('solution_win_delta','solution_m2_delta','direct_win_rate'))},
        gates=gates,qualified=all(gates.values()))
    folder=HERE/'pilotpruefung';folder.mkdir(exist_ok=True);compressed(folder/'spiele.jsonl.gz',raw)
    result['data_sha']=digest(folder/'spiele.jsonl.gz');save(folder/'ergebnis.json',result)
    print(json.dumps({'complete':192,'outcome':gates}),flush=True)


if __name__=='__main__':main()
