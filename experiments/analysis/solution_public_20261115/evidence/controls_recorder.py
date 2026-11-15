"""Passive public-input tracing for V14/Solution. No hidden engine state enters the trace.

Usage: <course-python> /tmp/sherlock_solution_public_window.py --project PROJECT --out NEW_DIR --panel cases
Use a different NEW_DIR and --panel controls for the prespecified broader case-control diagnosis.
"""
import argparse, csv, gzip, hashlib, json, sys
from pathlib import Path
import numpy as np

CASES=(7150052,7150096)
# Four lowest other Dev A seeds with >=1 lost seat, four lowest with two won seats.
# Both seats on each map. Membership uses archived GAME outcomes only.
CONTROLS=(7150003,7150011,7150035,7150037,7150000,7150001,7150002,7150004)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PublicRecorder:
    def __init__(self,agent,sink):
        self.agent,self.sink=agent,sink

    def __getattr__(self,name): return getattr(self.agent,name)

    def act(self,step,obs):
        from agents.sherlock import geometry
        from agents.sherlock.imitation_agent import canonical_action
        a=self.agent
        actions=a.act(step,obs)
        ms=int(obs["match_steps"])
        if step//101 not in (1,2) or not 25<=ms<=100: return actions
        cache=a._cache
        if cache is None or cache[0]!=step or cache[1] is not a._prev_ctx: raise ValueError("missing active decision cache")
        _,ctx,ids,_,masks,_=cache
        mirror=a.belief.mirrored
        sensor=np.asarray(obs["sensor_mask"],bool)
        if mirror: sensor=geometry.mirror_map(sensor)
        units=[]
        for uid in ids:
            goal=ctx["assigned"].get(int(uid))
            units.append(dict(uid=int(uid),pos=ctx["ally_pos"][uid].tolist(),energy=int(ctx["ally_ene"][uid]),
                assigned=(list(map(int,goal)) if goal is not None else None),
                allowed=np.flatnonzero(masks[uid]).tolist(),action=canonical_action(actions[uid],mirror)))
        enemies=[dict(uid=int(i),pos=p.tolist(),energy=int(e)) for i,p,e in
                 zip(ctx["enemy_vis_ids"],ctx["enemy_coords"],ctx["enemy_energies"])]
        self.sink(dict(step=int(step),match=step//101+1,mstep=ms,own_points=int(ctx["own_points"]),
            opp_points=int(ctx["opp_points"]),own_wins=int(ctx["own_wins"]),opp_wins=int(ctx["opp_wins"]),move_cost=int(ctx["move_cost"]),sap_cost=int(ctx["sap_cost"]),
            sap_range=int(ctx["sap_range"]),width=ctx["W"],height=ctx["H"],mirrored=bool(mirror),
            units=units,visible_enemies=enemies,direct_visibility=np.packbits(sensor,axis=1).tolist(),
            known_points=np.argwhere(ctx["point_tiles"]).tolist(),candidate=np.argwhere(ctx["candidate"]).tolist(),
            blocked_belief=np.argwhere(~ctx["passable"]).tolist(),nebula_belief=np.argwhere(ctx["nebula"]).tolist()))
        return actions


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--panel',choices=('cases','controls'),required=True);args=ap.parse_args()
    root=args.project.resolve();sys.path.insert(0,str(root))
    from scripts import solution_passive as historic
    from scripts.common import make_opponent,play_game
    from scripts.experiment import limit_threads
    from scripts.imitate import make_player
    from scripts.par_eval import require_no_agent_errors
    from luxai_s3.wrappers import LuxAIS3GymEnv
    if (sha(historic.SOURCE),sha(historic.WEIGHTS))!=(historic.SOURCE_SHA,historic.V14_SHA): raise ValueError("different original")
    with historic.SOURCE.open() as f: ref={(int(r['seed']),r['side']):r for r in csv.DictReader(f) if r['opponent']=='solution92'}
    args.out.mkdir(parents=True,exist_ok=False);limit_threads()
    env=LuxAIS3GymEnv(numpy_output=True); stock=make_player("v14","player_0"); summary=[]
    try:
        for seed in (CASES if args.panel=='cases' else CONTROLS):
            for side in ('player_0','player_1'):
                p=args.out/f'{seed}_{side}.jsonl.gz'
                frames=[]
                opp=make_opponent("solution92",f"player_{1-int(side[-1])}")
                actor=PublicRecorder(stock,frames.append)
                actual=play_game(env,actor,opp,seed,side,train=False)
                require_no_agent_errors(actor,opp)
                historical=ref[seed,side]
                diffs=[k for k,v in historical.items() if k not in ('seed','side','opponent','secs')
                       and not np.isclose(float(actual[k]),float(v),rtol=0,atol=1e-10)]
                if (len(frames)!=152 or diffs or int(actual['steps'])!=303):
                    raise ValueError(f'{seed}/{side} differs: {len(frames)} frames, {diffs}; no diagnosis')
                with gzip.open(p,'xt') as f:
                    for frame in frames: f.write(json.dumps(frame,allow_nan=False,separators=(',',':'))+'\n')
                summary.append(dict(seed=seed,side=side,path=p.name,sha256=sha(p),our_wins=actual['our_wins'],
                                    opp_wins=actual['opp_wins'],frames=len(frames)))
    finally: env.close()
    with (args.out/'summary.json').open('x') as f:
        json.dump(dict(panel=args.panel,cases=CASES,controls=CONTROLS,records=summary,
                       coordinate_system='V14 canonical',visibility='np.unpackbits(...,axis=1)[:, :height]; direct sensor only',
                       comparator_sha256=historic.SOURCE_SHA,v14_sha256=historic.V14_SHA,recorder_sha256=sha(Path(__file__))),f,indent=2)

if __name__=='__main__': main()
