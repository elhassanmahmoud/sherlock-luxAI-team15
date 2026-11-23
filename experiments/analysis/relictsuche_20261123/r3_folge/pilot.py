"""Conditional, independent 32-map complete-game pilot for the frozen M2 intervention."""
import argparse
from fcntl import LOCK_EX, LOCK_NB, flock
import json
import random
from pathlib import Path

import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

from berater import Advice
from gegenrunde import cards, identity
from originale import HERE, PACKAGE, SCRATCH, digest, limit_threads, make_opponent, r3_package_agent
from spielen import Monitor, play_game, require_no_agent_errors, stamp, write_once


class FullMonitor(Monitor):
    def __init__(self,env,team,actor):
        super().__init__(env,team,'discovery')
        self.advisor=actor
        self.native=None
        if actor is not None:
            original=actor.base.act
            def keep(*a,**kw):
                assert self.native is None
                order=original(*a,**kw);self.native=np.asarray(order).copy()
                return order
            actor.base.act=keep

    def step(self,actions):
        if self.advisor is not None:
            assert self.native is not None
            submitted=np.asarray(actions[self.side])
            delta=np.where(np.any(submitted!=self.native,axis=1))[0]
            assert len(delta)<=1
            if len(delta):
                u=int(delta[0]);first=self.advisor.first;assert first is not None
                assert self.turn//101==1 and self.turn%101 in range(8,58)
                assert first['uid']==u and self.matches[0]['win']==1 and self.old['units_mask'][self.team,u]
                assert 0<=self.native[u,0]<5 and 1<=submitted[u,0]<5 and (submitted[u,1:]==0).all()
                assert (self.advisor.last_r3[u]==submitted[u]).all()
                self.events.append([self.turn,u,int(self.native[u,0]),int(submitted[u,0]),first['goal']])
            assert self.events==self.advisor.events
            self.native=None
        return super().step(actions)


def game(env,seed,team,arm,source):
    side=f'player_{team}';other=f'player_{1-team}'
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    actor=r3_package_agent(side,PACKAGE) if arm=='reference' else Advice(side,True)
    opp=r3_package_agent(other,PACKAGE) if arm=='direct' else make_opponent('solution92',other)
    monitor=FullMonitor(env,team,actor if arm!='reference' else None)
    raw=play_game(monitor,actor,opp,seed,side,False)
    require_no_agent_errors(actor,opp)
    if arm!='reference':
        require_no_agent_errors(actor.base,opp)
        assert actor.teacher is not None and not actor.teacher.caught_errors
        assert len({r[1] for r in monitor.events})<=1 and len(monitor.events)<=3
    assert raw['steps']==monitor.turn==303 and monitor.counts==[303,303]
    wins=[m['win'] for m in monitor.matches]
    assert len(wins)==3 and raw['game_win']==int(sum(wins)>=2)
    return dict(seed=seed,team=team,arm=arm,source=source,sensor=monitor.sensor,matches=monitor.matches,win=raw['game_win'],
            sight=monitor.first_sight,credit=monitor.first_credit,events=monitor.events,engine_actions=monitor.counts,
            trace=monitor.digest.hexdigest(),errors=[0,0])


def run(lane):
    limit_threads()
    result=json.loads((HERE/'gegenpruefung/ergebnis.json').read_text())
    assert result['qualified'] and all(result['gates'].values())
    assert (HERE/'gegenpruefung/nachrechnung.json').is_file()
    base=identity();source=dict(causal=base,pilot=digest(Path(__file__)),gate=digest(HERE/'gegenpruefung/ergebnis.json'))
    work=SCRATCH/'pilot';work.mkdir(exist_ok=True);write_once(work/'quelle.json',source);version=stamp(source)
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        with (work/f'lane{lane}.lock').open('a+') as lock:
            flock(lock,LOCK_EX|LOCK_NB)
            for i,seed in enumerate(cards(163420000,32)):
                for team in (0,1):
                    for j,arm in enumerate(('reference','solution','direct')):
                        if (6*i+3*team+j+i)%2!=lane:continue
                        target=work/f'{seed}-{team}-{arm}.json'
                        if target.exists():
                            assert json.loads(target.read_text())['source']==version
                            continue
                        write_once(target,game(env,seed,team,arm,version))
    finally:env.close()
    assert identity()==base
    print('Completed pilot lane',lane,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('lane',type=int,choices=(0,1));run(p.parse_args().lane)
