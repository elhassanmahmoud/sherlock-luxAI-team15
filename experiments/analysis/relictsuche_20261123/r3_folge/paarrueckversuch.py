"""Four fixed one-map interventions at the boundary, checked against complete pilot anchors."""
import argparse
from hashlib import sha256
import gzip
import json
from pathlib import Path
import pickle
import random

import jax
from luxai_s3.wrappers import LuxAIS3GymEnv
import numpy as np
import torch

from archiv import compressed, save
from berater import Advice
from gegenrunde import credited, hash_value, update_hash
from originale import HERE, PACKAGE, SCRATCH, digest, limit_threads, make_opponent, r3_package_agent
from pilot import FullMonitor
from scripts.scoring import match_points_after_step, point_tile_map
from spielen import play_game, require_no_agent_errors, write_once

SEED=163420124
PAIR=((12,2),(21,11))
IDS={24*x+y for x,y in PAIR}
MODES=('native','plus','advice','minus')


def visible_status(b):
    return dict(points=sorted(b._point),dead=sorted(f for f in IDS if f in b._dead),
                dead_hist=sorted(f for f in IDS if f in b._dead_hist),records=len(b.records))


def set_status(b,mode):
    assert b.symmetry and not b.mirrored and b.match_idx==2 and b.match_step==0 and b._last_step==202
    assert not b.records
    b._refresh_candidates();b.point_coords()
    before=visible_status(b);old_points=b.point_tiles.copy();old_dead=b.dead_tiles.copy();old_candidates=b.candidate.copy()
    # Whole-field arrays and integer sets are reconciled separately, including all 574 untouched cells.
    allowed={'_point','_dead','point_tiles','dead_tiles','candidate','_cache','_coords_dirty','_cand_dirty'}
    preserve={k:pickle.dumps(v,protocol=5) for k,v in vars(b).items() if k not in allowed}
    old_dead_set=set(b._dead);other=np.ones((24,24),bool)
    for xy in PAIR:other[xy]=False
    assert (IDS<=b._point) if mode in ('advice','minus') else not (IDS&b._point)
    if mode=='plus':
        previous_newly_proven=b.newly_proven
        b._mark_point(min(IDS))
        b.newly_proven=previous_newly_proven
    elif mode=='minus':
        assert not (IDS&b._dead) and not any(b.dead_tiles[p] for p in PAIR)
        b._point.difference_update(IDS)
        for xy in PAIR:b.point_tiles[xy]=False
        b._coords_dirty=True;b._cand_dirty=True
    b._refresh_candidates();coords={tuple(x) for x in b.point_coords().tolist()}
    assert coords=={divmod(i,24) for i in b._point}
    after=visible_status(b)
    assert set(after['points'])^set(before['points'])==(IDS if mode in ('plus','minus') else set())
    assert (old_dead_set^b._dead)<=IDS
    for arr,previous in ((b.point_tiles,old_points),(b.dead_tiles,old_dead),(b.candidate,old_candidates)):
        assert np.array_equal(arr[other],previous[other])
    assert all(pickle.dumps(vars(b)[k],protocol=5)==v for k,v in preserve.items())
    return dict(before=before,after=after,untouched_fields=int(other.sum()))


class PairMonitor(FullMonitor):
    def __init__(self,env,actor,mode):
        self.is_advice=mode in ('advice','minus')
        super().__init__(env,0,actor if self.is_advice else None)
        self.actor_for_state=actor;self.mode=mode;self.history=sha256();self.actions=sha256();self.boundary=None;self.intervention=None
        self.turns=[];self.credit=[[0,0],[0,0]];self.all_post_gains=[0,0]

    def reset(self,**kwargs):
        result=super().reset(**kwargs);self.both=result[0]
        return result

    def step(self,commands):
        t=self.turn;o=self.old
        if t<202:
            update_hash(self.history,self.both);update_hash(self.history,commands)
            for i in (0,1):self.actions.update(np.asarray(commands[f'player_{i}']).astype('<i4',copy=False).tobytes())
        policy=self.actor_for_state.base._imitation if self.is_advice else self.actor_for_state._imitation
        b=policy.belief
        if t==202:
            assert not np.any(commands['player_0']) and int(o['match_steps'])==0
            assert all(point_tile_map(self.env.state)[xy] for xy in PAIR)
            self.boundary=dict(both_public_and_commands=self.history.hexdigest(),all_202_commands=self.actions.hexdigest(),
                engine=hash_value(self.env.state),rng=hash_value(jax.random.key_data(self.env.rng_key)),public_now=hash_value(self.both),
                finished_matches=self.matches[:],team_wins=np.asarray(o['team_wins']).tolist())
            self.intervention=set_status(b,self.mode)
        known=[bool(b.point_tiles[p]) for p in PAIR] if t>=202 else None
        out=super().step(commands);self.both=out[0]
        if t>=202:
            new=out[0][self.side];s=out[4]['final_state'] if t==302 else self.env.state
            cells=credited(s);points=match_points_after_step(o,new,out[4]);inc=(points-np.asarray(o['team_points'])).tolist()
            assert inc==[len(c) for c in cells]
            for i in (0,1):
                self.all_post_gains[i]+=inc[i]
                for j,(x,y) in enumerate(PAIR):self.credit[j][i]+=int(24*x+y in cells[i])
            self.turns.append(dict(turn=t-202,known=known,own=hash_value(commands['player_0']),opp=hash_value(commands['player_1']),
                  score=points.tolist(),occupied=[[int(24*x+y in c) for c in cells] for x,y in PAIR]))
        return out


