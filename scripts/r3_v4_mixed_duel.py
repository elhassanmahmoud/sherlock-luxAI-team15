"""One fixed paired R3 vs v4 mixed duel on 24 fresh maps, with eight historical preflight games.

In the prepared b2bd67e snapshot:
  python -B -m scripts.r3_v4_mixed_duel check
  python -B -u -m scripts.r3_v4_mixed_duel run --out NEW_OR_RESUMED_DIR
  python -B -m scripts.r3_v4_mixed_duel assess --out FINISHED_DIR
"""
import argparse
import csv
from hashlib import sha256
from importlib import import_module, metadata, util
import json
import os
from pathlib import Path
import platform
import random
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import zipfile

import numpy as np

from scripts.final_battle_select import SEATS, checked_run_files
from scripts.residual_ensemble_compare import interval
from scripts.scoring import match_points_after_step

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/"experiments/analysis/movement_soft_20261115"
PARITY=STUDY/"candidate_package/parity.json"
R3ZIP=PARITY.with_name("r3-final-candidate.zip")
V14=ROOT/"agents/sherlock/weights/agent_p0.pth"
STUDENT=ROOT/"experiments/candidates/umbau_20261115/student_v4.pth"
CSV=ROOT/"experiments/analysis/umbau_20261115/confirm/v15_candidate.csv"
MAPS=range(7170000,7170024)
OVERRIDES={"imit_stay_bias":1.5,"imit_unstack":True}
SELECTION={"r3":(7273200,7273201),"v4":(7158000,7158015)}
FIELDS=("result","wins","losses","points","opp_points","steps")
EXPECTED_SOURCES="cd7be0b70d431c3cf233529ad34d2bd2928163a0eb878b4a603c456e4e0aa040"
R3_RESEARCH="0105658188b2ec5eaf5c3a4b0ef477be9a1412f8"
V4_SOURCE="b2bd67e43f213cd99669bf3eee759e3fdeb1c0f5"
PINS={"v14":"98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8",
      "student":"0e8b280cb2173c4efd0d0c94e38119bf2f570dd5af06f52e1b5a7c9743ad7b7f",
      "r3_zip":"8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d",
      "r3_parity":"bf8a159eb3c1fd2cb47d13426fdaaaeb7c593d5fbc6a14be35079363b1bfcf16",
      "v4_table":"1cc603732dafff379e57f236be4fc37a0bdd7dfcfa35fcc0e7ce78c95387c4cd"}
V15_PUBLISHED_PACK="28933a3b7810037b0af37b9ccfbf261c7c9b2b1353c8e0e8ef3b25e2c77cae45"


def require(ok,why):
    if not ok: raise ValueError(why)


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def selection(rows,arm):
    expected={}
    for seat in SEATS:
        for won in (0,1):
            seed=min(s for (s,p),r in rows.items() if p==seat and r["result"]==won)
            require(seed==SELECTION[arm][1-won],f"Different predeclared {arm} case {seat}/{won}")
            expected[arm,seed,seat]=rows[seed,seat]
    return expected


def historical():
    direct,m,h=checked_run_files(STUDY/"confirmation/direct","selective_movement",range(7273200,7273260),("v14",))
    require(h=={"manifest_sha256":"db650772a8858bb0cfc2828b7445d8c961bef8f5e3c1516055aec068b5f657b8",
                "games_sha256":"5a7c9322d6eae5fcf76fb61b0ceb1f15bcef380f012407b4ffc83863d9b8c3a0"},"R3 archive")
    old={(s,p):{k:int(r[k]) for k in FIELDS} for (_,s,p),r in direct.items()}
    require(digest(CSV)==PINS["v4_table"],"Wrong V15 archive")
    v4={}
    with CSV.open(newline="") as f:
        for r in csv.DictReader(f):
            if r["opponent"]!="self:agents/sherlock/weights/agent_p0.pth":continue
            k=int(r["seed"]),r["side"]
            require(k not in v4,"Repeated published v4 control")
            v4[k]=dict(zip(FIELDS,(int(r[c]) for c in ("game_win","our_wins","opp_wins","our_points","opp_points","steps"))))
            q=v4[k]
            require(q["steps"]==303 and q["wins"]+q["losses"]==3 and q["result"]==int(q["wins"]>q["losses"])==float(r["result"]),"Published score")
    require(set(v4)=={(s,p) for s in range(7158000,7158400) for p in SEATS},"Missing v4 direct seats")
    return {**selection(old,"r3"),**selection(v4,"v4")}


