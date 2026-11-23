"""Replay all 20 archived original seats; execute both one-command counterfactuals for suitable pairs."""
import base64
from datetime import datetime
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import sys
import zlib

import numpy as np
import torch

HERE=Path(__file__).resolve().parent
D=HERE.parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from experiments.analysis.relictsuche_20261123.richtungskontrolle.spieler import OneMove
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,THREADS,Monitor,common_source,require,sha,stamp,write_once
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors

WORK=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/richtungskontrolle')
CARDS=(162640018,162640022,162640027,162640186,162640213,162860060,162860075,164050032,164050036,164050141)
FILES=(D/'schwere_starts/partien.jsonl.gz',D/'ortundflotte/duelle_karten.jsonl.gz')


def load_rows():
    result={}
    for index,path in enumerate(FILES):
        with gzip.open(path,'rt') as stream:
            for row in map(json.loads,stream):
                if row['seed'] not in CARDS or row.get('opponent','solution92')!='solution92':continue
                arm=row['name'] if index==0 else row['id']
                name={'v16':'original','reference':'original','gemeinsam':'route','scout':'route'}.get(arm)
                if not name:continue
                key=(row['seed'],row['team'],name)
                require(key not in result,'Duplicated archive record')
                result[key]=dict(digest=row.get('digest',row.get('action_hash')),events=row['events'],
                                 sight=row['sight'],credit=row['credit'],matches=row['matches'],win=row['win'])
    require(len(result)==40,'Wrong set of source cases')
    return result


def hash_observations(public):
    h=sha256()
    def add(path, node):
        if isinstance(node,dict):
            for k in sorted(node):add(path+'/'+k,node[k])
        else:
            a=np.asarray(node)
            h.update((path+str(a.shape)+str(a.dtype)).encode());h.update(a.tobytes())
    add('',public)
    return h.hexdigest()


class Game(Monitor):
    def __init__(self,env,team,actor):
        super().__init__(env,team,'discovery',actor)
        self.actions=[];self.observations=[];self.knowledge=[];self.seen=np.zeros((24,24),bool)

    def reset(self,**kwargs):
        data=super().reset(**kwargs)
        self.public=data[0]
        return data

    def step(self,actions):
        step=self.turn
        self.actions.append(np.stack([actions[f'player_{t}'] for t in (0,1)]).astype(np.int8))
        self.observations.append(hash_observations(self.public))
        self.seen|=np.asarray(self.old['sensor_mask'],bool)
        known=self.actor.base._imitation.belief.point_tiles
        known_tiles=np.flatnonzero(known).tolist() if (step%101==100) else []
        out=super().step(actions)
        self.public=out[0]
        mask=np.asarray(self.public[self.side]['sensor_mask'],bool)
        self.knowledge.append(dict(novel=int(np.count_nonzero(mask&~self.seen)),coverage=int((mask|self.seen).sum()),
                                   known=int(np.count_nonzero(known)),known_tiles=known_tiles))
        return out


def decode(row):
    return np.frombuffer(zlib.decompress(base64.b64decode(row['actions'])),dtype=np.int8).reshape(303,2,16,3)


def check(row,orig,chosen_route,base=None):
    a=decode(row);t=row['team'];decision=row['decision'];arm=row['arm']
    require(sha256(a.astype('<i4').tobytes()).hexdigest()==row['digest'] and len(row['observations'])==303 and len(row['knowledge'])==303,'Corrupt game record')
    historic=chosen_route['events'][:1]
    actual=[] if decision is None else [[decision['step'],decision['uid'],decision['original'],decision['learned']]]
    require(actual==historic, 'Earliest actual proposed move differs from frozen full route')
    if arm=='original':
        require(not row['events'] and row['digest']==orig['digest'] and all(row[k]==orig[k] for k in ('matches','win','sight','credit')),'Original differs from real archive')
        return
    require(decision==base['decision'] and decision['alternative'] is not None,'Arms did not identify the same eligible direction pair')
    s=decision['step'];u=decision['uid'];raw=decode(base)
    d=decision['learned'] if arm=='gelernt' else decision['alternative']
    require(row['events']==[[s,u,decision['original'],d]],'Wrong one and only intervention')
    require(row['observations'][:s+1]==base['observations'][:s+1] and np.array_equal(a[:s],raw[:s]),'Different public prefix or preceding commands')
    expected=raw[s].copy();expected[t,u]=[d,0,0]
    require(np.array_equal(a[s],expected),'Earlier/different opponent or teammate choice')


