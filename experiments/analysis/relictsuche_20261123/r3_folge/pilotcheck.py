"""Reconcile each complete-game claim with chronological match records in the archived pilot."""
from collections import Counter, defaultdict
from hashlib import sha256
import gzip
import json
from pathlib import Path


def main():
    folder=Path(__file__).resolve().parent/'pilotpruefung'
    result=json.loads((folder/'ergebnis.json').read_text())
    archive=folder/'spiele.jsonl.gz';assert sha256(archive.read_bytes()).hexdigest()==result['data_sha']
    by_seat=defaultdict(dict);totals=Counter();m2=Counter();engines=Counter();same=0;eligible=0
    for line in gzip.decompress(archive.read_bytes()).splitlines():
        r=json.loads(line);arm=r['arm'];base=(r['seed'],r['team']);assert arm not in by_seat[base]
        w=[m['win'] for m in r['matches']];assert len(w)==3 and r['win']==int(sum(w)>1)
        assert all(a in (0,1) for a in w)
        assert all(m['points'][0]==m['points'][1] or int(m['points'][0]>m['points'][1])==m['win'] for m in r['matches'])
        by_seat[base][arm]=r;totals[arm]+=r['win'];m2[arm]+=w[1];engines[arm]+=r['engine_actions'][0]
        assert r['errors']==[0,0] and r['engine_actions']==[303,303]
        if r['events']:
            assert w[0]==1 and arm!='reference' and len({(e[1],e[4]) for e in r['events']})==1 and len(r['events'])<=3
            eligible+=1
    assert len(by_seat)==64 and len({s for s,t in by_seat})==32
    for (s,t),p in by_seat.items():
        assert (s,1-t) in by_seat and set(p)=={'reference','solution','direct'}
        control,active=p['reference'],p['solution'];assert control['matches'][0]==active['matches'][0]
        if not active['events']:
            assert control['trace']==active['trace'] and control['matches']==active['matches'];same+=1
    gates=(totals['solution']>totals['reference'],m2['solution']>=m2['reference'],2*totals['direct']>len(by_seat))
    assert result['qualified']==all(gates)
    assert [result['gates'][k] for k in ('more_solution_games','m2_nonnegative','direct_more_than_half')]==list(gates)
    assert all(result['counts'][a]['wins']==totals[a] and result['counts'][a]['rounds'][1]==m2[a] for a in totals)
    out=dict(whole_wins=dict(totals),second_match_wins=dict(m2),distinct_seats=len(by_seat),native_m1_pairs=len(by_seat),identical_inert_external=same,
             total_full_steps_per_arm=dict(engines),active_games=eligible,qualified=all(gates))
    dest=folder/'nachrechnung.json'
    if dest.is_file():assert json.loads(dest.read_text())==out
    else:dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('Independent check verified every paired M1, 192 game winners and the pilot decision')


if __name__=='__main__':main()
