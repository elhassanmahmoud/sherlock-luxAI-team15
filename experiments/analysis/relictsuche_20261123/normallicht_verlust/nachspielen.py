"""Reproduce both archived V16/Solution seats on one map and play only its two native R3 controls."""
import argparse
import base64
import gzip
from hashlib import sha256
import json
from pathlib import Path
import random
import sys
import zlib

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,PACKAGE,require,sha,write_once
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map,match_points_after_step

SEED=164300077
ARCHIVE=HERE.parent/'abschlusspruefung/partien.jsonl.gz'
R3=ROOT/'experiments/releases/20261116_r3_finale/agent.zip'
HASH={'v16':'0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099','r3':'8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d'}


def selected():
    with gzip.open(ARCHIVE,'rt') as f:rows=list(map(json.loads,f))
    original=[r for r in rows if r['key'][2:]==['ortundflotte','solution92'] and r['win']==0]
    require(len(rows)==960 and [r['key'][:2] for r in original]==[[SEED,0]],'Wrong source selection')
    targets={}
    for t in (0,1):
        v,c=[next(r for r in rows if r['key']==[SEED,t,k,'solution92']) for k in ('v16','ortundflotte')]
        require(v['tape']==c['tape'] and v['matches']==c['matches'] and v['sensor']==c['sensor']==2,'Wrong control source or sensor')
        a=np.frombuffer(zlib.decompress(base64.b64decode(v['tape'],validate=True)),np.int8).reshape(303,2,16,3)
        require(sha256(a.astype('<i4').tobytes()).hexdigest()==v['digest'],'Source command hash')
        targets[t]=(v,a)
    return targets


class Audit(Monitor):
    def __init__(self,env,team,actor,policy,tape):
        super().__init__(env,team,'general')
        self.player=actor;self.policy=policy;self.original=tape;self.log=[];self.commands=[]

    def reset(self,**params):
        out=super().reset(**params);self.public=out[0];return out

    def step(self,actions):
        t=self.turn;ms=t%101
        proposed=np.stack([actions[f'player_{side}'] for side in (0,1)])
        require(proposed.shape==(2,16,3) and np.all((proposed[:,:,0]>=0)&(proposed[:,:,0]<=5)),'Commands invalid')
        if self.original is not None:
            require(np.array_equal(proposed,self.original[t]),f'Actual competitors diverged from archive on turn {t}')
            actions={f'player_{side}':self.original[t,side].astype(np.int32) for side in (0,1)}
        self.commands.append(proposed.astype(np.int8))
        before=self.old
        views=[sorted(set((np.flatnonzero(v['relic_nodes_mask'])%3+1).tolist())) for v in (self.public[self.side],self.public[f'player_{1-self.team}'])]
        belief=self.player._imitation.belief if self.policy=='v16' else self.player._actor.belief
        def world(x):return x[::-1,::-1].T if belief.mirrored else x
        positive=world(belief.point_tiles).copy();zone=world(belief.relic_zone).copy()
        out=super().step(actions);self.public=out[0];state=out[4]['final_state']
        expected=match_points_after_step(before,self.public[self.side],out[4]);prev=np.asarray(before['team_points'],int)
        wg=np.asarray(state.relic_nodes_map_weights);pay=point_tile_map(state)
        position=np.asarray(state.units.position);live=np.asarray(state.units_mask,bool)&(np.asarray(state.units.energy)[...,0]>=0)
        scored=[]
        for side in (self.team,1-self.team):
            tiles=[]
            for x,y in sorted(set(map(tuple,position[side,live[side]].tolist()))):
                if not pay[x,y]:continue
                # From Sherlock's pre-action public knowledge in both columns.
                tiles.append([x,y,int(wg[x,y]),'positiv' if positive[x,y] else 'nur_gebiet' if zone[x,y] else 'ausserhalb'])
            require(len(tiles)==int(expected[side]-prev[side]),'Credited occupancy does not match Referee points')
            scored.append(tiles)
        self.log.append(dict(t=t,match=t//101+1,local=ms,views=views,active=np.flatnonzero(np.asarray(state.relic_nodes_mask)[:3]).tolist(),
                             scores=expected[[self.team,1-self.team]].tolist(),tiles=scored))
        return out


def main(policy):
    limit_threads();targets=selected();package=PACKAGE if policy=='v16' else R3
    require(sha(package)==HASH[policy],'Wrong official package')
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for t in (0,1):
            raw,tape=targets[t]
            random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED)
            side=f'player_{t}';subject=r3_package_agent(side,package);enemy=make_opponent('solution92',f'player_{1-t}')
            mon=Audit(env,t,subject,policy,tape if policy=='v16' else None)
            result=play_game(mon,subject,enemy,SEED,side,False)
            require_no_agent_errors(subject,enemy)
            require(mon.turn==result['steps']==303 and mon.sensor==2 and len(mon.matches)==3 and mon.counts==[303,303],'Incomplete game')
            require(result['game_win']==int(sum(m['win'] for m in mon.matches)>=2),'Wrong winner')
            cmd=np.stack(mon.commands);h=sha256(cmd.astype('<i4').tobytes()).hexdigest();require(mon.digest.hexdigest()==h,'Wrong played-command hash')
            if policy=='v16':require(mon.matches==raw['matches'] and result['game_win']==raw['win'] and mon.first_sight==raw['sight'] and mon.first_credit==raw['credit'] and raw['digest']==h,'Original tape result mismatch')
            row=dict(policy=policy,side=t,seed=SEED,sensor=2,matches=mon.matches,win=result['game_win'],sight=mon.first_sight,credit=mon.first_credit,command_sha=h,
                     archive_sha=sha(ARCHIVE),policy_sha=sha(package),code_sha=sha(Path(__file__)),turns=mon.log,tape=base64.b64encode(zlib.compress(cmd.tobytes())).decode())
            target=HERE/f'{policy}_p{t}.json.gz';plain=(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode()
            if not target.exists():target.write_bytes(gzip.compress(plain,mtime=0))
            require(gzip.decompress(target.read_bytes())==plain,'Conflicting prior game');print(policy,t,h,mon.matches,flush=True)
    finally:env.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('policy',choices=('v16','r3'));main(p.parse_args().policy)
