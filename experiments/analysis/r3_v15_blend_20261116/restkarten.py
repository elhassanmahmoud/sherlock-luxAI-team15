"""Complete the untouched 60-map remainder after the primary Solution comparison hit a ceiling."""
import argparse
import concurrent.futures
import csv
import hashlib
import json
import multiprocessing
from pathlib import Path
from spiele import HERE, ROOT, SEATS, initialize, run_one


def play(args):
    full = [(args.arm,'solution',seed,side) for seed in range(7151040,7151100) for side in SEATS]
    args.out.mkdir(parents=True,exist_ok=False)
    log = args.out/'games.jsonl'
    with log.open('x') as writer, concurrent.futures.ProcessPoolExecutor(max_workers=args.workers,
            mp_context=multiprocessing.get_context('spawn'),initializer=initialize,initargs=(args.runtime.resolve(),)) as pool:
        for row in pool.map(run_one,full):
            writer.write(json.dumps(row,sort_keys=True)+'\n')
            writer.flush()
    rows=log.read_bytes()
    if [(r['arm'],r['opponent'],r['seed'],r['seat']) for r in map(json.loads,rows.splitlines())]!=full:
        raise ValueError('Unexpected remainder schedule')
    (args.out/'complete.json').write_text(json.dumps(dict(n=len(full),sha256=hashlib.sha256(rows).hexdigest()),indent=2)+'\n')


def evaluate():
    import numpy as np
    def read(arm):
        folder=HERE/('rest_'+arm)
        buf=(folder/'games.jsonl').read_bytes()
        seal=json.loads((folder/'complete.json').read_bytes())
        if seal!={'n':120,'sha256':hashlib.sha256(buf).hexdigest()}: raise ValueError(arm)
        group={}
        for r in map(json.loads,buf.splitlines()):
            if not (r['arm']==arm and r['opponent']=='solution' and r['steps']==303 and r['our_wins']+r['opp_wins']==3
                    and r['game_win']==int(r['our_wins']>r['opp_wins'])): raise ValueError(r)
            key=(r['seed'],r['seat'])
            if key in group: raise ValueError(key)
            group[key]=r['game_win']
        return group
    base=read('r3'); blend=read('blend')
    keys=[(seed,side) for seed in range(7151040,7151100) for side in SEATS]
    path=ROOT/'experiments/analysis/kaggle3_20261115/devB_hyb_v4_mixed.csv'
    with path.open() as f:
        orig=[r for r in csv.DictReader(f) if r['opponent']=='solution92' and 7151040<=int(r['seed'])<7151100]
    v15={(int(r['seed']),r['side']):int(r['game_win']) for r in orig}
    if not(len(orig)==120 and set(base)==set(blend)==set(v15)==set(keys) and all(int(r['point_counting_version'])==2 for r in orig)):
        raise ValueError('Invalid paired arms')
    result={'r3_wins':sum(base.values()),'blend_wins':sum(blend.values()),'v15_wins':sum(v15.values()),'games_per_arm':len(keys),'v15_csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    for name,ref in [('r3',base),('v15',v15)]:
        delta=np.asarray([blend[k]-ref[k] for k in keys]).reshape(-1,2).mean(1)
        means=np.random.default_rng(2711).choice(delta,size=(10000,len(delta))).mean(1)
        result[name+'_comparison']={'delta':float(delta.mean()),'ci95':np.quantile(means,[.025,.975]).tolist(),
            'gained':[k for k in keys if blend[k]>ref[k]],'lost':[k for k in keys if blend[k]<ref[k]]}
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    run=sub.add_parser('play')
    run.add_argument('arm',choices=('blend','r3'));run.add_argument('--runtime',required=True,type=Path)
    run.add_argument('--out',type=Path,required=True);run.add_argument('--workers',type=int,default=2)
    sub.add_parser('assess')
    args=parser.parse_args()
    if args.mode=='play':
        play(args)
    else:
        evaluate()
