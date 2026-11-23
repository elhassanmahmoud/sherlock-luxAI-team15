"""Repeat the frozen scout on one declared, disjoint sensor-one map panel."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import jax
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.abschlusspruefung import vergleich as old
from experiments.analysis.relictsuche_20261123.abschlusspruefung.nachrechnen import verify
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,sha,stamp,write_once
from scripts.experiment import limit_threads
HERE=Path(__file__).resolve().parent
LABEL='ortundflotte'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('op',choices=('seal','play','score'))
    p.add_argument('lane',type=int,nargs='?',default=0);p.add_argument('stride',type=int,nargs='?',default=1)
    a=p.parse_args();limit_threads()
    original=json.loads((old.HERE/'nominierung.json').read_bytes())
    assert old.nomination(LABEL,original['sources'])==original
    record=HERE/'karten.json'
    if a.op=='seal':
        pool=np.arange(165300000,165301500,dtype=np.int32)
        cards=list(map(int,pool[np.asarray(jax.jit(jax.vmap(sensor))(pool))==1][:96]))
        assert len(cards)==len(set(cards))==96 and min(cards)>164300159
        write_once(record,dict(cards=cards,policy=sha(old.HERE/'nominierung.json'),plan=sha(HERE/'PLAN.md'),
                   previous=sha(old.HERE/'nachrechnung.json'),runner=sha(Path(__file__))))
        return
    info=json.loads(record.read_bytes());seeds=info['cards']
    assert info['plan']==sha(HERE/'PLAN.md') and info['runner']==sha(Path(__file__)) and info['policy']==sha(old.HERE/'nominierung.json')
    source=stamp(info)
    keys=[(s,t,m,o) for s in seeds for t in (0,1) for m,o in (('v16','solution92'),(LABEL,'solution92'),(LABEL,'v16'))]
    def file(k):return a.folder/('_'.join(map(str,k))+'.json')
    if a.op=='play':
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            order=[k for offset in range(a.stride) for k in keys[(a.lane+offset)%a.stride::a.stride]]
            for k in order:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                old.play_if_available(file(k),source,lambda:old.run(env,k,source))
        finally:env.close()
        return
    data={k:json.loads(file(k).read_bytes()) for k in keys}
    assert len(data)==576 and all(tuple(r['key'])==k and r['source']==source and r['sensor']==1 for k,r in data.items())
    result,seats=verify(data,LABEL);overall=result['all']
    ok=overall['exact_p_solution']<=.0125 and overall['gain_ci'][0]>0 and overall['direct']>=96 and overall['direct_ci'][0]>=.45
    archive=gzip.compress(b''.join(json.dumps(r,separators=(',',':')).encode()+b'\n' for r in data.values()),mtime=0)
    (HERE/'partien.jsonl.gz').write_bytes(archive)
    write_once(HERE/'ergebnis.json',dict(source=source,archive=sha(HERE/'partien.jsonl.gz'),games=len(data),
                                         qualified=bool(ok),panel=overall,seats=seats))


if __name__=='__main__':main()
