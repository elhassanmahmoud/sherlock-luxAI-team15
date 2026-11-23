"""Independent arithmetic check of the fitted decision and of all four held-out mechanism gates."""
import gzip
import json
from hashlib import sha256

import numpy as np

from anfahrt import HERE

def main():
    model=json.loads((HERE/'modell.json').read_bytes());report=json.loads((HERE/'mechanik.json').read_bytes());audit=json.loads((HERE/'gegenpruefung_mechanik_80.json').read_bytes());cases={r['seed']:r for r in audit['examples']}
    data=[json.loads(line) for line in gzip.decompress((HERE/'mechanik_80.jsonl.gz').read_bytes()).splitlines()]; rows=[]
    for packet in data:
        r=packet['base'];s=r['selection'];x=s['x'] if s else []
        pred=(float(model['coef'][0])+sum((f-m)/w*b for f,m,w,b in zip(x,model['mean'],model['scale'],model['coef'][1:],strict=True))) if s else 0.
        chosen=s is not None and pred>model['threshold'];c=cases.get(r['seed']);early=bool(c and c['first_new_credit_ahead']>0 and c['new_ship_arrivals'])
        rows.append({'seed':r['seed'],'team':r['team'],'opponent':r['opponent'],'eligible':s is not None,'pred':pred,'chosen':chosen,'arrived':bool(c and c['new_ship_arrivals']),
                  'earlier':early,'extra':c['extra_target'] if c else 0,'own':c['extra_own'] if c else 0,'foe':c['extra_foe'] if c else 0})
    sel=[r for r in rows if r['chosen']];rejected=[r for r in rows if r['eligible'] and not r['chosen']]
    def describe(rows):return dict(n=len(rows),arrived=sum(r['arrived'] for r in rows),earlier=sum(r['earlier'] for r in rows),better=sum(r['extra']>0 for r in rows),worse=sum(r['extra']<0 for r in rows),extra=sum(r['extra'] for r in rows),own=sum(r['own'] for r in rows),foe=sum(r['foe'] for r in rows))
    cs=describe(sel);flags={'five_maps':cs['n']>=5,'three_early':cs['earlier']>=3,'more_better':cs['better']>cs['worse'],'own_points':cs['own']>=0}
    if flags!=report['gates'] or all(flags.values())!=report['passed']:raise ValueError('Independent mechanism decision differs')
    if set(r['seed'] for r in sel)!={r['seed'] for r in report['cases'] if r['chosen']}:raise ValueError('Different selections')
    draw=np.random.default_rng(162515000).integers(0,80,size=(20000,80));intervals={}
    for k in ('chosen','arrived','earlier','extra','own','foe'):
        v=np.asarray([float(r[k]) if r['chosen'] else 0. for r in rows]);intervals[k]={'mean':float(v.mean()),'ci95':np.quantile(v[draw].mean(1),[.025,.975]).tolist()}
    out={'passed':all(flags.values()),'gates':flags,'selected':cs,'rejected':describe(rejected),'intervals_all_80':intervals,'selected_cases':sel,'model_sha':sha256((HERE/'modell.json').read_bytes()).hexdigest(),'archive_sha':audit['archive_sha']}
    (HERE/'auswahlpruefung.json').write_text(json.dumps(out,indent=2)+'\n');print(out['gates'],out['selected'],out['rejected'])

if __name__=='__main__':main()
