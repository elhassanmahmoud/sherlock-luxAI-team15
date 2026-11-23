"""Independent identity, route, timing, scoring-mask and public-commitment audit."""
from collections import Counter
import gzip
import json
from pathlib import Path

import numpy as np

from befund import DATA, DEAD, HERE, WORK, digest, load


def reflect(c):
    x,y=divmod(c,24);return (23-y)*24+23-x


PAIRS=[i for i in range(576) if i//24+i%24<24]
ORBIT={pos:k for k,c in enumerate(PAIRS) for pos in (c,reflect(c))}
DIRECTION={(0,-1):1,(1,0):2,(0,1):3,(-1,0):4}


def route_check(pub,meta,m,path,uid,t):
    team=meta['team'];origin=tuple(pub['position'][t,team,uid]);assert origin==divmod(path[0],24)
    energy=pub['energy'][t,team,uid].item();assert energy>=max(30,8*meta['cfg']['unit_move_cost'])
    assert pub['units_mask'][t,team,uid] and not pub['protected'][t,uid] and pub['commands'][t,uid,0]<=4
    assert 1<=t-101*m<=49 and 2<=len(path)<=9
    enemies={int(x)*24+int(y) for x,y in pub['position'][t,1-team][pub['units_mask'][t,1-team]]}
    for i,(a,b) in enumerate(zip(path,path[1:])):
        x,y=divmod(a,24);u,v=divmod(b,24);d=DIRECTION[u-x,v-y]
        assert pub['terrain'][t,u,v] in (0,1) and b not in enemies
        if i==0:assert pub['move_mask'][t,uid,d] and d!=pub['commands'][t,uid,0]


def analyze():
    prim=[];adj=[];score_context=[];controls=Counter();seen=set()
    for f in sorted(DATA.glob('*.json')):
        meta=json.loads(f.read_text()); seed=meta['seed'];team=meta['team']
        rawfile=WORK/'zweiterfund'/(f.stem+'.json'); secondfile=WORK/'zweiterfund_sicht'/(f.stem+'.json')
        a=json.loads(rawfile.read_text());b=json.loads(secondfile.read_text())
        assert b['source']['primary']==digest(rawfile) and a['seed']==b['seed']==seed and seed not in seen; seen.add(seed)
        pub=load(DATA,meta,'public');judge=load(DATA,meta,'private');weight=judge['weights'].ravel()
        with np.load(DEAD/(f.stem+'.npz')) as z:h=np.unpackbits(z['bits'],axis=-1,bitorder='little').astype(bool)
        active=judge['active'].sum(1); truth=(weight[None]>0)&(weight[None]<=active[:,None]); scoring=np.unpackbits(judge['scoring'],axis=-1,bitorder='little').astype(bool)
        assert np.all(~(h[:,0]&truth)|h[:,1]);assert int(np.sum(h[:,0]&truth))==a['false_dead_world_ticks']
        controls['false_world_ticks']+=a['false_dead_world_ticks'];controls['affected_maps']+=bool(a['false_dead_world_ticks'])
        controls['public_turns']+=a['checks'];controls['visibility_checks']+=b['checks']['original_sensor_arrays'];controls['engine_checks']+=b['checks']['physical_sights']
        controls['opponent_'+meta['opponent']]+=1;controls['seat_'+str(team)]+=1
        for idx,m in enumerate((1,2)):
            start=101*m;end=start+101
            am,bm=a['matches'][idx],b['matches'][idx]
            flag=pub['relic_nodes_mask'][start:end,m]|pub['relic_nodes_mask'][start:end,m+3]
            first=start+int(np.nonzero(flag)[0][0]) if flag.any() else end
            assert am['first']==bm['first']==first
            for order in am['public_orders'].values():route_check(pub,meta,m,order['path'],order['uid'],order['depart'])
            for tag,mo in (('exact',am),('sensor',bm)):
                for mode,e in mo['modes'].items():
                    t=e['at'];assert start<=t<end and judge['active'][t,m] and t<=first-3
                    x,y=map(int,judge['centres'][m]);target=x*24+y
                    def in_zone(z):
                        a,b=divmod(z,24)
                        return any(max(abs(a-c//24),abs(b-c%24))<=2 for c in {target,reflect(target)})
                    pre={ORBIT[c] for c in np.flatnonzero(h[t,1]&truth[t]) if in_zone(int(c))}
                    assert pre==set(e['pairs']) and set(e['opened'])<=pre and set(e['earlier'])<=pre
                    assert set(map(int,e['first_classified']))==set(e['earlier'])
                    if mode!='ideal':
                        route_check(pub,meta,m,e['path'],e['uid'],e['depart'])
                        off=t-e['depart'];assert 1<=off<=8
                        if tag=='exact':
                            cell=e['path'][min(off,len(e['path'])-1)]
                            assert cell in {target,reflect(target)}
                    leads=[]
                    for pkey,alt_first in e['first_classified'].items():
                        pair=PAIRS[int(pkey)];mirror=reflect(pair)
                        mask=pub['known_points'][start:end].reshape(101,576)[:,[pair,mirror]].any(1)
                        first_known=start+int(np.flatnonzero(mask)[0]) if mask.any() else end
                        assert t<=alt_first<first_known and truth[alt_first,pair]
                        leads.append(first_known-alt_first)
                    primary_cells={z for k in pre for z in (PAIRS[k],reflect(PAIRS[k]))}
                    # Already observed credits on these fields describe the stakes; they are not incremental rewards.
                    cell_ids=sorted(primary_cells);clock=np.arange(t,end)
                    unresolved=h[clock,0][:,cell_ids]&truth[clock][:,cell_ids]
                    own=int(np.sum(scoring[clock,team][:,cell_ids]&unresolved));enemy=int(np.sum(scoring[clock,1-team][:,cell_ids]&unresolved))
                    score_context.append(dict(seed=seed,match=m,mode=mode,definition=tag,own=own,enemy=enemy,classification_leads=leads))
        prim.append(a);adj.append(b)
    assert len(seen)==160 and controls['false_world_ticks']==5288 and controls['affected_maps']==55
    def summarize(rows,tag):
        modes={}
        for name in ('ideal','route','conditional','marginal'):
            events=[(r,m,m['modes'][name]) for r in rows for m in r['matches'] if name in m['modes']]
            def tally(pred):
                kept=[(r,m,e) for r,m,e in events if pred(e)]
                return dict(maps=len({r['seed'] for r,m,e in kept}),matches=len(kept),
                            maps_by_opponent={op:len({r['seed'] for r,m,e in kept if r['opponent']==op}) for op in ('solution92','v16')},
                            match_regions=dict(Counter(m['relation'] for r,m,e in kept)), by_match=dict(Counter(m['match']+1 for r,m,e in kept)))
            c=[s for s in score_context if s['definition']==tag and s['mode']==name]
            lead=[l for z in c for l in z['classification_leads']]
            modes[name]=dict(reachable=tally(lambda e:True),opened=tally(lambda e:e['opened']),earlier=tally(lambda e:e['earlier']),
                             false=tally(lambda e:e['false_positive']),newly_active=tally(lambda e:e['new_pairs']),
                             total_opened_match_pairs=sum(len(e['opened']) for r,m,e in events),total_earlier_match_pairs=len(lead),
                             classification_pair_ticks=sum(e['classification_pair_ticks'] for r,m,e in events),
                             early_sight_steps=[m['first']-e['at'] for r,m,e in events],classification_leads=lead,
                             original_credits_while_marked_dead=[sum(z[k] for z in c) for k in ('own','enemy')])
        return modes
    main=summarize(prim,'exact');side=summarize(adj,'sensor')
    tube=main['route']; anchor=main['conditional']
    gates=dict(routes_12=tube['reachable']['maps']>=12,routes_four_per_opponent=min(tube['reachable']['maps_by_opponent'].values())>=4,
               classification_eight=tube['earlier']['maps']>=8,classification_two_per_opponent=min(tube['earlier']['maps_by_opponent'].values())>=2,
               public_four=anchor['reachable']['maps']>=4)
    public={}
    for name in ('conditional','marginal'):
        public[name]=dict(ordered_matches=sum(name in m['public_orders'] for r in prim for m in r['matches']),
                          physical_earlier_maps=len({r['seed'] for r in adj for m in r['matches'] if name in m['any_first']}),
                          physical_earlier_matches=sum(name in m['any_first'] for r in adj for m in r['matches']))
    def archive(path,rows):
        raw=''.join(json.dumps(r,separators=(',',':'),sort_keys=True)+'\n' for r in rows).encode()
        if path.exists():assert gzip.decompress(path.read_bytes())==raw
        else:path.write_bytes(gzip.compress(raw,mtime=0))
    archive(HERE/'grundlagen.jsonl.gz',prim);archive(HERE/'sichtwege.jsonl.gz',adj);archive(HERE/'gutschriften.jsonl.gz',score_context)
    result=dict(control=controls,main=main,with_sensor=side,public_decisions=public,geometric_upper_maps=len({r['seed'] for r in prim if any(m['broad'] for m in r['matches'])}),
                gates=gates,passed=all(gates.values()),data={n:digest(HERE/n) for n in ('grundlagen.jsonl.gz','sichtwege.jsonl.gz','gutschriften.jsonl.gz')})
    path=HERE/'ergebnis.json';raw=json.dumps(result,sort_keys=True,indent=2)+'\n'
    if path.exists():assert json.loads(path.read_text())==json.loads(raw)
    else:path.write_text(raw)
    print('160 archived games verified',flush=True)


if __name__=='__main__':analyze()
