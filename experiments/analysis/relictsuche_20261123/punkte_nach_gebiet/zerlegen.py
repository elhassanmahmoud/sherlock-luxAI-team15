"""Attribute every actual referee point in archived games to its activation pair and previous public knowledge."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import zlib

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.kundschafter_feldwissen.spielen import archive, read
from experiments.analysis.relictsuche_20261123.vergleich.spielen import PACKAGE, sha, write_once
from scripts.experiment import limit_threads
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def source():
    phases = {}
    for name, fname in [('entwicklung', 'partien'), ('kontrolle', 'allgemein_partien')]:
        bank = read(ROOT/f"punktwissen/{fname}.jsonl.gz")
        for r in bank:
            if r['version'] == 'v16' and r['opponent'] == 'solution92' and r['sensor'] == 1:
                phases[(name, r['seed'], r['team'])] = (r['tape'], r['digest'], r['matches'])
    lookup, _, _ = archive()
    wanted = {(v['seed'], v['team']) for v in json.loads((ROOT/'spaetes_feldwissen/ergebnis.json').read_bytes())['cases']}
    runs = [(v['seed'], v['team'], v['tape'], v['digest']) for v in read(ROOT/'schwere_starts/partien.jsonl.gz') if v['name'] == 'gemeinsam']
    runs.extend((v['seed'], v['team'], v['tape'], v['hash']) for v in read(ROOT/'kundschafter_feldwissen/faelle_partien.jsonl.gz') if v['arm'] == 'beide')
    for s, t, tape, digest in runs:
        if (s,t) in wanted and digest == lookup[s,t,'joint']['hash']:
            phases['ursachenprobe',s,t] = (tape, digest, lookup[s,t,'joint']['matches'])
    assert len([k for k in phases if k[0] == 'ursachenprobe']) == 4
    return phases


def measure(env, key, saved):
    phase, seed, team = key
    tape, digest, matches = saved
    raw = zlib.decompress(base64.b64decode(tape))
    moves = np.frombuffer(raw,np.int8).reshape(303,2,16,3)
    assert hashlib.sha256(moves.astype('<i4').tobytes()).hexdigest() == digest
    obs, info = env.reset(seed=seed)
    actor = r3_package_agent(f'player_{team}', PACKAGE)
    actor.new_game(f'player_{team}')
    actor.set_env_cfg(info['params'])
    belief = actor._imitation.belief
    assert info['params']['unit_sensor_range'] == 1
    pts = np.zeros((3,2,3,2), int)
    hundred = []
    by_t = []
    for tick, cmd in enumerate(moves):
        match, turn = divmod(tick,101)
        before = obs[f'player_{team}']
        belief.observe(before)
        zone = belief.relic_zone if not belief.mirrored else belief.relic_zone[::-1,::-1].T
        known = belief.point_tiles if not belief.mirrored else belief.point_tiles[::-1,::-1].T
        if turn == 0:
            truth = point_tile_map(env.state)
            hundred.append(dict(centers=len(belief.relic_positions), area=int(zone.sum()),active=int(truth.sum()),
                                active_known=int((known&truth).sum()),missing_known_area=int((truth&zone&~known).sum())))
        obs, _, _, _, report = env.step({f'player_{i}':cmd[i].astype(np.int32) for i in (0,1)})
        state = report['final_state']
        valid = np.asarray(state.units_mask,bool) & (np.asarray(state.units.energy)[...,0] >= 0)
        pos = np.asarray(state.units.position)
        level = np.asarray(state.relic_nodes_map_weights)
        active = point_tile_map(state)
        gains = []
        for i, side in enumerate((team,1-team)):
            occupied = np.unique(pos[side][valid[side]],axis=0)
            x,y = occupied.T
            exists = active[x,y]
            x,y = x[exists], y[exists]
            np.add.at(pts[match,i],(level[x,y].astype(int)-1,known[x,y].astype(int)),1)
            gains.append(len(x))
        if turn < 100:
            nextpoints = np.asarray(obs[f'player_{team}']['team_points'],int) - np.asarray(before['team_points'],int)
            assert list(nextpoints[[team,1-team]]) == gains
        by_t.append(gains)
    assert pts.sum(axis=(2,3)).tolist() == [m['points'] for m in matches]
    assert len(hundred)==3
    return dict(phase=phase,seed=seed,team=team,digest=digest,referee=matches,boundaries=hundred,points=pts.tolist(),gains=by_t)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder',type=Path)
    p.add_argument('lane',type=int)
    p.add_argument('stride',type=int)
    a=p.parse_args()
    bank=source()
    limit_threads()
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for k in sorted(bank)[a.lane::a.stride]:
            dest=a.folder/('_'.join(map(str,k))+'.json')
            if dest.exists():
                assert json.loads(dest.read_bytes())['digest']==bank[k][1]
                continue
            write_once(dest,measure(env,k,bank[k]))
    finally:
        env.close()


if __name__=='__main__':
    main()