def inputs():
    for name,path in (("v14",V14),("student",STUDENT),("r3_zip",R3ZIP),("r3_parity",PARITY),("v4_table",CSV)):
        require(digest(path)==PINS[name],f"Different input {name}")
    q=json.loads(PARITY.read_bytes())
    require(q["result"]=="passed" and q["research_commit"]==R3_RESEARCH and q["zip_sha256"]==PINS["r3_zip"] and
            q["r3_sha256"]=="99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9" and
            {g["side"] for g in q["games"]}==set(SEATS) and sum(g["equal_action_matrices"] for g in q["games"])==606,
            "Original R3 course parity is missing")
    with zipfile.ZipFile(R3ZIP) as z:
        require(sha256(z.read("sherlock/weights/agent.pth")).hexdigest()==q["course_weights_sha256"],"R3 embedded weights")
    sources={str(p.relative_to(ROOT)):digest(p) for folder in ("agents","lux","scripts")
             for p in (ROOT/folder).rglob("*.py") if p.resolve()!=Path(__file__).resolve()}
    source=sha256(json.dumps(sources,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    require(source==EXPECTED_SOURCES,"Need a clean b2bd67e source tree plus this runner")
    engine=Path(util.find_spec("luxai_s3").origin).parent
    engine_files={p.name:digest(p) for p in engine.glob("*.py")}
    require(all(engine_files[k.split(".")[-1]+".py"]==v for k,v in q["engine_sha256"].items()),"Different course engine")
    return dict(pins=PINS,r3_research=R3_RESEARCH,v4_source=V4_SOURCE,v4_sources_sha256=source,
                pack_mode="mixed",combat_radius=5,student_overrides=OVERRIDES,published_pack_sha256=V15_PUBLISHED_PACK,
                tool_sha256=digest(Path(__file__)),seeds=list(MAPS),seats=list(SEATS),engine=engine_files,
                python=platform.python_version(),machine=platform.machine(),platform=platform.system(),
                versions={k:metadata.version(k) for k in ("scipy","numpy","torch","jax","jaxlib","luxai-s3")},
                flags={k:os.getenv(k) for k in ("PYTHONHASHSEED","JAX_PLATFORMS","XLA_FLAGS","CUDA_VISIBLE_DEVICES")})


def agents(temp):
    import torch
    from agents.sherlock.main import Agent_x
    from scripts.check_candidate_runner import verify_loaded
    from scripts.imitate import cmd_pack_hybrid
    with zipfile.ZipFile(R3ZIP) as z:
        z.extractall(temp)
    # R3's package has only relative agent imports. Its historical V14 modules remain
    # in sherlock.v14; b2bd67e uses agents.sherlock. No patching of either policy.
    sys.path.insert(0,str(temp))
    r3module=import_module("sherlock.main")
    require(Path(r3module.__file__).resolve()==temp/"sherlock/main.py","Wrong R3 module")
    r3=r3module.Agent_x("player_0",agent_path=str(temp/"sherlock/weights/agent.pth"))
    packed=temp/"v4_mixed.pth"
    cmd_pack_hybrid(SimpleNamespace(student=str(STUDENT),out=str(packed),mode="mixed",combat_radius=5,
                                    set=["imit_stay_bias=1.5","imit_unstack=true"]))
    v4=Agent_x("player_1",agent_path=str(packed),train=False,seed=0)
    v4.set_to_eval_mode()
    v4.autosave_on_terminate=False
    # Compare the loaded modules directly against the two pinned input checkpoints,
    # not just against whatever was embedded by the repack.
    original={"kind":"hybrid","mode":"mixed","combat_radius":5,"student_overrides":OVERRIDES,
              "v14_ckpt":torch.load(V14,map_location="cpu",weights_only=False),
              "student_ckpt":torch.load(STUDENT,map_location="cpu",weights_only=False)}
    verify_loaded(v4,original)
    require(Path(sys.modules[type(v4).__module__].__file__).resolve()==ROOT/"agents/sherlock/main.py" and
            Path(sys.modules[type(v4._imitation).__module__].__file__).resolve()==ROOT/"agents/sherlock/hybrid_agent.py" and
            Path(sys.modules[type(r3._actor).__module__].__file__).resolve()==temp/"sherlock/r3_adviser.py",
            "Agents are not using their registered separate module trees")
    require(not v4._imitation.v14.training and not v4._imitation.student.training and v4._imitation.student.has_sap_head,
            "Hybrid has a trainable or missing component")
    return {"r3":r3,"v4":v4},dict(local_pack_sha256=digest(packed),loaded_components_match_pinned_inputs=True,
                                  matches_published_pack_bytes=digest(packed)==V15_PUBLISHED_PACK)


def control(arm,side):
    # Original direct reference for each policy: native Agent_x, native params/defaults.
    namespace="sherlock.v14.main" if arm=="r3" else "agents.sherlock.main"
    player=import_module(namespace).Agent_x(side,agent_path=str(V14),name="Self-Play Snapshot",train=False)
    player.set_to_eval_mode()
    return player


def play(env,actors,arm,seed,seat,versus):
    own=actors[arm]; other=SEATS[1-SEATS.index(seat)]
    rival=actors[versus] if versus in actors else control(arm,other)
    pair={seat:own,other:rival}
    for player,a in pair.items(): a.new_game(player)
    random.seed(seed);np.random.seed(seed%(2**32))
    obs,info=env.reset(seed=seed)
    for a in pair.values():a.set_env_cfg(info["params"])
    totals=np.zeros(2,np.int64); matches=[]; steps=0
    updates={side:0 for side in SEATS}; action_sha={side:sha256() for side in SEATS}
    while True:
        orders={s:np.asarray(a.act(step=steps,obs=obs[s])) for s,a in pair.items()}
        for s,action in orders.items():
            require(action.shape==(16,3) and np.issubdtype(action.dtype,np.integer) and np.all((action[:,0]>=0)&(action[:,0]<=5)),"World command")
            action_sha[s].update(action.astype("<i8").tobytes())
        after,reward,term,trunc,info=env.step(orders)
        done={s:bool(term[s]) or bool(trunc[s]) for s in SEATS}
        require(done[seat]==done[other] and steps<303,"Course clock")
        for s,a in pair.items():
            # Both entrants receive their real submitted order and own transition.
            # The historical reference opponent follows its published train=False evaluation.
            if s==seat or versus in actors:
                a.update(step=steps,obs=obs[s],reward=reward[s],action=orders[s],terminated=done[s],next_obs=after[s])
                updates[s]+=1
        points=match_points_after_step(obs[seat],after[seat],info)
        totals+=points-np.asarray(obs[seat]["team_points"])
        win=np.asarray(after[seat]["team_wins"])-np.asarray(obs[seat]["team_wins"])
        if win.sum():
            require(int(obs[seat]["match_steps"])==100 and tuple(win.tolist()) in ((1,0),(0,1)),"Missing official match award")
            matches.append(dict(winner=SEATS[int(np.argmax(win))],world_points=points.tolist()))
        steps+=1;obs=after
        if done[seat]:break
    end=np.asarray(obs[seat]["team_wins"]).astype(int)
    team=SEATS.index(seat)
    require(steps==303 and len(matches)==3 and int(end.sum())==3 and updates[seat]==303 and
            updates[other]==(303 if versus in actors else 0),"Incomplete course game or update lifecycle")
    require(all(int(getattr(a,"caught_errors",0))==0 for a in pair.values()),"Entrant or opponent caught an error")
    if "v4" in (arm,versus):
        h=actors["v4"]._imitation
        require(not any(getattr(a,"caught_errors",0) for a in (h,h.v14,h.student)),"Hybrid child caught an error")
    return dict(arm=arm,opponent=versus,seed=seed,side=seat,result=int(end[team]>end[1-team]),wins=int(end[team]),
                losses=int(end[1-team]),points=int(totals[team]),opp_points=int(totals[1-team]),steps=steps,matches=matches,
                updates=updates,commands_sha256={s:h.hexdigest() for s,h in action_sha.items()})


def assessment(path):
    raw=path.read_bytes()
    rows=[json.loads(l) for l in raw.splitlines()]
    game={(r["seed"],r["side"]):r for r in rows}
    require(len(rows)==len(game)==2*len(MAPS) and set(game)=={(s,p) for s in MAPS for p in SEATS},"Missing, duplicate or extraneous duel")
    for r in rows:
        a=SEATS.index(r["side"]); matches=r["matches"]
        require(r["arm"]=="r3" and r["opponent"]=="v4" and r["steps"]==303 and r["wins"]+r["losses"]==3
                and r["result"]==int(r["wins"]>=2) and r["updates"]==dict.fromkeys(SEATS,303) and len(matches)==3 and
                sum(m["winner"]==r["side"] for m in matches)==r["wins"] and sum(m["world_points"][a] for m in matches)==r["points"] and
                sum(m["world_points"][1-a] for m in matches)==r["opp_points"],"Invalid sealed duel score")
    values=np.array([[game[s,p]["result"] for p in SEATS] for s in MAPS])
    wins=int(values.sum()); n=values.size
    mw=sum(r["wins"] for r in rows)
    return dict(maps=len(MAPS),games=n,r3_wins=wins,v4_wins=n-wins,r3_matches=mw,v4_matches=3*n-mw,
                r3_game_share=wins/n,paired_card_ci95=interval(values.mean(1),seed=2711,draws=10000),
                r3_wins_by_seat=dict(zip(SEATS,map(int,values.sum(0)))),map_two_one_zero=[int((values.sum(1)==i).sum()) for i in (2,1,0)],
                bootstrap="whole map, both seats; 10000 PCG64 draws, seed 2711, 95% percentiles",games_sha256=sha256(raw).hexdigest())


def check_replays(rows,expected):
    require(len(rows)==len(expected) and {(r["arm"],r["seed"],r["side"]) for r in rows}==expected.keys(),
            "Eight distinct preflight keys required")
    mismatches=[]
    for r in rows:
        key=r["arm"],r["seed"],r["side"]
        actual={f:r[f] for f in FIELDS}
        require(r["opponent"]=="historical_v14" and r["updates"][r["side"]]==303,"Wrong reproduction")
        if actual!=expected[key]:mismatches.append(dict(key=key,expected=expected[key],actual=actual))
    return mismatches


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("check","run","assess"))
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    stamp=inputs(); expected=historical()
    if a.mode=="check":
        print(json.dumps(dict(stamp=stamp,reproductions=[dict(arm=k[0],seed=k[1],side=k[2],**r) for k,r in sorted(expected.items())]),indent=2))
        return
    if not a.out:p.error("--out required")
    out=a.out.resolve()
    def read(p):return json.loads(p.read_bytes())
    if a.mode=="run":
        import fcntl
        import torch
        from luxai_s3.wrappers import LuxAIS3GymEnv
        from scripts.train_combat_advice import publish_json
        out.mkdir(parents=True,exist_ok=True)
        with (out/".lock").open("a") as guard, TemporaryDirectory(prefix="source-duel-") as tmp:
            fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
            mf=out/"manifest.json"
            if mf.exists():require(read(mf)==stamp,"Different run configuration on resume")
            else:
                require(not any(p.name!=".lock" for p in out.iterdir()),"Unbound output directory")
                publish_json(mf,stamp)
            torch.set_num_threads(1);torch.manual_seed(0)
            models,pack=agents(Path(tmp).resolve());env=LuxAIS3GymEnv(numpy_output=True)
            try:
                history=out/"reproduction.json"
                if not history.exists():
                    rows=[play(env,models,arm,seed,seat,"historical_v14") for arm,seed,seat in sorted(expected)]
                    failed=check_replays(rows,expected)
                    publish_json(history,dict(games=rows,pack=pack,mismatches=failed))
                prior=read(history)
                require(not check_replays(prior["games"],expected) and not prior["mismatches"],"Published scores differ; inspect reproduction.json")
                path=out/"games.jsonl"
                rows=[json.loads(l) for l in path.read_bytes().splitlines()] if path.exists() else []
                jobs=[(s,p) for s in MAPS for p in SEATS]
                require([(r["seed"],r["side"]) for r in rows]==jobs[:len(rows)] and all(
                    r["arm"]=="r3" and r["opponent"]=="v4" and r["steps"]==303 for r in rows),"Different incomplete history")
                with path.open("a") as stream:
                    for seed,seat in jobs[len(rows):]:
                        r=play(env,models,"r3",seed,seat,"v4")
                        stream.write(json.dumps(r,allow_nan=False)+"\n");stream.flush()
                        print(seed,seat,r["wins"],r["losses"],flush=True)
            finally:
                env.close()
            require(inputs()==stamp,"Changed study source")
            report=assessment(path)
            report.update(reproduction_sha256=digest(history),manifest_sha256=digest(mf))
            if not (out/"completed.json").exists():publish_json(out/"completed.json",report)
    require(read(out/"manifest.json")==stamp,"Wrong frozen configuration")
    history=out/"reproduction.json"
    require(not check_replays(read(history)["games"],expected) and not read(history)["mismatches"],"Failed recreation")
    report=assessment(out/"games.jsonl")
    report.update(reproduction_sha256=digest(history),manifest_sha256=digest(out/"manifest.json"))
    require(report==read(out/"completed.json"),"Changed study after completion")
    print(json.dumps(report,indent=2))


if __name__=="__main__":main()
