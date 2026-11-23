"""Counterfactually transfer only later-match point memories at each of the three additional wins."""
import gzip
import json
from pathlib import Path

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.ortundflotte.kandidat import create
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,PACKAGE,sha,write_once
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map

HERE=Path(__file__).resolve().parent


class Trace(Monitor):
    def __init__(self,env,team,actor,branch,boundary,fields):
        super().__init__(env,team,'discovery',actor if branch else None)
        native=actor.base if branch else actor
        decide=native.act
        self.before={};self.applied=[]
        def read(step,obs):
            if step in (101,202):
                b=native._imitation.belief;b.observe(obs)
                truth=point_tile_map(env.state)
                if b.mirrored:truth=truth[::-1,::-1].T
                true=set(np.flatnonzero(truth).tolist())
                self.before[str(step)]=dict(known=sorted(b._point),true=sorted(true),digest=self.digest.hexdigest())
                if step==boundary:
                    extra=set(fields)-b._point
                    assert extra==set(fields) and extra<=true
                    if extra & b._dead:b.records.clear()
                    for c in sorted(extra):b._mark_point(c)
                    if extra:b._refresh_candidates()
                    self.applied=sorted(extra)
            return decide(step=step,obs=obs)
        native.act=read


def play(env,s,t,branch=False,boundary=None,fields=()):
    side=f'player_{t}'
    actor=create(side) if branch else r3_package_agent(side,PACKAGE)
    opp=make_opponent('solution92',f'player_{1-t}')
    m=Trace(env,t,actor,branch,boundary,fields)
    outcome=play_game(m,actor,opp,s,side,False);require_no_agent_errors(actor,opp)
    assert m.turn==303 and outcome['game_win']==int(sum(r['win'] for r in m.matches)>=2)
    return dict(matches=m.matches,win=outcome['game_win'],digest=m.digest.hexdigest(),states=m.before,applied=m.applied)


def main():
    limit_threads()
    clean=HERE.parent/'abschlusspruefung'
    accounting=json.loads((clean/'nachrechnung.json').read_bytes())
    saved=[(v['seed'],v['team']) for v in accounting['seats'] if v['gain']>0]
    assert len(saved)==3 and not any(v['gain']<0 for v in accounting['seats'])
    with gzip.open(clean/'partien.jsonl.gz','rt') as f:
        bank={tuple(r['key']):r for r in map(json.loads,f)}
    env=LuxAIS3GymEnv(numpy_output=True);listings=[]
    try:
        for s,t in saved:
            baseline,candidate=(play(env,s,t,flag) for flag in (False,True))
            for arm,actual in (('v16',baseline),('ortundflotte',candidate)):
                anchor=bank[s,t,arm,'solution92']
                assert anchor['digest']==actual['digest'] and anchor['matches']==actual['matches']
            trials=[]
            for tick in (101,202):
                k=str(tick);orig,other=[r['states'][k] for r in (baseline,candidate)]
                assert orig['true']==other['true']
                extra=sorted((set(other['known'])-set(orig['known']))&set(orig['true']))
                altered=play(env,s,t,boundary=tick,fields=extra) if extra else baseline
                assert altered['states'][k]==orig and altered['applied']==extra
                assert altered['matches'][:tick//101]==baseline['matches'][:tick//101]
                trials.append(dict(turn=tick,fields=extra,matches=altered['matches'],win=altered['win'],digest=altered['digest']))
            listings.append(dict(seed=s,team=t,original=baseline,scout=candidate,transfers=trials))
    finally:env.close()
    write_once(HERE/'ergebnis.json',dict(archive=sha(clean/'partien.jsonl.gz'),cases=listings))


if __name__=='__main__':main()