def run(family):
    limit_threads();env=LuxAIS3GymEnv(numpy_output=True);work=SCRATCH/'paarrueckversuch';work.mkdir(exist_ok=True)
    anchors={r['arm']:r for s in gzip.decompress((HERE/'pilotpruefung/spiele.jsonl.gz').read_bytes()).splitlines()
             if (r:=json.loads(s))['seed']==SEED and r['team']==0}
    modes=MODES[:2] if family=='native' else MODES[2:]
    try:
        for mode in modes:
            assert mode in MODES
            anchor=anchors['reference' if family=='native' else 'solution'];side='player_0'
            random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED)
            actor=Advice(side,True) if family=='advice' else r3_package_agent(side,PACKAGE)
            rival=make_opponent('solution92','player_1');mon=PairMonitor(env,actor,mode)
            g=play_game(mon,actor,rival,SEED,side,False);require_no_agent_errors(actor,rival)
            assert g['steps']==303 and mon.turn==303 and len(mon.turns)==101 and mon.matches[-1]['points']==mon.all_post_gains
            assert mon.matches[:2]==anchor['matches'][:2] and mon.events==anchor['events']
            if mode in ('native','advice'):assert mon.digest.hexdigest()==anchor['trace'] and mon.matches==anchor['matches']
            row=dict(mode=mode,matches=mon.matches,win=g['game_win'],boundary=mon.boundary,intervention=mon.intervention,field_credit=mon.credit,
                     trace=mon.digest.hexdigest(),turns=mon.turns,source=digest(Path(__file__)),plan=digest(HERE/'PAARPLAN.md'))
            write_once(work/(mode+'.json'),row)
    finally:env.close()


def summarize():
    work=SCRATCH/'paarrueckversuch';raw={m:json.loads((work/(m+'.json')).read_text()) for m in MODES};out=HERE/'paartransfer';out.mkdir(exist_ok=True)
    stats={}
    for mode,r in raw.items():
        base=raw['native' if mode in ('native','plus') else 'advice']
        assert r['source']==digest(Path(__file__)) and r['plan']==digest(HERE/'PAARPLAN.md')
        assert r['boundary']==base['boundary'] and r['intervention']['before']==base['intervention']['before']
        own_first=next((row['turn'] for row,b in zip(r['turns'],base['turns'],strict=True) if row['own']!=b['own']),None)
        enemy_first=next((row['turn'] for row,b in zip(r['turns'],base['turns'],strict=True) if row['opp']!=b['opp']),None)
        score_first=next((row['turn'] for row,b in zip(r['turns'],base['turns'],strict=True) if row['score']!=b['score']),None)
        first_known=next((row['turn'] for row in r['turns'] if all(row['known'])),None)
        stats[mode]=dict(matches=r['matches'],whole_win=r['win'],credit_on_pair=r['field_credit'],both_first_known_m3=first_known,
                         first_own_command_changed=own_first,first_enemy_command_changed=enemy_first,first_scores_changed=score_first,
                         prefix_sha=r['boundary']['all_202_commands'],full_sha=r['trace'],status=r['intervention'])
    result=dict(seed=SEED,team=0,world_fields=PAIR,arms=stats,native_plus_sufficient=bool(raw['plus']['win'] and raw['plus']['matches'][2]['win']),
        full_r3_with_pair_removed_wins=bool(raw['minus']['win']),complete_anchors=2,full_games=4,checked_m3_post_states=404)
    compressed(out/'verlaeufe.jsonl.gz',raw.values());save(out/'ergebnis.json',result)
    print({m:r['matches'][-1]['points'] for m,r in stats.items()})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family',choices=('native','advice','auswerten'));f=p.parse_args().family
    summarize() if f=='auswerten' else run(f)
