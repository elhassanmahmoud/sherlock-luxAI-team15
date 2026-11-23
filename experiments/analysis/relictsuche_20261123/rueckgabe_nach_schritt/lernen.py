"""Train a return-to-V16 decision using the observations made after the scout's first real move."""
import argparse
import gzip
import json
import random
from pathlib import Path

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.abschlusspruefung.vergleich import make
from experiments.analysis.relictsuche_20261123.vergleich.panel import sensor
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor, sha, stamp, write_once
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors


HERE = Path(__file__).resolve().parent
NAMES = ["turn", "route_left", "new_team", "new_near", "seen_share", "near_friend", "energy", "home_sum", "visible_near"]


def snapshot(obs, player, step):
    t, uid = player.team_id, player.uid
    seen = player.history.last_seen
    visible = np.asarray(obs["sensor_mask"], bool)
    pos = np.asarray(obs["units"]["position"][t, uid], int)
    if t:
        seen = seen[::-1, ::-1].T
    grid = np.indices(visible.shape)
    nearby = np.maximum(abs(grid[0] - pos[0]), abs(grid[1] - pos[1])) <= 2
    new = visible & (seen < 0)
    mask = np.asarray(obs["units_mask"][t], bool).copy()
    mask[uid] = False
    friends = np.asarray(obs["units"]["position"][t])[mask]
    distance = np.abs(friends - pos).sum(axis=1).min() if len(friends) else 46
    canonical = 23 - pos[::-1] if t else pos
    return [float(v) for v in (step, len(player.route), new.sum(), (new & nearby).sum(), (seen>=0).mean(),
                               distance, np.asarray(obs["units"]["energy"][t,uid]).item(), canonical.sum(), (visible & nearby).sum())]


def opening(env, seed, t, stop):
    random.seed(seed)
    np.random.seed(seed)
    side, other = f"player_{t}", f"player_{1-t}"
    own, rival = make("ortundflotte", side), make("solution92", other)
    monitor = Monitor(env, t, "discovery")
    obs, info = monitor.reset(seed=seed)
    for agent, seat in ((own, side), (rival, other)):
        if hasattr(agent, "new_game"):
            agent.new_game(seat)
        if hasattr(agent, "set_env_cfg"):
            agent.set_env_cfg(info["params"])
    picture = None
    prefix = None
    for step in range(101):
        if picture is None and own.changes > 0 and not own.done:
            picture = snapshot(obs[side], own, step)
            prefix = monitor.digest.hexdigest()
            if stop:
                own.done = True
        actions = {side:own.act(step, obs[side]), other:rival.act(step, obs[other])}
        obs = monitor.step(actions)[0]
    require_no_agent_errors(own.base, rival)
    return dict(features=picture, prefix=prefix, digest=monitor.digest.hexdigest(),
                sight=monitor.first_sight, credit=monitor.first_credit)


def fit(rows):
    train = [r for r in rows if r["split"] == "train" and r["keep"]["features"] is not None]
    x = np.asarray([r["keep"]["features"] for r in train])
    y = np.array([r["keep"]["sight"] - r["stop"]["sight"] for r in train])
    mean, sd = x.mean(0), x.std(0).clip(.001)
    z = (x-mean)/sd
    b = np.linalg.solve(z.T@z + 32*np.eye(x.shape[1]), z.T@(y-y.mean()))
    return dict(mean=mean.tolist(), sd=sd.tolist(), weights=b.tolist(), intercept=float(y.mean()), n=len(y))


def score(rows, model):
    chosen = []
    for r in rows:
        features = r["keep"]["features"]
        prediction = None if features is None else model["intercept"] + np.dot(
            (np.asarray(features)-model["mean"])/model["sd"], model["weights"])
        stop = prediction is not None and prediction >= 1
        pick = r["stop"] if stop else r["keep"]
        chosen.append([r["keep"]["sight"],r["stop"]["sight"],pick["sight"],r["keep"]["credit"],pick["credit"],
                       r["keep"]["digest"] != r["stop"]["digest"],stop])
    a = np.asarray(chosen)
    return dict(cards=len(rows), different=int(a[:,5].sum()), stopped=int(a[:,6].sum()),
                turns=(a[:,:5].mean(0)).tolist(), vs_keep=float((a[:,0]-a[:,2]).mean()),
                vs_stop=float((a[:,1]-a[:,2]).mean()), credit_vs_keep=float((a[:,3]-a[:,4]).mean()))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("freeze","play","fit"))
    p.add_argument("folder",type=Path)
    p.add_argument("lane",type=int,nargs="?",default=0)
    p.add_argument("workers",type=int,nargs="?",default=8)
    a = p.parse_args()
    limit_threads()
    manifest = HERE/"karten.json"
    if a.stage == "freeze":
        import jax
        entries=[]
        for split, offset, size in (("train",166100000,96),("valid",166110000,48)):
            seeds=np.arange(offset,offset+1200,dtype=np.int32)
            chosen=seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds))==1][:size]
            assert len(chosen)==size
            entries.extend([[split,int(s),i%2] for i,s in enumerate(chosen)])
        write_once(manifest,dict(entries=entries,plan=sha(HERE/"PLAN.md"),implementation=sha(Path(__file__))))
        return
    spec=json.loads(manifest.read_bytes())
    assert spec["plan"]==sha(HERE/"PLAN.md") and spec["implementation"]==sha(Path(__file__))
    token=stamp(spec)
    def path(seed):
        return a.folder/f"{seed}.json"
    if a.stage=="play":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for split,seed,t in spec["entries"][a.lane::a.workers]:
                keep=opening(env,seed,t,False)
                stop=opening(env,seed,t,True)
                assert keep["prefix"]==stop["prefix"] and keep["features"]==stop["features"]
                if keep["features"] is None:
                    assert keep==stop
                write_once(path(seed),dict(split=split,seed=seed,team=t,source=token,keep=keep,stop=stop))
        finally:
            env.close()
        return
    rows=[json.loads(path(s).read_bytes()) for _,s,_ in spec["entries"]]
    assert all([r["split"],r["seed"],r["team"]]==e and r["source"]==token for r,e in zip(rows,spec["entries"],strict=True))
    model=fit(rows)
    result={s:score([r for r in rows if r["split"]==s],model) for s in ("train","valid")}
    v=result["valid"]
    passed=v["different"]>=12 and min(v["vs_keep"],v["vs_stop"])>0 and v["credit_vs_keep"]>=0
    write_once(HERE/"ergebnis.json",dict(source=token,features=NAMES,model=model,results=result,passed=bool(passed)))
    (HERE/"eroeffnungen.jsonl.gz").write_bytes(gzip.compress(b"".join((json.dumps(r)+"\n").encode() for r in rows),mtime=0))


if __name__=="__main__":
    main()
