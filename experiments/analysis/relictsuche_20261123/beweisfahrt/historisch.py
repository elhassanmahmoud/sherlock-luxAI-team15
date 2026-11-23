"""Separate, deliberately targeted historical reproductions, excluded from abundance and training."""
import json

import anfahrt
import gegenfahrten as engine
from anfahrt import HERE
from scripts.experiment import limit_threads

def main():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads();env=LuxAIS3GymEnv(numpy_output=True);rows=[];original=anfahrt.options;seed=161620068
    try:
        for team,at,uid,target in ((0,135,0,74),(1,139,7,524)):
            def exact(public,policy,evidence,side,lead=0):
                if public['step']!=at or side!=team:return []
                return [r for r in original(public,policy,evidence,side,lead) if r['uid']==uid and r['target']==target]
            anfahrt.options=exact
            a=engine.play(env,seed,team,'solution92','base');b=engine.play(env,seed,team,'solution92','force')
            engine.check(a['selection'] is not None and a['prefix']==b['prefix'] and a['selection']==b['selection'],'Unequal historical start')
            engine.check(len(b['selection']['route'])==2,'Different historical path')
            rows.append({'baseline':a,'alternative':b})
    finally:anfahrt.options=original;env.close()
    r={'cards':1,'seats':2,'purpose':'targeted historical case only','source':engine.common.stamp(engine.binding()),'script_sha':engine.common.sha(HERE/'historisch.py'),'rows':rows}
    engine.common.write_once(HERE/'historisch.json',r)
    print([(g['alternative']['team'],g['alternative']['events'],[(i+1,b['arrival'],a['credit'],b['credit']) for i,(a,b) in enumerate(zip(g['baseline']['after'],g['alternative']['after'],strict=True))]) for g in rows])

if __name__=='__main__':main()
