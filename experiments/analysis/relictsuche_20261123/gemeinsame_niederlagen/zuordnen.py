"""Replay the two recorded policies on each jointly lost Solution seat, counting generation subtotals."""
import argparse,gzip,json,sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];D=HERE.parent;sys.path.insert(0,str(ROOT))
from experiments.analysis.relictsuche_20261123.punkte_nach_gebiet.zerlegen import measure
from experiments.analysis.relictsuche_20261123.vergleich.spielen import sha,write_once
from scripts.experiment import limit_threads
from luxai_s3.wrappers import LuxAIS3GymEnv

ARCH=D/'sicht1_wiederholung/partien.jsonl.gz';WORK=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/gemeinsame_niederlagen')

def select():
    ref=json.loads((ARCH.parent/'ergebnis.json').read_bytes());assert ref['archive']==sha(ARCH)
    with gzip.open(ARCH,'rt') as f:rows=list(map(json.loads,f))
    assert len(rows)==576==ref['games']
    idx={tuple(r['key']):r for r in rows};assert len(idx)==576
    pairs=[]
    for (s,t,a,o),r in sorted(idx.items()):
        if a!='v16' or o!='solution92' or r['win']:continue
        new=idx[s,t,'ortundflotte',o]
        if not new['win']:pairs.append((r,new))
    assert len(pairs)==11
    return pairs


class Tracker:
    def __init__(self,env):self.env=env
    def __getattr__(self,n):return getattr(self.env,n)
    def reset(self,**kwargs):self.active=[0,0,0];self.turn=0;return self.env.reset(**kwargs)
    def step(self,a):
        out=self.env.step(a);g=int(np.asarray(out[4]['final_state'].relic_nodes_mask).sum())//2;m=self.turn//101;self.active[m]=max(self.active[m],g);self.turn+=1
        return out


def run(lane):
    limit_threads();pairs=select();env=Tracker(LuxAIS3GymEnv(numpy_output=True));identity=sha(ARCH)+sha(Path(__file__))+sha(D/'punkte_nach_gebiet/zerlegen.py')
    try:
        for i in range(lane,len(pairs),2):
            first=None
            for src in pairs[i]:
                seed,t,arm,opp=src['key'];path=WORK/f'{seed}_{t}_{arm}.json'
                if path.exists():
                    row=json.loads(path.read_bytes());assert row['source']==identity
                elif first is not None and src['digest']==first['digest']:
                    assert first['referee']==src['matches'] and src['tape']==pairs[i][0]['tape'];row=dict(first,phase=arm,identical_tape_reused=True);write_once(path,row)
                else:
                    row=measure(env,(arm,seed,t),(src['tape'],src['digest'],src['matches']));assert env.turn==303
                    row.update(active_groups=env.active,source=identity,identical_tape_reused=False);write_once(path,row)
                if first is None:first=row
                print(seed,t,arm,'reused',row['identical_tape_reused'],flush=True)
    finally:env.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('lane',type=int,choices=(0,1));run(p.parse_args().lane)
