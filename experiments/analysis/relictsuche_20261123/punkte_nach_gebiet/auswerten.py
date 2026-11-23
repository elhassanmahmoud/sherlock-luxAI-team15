"""Check all match totals a second time and describe scoring sources separately for each predefined panel."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import numpy as np
from experiments.analysis.relictsuche_20261123.punkte_nach_gebiet.zerlegen import HERE, source
from experiments.analysis.relictsuche_20261123.vergleich.spielen import write_once


def summary(rows):
    out = {}
    for won in (0,1):
        samples = [(np.asarray(r['points'])[m],r['seed']) for r in rows for m in (1,2) if r['referee'][m]['win'] == won]
        values=np.array([v for v,_ in samples]); net=values[:,0]-values[:,1]
        old=net[:,0].sum(1);later=net[:,1:].sum((1,2))
        out[str(won)] = dict(matches=len(samples),cards=len({s for _,s in samples}),mean_by_team_pair_known=values.mean(0).tolist(),
            old_net=float(old.mean()),later_net=float(later.mean()),ahead_old_behind_new=int(((old>=0)&(later<0)).sum()),
            enemy_later_known=float(values[:,1,1:,1].sum(1).mean()),enemy_later_unknown=float(values[:,1,1:,0].sum(1).mean()))
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('folder',type=Path)
    a=parser.parse_args();bank=source();rows=[]
    for key, (tape,digest,matches) in sorted(bank.items()):
        r=json.loads((a.folder/('_'.join(map(str,key))+'.json')).read_bytes())
        assert (r['phase'],r['seed'],r['team'])==key and r['digest']==digest and r['referee']==matches
        actual=np.asarray([m['points'] for m in matches])
        assert np.array_equal(actual,np.array(r['points']).sum((2,3)))
        assert np.array_equal(actual,np.array(r['gains']).reshape(3,101,2).sum(1))
        rows.append(r)
    result={name:summary([r for r in rows if r['phase']==name]) for name in ('entwicklung','kontrolle')}
    result['selected']=[dict(seed=r['seed'],team=r['team'],boundaries=r['boundaries'],results=r['referee'],
        net_by_match_and_pair=(np.array(r['points'])[:,0].sum(2)-np.array(r['points'])[:,1].sum(2)).tolist()) for r in rows if r['phase']=='ursachenprobe']
    write_once(HERE/'ergebnis.json',dict(counts=dict(Counter(r['phase'] for r in rows)),**result))
    data=b''.join(json.dumps(r,separators=(',',':')).encode()+b'\n' for r in rows)
    (HERE/'karten.jsonl.gz').write_bytes(gzip.compress(data,mtime=0))


if __name__=='__main__':main()
