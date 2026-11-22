"""Read completed baseline and eight-step continuation records, never partial games."""
import argparse
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import numpy as np

HERE=Path(__file__).resolve().parent


def read(source):
    return json.loads(source.read_text())


def evaluate(folder):
    orig=[read(p) for p in sorted(folder.glob('*.json')) if '_m' not in p.stem]
    if len(orig) not in (8,16):
        raise ValueError('Missing diagnostic games')
    expected={(s, t) for s in range(160347000,160347000+len(orig)//2) for t in range(2)}
    if {(r['seed'],r['side']) for r in orig}!=expected or len(orig)!=len(expected):
        raise ValueError('Seed or seat mismatch')
    for r in orig:
        if r['steps']!=303 or len(r['frames'])!=303 or sum(r['match_wins'])!=3:
            raise ValueError('Incomplete diagnostic')
        if any(f['step']!=i for i,f in enumerate(r['frames'])):
            raise ValueError('Frame index')
    first=[r for r in orig if r['seed']<160347004]
    required=8 if sum(bool(r['selected']) for r in first)==8 else 16
    if len(orig)!=required:
        raise ValueError(f'Predeclared sample size {required}')
    cases={}; censored=[]; effects=[]; causes=defaultdict(lambda:Counter()); teachers=Counter(); barriers=Counter()
    for r in orig:
        for event in r['events']:
            if not (65<=event['ms']<=94 and event['energy']>=10 and event['old']!=5 and event['gap']<=np.log(8)):
                raise ValueError('Unsupported move')
            teachers['proposed' if event['teacher']==event['move'] else 'original' if event['teacher']==event['old'] else 'other']+=1
        if r['seed']!=160347000:  # fixed coverage of the original diagnostic
            barriers.update(r['barriers'])
        for row in r['losses']:
            causes[row['cause']].update({'episodes':1,'vacant_turns':row['vacant_turns'],'returned':int(row['returned'])})
        for case in r['selected']:
            k=(r['seed'],r['side'],case['match'])
            if case['ms']>93:
                censored.append(k)
                continue
            if k in cases: raise ValueError('Duplicate case')
            expected_event=next(e for e in r['events'] if e['match']==case['match'])
            if any(case[key]!=value for key,value in expected_event.items()): raise ValueError('Case selection')
            cases[k]=case
    for p in sorted(folder.glob('*_m*.json')):
        c=read(p); case=c['event'];k=(c['seed'],c['side'],case['match'])
        if cases.pop(k)!=case or c['steps']!=case['step']+8:
            raise ValueError('Wrong counterfactual')
        a=c['alternative'];b=c['original']
        own=a['points'][0]-b['points'][0]; opp=a['points'][1]-b['points'][1]
        effects.append(dict(seed=c['seed'],side=c['side'],match=case['match'],ms=case['ms'],own=own,opp=opp,
                            net=own-opp,reoccupancy=a['tile_turns']-b['tile_turns']))
    if cases:
        raise ValueError(f'{len(cases)} missing continuations')
    by_seed=defaultdict(list)
    for e in effects:by_seed[e['seed']].append(e['net'])
    means={s:statistics.mean(v) for s,v in sorted(by_seed.items())}
    own=sum(e['own'] for e in effects);net=sum(e['net'] for e in effects)
    gates=dict(eight=len(effects)>=8,four_maps=len(means)>=4,own=own>0,net=net>0,
               majority=sum(v>0 for v in means.values()) > sum(v<0 for v in means.values()))
    return dict(games=len(orig),maps=len(orig)//2,events=sum(teachers.values()),event_games=sum(bool(r['events']) for r in orig),
                decisions_by_teacher=teachers,losses=causes,barrier_games=sum(r['seed']!=160347000 and 'barriers' in r for r in orig),vacancy_barriers=barriers,
                right_censored_cases=censored,effect_by_event=effects,mean_net_by_map=means,gates=gates,passed=all(gates.values()))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);args=p.parse_args()
    print(json.dumps(evaluate(args.folder),indent=2,ensure_ascii=False))
