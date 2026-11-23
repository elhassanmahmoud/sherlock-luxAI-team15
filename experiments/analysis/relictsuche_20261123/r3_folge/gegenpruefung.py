"""Paired map-level evaluation of every requested counterfactual continuation."""
from collections import Counter
import json

import numpy as np

from archiv import compressed, save
from gegenrunde import cards, identity
from originale import HERE, SCRATCH, digest
from spielen import stamp


def metrics(row):
    b=row['control'];a=row['treatment'];team=row['team'];opp=1-team
    out=dict(trigger=int(bool(a)),earlier=0,later=0,our6=0,our12=0,net6=0,net12=0,changes=0,wrong_target=0)
    if not a:
        assert b['decision'] is None and b['events']==[] and b['track']==[]
        return out
    assert a['decision']==b['decision'] and not b['events'] and a['events'] and len(a['track'])==len(b['track'])==12
    assert a['action_steps']==b['action_steps']==a['decision']['first']['step']+12
    assert a['decision']['prior_match_wins'][team]==1
    for i in (6,12):
        old=b['track'][i-1]['team_points'];new=a['track'][i-1]['team_points']
        out['our'+str(i)]=new[team]-old[team]
        out['net'+str(i)]=(new[team]-old[team])-(new[opp]-old[opp])
    def first(x):return next((i+1 for i,t in enumerate(x['track']) if t['target_credited']),13)
    out.update(earlier=int(first(a)<first(b)),later=int(first(a)>first(b)),changes=len(a['events']),
               wrong_target=int(not a['track'][0]['target_true']))
    return out


def main():
    queue=cards();raw=[];small=[];work=SCRATCH/'gegenrunde';source=stamp(identity())
    assert len(list(work.glob('*-*-*.json')))==128
    for i,s in enumerate(queue):
        for opp in ('solution92','v16'):
            row=json.loads((work/f'{s}-{i%2}-{opp}.json').read_text())
            assert [row[k] for k in ('seed','team','rival','source')]==[s,i%2,opp,source]
            raw.append(row);small.append(dict(seed=s,team=i%2,rival=opp,m1_win=row['control']['m1'],**metrics(row)))
    def describe(rows):
        n=len(rows)
        out={k:sum(r[k] for r in rows) for k in ('m1_win','trigger','earlier','later','changes','wrong_target','net6','net12','our6','our12')}
        out['rows']=n;out['mean_net12']=out['net12']/n
        for k in ('earlier','later','trigger'):
            out[k+'_maps']=sorted({r['seed'] for r in rows if r[k]})
        out['net12_changed_games']=sum(r['net12']!=0 for r in rows)
        out['net12_gain_games']=sum(r['net12']>0 for r in rows)
        out['net12_harm_games']=sum(r['net12']<0 for r in rows)
        return out
    stats={k:describe([r for r in small if r['rival']==k]) for k in ('solution92','v16')}
    stats['both']=describe(small)
    stats['by_seat']={str(t):describe([r for r in small if r['team']==t]) for t in (0,1)}
    arr=np.asarray([r['net12'] for r in small],float).reshape(64,2).mean(1)
    rng=np.random.default_rng(163410);boot=arr[rng.integers(0,len(arr),(20000,len(arr)))].mean(1)
    stats['net12_ci95']=np.percentile(boot,[2.5,97.5]).tolist()
    stats['gates']=dict(ten_trigger_maps=len(stats['both']['trigger_maps'])>=10,
            four_games_per_opponent=min(stats[k]['trigger'] for k in ('solution92','v16'))>=4,
            four_earlier_target_maps=len(stats['both']['earlier_maps'])>=4,
            positive_lower_net12=stats['net12_ci95'][0]>0,
            each_opponent_nonnegative=min(stats[k]['net12'] for k in ('solution92','v16'))>=0,
            common_prefix_and_uid=all(a['control']['decision']==a['treatment']['decision']
                  and len({e[1] for e in a['treatment']['events']})==1 for a in raw if a['treatment']))
    stats['qualified']=all(stats['gates'].values())
    out=HERE/'gegenpruefung';out.mkdir(exist_ok=True)
    compressed(out/'fortsetzungen.jsonl.gz',raw);compressed(out/'differenzen.jsonl.gz',small)
    stats['raw_sha']=digest(out/'fortsetzungen.jsonl.gz');stats['source']=json.loads((work/'quelle.json').read_text())
    save(out/'ergebnis.json',stats)
    print(json.dumps({'qualified':stats['qualified'],'gates':stats['gates'],'net12':stats['both']['mean_net12']}),flush=True)


if __name__=='__main__':main()
