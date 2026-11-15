"""Read only the recorded public windows and the prior four passive match summaries."""
import argparse
from collections import Counter, defaultdict
import csv, gzip, hashlib, json
from pathlib import Path

D=((0,0),(0,-1),(1,0),(0,1),(-1,0))
RAW = Path(__file__).resolve().parents[1]
WORK = RAW.parents[2]
PASS=json.loads((WORK/'experiments/analysis/solution_passive_20261115/summary.json').read_text())
HIST=WORK/'experiments/analysis/kaggle3_20261115/v14_devA.csv'
REF={(int(r['seed']),r['side']):r for r in csv.DictReader(HIST.open()) if r['opponent']=='solution92'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def living(f):return {u['uid']:u for u in f['units'] if u['energy']>=0}
def positions(units): return {tuple(u['pos']) for u in units.values()}
def dist(p,q): return sum(abs(a-b) for a,b in zip(p,q))
def expected_target(u):
    x,y=u['pos']; a=u['action'][0]
    return (x+D[a][0],y+D[a][1]) if 0<=a<5 else (x,y)

def analyze(f,nxt,later):
    now,live_next=living(f),living(nxt); future_pos=positions(live_next)
    known=set(map(tuple,f['known_points']))
    lost=(known & positions(now))-future_pos
    events=[]
    for tile in sorted(lost):
        holders=[u for u in now.values() if tuple(u['pos'])==tile]
        holders_detail=[]
        for u in holders:
            uid=u['uid']; a=u['action'][0]
            later_u=next((z for z in nxt['units'] if z['uid']==uid),None)
            same_xy=later_u is not None and tuple(later_u['pos'])==tile
            if (a in (0,5) and same_xy and later_u['energy']<0):
                cat='stationary_energy_negative'
            elif a in (0,5) and (later_u is None or dist(tile,later_u['pos'])>1):
                cat='stationary_disappeared_or_slot_reused'
            elif (1<=a<=4 and later_u is not None and later_u['energy']>=0 and
                  tuple(later_u['pos'])==expected_target(u) and (dist(later_u['pos'],(0,0))>0)):
                cat='moved_and_survived'
            else:
                cat='move_or_slot_ambiguous'
            holders_detail.append(dict(uid=uid,energy=u['energy'],action=u['action'],next_unit=later_u,cat=cat))
        cat='multiple_prior_holders' if len(holders)>1 else holders_detail[0]['cat']
        nearby=[u for u in f['visible_enemies'] if u['energy']>=0 and dist(u['pos'],tile)<=1]
        shoot=[u for u in f['visible_enemies'] if u['energy']>=f['sap_cost'] and
               max(abs(i-j) for i,j in zip(tile,u['pos']))<=f['sap_range']]
        donors=[]
        for u in now.values():
            if tuple(u['pos']) in known or u['energy']<f['move_cost'] or dist(u['pos'],tile)!=1: continue
            direction=D.index(tuple(a-b for a,b in zip(tile,u['pos'])))
            if direction not in u['allowed']: continue
            donors.append((u['uid'],u['action'][0],expected_target(u) in known))
        vacancy3=(all(tile not in positions(living(r)) for r in later) if len(later)==3 else None)
        undo=(cat=='stationary_energy_negative' and holders[0]['action'][0]==5 and
              holders_detail[0]['next_unit']['energy']+f['sap_cost']>=0)
        events.append(dict(ms=f['mstep'],tile=list(tile),classification=cat,holder_details=holders_detail,
                       legal_neighbors=donors,visible_contact=len(nearby),visible_armed=len(shoot),
                       vacant_next_3=vacancy3,one_step_recoverable_without_own_sap=undo))
    return events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    catalog=[]
    for group in ('cases','controls'):
        p=RAW/(group+'_v1'); manifest=json.loads((p/'summary.json').read_text())
        expected={(seed,f'player_{s}') for seed in manifest[group] for s in (0,1)}
        assert {(r['seed'],r['side']) for r in manifest['records']}==expected
        assert manifest['v14_sha256']==sha(WORK/'agents/sherlock/weights/agent_p0.pth')
        assert manifest['comparator_sha256']==sha(HIST)
        for r in manifest['records']:
            path=p/r['path']; assert sha(path)==r['sha256']
            reference=REF[r['seed'],r['side']]
            assert int(reference['steps'])==303 and [r['our_wins'],r['opp_wins']]==[int(reference[k]) for k in ('our_wins','opp_wins')]
            frames=[json.loads(line) for line in gzip.open(path,'rt')]
            assert [f['step'] for f in frames]==[i*101+ms for i in (1,2) for ms in range(25,101)]
            assert len(frames)==r['frames']==152
            if group=='cases':
                original=next(g for g in PASS['games'] if (g['seed'],g['side'])==(r['seed'],r['side']))
                wins=[bool(m['won']) for m in original['matches'][1:]]
            else:
                before2, before3=frames[0]['own_wins'],frames[76]['own_wins']
                w=[before3-before2,r['our_wins']-before3]; assert set(w)<={0,1}
                wins=list(map(bool,w))
            for m in (2,3):
                rows=[f for f in frames if f['match']==m]
                events=[]
                for i,f in enumerate(rows[:-1]): events.extend(analyze(f,rows[i+1],rows[i+1:i+4]))
                catalog.append(dict(panel=group,seed=r['seed'],side=r['side'],match=m,
                    match_win=wins[m-2],game_win=r['our_wins']>r['opp_wins'],events=events))
    groups=[]
    for panel in ('cases','controls'):
        for won in (False,True):
            matches=[g for g in catalog if g['panel']==panel and g['match_win']==won]
            events=[(g,e) for g in matches for e in g['events']]
            groups.append(dict(panel=panel,match_won=won,n_matches=len(matches),
                n_events=len(events),classes=dict(Counter(e['classification'] for g,e in events)),
                n_match_with_sap_recovery=sum(any(e['one_step_recoverable_without_own_sap'] for e in g['events']) for g in matches),
                n_maps_with_any=len(set(g['seed'] for g in matches if g['events'])),
                disappearance_with_legal_neighbor=sum(bool(e['legal_neighbors']) for g,e in events),
                vacancy3=sum(e['vacant_next_3'] is True for g,e in events),
                one_step_recoveries=sum(e['one_step_recoverable_without_own_sap'] for g,e in events),
                occupied_observations=sum(len(g['events'])>0 for g in matches)))
    result=dict(groups=groups, catalog=catalog)
    with args.out.open('x') as output:
        output.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(groups,indent=1))
if __name__=='__main__': main()
