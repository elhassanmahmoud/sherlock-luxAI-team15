"""Reproduce both published two-step routes from stored public observations, independent of active training."""
import gzip
from hashlib import sha256
import json

from anfahrt import HERE,PROOF,Evidence,options,stationary

def main():
    src=PROOF/'archiv/beobachtungen.jsonl.gz';rows=[]
    for game in map(json.loads,gzip.decompress(src.read_bytes()).splitlines()):
        if game['seed']!=161620068:continue
        side=game['team'];decision=(135,139)[side];target=(74,524)[side];uid=(0,7)[side];middle=(75,500)[side];ev=Evidence()
        for p,pol in zip(game['public'],game['policy'],strict=True):
            p={**p,'gain':p['points']-ev.previous_score if p['ms'] else 0};ev.observe(p)
            if p['step']!=decision:continue
            routes=[r for r in options(p,pol,ev,side) if r['uid']==uid and r['target']==target]
            if len(routes)!=1 or routes[0]['route']!=[middle,target] or not stationary(pol)[middle]:raise ValueError('Historical two-step guard or route was not reproduced')
            rows.append({'seed':game['seed'],'team':side,'step':decision,'uid':uid,'target':target,'proof':routes[0]['proof'],'path':routes[0]['route'],'stationary_holders':stationary(pol)[middle]});break
    if len(rows)!=2:raise ValueError('Missing historic example')
    result={'rows':rows,'public_archive':sha256(src.read_bytes()).hexdigest(),'route_source':sha256((HERE/'anfahrt.py').read_bytes()).hexdigest(),'proof_source':sha256((PROOF/'beweise.py').read_bytes()).hexdigest()}
    (HERE/'archivprobe.json').write_text(json.dumps(result,indent=2)+'\n');print(rows)

if __name__=='__main__':main()
