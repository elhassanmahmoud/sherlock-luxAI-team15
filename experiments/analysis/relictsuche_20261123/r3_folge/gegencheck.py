"""Recompute physical credits and map bootstrap from jointly serialized decision windows."""
from collections import defaultdict
import gzip
import json

import numpy as np

from archiv import save
from originale import HERE, digest


def main():
    folder=HERE/'gegenpruefung';raw=folder/'fortsetzungen.jsonl.gz';summary=json.loads((folder/'ergebnis.json').read_text())
    assert digest(raw)==summary['raw_sha']
    by_map=defaultdict(dict);triggers=defaultdict(set);speedups=set();decisions=actions=checks=0
    for line in gzip.decompress(raw.read_bytes()).splitlines():
        r=json.loads(line);seed=r['seed'];opponent=r['rival'];team=r['team'];original=r['control'];alternative=r['treatment']
        assert opponent not in by_map[seed]
        change=0
        if alternative:
            decisions+=1;triggers[opponent].add(seed)
            a=original['decision'];b=alternative['decision'];assert a==b
            for k in ('engine','rng','current_native','current_advice','public_history','current_opponent'):
                assert len(a[k])==64
            assert original['events']==[] and all(e[1]==a['first']['uid'] and e[4]==a['first']['goal'] for e in alternative['events'])
            actions+=len(alternative['events']);times=[];gains=[]
            for branch in (original,alternative):
                observations=branch['track'];assert len(observations)==12
                assert all(not x['target_credited'] or x['target_true'] for x in observations)
                times.append(min([i+1 for i,x in enumerate(observations) if x['target_credited']]+[13]))
                start=np.asarray(a['prior_points']);final=np.asarray(observations[-1]['team_points'])
                points=final-start;gains.append(int(points[team]-points[1-team]))
                checks+=len(observations)
            if times[1]<times[0]:speedups.add(seed)
            change=gains[1]-gains[0]
        else:assert original['decision'] is None and not original['events']
        by_map[seed][opponent]=change
    assert len(by_map)==64 and all(set(x)=={'solution92','v16'} for x in by_map.values())
    assert decisions==summary['both']['trigger'] and actions==summary['both']['changes'] and sorted(speedups)==summary['both']['earlier_maps']
    for name in ('solution92','v16'):
        assert len(triggers[name])==summary[name]['trigger']
        assert sum(v[name] for v in by_map.values())==summary[name]['net12']
    per_map=np.array([sum(by_map[k].values())/2 for k in sorted(by_map)])
    rng=np.random.default_rng(163410);distribution=[]
    for _ in range(40):
        selection=rng.integers(0,len(per_map),size=(500,len(per_map)))
        distribution.extend(np.mean(per_map[selection],axis=1).tolist())
    limits=np.quantile(distribution,[.025,.975]).tolist();assert np.allclose(limits,summary['net12_ci95'])
    save(folder/'nachrechnung.json',dict(maps=len(by_map),opponent_rows=2*len(by_map),identical_decision_histories=decisions,
        alternative_moves=actions,referee_observations=checks,earlier_credit_maps=len(speedups),mean=float(per_map.mean()),interval=limits))
    print('Raw counterfactuals and all map-cluster contrasts independently reconciled')


if __name__=='__main__':main()
