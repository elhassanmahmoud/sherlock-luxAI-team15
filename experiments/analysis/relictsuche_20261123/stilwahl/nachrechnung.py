"""Independent per-UID direction counts and distance-vote check on the frozen public archives."""
from collections import Counter
import gzip
import json

import numpy as np

from daten import ARCH, HERE, save


def traces(pos, live, side):
    foes=1-side
    numer=[0,0,0,0];denom=[0,0,0,0];moved=0;previous={};last_seen={}
    totals=Counter();line=Counter()
    for t in range(101):
        visible={u:tuple(map(int,pos[t,foes,u])) for u in range(16) if live[t,foes,u]}
        for u,xy in visible.items():
            line[sum(xy) if side==0 else 46-sum(xy)]+=1
            if u in last_seen:
                age,p=last_seen[u]
                if t>age+1 and p!=xy:totals['changed_position_after_gap']+=1
            last_seen[u]=(t,xy)
        currents={}
        if t:
            us=[tuple(map(int,pos[t-1,side,k])) for k in range(16) if live[t-1,side,k]]
            for u,xy in visible.items():
                if not live[t-1,foes,u]:continue
                old=tuple(map(int,pos[t-1,foes,u]));d=(xy[0]-old[0],xy[1]-old[1]);n=sum(map(abs,d))
                totals['same_id_consecutive']+=1
                totals['stationary' if n==0 else 'one_step' if n==1 else 'jump']+=1
                if n!=1:continue
                moved+=1;currents[u]=(old,d)
                if u in previous:
                    q=previous[u][1]
                    denom[0]+=1;denom[1]+=1
                    numer[0]+=int(d==q);numer[1]+=int(d==(-q[0],-q[1]))
                if us:
                    before=min(abs(old[0]-x)+abs(old[1]-y) for x,y in us)
                    after=min(abs(xy[0]-x)+abs(xy[1]-y) for x,y in us)
                    denom[2]+=1;numer[2]+=int(after<before)
            for u,(p,d) in currents.items():
                for j,(q,e) in currents.items():
                    if u>=j or abs(p[0]-q[0])+abs(p[1]-q[1])>4:continue
                    denom[3]+=1;numer[3]+=int(d==e)
        previous=currents
    return dict(moving=moved,consecutive=denom[0],counts=numer,totals=denom),totals,line


def check_vote(row,train,full):
    if not row['eligible'] or not row['observable']:return None
    train=[t for t in train if t['eligible'] and t['observable']]
    if len(train)<12:return None
    squared=np.zeros(len(train))
    for block in (['input','style'] if full else ['input']):
        matrix=np.array([r[block] for r in train]);mean=matrix.mean(0);sd=np.maximum(matrix.std(0),.05)
        query=np.clip((row[block]-mean)/sd,-3,3)
        for i,a in enumerate(matrix):
            normalized=np.clip((a-mean)/sd,-3,3)
            squared[i]+=sum(float(v)**2 for v in normalized-query)/len(query)
    indices=sorted(range(len(train)),key=lambda i:squared[i])
    boundary=squared[indices[11]]
    near=[i for i in indices if squared[i]<boundary];ties=[i for i in indices if squared[i]==boundary]
    vote=sum(train[i]['target'] for i in near)+(12-len(near))*sum(train[i]['target'] for i in ties)/len(ties)
    return vote/12


def main():
    rows=[json.loads(l) for l in gzip.decompress((HERE/'kreuzkarten.jsonl.gz').read_bytes()).splitlines()]
    result=json.loads((HERE/'ergebnis.json').read_text());group={};checks=0;votes=0
    for r in rows:
        file=ARCH/f"{r['seed']}-{r['team']}.npz"
        with np.load(file,allow_pickle=False) as z:
            pos=z['position'][:101];live=z['units_mask'][:101]&(z['energy'][:101].reshape(101,2,16)>=0)
        stats,observed,diagonal=traces(pos,live,r['team'])
        assert stats==r['tracks'];checks+=1
        for label in ('all', 'won' if r['eligible'] else 'lost'):
            key=r['opponent']+'_'+label
            g=group.setdefault(key,dict(maps=0,with_visible=0,reacquired_on_map=0,counts=Counter(),diagonal=Counter()))
            g['maps']+=1;g['with_visible']+=int(sum(diagonal.values())>0)
            g['reacquired_on_map']+=int(observed['changed_position_after_gap']>0)
            g['counts'].update(observed);g['diagonal'].update(diagonal)
        train=[a for a in rows if a['fold']!=r['fold']]
        assert len(train)==120 and r['seed'] not in {t['seed'] for t in train}
        for name in ('base21','extended'):
            score=check_vote(r,train,name=='extended')
            if score is None:assert r[name+'_score'] is None and not r[name]
            else:assert abs(score-r[name+'_score'])<1e-12 and bool(score>.05)==r[name];votes+=1
    for g in group.values():
        g['ship_turns']=sum(g['diagonal'].values())
        g['counts']=dict(g['counts']);g['diagonal']={str(k):v for k,v in sorted(g['diagonal'].items())}
    assert group['v16_won']['diagonal']=={'24':3212}
    assert sum(r['target']>0 for r in rows)==1 and sum(r['target']<0 for r in rows)==25
    assert len(rows)==160 and result['models']['extended']['both']['switched']==sum(r['extended'] for r in rows)
    save(HERE/'nachrechnung.json',dict(independent_public_trajectories=checks,available_numeric_votes_reproduced=votes,
               verified_null_or_numeric_decisions=2*len(rows),trajectory_geometry=group))
    print('All 160 public opening tracks and 320 held-out decisions independently verified')


if __name__=='__main__':main()
