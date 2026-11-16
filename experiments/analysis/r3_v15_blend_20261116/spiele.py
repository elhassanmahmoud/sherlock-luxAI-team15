"""Run deterministic full games using the frozen R3/V15 parent implementations."""
import argparse
import concurrent.futures
import csv
import hashlib
import json
import multiprocessing
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SEATS = ('player_0', 'player_1')
GAME = ('game_win', 'our_wins', 'opp_wins', 'our_points', 'opp_points', 'steps')
DIRECT = range(7173400, 7173416)
SOLUTION = range(7151000, 7151040)


def jobs(phase):
    if phase in ('diagnosis_blend','diagnosis_contact'):
        with (ROOT/'experiments/analysis/movement_soft_20261115/shared_400/sitzvergleich/joined.csv').open() as f:
            return [(phase.split('_')[1], 'solution', int(row['seed']), row['side']) for row in csv.DictReader(f)
                    if row['opponent']=='solution92' and row['r3_win']=='0']
    challenger = 'contact' if phase=='contact' else 'blend'
    pairs = [('r3', 'solution', SOLUTION), ('r3', 'v15', DIRECT)] if phase == 'control' else [
        (challenger, 'solution', SOLUTION), (challenger, 'r3', DIRECT), (challenger, 'v15', DIRECT)]
    return [(a,b,s,p) for a,b,seeds in pairs for s in seeds for p in SEATS]


def initialize(runtime):
    global actors, env
    sys.path.insert(0, str(runtime))
    from scripts.experiment import limit_threads
    limit_threads()
    import torch
    torch.manual_seed(0)
    from luxai_s3.wrappers import LuxAIS3GymEnv
    env = LuxAIS3GymEnv(numpy_output=True)
    actors = {}


def actor(name, seat):
    from scripts.common import make_opponent
    from scripts.r3_v4_contact_agent import ContactAgent, make_r3, make_v4
    if name == 'solution':
        return make_opponent('solution92', seat)
    if name not in actors:
        if name == 'blend':
            from kombination import Blend
            actors[name] = Blend(seat)
        else:
            actors[name] = {'r3': make_r3, 'v15': make_v4, 'contact': ContactAgent}[name](seat)
    return actors[name]


def run_one(key):
    from scripts.common import play_game
    from scripts.par_eval import require_no_agent_errors
    a,b,seed,seat = key
    own = actor(a,seat)
    other = actor(b, SEATS[1-SEATS.index(seat)])
    score = play_game(env, own, other, seed, seat, False)
    require_no_agent_errors(own,other)
    for policy in (own,other):
        if hasattr(policy, 'student'):
            require_no_agent_errors(policy.v14,policy.student)
    game = {k:int(score[k]) for k in GAME}
    if (game['steps'] != 303 or game['our_wins']+game['opp_wins'] != 3
        or game['game_win'] != int(game['our_wins']>=2)):
        raise ValueError(f'Incomplete game on {key}')
    row = dict(arm=a,opponent=b,seed=seed,seat=seat,**game)
    if a in ('blend','contact'):
        row['routing']=own.episode_stats()
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=('control','candidate','contact','smoke','diagnosis_blend','diagnosis_contact'))
    parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args()
    keys=jobs(args.phase) if args.phase!='smoke' else [(a,'solution',7158000,p) for a in ('r3','v15') for p in SEATS]
    if args.phase=='smoke':
        with (ROOT/'experiments/analysis/movement_soft_20261115/shared_400/sitzvergleich/joined.csv').open() as f:
            refs = {(r['opponent'],int(r['seed']),r['side']):r for r in csv.DictReader(f)}
    args.out.mkdir(parents=True,exist_ok=False)
    with (args.out/'games.jsonl').open('x') as dst, concurrent.futures.ProcessPoolExecutor(max_workers=args.workers,
            mp_context=multiprocessing.get_context('spawn'), initializer=initialize,initargs=(args.runtime.resolve(),)) as pool:
        for row in pool.map(run_one,keys):
            if args.phase=='smoke':
                ref=refs['solution92',row['seed'],row['seat']]
                # Compare complete native end scores; these are the earliest published seats.
                for new,old in zip(GAME[:5],('win','matches_won','matches_lost','points','opp_points')):
                    if row[new]!=int(ref[row['arm']+'_'+old]): raise ValueError((new,row,ref))
            dst.write(json.dumps(row,sort_keys=True)+'\n'); dst.flush()
    rows=(args.out/'games.jsonl').read_bytes()
    actual=[json.loads(line) for line in rows.splitlines()]
    if [(r['arm'],r['opponent'],r['seed'],r['seat']) for r in actual]!=keys: raise ValueError('Unexpected schedule')
    (args.out/'complete.json').write_text(json.dumps(dict(n=len(keys),sha256=hashlib.sha256(rows).hexdigest()),indent=2)+'\n')


if __name__=='__main__':
    main()
