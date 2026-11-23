"""Check that shadow proposals leave complete native V16 action tapes bit-identical."""
import json

from luxai_s3.wrappers import LuxAIS3GymEnv
import numpy as np

from technik import frame
from archiv import TAPES, save
from berater import Advice
from originale import HERE, digest, limit_threads


def main():
    limit_threads();env=LuxAIS3GymEnv(numpy_output=True);rows=[]
    try:
        for team in (0,1):
            side=f'player_{team}'
            metas=[json.loads(p.read_text()) for p in sorted(TAPES.glob(f'v16_*_{side}.json'))]
            meta=next(r for r in metas if r['seat']['sensor']==1 and r['actual']['matches']==3)
            seed=meta['seat']['seed'];tape=TAPES/meta['filename']
            assert digest(tape)==meta['sha256']
            with np.load(tape,allow_pickle=False) as blob:z={k:blob[k] for k in blob.files}
            obs,info=env.reset(seed=seed);agent=Advice(side,False);agent.new_game(side);agent.set_env_cfg(info['params'])
            assert agent.teacher is not None
            for t in range(160):
                proposed=agent.act(t,frame(z,t))
                assert np.array_equal(proposed,z['commands'][t]),(seed,side,t,'Native action changed in shadow')
            rows.append(dict(seed=seed,team=team,steps=160,equal_unit_actions=2560,shadow_would_trigger=agent.first,tape=meta['sha256']))
            assert agent.changes==0 and not agent.base.caught_errors and (agent.teacher is None or not agent.teacher.caught_errors)
    finally:env.close()
    save(HERE/'schatten.json',dict(source=digest(HERE/'berater.py'),rows=rows))
    print('Both unchanged shadow tapes match native V16 exactly')


if __name__=='__main__':main()
