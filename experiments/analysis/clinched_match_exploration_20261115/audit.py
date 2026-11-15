"""Read archived public observations; no agent, model or engine imports."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

DIR = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0), (0, 0))

def scenarios(candidate, known, blocked, units, size=24):
    # Even in a clinched match, keep SAP, sole point holders and the baseline's intended destinations.
    # An unvisited own-half candidate one legal step away is a mechanically feasible public target.
    origins = Counter(q[0] for q in units)
    dest = []
    for (x,y), action, _, _ in units:
        dx,dy = DIR[action]
        dest.append((x+dx, y+dy))
    available = set()
    single = set()
    for i, ((x,y), action, can_move, mask) in enumerate(units):
        if action == 5 or not can_move or ((x,y) in known and origins[x,y] == 1):
            continue
        for d,(dx,dy) in enumerate(DIR[1:5], 1):
            target=(x+dx,y+dy)
            if d not in mask or target not in candidate or target in blocked or sum(target)>=size-1:
                continue
            if target in origins or target in dest: continue
            available.add(target)
            if not any(v in candidate for j,v in enumerate(dest) if j!=i):
                single.add(target)
    return available,single

def frames(rows):
    possible=set(); single=set(); first=None; first_single=None; n=0
    for ms,own,opp,cand,pt,block,units in rows:
        # Before the action at match_step ms, ms..100 (both inclusive) can still score.
        # Reserve the last action: public point inference should observe the result before reset.
        if ms>=100 or own-opp <=16*(101-ms): continue
        n+=1
        a,b=scenarios(cand,pt,block,units)
        possible |= a; single |= b
        if a and first is None: first=ms
        if b and first_single is None: first_single=ms
    return dict(frames=n, first=first, first_single=first_single, destinations=sorted(possible), single=sorted(single))

def cells(mask):
    return set(map(tuple,np.argwhere(mask)))

def packed(directory):
    # Invert the exact archived float32 -> float16 feature for integer point differences.
    # First preimage gives a rigorous lower bound even when tanh saturates to 1.0.
    margins = np.arange(-1616,1617)
    packed_margin=np.tanh(margins/20.).astype(np.float32).astype(np.float16)
    possible_lower={float(x):int(margins[np.nonzero(packed_margin==x)[0][0]]) for x in np.unique(packed_margin)}
    out=[]
    for p in sorted(directory.glob('*_solution92.npz')):
        seed=int(p.name.split('_')[0][1:])
        if not 7287000<=seed<7287048: continue
        with np.load(p,allow_pickle=False) as z:
            meta=json.loads(z['meta'].item()); f=z['feats']; g=z['global_step'].astype(int); si=z['step']; pos=z['pos']; board=z['planes']; mask=z['mask']; acted=z['played_act']
        groups=[[] for _ in range(2)]
        for fi,step in enumerate(g):
            m,ms=divmod(int(step),101)
            if m>=2 or ms<85 or ms>=100: continue
            idx=np.flatnonzero(si==fi); f0=f[idx[0]]
            if round(float(f0[12])*3)>=1 and m==1: continue  # a win now already wins the game
            lower=possible_lower[float(f0[11])]
            if lower<=16*(101-ms): continue
            units=[(tuple(map(int,pos[j])),int(acted[j]),f[j,3]==0,set(np.flatnonzero(mask[j]))) for j in idx]
            groups[m].append((ms,lower,0,cells(board[fi,1]),cells(board[fi,0]),cells(board[fi,5]),units))
        for m,rows in enumerate(groups):
            data=frames(rows); nxt=np.flatnonzero(g==(m+1)*101+1)
            if len(nxt)!=1: raise ValueError((p.name,m))
            bk=board[nxt[0]]; next_unknown=cells(bk[1]); possible=set(map(tuple,data['destinations']))
            data['stayed_candidate_next_match']=sorted(possible & next_unknown)
            out.append(dict(seed=seed,side=meta['side'],series_won=meta['our_wins']>meta['opp_wins'],match=m+1,**data))
    return out

def public(directory):
    out=[]
    for panel in ('cases_v1','controls_v1'):
        root=directory/panel; manifest=json.loads((root/'summary.json').read_text())
        for game in manifest['records']:
            # This panel only logged matches 2/3. Among whole-game LOSSES (1:2), if M2 was
            # clinched from ahead it cannot have been the second match win of the series.
            if game['our_wins']>=game['opp_wins']: continue
            p=root/game['path']; assert hashlib.sha256(p.read_bytes()).hexdigest()==game['sha256']
            rows=[]; observations=[]
            with gzip.open(p,'rt') as fp:
                for line in fp:
                    o=json.loads(line)
                    observations.append(o)
                    if o['match']!=2: continue
                    conv=lambda k: set(map(tuple,o[k]))
                    units=[(tuple(u['pos']),u['action'][0],u['energy']>=o['move_cost'],set(u['allowed'])) for u in o['units']]
                    rows.append((o['mstep'],o['own_points'],o['opp_points'],conv('candidate'),conv('known_points'),conv('blocked_belief'),units))
            result=frames(rows)
            targets=[list(t) for t in result['destinations']]
            first_next=next(o for o in observations if o['match']==3 and o['mstep']==25)
            result['still_candidate_at_m3_step25']=[t for t in targets if t in first_next['candidate']]
            result['first_m3_confirmations']=[dict(target=t,step=next(o['mstep'] for o in observations if o['match']==3 and t in o['known_points'])) for t in targets if any(o['match']==3 and t in o['known_points'] for o in observations)]
            out.append(dict(seed=game['seed'],side=game['side'],**result))
    return out

def retrace(directory):
    out=[]
    for arm in ['r3','v14']:
        for p in sorted((directory/arm).glob('*_player_*.json')):
            a=json.loads(p.read_text()); assert a['reproduced'] and not a['differences']
            game=a['game']; wins=0
            for m in a['observation']['matches'][:2]:
                trace=m['point_trace_own_rival']
                t=next((t for t,(u,v) in enumerate(trace[:100]) if u-v>16*(100-t)),None) if not wins else None
                out.append(dict(arm=arm,seed=game['seed'],side=game['side'],series_won=bool(game['result']),match=m['match'],remaining=100-t if t is not None else 0,lead_at_clinch=trace[t] if t is not None else None))
                wins+=m['final']['own_won']
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('repo',type=Path);args=ap.parse_args()
    root=args.repo/'experiments'
    mroot=root/'analysis'
    with (mroot/'kaggle3_20261115/student_hyb_v4_mixed.csv').open() as fp:
        v15=[row for row in csv.DictReader(fp) if row['opponent']=='solution92']
    assert len(v15)==200 and len({(r['seed'],r['side']) for r in v15})==200
    triage={(7150035,'player_1'),(7150079,'player_1'),(7150096,'player_0')}
    v15_relevance=[dict(seed=int(r['seed']),side=r['side'],matches=[int(r['our_wins']),int(r['opp_wins'])]) for r in v15 if (int(r['seed']),r['side']) in triage or r['game_win']=='0']
    print(json.dumps(dict(v15_dev_a=v15_relevance,retrace=retrace(root/'analysis/movement_soft_20261115/dev_a_retrace/run1'),
              public_v14=public(root/'analysis/solution_public_20261115'),
              r3_learning_only=packed(root/'imitation/final_20261115_r3_context')),indent=2))