def play(env,seed,team,mode,signature):
    require(datetime.now(CUTOFF.tzinfo)<CUTOFF,'Study deadline')
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    side=f'player_{team}';actor=OneMove(side,mode);enemy=make_opponent('solution92',f'player_{1-team}')
    m=Game(env,team,actor)
    result=play_game(m,actor,enemy,seed,side,False)
    require_no_agent_errors(actor.base,enemy)
    require_no_agent_errors(actor.scout.base,enemy)
    require(m.turn==303 and m.counts==[303,303] and len(m.matches)==3 and int(sum(x['win'] for x in m.matches)>=2)==result['game_win'],'Incomplete real match')
    arr=np.stack(m.actions)
    return dict(seed=seed,team=team,arm=mode,source=signature,decision=actor.decision,observations=m.observations,
                actions=base64.b64encode(zlib.compress(arr.tobytes())).decode(),digest=m.digest.hexdigest(),knowledge=m.knowledge,
                matches=m.matches,sight=m.first_sight,credit=m.first_credit,events=m.events,win=result['game_win'])


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    require(all(os.getenv(k)=='1' for k in THREADS) and os.getenv('PYTHONHASHSEED')=='0','Process settings')
    limit_threads();arch=load_rows()
    provenance=json.loads((D/'ortflottenkurs/pakete.json').read_text())
    lineage=provenance['runtime_and_lineage']
    require(all(sha(ROOT/k)==v for k,v in lineage.items()), 'Frozen scout sources changed')
    inputs=[*FILES,HERE/'PLAN.md',HERE/'spieler.py',Path(__file__),D/'ortflottenkurs/pakete.json']
    data=dict(cards=list(CARDS),configuration=common_source(),hashes={str(p.relative_to(ROOT)):sha(p) for p in inputs},scout_sources=lineage)
    signature=stamp(data);manifest=dict(identity=signature,inputs=data)
    write_once(WORK/'manifest.json',manifest)
    env=LuxAIS3GymEnv(numpy_output=True);rows=[]
    try:
        for seed in CARDS:
            for team in (0,1):
                original=None
                for arm in ('original','gelernt','alternative'):
                    if arm!='original' and (original['decision'] is None or original['decision']['alternative'] is None):continue
                    path=WORK/'spiele'/f'{seed}_{team}_{arm}.json'
                    row=json.loads(path.read_bytes()) if path.exists() else play(env,seed,team,arm,signature)
                    require(row['source']==signature and (row['seed'],row['team'],row['arm'])==(seed,team,arm),'Different source or identity')
                    check(row,arch[seed,team,'original'],arch[seed,team,'route'],original)
                    write_once(path,row);rows.append(row)
                    if arm=='original':original=row
                    print(seed,team,arm,flush=True)
    finally:env.close()
    require(all(sha(ROOT/k)==v for k,v in data['hashes'].items()) and all(sha(ROOT/k)==v for k,v in lineage.items()),'Changed sources')
    blob=''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rows).encode()
    path=HERE/'partien.jsonl.gz'
    if not path.exists():path.write_bytes(gzip.compress(blob,mtime=0))
    require(gzip.decompress(path.read_bytes())==blob,'Different final archive')
    write_once(HERE/'manifest.json',manifest)
    print('Fertig',len(rows),sha(path),flush=True)


if __name__=='__main__':main()
