"""Fixed residual-pilot game plans and whole-map outcome analysis."""
from __future__ import annotations

import numpy as np


def keys(start, count):
    return [dict(seed=s,side=f'player_{p}') for s in range(start,start+count) for p in (0,1)]


def fixed_jobs(phase, nominee=None):
    jobs=[]
    def add(agent,opponent,start,count,label=None):
        jobs.append(dict(name=f'{agent}_{label or opponent}',agent=agent,opponent=opponent,
                         keys=keys(start,count)))
    if phase=='selection':
        for agent in ('R61','R62','V14'): add(agent,'solution92',11011000,20)
        for agent in ('R61','R62'): add(agent,'self',11011100,20,'direct')
    elif phase=='confirmation' and nominee in ('R61','R62'):
        add(nominee,'self',11012000,100,'direct')
        for opponent,start,count in [('solution92',11012200,50),('sol92_sq',11012300,20),
                                     ('v13',11012300,20),('default',11012400,10)]:
            for agent in (nominee,'V14'): add(agent,opponent,start,count)
    else:
        raise ValueError('Unknown phase or missing nominated final model')
    return jobs


def validate_rows(job, rows):
    expected=[(k['seed'],k['side']) for k in job['keys']]
    if [(r['seed'],r['side']) for r in rows]!=expected or len(set(expected))!=len(expected):
        raise ValueError('Missing, duplicate or reordered fixed game keys')
    for r in rows:
        expected_win=int(r['our_wins']>r['opp_wins'])
        score=1. if expected_win else .5 if r['our_wins']==r['opp_wins'] else 0.
        if (r['steps']!=303 or r['point_counting_version']!=2 or r['caught_errors']!=0
                or r['game_win']!=expected_win or r['result']!=score
                or not 0<=r['our_wins']<=3 or not 0<=r['opp_wins']<=3
                or r['our_points']<0 or r['opp_points']<0):
            raise ValueError('Invalid complete-game outcome')


def interval(values):
    """Input is one mean per whole map, already keeping roles/players paired."""
    values=np.asarray(values,dtype=float)
    samples=np.random.Generator(np.random.PCG64(0)).integers(0,len(values),(5000,len(values)))
    return np.quantile(values[samples].mean(1),[.025,.975]).tolist()


def summarize(phase,jobs,data):
    if set(data)!={j['name'] for j in jobs}:
        raise ValueError('Missing/excess job')
    for j in jobs: validate_rows(j,data[j['name']])
    wins={k:sum(r['game_win'] for r in rows) for k,rows in data.items()}
    scores={k:np.array([r['result'] for r in rows]).reshape(-1,2).mean(1) for k,rows in data.items()}
    report=dict(phase=phase,wins=wins,games={k:len(v) for k,v in data.items()},
                score_intervals={k:interval(v) for k,v in scores.items()})
    if phase=='selection':
        gates={a:(wins[f'{a}_direct']>=24 and wins[f'{a}_solution92']>=wins['V14_solution92'])
               for a in ('R61','R62')}
        ranked=sorted(gates,key=lambda a:(-wins[f'{a}_direct'],-wins[f'{a}_solution92'],a))
        report.update(gates=gates,nominee=ranked[0] if all(gates.values()) else None,
                      solution_paired_intervals={a:interval(scores[f'{a}_solution92']-scores['V14_solution92'])
                                                 for a in gates})
    elif phase=='confirmation':
        a=next(j['agent'] for j in jobs if j['agent']!='V14')
        direct=scores[f'{a}_direct']; direct_ci=interval(direct)
        panel=np.stack([scores[f'{a}_{o}']-scores[f'V14_{o}'] for o in ('sol92_sq','v13')]).mean(0)
        gates=dict(direct_wins=wins[f'{a}_direct']>100,direct_interval=direct_ci[0]>.5,
                   solution=wins[f'{a}_solution92']>=max(95,wins['V14_solution92']),
                   panel_mean=float(panel.mean())>=0,
                   square=wins[f'{a}_sol92_sq']>=wins['V14_sol92_sq']-2,
                   v13=wins[f'{a}_v13']>=wins['V14_v13']-2,
                   default_perfect=wins[f'{a}_default']==20)
        report.update(gates=gates,qualified=all(gates.values()),nominee=a,
                      direct_interval=direct_ci,panel_paired_mean=float(panel.mean()),
                      panel_paired_interval=interval(panel),
                      solution_paired_interval=interval(scores[f'{a}_solution92']-scores['V14_solution92']))
    else: raise ValueError('Unknown analysis phase')
    return report
