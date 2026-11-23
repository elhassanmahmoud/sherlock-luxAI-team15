"""Independently replay arithmetic on all original Feldbindung files, before assessing the added hold."""
from pathlib import Path
import gzip
from hashlib import sha256
import json

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;WORK=Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/feldbindung/spiele')

def main():
    rows=[json.loads(x) for x in gzip.decompress((ROOT/'feldprobe/ganze_partien.jsonl.gz').read_bytes()).splitlines()];base={(r['seed'],r['team'],r['arm'],r['opponent']):r for r in rows};panel=[json.loads(x) for x in gzip.decompress((ROOT/'feldbindung/fenster.jsonl.gz').read_bytes()).splitlines()];table={(r['seed'],r['side'],r['opponent']):r for r in panel};groups={};certified=0;packets=list(WORK.glob('*.json'))
    for f in packets:
        v=json.loads(f.read_bytes());key=tuple(v['key']);assert len(v['matches'])==3 and len(v['hash'])==64
        if key in base:assert base[key]['hash']==v['hash'] and base[key]['matches']==v['matches'];certified+=1
        if key[2]!='probe':continue
        s,team,_,op=key;e=base[key]['event'];reading=v['readings'][str(team)];u=e['u'];first,second=reading[:2]
        scoring=bool(first['own_point'] and u in first['own_units']);eligible=bool(scoring and second['here'] and second['energy']>=30 and not second['known'] and 1<=second['act']<=4 and second['enemy_dist']>second['sap_range']);stayed=bool(scoring and all(u in q['own_units'] for q in reading[:4]));prev=table[s,team,op]
        assert (scoring,eligible,stayed)==(prev['initial'],prev['eligible_to_hold'],bool(prev['initial'] and prev['scout_first4']))
        z=groups.setdefault(op,{'events':0,'scored':0,'stayed_four':0,'eligible':0});z['events']+=1;z['scored']+=scoring;z['stayed_four']+=stayed;z['eligible']+=eligible
    assert len(packets)==100 and len(panel)==56;out={'source_games':len(packets),'known_full_hashes_and_scores_rechecked':certified,'events':len(panel),'groups':groups,'source_archive_sha':sha256((ROOT/'feldbindung/fenster.jsonl.gz').read_bytes()).hexdigest()};(HERE/'vorbefund.json').write_text(json.dumps(out,indent=2)+'\n');print(out)

if __name__=='__main__':main()
