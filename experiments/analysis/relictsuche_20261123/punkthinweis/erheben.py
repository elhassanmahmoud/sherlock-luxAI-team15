"""Record authentic unchanged first matches and keep private grading arrays outside public trajectories."""
from hashlib import sha256
import gzip
import json
import os
from pathlib import Path
import random
import sys

import jax
import jax.numpy as jnp
import numpy as np
from luxai_s3.params import env_params_ranges
from luxai_s3.wrappers import LuxAIS3GymEnv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from scripts.common import make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step

FOLDER = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/punkthinweis")
ZIP = ROOT/"experiments/releases/20261117_sherlock_v16/agent.zip"
V16 = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
MIRROR = (0, 2, 1, 4, 3)


def sensor(seed):
    key, _ = jax.random.split(jax.random.key(seed))
    for name, values in env_params_ranges.items():
        key, sub = jax.random.split(key)
        if name == "unit_sensor_range":
            return jax.random.choice(sub, jnp.asarray(values))
    raise ValueError("Missing public sensor")


def save_npz(path, obj):
    tmp = path.with_suffix(".pending.npz")
    np.savez_compressed(tmp, **obj)
    tmp.replace(path)
    return sha256(path.read_bytes()).hexdigest()


def collect(env, seed, team, prefix):
    side, other = f"player_{team}", f"player_{1-team}"
    agent = r3_package_agent(side, ZIP)
    rival = make_opponent("solution92", other)
    agent.new_game(side)
    if hasattr(rival, "new_game"):
        rival.new_game(other)
    random.seed(seed)
    np.random.seed(seed)
    obs, info = env.reset(seed=seed)
    cfg = info["params"]
    if cfg["unit_sensor_range"] != 1:
        raise ValueError("Wrong sensor range")
    for p in (agent,rival):
        p.set_env_cfg(cfg)
    from sherlock.features import FEATURE_NAMES
    point_columns = [FEATURE_NAMES.index(d+"_point") for d in "curdl"]
    threat_column = FEATURE_NAMES.index("enemies_in_sap")
    s = env.state
    oracle = {"first_pair": np.asarray(s.relic_nodes)[[0,3]], "points": np.asarray(s.relic_nodes_map_weights)==1,
              "spawn": int(s.relic_spawn_schedule[0])+1}
    public = {}
    def put(key,val):
        public.setdefault(key, []).append(np.asarray(val).copy())
    for step in range(101):
        o = obs[side]
        if int(o["match_steps"]) != step or int(o["steps"]) != step:
            raise ValueError("Unexpected match boundary")
        cmd = agent.act(step, o)
        student = agent._imitation
        masks = np.zeros((16,5), bool)
        protected = np.ones(16, bool)
        if student.last_fz is not None:
            ctx, ids, f, m, _, _, _ = student.last_fz
            ids = np.asarray(ids)
            masks[ids] = m[:,:5][:,MIRROR] if team else m[:,:5]
            protected[ids] = (f[:,point_columns].max(1)>0) | (f[:,threat_column]>0)
        for k in ("sensor_mask", "relic_nodes_mask", "team_points", "units_mask"):
            put(k, o[k])
        for k in ("position","energy"):
            put(k,o["units"][k])
        for k, m in (("terrain",student.belief.tile_type),("known_points",student.belief.point_tiles)):
            put(k,m[::-1,::-1].T if team else m)
        put("commands",cmd)
        put("move_mask",masks)
        put("protected",protected)
        enemy = rival.act(step, obs[other])
        obs, _, term, trunc, info = env.step({side:cmd,other:enemy})
        if term[side] or trunc[side]:
            raise ValueError("Unexpected episode end")
        put("after", match_points_after_step(o,obs[side],info))
        if step==100:
            if int(obs[side]["match_steps"])!=0 or np.asarray(obs[side]["team_wins"]).sum()!=1:
                raise ValueError("Incomplete first match")
            match_won = int(obs[side]["team_wins"][team])
            for k in ("position","energy"):
                oracle["end_"+k] = np.asarray(obs[side]["units"][k][team])
            oracle["end_live"] = np.asarray(obs[side]["units_mask"][team])
    require_no_agent_errors(agent,rival)
    obs_hash = save_npz(prefix.with_suffix(".npz"),{k:np.stack(v) for k,v in public.items()})
    truth_hash = save_npz(prefix.with_suffix(".richter.npz"),oracle)
    return dict(seed=seed,team=team,steps=101,match_won=match_won,points=public["after"][-1].tolist(),
                cfg=cfg,public_sha=obs_hash,label_sha=truth_hash)


def main():
    if os.getenv("PYTHONHASHSEED")!="0" or sha256(ZIP.read_bytes()).hexdigest()!=V16:
        raise ValueError("Policy identity mismatch")
    limit_threads()
    seeds=np.arange(161420000,161421000,dtype=np.int32)
    selected=seeds[np.asarray(jax.jit(jax.vmap(sensor))(seeds))==1][:80].tolist()
    source={p.name:sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), HERE/"PLAN.md", ZIP)}
    binding=sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
    FOLDER.mkdir(exist_ok=True,parents=True)
    rows=[]
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for seed in selected:
            for team in (0,1):
                prefix=FOLDER/f"{seed}-{team}-{binding[:12]}"
                manifest=prefix.with_suffix(".json")
                if manifest.exists():
                    doc=json.loads(manifest.read_bytes())
                    if (doc["binding"]!=binding or doc["seed"]!=seed or doc["team"]!=team or
                            sha256(prefix.with_suffix(".npz").read_bytes()).hexdigest()!=doc["public_sha"] or
                            sha256(prefix.with_suffix(".richter.npz").read_bytes()).hexdigest()!=doc["label_sha"]):
                        raise ValueError("Changed cached prefix")
                else:
                    doc=collect(env,seed,team,prefix)
                    doc.update(binding=binding,name=prefix.name)
                    tmp=manifest.with_suffix(".tmp")
                    tmp.write_text(json.dumps(doc,sort_keys=True)+"\n")
                    tmp.replace(manifest)
                rows.append(doc)
            print(f"{len(rows)}/160 unveränderte Eröffnungen",flush=True)
    finally:
        env.close()
    summary=dict(sources=source,binding=binding,count=len(rows),seeds=selected,rows=rows)
    (HERE/"quellen.json.gz").write_bytes(gzip.compress((json.dumps(summary,sort_keys=True)+"\n").encode(),mtime=0))


if __name__=="__main__":
    main()
