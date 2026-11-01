"""Shadow-belief diagnosis only: engine truth validates facts, never drives actions."""
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.experiment import limit_threads


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--first',type=int,default=830000)
    p.add_argument('--n',type=int,default=40)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from agents.sherlock import geometry as geo
    from scripts.common import make_opponent,play_game
    from scripts.oracle_probe import truth_maps
    weights=ROOT/'experiments/releases/20261101_v14_baseline/agent_p0.pth'
    expected='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
    if not weights.is_file():raise FileNotFoundError(weights)
    if hashlib.sha256(weights.read_bytes()).hexdigest()!=expected:
        raise ValueError('Probe reference is not the frozen V14 checkpoint')
    agent=Agent_x('player_0',agent_path=str(weights),train=False,seed=0)
    agent.autosave_on_terminate=False
    env=LuxAIS3GymEnv(numpy_output=True)
    b=agent.belief
    original_observe=b.observe
    original_new_game=agent.new_game
    state={}
    games=[]
    def new_game(side):
        original_new_game(side)
        shadow=copy.deepcopy(b)
        shadow.__dict__.pop('observe',None)
        shadow.overlap_infer=True
        state.update(shadow=shadow,point=set(),dead=set(),bad=[],steps=0,
                     extra_point_steps=0,extra_dead_steps=0,shadow_secs=0.,max_shadow_secs=0.)
    def observe(obs):
        fresh=int(np.asarray(obs['steps']))!=b._last_step
        original_observe(obs)
        shadow=state['shadow']
        shadow.sensor_range=b.sensor_range
        start=time.perf_counter()
        shadow.observe(obs)
        elapsed=time.perf_counter()-start
        if not fresh or int(np.asarray(obs['match_steps']))==0:return
        state['steps']+=1
        state['shadow_secs']+=elapsed
        state['max_shadow_secs']=max(state['max_shadow_secs'],elapsed)
        points=shadow._point-b._point
        dead=shadow._dead-b._dead
        state['extra_point_steps']+=len(points)
        state['extra_dead_steps']+=len(dead)
        state['point'].update((shadow.match_idx,int(t)) for t in points)
        state['dead'].update((shadow.match_idx,int(t)) for t in dead)
        truth,_=truth_maps(env.state)
        if b.mirrored:truth=geo.mirror_map(truth)
        bad_p=[int(t) for t in points if not truth.reshape(-1)[t]]
        bad_d=[int(t) for t in dead if truth.reshape(-1)[t]]
        if bad_p or bad_d:
            state['bad'].append(dict(step=int(np.asarray(obs['steps'])),points=bad_p,dead=bad_d))
    b.observe=observe
    agent.new_game=new_game
    try:
        for seed in range(args.first,args.first+args.n):
            for side in ('player_0','player_1'):
                opp=make_opponent('solution92','player_1' if side=='player_0' else 'player_0')
                result=play_game(env,agent,opp,seed,side,train=False)
                item=dict(seed=seed,side=side,result=result['result'],steps=state['steps'],
                    extra_point_facts=len(state['point']),extra_dead_facts=len(state['dead']),
                    extra_point_steps=state['extra_point_steps'],extra_dead_steps=state['extra_dead_steps'],
                    bad=state['bad'],shadow_secs=state['shadow_secs'],max_shadow_secs=state['max_shadow_secs'])
                games.append(item)
                print(json.dumps(item),flush=True)
    finally:env.close()
    assert hashlib.sha256(weights.read_bytes()).hexdigest()==expected
    report=dict(kind='shadow_information_diagnosis_not_strength_test',games=len(games),rows=games,
                extra_point_facts=sum(x['extra_point_facts'] for x in games),
                extra_dead_facts=sum(x['extra_dead_facts'] for x in games),
                false_additional_facts=sum(len(bad['points'])+len(bad['dead']) for x in games for bad in x['bad']))
    with args.out.open('x') as f:json.dump(report,f,indent=2)
    if report['false_additional_facts']:raise RuntimeError('Shadow derived incorrect facts; reject candidate')

if __name__=='__main__':main()
