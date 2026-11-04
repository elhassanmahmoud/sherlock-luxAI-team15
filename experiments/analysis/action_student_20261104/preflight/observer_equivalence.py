import hashlib,json,time
from contextlib import nullcontext
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import torch
from scripts import student_collect as sc
from scripts.common import play_game,make_opponent

torch.set_num_threads(1)
OUT=Path('/tmp/sherlock-action-student-20261104/observer_equivalence.json')
assert not OUT.exists()
student=Path('experiments/candidates/student_reward_20261104/S30.pth').resolve()
cp=sc.load_student(student)
pins=sc._pins();h=sc.sha256(student)
rows=[]
for side in (0,1):
    pair=[]
    for observed in (False,True):
        a=sc._agent(student,cp)
        before=sc._learning_digest(a)
        trace=hashlib.sha256();original=a.act
        def traced(step,obs):
            result=original(step,obs)
            trace.update(np.ascontiguousarray(result,dtype=np.int64).tobytes())
            return result
        a.act=traced
        start=time.monotonic()
        env=sc._env()
        try:
            with sc.ExactCollector(a) if observed else nullcontext() as capture:
                if capture is not None:
                    capture.set_game(dict(game_index=side,env_seed=500720,side=side,is_train=side==0))
                result=play_game(env,a,make_opponent('solution92',f'player_{1-side}'),500720,f'player_{side}',train=False)
                data=capture.arrays() if capture is not None else None
        finally:env.close()
        assert sc._learning_digest(a)==before
        assert result['steps']==303 and result['point_counting_version']==2
        if data is not None:
            with torch.no_grad():q=a.q(torch.from_numpy(data['s'])).numpy()
            assert np.allclose(q,data['student_q'],rtol=1e-5,atol=1e-5)
            assert len(data['s'])==len(np.unique(np.column_stack([data['env_step'],data['uid']]),axis=0))
        row=dict(side=side,observed=observed,actions_sha256=trace.hexdigest(),result={k:result[k] for k in ('result','our_wins','opp_wins','our_points','opp_points','steps','point_counting_version')},rows=len(data['s']) if data is not None else None,seconds=time.monotonic()-start)
        rows.append(row);pair.append(row)
    assert pair[0]['actions_sha256']==pair[1]['actions_sha256'] and pair[0]['result']==pair[1]['result']
assert h==sc.sha256(student) and pins==sc._pins()
OUT.write_text(json.dumps(dict(status='passed',completed_utc=datetime.now(timezone.utc).isoformat(),games=4,rows=rows,source_protected_before_after_equal=True,student_sha256=h),indent=2)+'\n')
print(OUT.read_text())
