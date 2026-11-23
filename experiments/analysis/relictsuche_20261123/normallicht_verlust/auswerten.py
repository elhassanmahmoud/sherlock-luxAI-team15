"""Attribute each official point once; partition generation and the agent's pre-action public knowledge."""
import gzip
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def summarize(r):
    result=[]
    for i,end in enumerate(r['matches']):
        turns=r['turns'][101*i:101*(i+1)];assert len(turns)==101 and end['points']==turns[-1]['scores']
        first=lambda indices:next(iter(indices),None)
        sides=[]
        for t in (0,1):
            gs={str(g):dict(points=0,positiv=0,nur_gebiet=0,ausserhalb=0) for g in (1,2,3)}
            k=Counter();coords=Counter();home=0;away=0;first_away=None
            for z in turns:
                for x,y,g,c in z['tiles'][t]:
                    gs[str(g)]['points']+=1;gs[str(g)][c]+=1;k[c]+=1;coords[(x,y,g)]+=1
                    assert x+y!=23, 'A paying tile lies on the symmetry line'
                    own_half=(x+y<23) if r['side']==0 else (x+y>23)
                    if own_half:home+=1
                    else:
                        away+=1
                        if first_away is None:first_away=z['local']
            for g in (1,2,3):
                gs[str(g)]['first_credit']=first(z['local'] for z in turns if any(a[2]==g for a in z['tiles'][t]))
                gs[str(g)]['first_sight']=first(z['local'] for z in turns if g in z['views'][t])
            assert sum(c['points'] for c in gs.values())==end['points'][t]
            sides.append(dict(generation=gs,home_half=home,opposite_half=away,first_in_opposite_half=first_away,public_knowledge={z:k[z] for z in ('positiv','nur_gebiet','ausserhalb')},
                              first_credit=first(z['local'] for z in turns if z['tiles'][t]),first_sight=first(z['local'] for z in turns if z['views'][t]),
                              top_tiles=[dict(x=x,y=y,generation=g,points=n) for (x,y,g),n in coords.most_common(5)]))
        margin=[z['scores'][0]-z['scores'][1] for z in turns]
        result.append(dict(match=i+1,points=end['points'],win=end['win'],sides=sides,first_behind=first(z for z,m in enumerate(margin) if m<0),
                           decisive_behind=(1+max(z for z,m in enumerate(margin) if m>=0)) if margin[-1]<0 and any(m>=0 for m in margin) else (0 if margin[-1]<0 else None),
                           deepest_deficit=dict(margin=min(margin),local=margin.index(min(margin))),margin_at={str(k):margin[k] for k in (0,25,40,50,60,70,75,80,90,95,100)},
                           generation_start={str(g):first(z['local'] for z in turns if g-1 in z['active']) for g in (1,2,3)}))
    assert r['sight']==result[0]['sides'][0]['first_sight'] and r['credit']==result[0]['sides'][0]['first_credit']
    return dict(policy=r['policy'],side=r['side'],seed=r['seed'],sight=r['sight'],credit=r['credit'],win=r['win'],source_actions=r['command_sha'],
                archive_sha=r['archive_sha'],policy_sha=r['policy_sha'],matches=result)


def main():
    allrows=[]
    for flavor in ('v16','r3'):
        for t in (0,1):
            p=HERE/f'{flavor}_p{t}.json.gz'
            if not p.exists():continue
            with gzip.open(p,'rt') as f:r=json.load(f)
            x=summarize(r);x['receipt_sha']=sha256(p.read_bytes()).hexdigest();allrows.append(x)
            for m in x['matches']:
                d=m['sides'];gen=[[v['points'] for v in s['generation'].values()] for s in d]
                when=[[q['first_credit'],q['first_sight']] for q in d];print(flavor,t,m['match'],m['points'],gen,when,m['decisive_behind'],[q['public_knowledge'] for q in d],m['margin_at'])
    (HERE/'bilanz.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
