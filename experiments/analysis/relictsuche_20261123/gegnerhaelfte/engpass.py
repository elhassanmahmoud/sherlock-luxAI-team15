"""Count public eligibility stages on the preselected training maps without changing a single option."""
from collections import Counter
from pathlib import Path
import inspect
import json

import numpy as np

import lernen as study


def instrument(c):
    src=inspect.getsource(study.offer)
    # Observe existing statements; the original function is still called separately as an equality oracle.
    replacements={
        'if not seen or t%4 or t>88 or not proof.positive:return None':"if not seen or t%4 or t>88:return None\n    c['sicht_und_zeitfenster']+=1\n    if not proof.positive:return None\n    c['positiver_beweis']+=1",
        "if not len(goals):return None":"if not len(goals):return None\n    c['gegnerisches_passierbares_beweisziel']+=1",
        'dists=bfs_maps(geo,goals);best=None;existing=[]':"dists=bfs_maps(geo,goals);best=None;existing=[];hit=set()",
        "rest=np.arange(len(idx))!=i;rest&=np.asarray(ene)[idx]>=0":"hit.add('freie_uid');rest=np.arange(len(idx))!=i;rest&=np.asarray(ene)[idx]>=0",
        'if not 1<=dist<=12 or ene[u]<dist*cost+10 or tuple(g) in occupied:continue':"if not 1<=dist<=12:continue\n            hit.add('freier_schiffsweg_bis12')\n            if ene[u]<dist*cost+10:continue\n            hit.add('energie_genuegt')\n            if tuple(g) in occupied:continue\n            hit.add('unreserviertes_ziel')",
        'if best is None:return None':"c.update(hit)\n    if best is None:return None\n    c['zulassig']+=1",
    }
    for before,after in replacements.items():
        assert before in src;src=src.replace(before,after)
    scope={**study.__dict__,'c':c};exec(compile(src,'public_eligibility_diagnostics','exec'),scope);return scope['offer']


def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    study.limit_threads();env=LuxAIS3GymEnv(numpy_output=True);real=study.offer;output=[]
    try:
        for r in study.select()[:12]:
            counts=Counter();observed=instrument(counts)
            def audit(*args):
                event=real(*args);assert event==observed(*args);return event
            study.offer=audit
            try:row=study.replay(env,r,'diagnostic')
            finally:study.offer=real
            output.append(dict(seed=r['seed'],team=r['team'],counts=counts,actual_offers=len(row['offers'])))
    finally:env.close()
    tot=Counter();[tot.update(r['counts']) for r in output]
    (study.HERE/'engpass.json').write_text(json.dumps(dict(maps=output,total=tot),indent=2)+'\n')
    print(tot,flush=True)


if __name__=='__main__':main()
