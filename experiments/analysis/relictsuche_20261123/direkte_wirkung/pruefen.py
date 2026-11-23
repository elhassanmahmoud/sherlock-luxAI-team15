"""Pair each existing sensor-one scout duel with the actual original V16 self-play on the exact same map."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.abschlusspruefung.vergleich import run
from experiments.analysis.relictsuche_20261123.abschlusspruefung.nachrechnen import decode
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once
from scripts.experiment import limit_threads
HERE=Path(__file__).resolve().parent
SRC=HERE.parent/'abschlusspruefung'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('store',type=Path);p.add_argument('op',choices=('play','score'))
    p.add_argument('lane',type=int,nargs='?',default=0);p.add_argument('stride',type=int,nargs='?',default=1)
    a=p.parse_args();limit_threads()
    report=json.loads((SRC/'nachrechnung.json').read_bytes())
    labels=sorted({r['seed'] for r in report['seats'] if r['level']==1});assert len(labels)==38
    controls=[(s,0) for s in labels]+[(s,1) for s in labels[:2]+labels[-2:]]
    token=sha(SRC/'partien.jsonl.gz')
    if a.op=='play':
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for s,t in controls[a.lane::a.stride]:
                f=a.store/f'{s}_{t}.json'
                if not f.exists():write_once(f,run(env,(s,t,'v16','v16'),token))
        finally:env.close()
        return
    with gzip.open(SRC/'partien.jsonl.gz','rt') as f:
        bank={(r['key'][0],r['key'][1]):r for r in map(json.loads,f) if r['key'][2:]==['ortundflotte','v16'] and r['sensor']==1}
    out=[];refs=[]
    for s,t in controls:
        row=json.loads((a.store/f'{s}_{t}.json').read_bytes())
        assert row['source']==token and row['key']==[s,t,'v16','v16'];decode(row);refs.append(row)
    by={(r['key'][0],r['key'][1]):r for r in refs}
    for s in labels:
        control=by[s,0];am=decode(control)
        if (s,1) in by:
            other=by[s,1];assert other['digest']==control['digest'] and control['win']+other['win']==1
            assert all(x['points']==y['points'][::-1] and x['win']+y['win']==1 for x,y in zip(control['matches'],other['matches'],strict=True))
        for t in (0,1):
            new=bank[s,t];bm=decode(new)
            events=np.flatnonzero(np.any(am!=bm,axis=(1,2,3)))
            um=None;when=None
            if len(events):
                when=int(events[0]);other=1-t
                assert 16<=when<=83 and np.array_equal(am[when,other],bm[when,other])
                ids=np.flatnonzero(np.any(am[when,t]!=bm[when,t],axis=1));assert len(ids)==1
                um=int(ids[0])
            orig=[dict(points=m['points'][::-1] if t else m['points'],win=1-m['win'] if t else m['win']) for m in control['matches']]
            orig_wins=[m['win'] for m in orig];new_wins=[m['win'] for m in new['matches']]
            base=int(sum(orig_wins)>=2)
            if when is None:assert new['matches']==orig and new['win']==base
            out.append(dict(seed=s,team=t,base=base,candidate=new['win'],swing=new['win']-base,turn=when,uid=um,
                            original=orig,new=new['matches'],match_delta=[b-a0 for a0,b in zip(orig_wins,new_wins,strict=True)]))
    assert len(out)==76 and sum(r['base'] for r in out)==38 and sum(r['candidate'] for r in out)==39
    measures={}
    for title,rows in [('alle',out),('gewonnen',[r for r in out if r['swing']>0]),('verloren',[r for r in out if r['swing']<0])]:
        measures[title]=dict(seats=len(rows),changed=sum(r['turn'] is not None for r in rows),
                            match_deltas=np.array([r['match_delta'] for r in rows]).sum(0).tolist() if rows else [0,0,0])
    write_once(HERE/'ergebnis.json',dict(source=token,controls=len(refs),groups=measures,seats=out))
    (HERE/'kontrollen.jsonl.gz').write_bytes(gzip.compress(b''.join(json.dumps(r,separators=(',',':')).encode()+b'\n' for r in refs),mtime=0))


if __name__=='__main__':main()
