"""Exact original games and real alternative one-step transitions at the geometric candidates."""
import argparse
from collections import Counter, defaultdict
import gzip
import json
import os
from pathlib import Path
import random
import sys

import jax
import numpy as np
import torch
from luxai_s3.wrappers import LuxAIS3GymEnv

from obergrenze import HERE, SOURCE, archived, geometry, sha
sys.path.insert(0,str(SOURCE))
from spuren import PACKAGE, Recorder, make_opponent, play_game, r3_package_agent, require_no_agent_errors
from scripts.experiment import limit_threads


def manual(positions, mask, terrain, reduction):
    power = np.zeros((24,24), dtype=np.int16)
    for x,y in positions[mask]:
        power[max(0,x-1):min(24,x+2),max(0,y-1):min(24,y+2)] += 1
        power[x,y] += 11
    return power - (terrain==1)*reduction > 0


class Replay(Recorder):
    def __init__(self, env, team, actor, raw, oracle, board, physical):
        super().__init__(env,team,actor)
        self.raw, self.oracle, self.board, self.physical = raw, oracle, board, physical
        self.candidates = defaultdict(list)
        for c in oracle["choices"]:
            self.candidates[c["t"]].append(c)
        self.outcomes = []
        self.checks = Counter()

    def visibility(self,state,terrain,uid,positions,mask):
        active = np.asarray(state.relic_nodes_mask,bool)
        places = np.asarray(state.relic_nodes,int)
        masks = [mask, mask & (np.arange(16)!=uid), mask & (np.arange(16)==uid)]
        output = []
        for available in masks:
            pix = np.asarray(self.physical(state,self.env.env_params,terrain,self.team,positions,available),bool)
            assert np.array_equal(pix,manual(positions,available,np.asarray(terrain),self.oracle["reduction"]))
            self.checks["engine_vs_independent_ablations"] += 1
            output.append(np.flatnonzero(active & pix[tuple(places.T)]).astype(int).tolist())
        return output

    def step(self, commands):
        t = self.turn
        pre = self.env.state
        _, key = jax.random.split(self.env.rng_key)
        result = super().step(commands)
        assert self.public[-1] == self.raw["public"][t] and self.policy[-1] == self.raw["policy"][t]
        assert self.referee[-1] == self.raw["referee"][t]
        self.checks["identical_archived_turns"] += 1
        if t>=100:
            return result
        after = self.env.state
        terrain = pre.map_features.tile_type
        nodes, schedule, _, grids, reduction = self.board
        team = self.team
        pos = np.asarray(after.units.position[team],int)
        mask = np.asarray(after.units_mask[team],bool)
        assert np.array_equal(np.asarray(terrain),grids[t])
        assert np.array_equal(np.asarray(after.relic_nodes_mask), (schedule>=0)&(schedule<=t))
        assert np.array_equal(np.asarray(after.relic_nodes),nodes)
        assert np.array_equal(manual(pos,mask,grids[t],reduction),self.old["sensor_mask"])
        self.checks["opening_terrain_activation_full_sensor"] += 1
        if t not in self.candidates:
            return result
        assert not np.asarray(self.old["relic_nodes_mask"]).any()
        for c in self.candidates[t]:
            uid,d = c["uid"], c["d"]
            chosen = np.array(commands[self.side],copy=True)
            assert int(chosen[uid,0])==c["original"] and int(chosen[uid,0])!=d
            chosen[uid] = (d,0,0)
            changed = {**commands,self.side:chosen}
            obs,alternative,_,_,_,_ = self.env.jax_env.step(key,pre,changed,self.env.env_params)
            npos = np.asarray(alternative.units.position[team],int)
            nmask = np.asarray(alternative.units_mask[team],bool)
            other = np.arange(16)!=uid
            rest_unchanged = np.array_equal(mask[other],nmask[other]) and np.array_equal(pos[other&mask],npos[other&mask])
            arrived = bool(nmask[uid] and tuple(npos[uid])==divmod(c["to"],24))
            actual = self.visibility(alternative,terrain,uid,npos,nmask)
            public = np.flatnonzero(np.asarray(obs[self.side].relic_nodes_mask,bool)).astype(int).tolist()
            assert actual[0]==public and np.array_equal(np.asarray(alternative.relic_nodes_mask), np.asarray(after.relic_nodes_mask))
            fixed_pos, fixed_mask = pos.copy(), mask.copy()
            fixed_pos[uid] = divmod(c["to"],24)
            fixed_mask[uid] = True
            fixed = self.visibility(after,terrain,uid,fixed_pos,fixed_mask)
            if arrived and rest_unchanged:
                assert fixed==actual
            for views in (fixed,actual):
                assert set(views[1])|set(views[2]) <= set(views[0])
            self.outcomes.append(dict(**c, arrived=arrived, rest_unchanged=bool(rest_unchanged),
                                      branch_points=int(obs[self.side].team_points[team]), actual=actual, fixed=fixed))
        return result


def main(lane):
    assert os.getenv("PYTHONHASHSEED")=="0"
    limit_threads()
    env = LuxAIS3GymEnv(numpy_output=True)
    @jax.jit
    def physical(st,params,terrain,team,positions,mask):
        alt = st.replace(map_features=st.map_features.replace(tile_type=terrain), units_mask=st.units_mask.at[team].set(mask),
                         units=st.units.replace(position=st.units.position.at[team].set(positions.astype(st.units.position.dtype))))
        return env.jax_env.compute_sensor_masks(alt,params).sensor_mask[team]
    try:
        for group in ("archiv","frisch"):
            folder=HERE/group
            oracle=json.loads(gzip.decompress((folder/"geometrie.json.gz").read_bytes()))
            source={p.name:sha(p) for p in (HERE/'PLAN.md',HERE/'obergrenze.py',Path(__file__),folder/'geometrie.json.gz',
                                            SOURCE/group/'beobachtungen.jsonl.gz',PACKAGE)}
            raw={(r['seed'],r['team']):r for r in archived(group)}
            rows=[]
            for entry in [r for r in oracle if r['choices']][lane::2]:
                seed,team=entry['seed'],entry['team']
                original=raw[seed,team]
                board=geometry(env,seed)
                random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
                side=f'player_{team}'
                actor=r3_package_agent(side,PACKAGE);rival=make_opponent('solution92',f'player_{1-team}')
                rec=Replay(env,team,actor,original,entry,board,physical)
                game=play_game(rec,actor,rival,seed,side,False)
                require_no_agent_errors(actor,rival)
                assert rec.matches==original['matches'] and rec.digest.hexdigest()==original['action_hash']
                # The shared match monitor labels the scoring action; the archived public score arrives one observation later.
                assert game['steps']==rec.turn==303 and rec.first_sight==entry['sight']
                assert min(101,rec.first_credit+1)==entry['credit']
                assert len(entry['choices'])==len(rec.outcomes)
                rows.append(dict(seed=seed,team=team,records=rec.outcomes,checks=rec.checks,action_hash=rec.digest.hexdigest(),source=source))
            payload=(json.dumps(rows,sort_keys=True,separators=(',',':'))+'\n').encode()
            out=folder/f'engine_{lane}.json.gz'
            if out.exists(): assert gzip.decompress(out.read_bytes())==payload
            else: out.write_bytes(gzip.compress(payload,mtime=0))
            print(group,lane,len(rows),'exact replays',flush=True)
    finally:
        env.close()


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('lane',type=int,choices=(0,1))
    main(p.parse_args().lane)
