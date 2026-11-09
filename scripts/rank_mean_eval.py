"""Fixed legal-rank technical/screen worker; never orchestrates other workers."""
from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

JOBS = ("off_solution", "on_solution", "on_direct")
TECH_KEYS = ((831006,"player_1"), (831000,"player_0"))
PROFILE = "rank_mean_screen_20261109"
V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
ZIP_SHA = "88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6"
HISTORY_SHA = "90324b008945da4a054a0559a108ee0023cf572d754b20af844160dfe4ebc435"
COHORTS = {"panel":list(range(9944000,9944020)),"direct":list(range(9944100,9944120))}


def require(ok, message="Rank screen contract failed"):
    if not ok: raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""): h.update(block)
    return h.hexdigest()


def plain(value):
    if isinstance(value,dict): return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,set)): return [plain(v) for v in value]
    if hasattr(value,"tolist"): return value.tolist()
    return value


def write(path, document):
    payload = json.dumps(plain(document),allow_nan=False,sort_keys=True,indent=2)+"\n"
    with Path(path).open("x") as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())


def bound(inventory, path):
    path = Path(path).resolve()
    require(inventory.get(str(path)) == digest(path),"Missing or changed bound evidence")
    return json.loads(path.read_text())


def keys(job):
    require(job in JOBS,"Unknown fixed job")
    start = 9944100 if job == "on_direct" else 9944000
    return [(seed, side) for seed in range(start,start+20) for side in ("player_0","player_1")]


def summarize(rows):
    import numpy as np
    from scripts.league_gates import _bootstrap
    require(set(rows)==set(JOBS),"All three complete jobs required")
    normalized, reports = {}, {}
    for job in JOBS:
        records=rows[job]; expected=set(keys(job)); found={}; counts={"W":0,"D":0,"L":0}
        require(len(records)==40,"Exactly40 games per job required")
        for r in records:
            key=(r["seed"],r["side"])
            require(type(r["seed"]) is int and key in expected and key not in found,"Duplicate/wrong game key")
            require(r["steps"]==303 and r["point_counting_version"]==2 and r["caught_errors"]==0,"Invalid complete game")
            require(all(type(r[k]) in (int,float) and math.isfinite(r[k]) and r[k]>=0
                        for k in ("our_wins","opp_wins","our_points","opp_points")),"Invalid game numbers")
            require(all(float(r[k]).is_integer() for k in ("our_wins","opp_wins","our_points","opp_points"))
                    and r["our_wins"]<=3 and r["opp_wins"]<=3,"Noninteger game result")
            score=1 if r["our_wins"]>r["opp_wins"] else 0 if r["our_wins"]<r["opp_wins"] else .5
            require(r["result"]==score,"Result differs from match wins")
            changes=r["aggregation"].get("proposal_changed_steps",0)
            units=r["aggregation"].get("proposal_changes",0)
            require(type(changes) is int and 0<=changes<=300 and changes==r["observed_proposal_changed_steps"]
                    and type(units) is int and changes<=units<=changes*16
                    and (job!="off_solution" or changes==0),"Invalid proposal change count")
            found[key]=r; counts[{1:"W",.5:"D",0:"L"}[score]]+=1
        require(set(found)==expected,"Missing game keys")
        values=np.array([(found[(seed,"player_0")]["result"]+found[(seed,"player_1")]["result"])/2
                         for seed in sorted({k[0] for k in expected})])
        normalized[job]=found
        reports[job]=dict(**counts,score=float(values.mean()),ci95=list(_bootstrap(values)))
    panel=COHORTS["panel"]
    differences=np.array([sum(normalized["on_solution"][(seed,side)]["result"]-
                              normalized["off_solution"][(seed,side)]["result"]
                              for side in ("player_0","player_1"))/2 for seed in panel])
    exposure=sum(any(normalized["on_solution"][(seed,side)]["aggregation"].get("proposal_changed_steps",0)>0
                     for side in ("player_0","player_1")) for seed in panel)
    doubled=lambda job:2*reports[job]["W"]+reports[job]["D"]
    gates=dict(exposure=exposure>=5,solution=doubled("on_solution")>=doubled("off_solution"),
               direct=doubled("on_direct")>=48)
    return dict(status="complete_descriptive",games=120,exposed_panel_maps=exposure,
                solution={k:reports[k] for k in JOBS[:2]},direct=reports["on_direct"],
                solution_delta=float(differences.mean()),solution_delta_ci95=list(_bootstrap(differences)),
                gates=gates,eligible_for_separate_design=all(gates.values()),promotion=False,
                exposure_definition="Changed legal network proposal; not proof of a changed final action after rules",
                uncertainty="20 whole-map clusters/block;5000 bootstrap draws,PCG64 seed0,unadjusted95%; descriptive")


def check_owner(state, job, argv, *, pid,pgid,ppid,executable,actual):
    record=state.get("jobs",{}).get(job,{})
    require(state.get("status")=="running" and state.get("profile")==PROFILE
            and 1<=len(state.get("active",[]))<=2 and job in state["active"]
            and set(state["active"])<=({"technical"} if job=="technical" else set(JOBS))
            and state.get("owner_pid")==ppid and ppid>1
            and record.get("pid")==record.get("pgid")==pid==pgid
            and record.get("owner_pid")==ppid and record.get("argv")==argv
            and executable==argv[0] and isinstance(actual,list)
            and len(actual)==len(argv) and actual[1:]==argv[1:],"Unowned/mismatched worker launch")


class Guard:
    def __init__(self,admission,path,sha,state_path,job,argv):
        self.a,self.path,self.sha,self.state_path,self.job,self.argv=admission,path,sha,Path(state_path),job,argv
        self.last=0.

    def __call__(self,force=False):
        from scripts.fog_reward_supervisor import guard
        a=self.a
        require(not Path(a["stop_file"]).exists(),"External STOP")
        if not force and time.monotonic()-self.last<10:return
        deadline=time.monotonic()+15
        wave=("technical",) if self.job=="technical" else JOBS[:2] if self.job in JOBS[:2] else ("on_direct",)
        while True:
            state=json.loads(self.state_path.read_text())
            if self.last or all(name in state.get("jobs",{}) for name in wave):break
            require(time.monotonic()<deadline and not Path(a["stop_file"]).exists(),"Initial ownership registration missing/STOP")
            time.sleep(.05)  # Registration only; no model, game, or retry.
        if self.job=="on_direct":
            require(all(state["jobs"].get(j,{}).get("returncode")==0 for j in JOBS[:2])
                    and state["active"]==["on_direct"],"Direct job follows both completed panel jobs")
        check_owner(state,self.job,self.argv,pid=os.getpid(),pgid=os.getpgrp(),ppid=os.getppid(),
                    executable=sys.executable,actual=getattr(sys,"orig_argv",None))
        require(type(state.get("allow_battery")) is bool and all(state.get(k)==a[k] for k in
                ("root","out","python","plans","source","protected","stop_file","allow_battery")),
                "Ownership state differs from Root admission")
        require(state.get("admission_sha256")==self.sha and digest(self.path)==self.sha
                and state["inputs"].get(str(self.path))==self.sha
                and all(state["inputs"].get(k)==v for k,v in a["inputs"].items()),"Owner input/admission binding differs")
        guard(state,{},allow_battery=a["allow_battery"])
        self.last=time.monotonic()


def check_technical(games):
    expected=[(mode,seed,side) for mode in (False,True) for seed,side in TECH_KEYS]
    require(len(games)==4 and [(r["mode"],r["seed"],r["side"]) for r in games]==expected
            and all(r["steps"]==303 and (r["mode"] or r["off_reproduced"] is True) for r in games)
            and sum(r["observed_proposal_changed_steps"] for r in games if r["mode"])>0
            and sum(r["native_divergent_frames"] for r in games if r["mode"])>0,
            "Four technical proofs require OFF reproduction, ON legal proposal and native stream divergence")


def admission(path,sha,stage):
    from scripts.early_curriculum_study import source_identity,hashes
    path=Path(path).resolve();require(digest(path)==sha,"Root admission SHA mismatch")
    a=json.loads(path.read_text());root=Path(a["root"]).resolve()
    require(a.get("schema_version")==1 and a.get("profile")==PROFILE and a.get("stage")==stage
            and a.get("start_authorized") is True,"Separate explicit Root start decision required")
    require(type(a.get("allow_battery")) is bool,"Root admission must bind boolean allow_battery")
    require(root==Path(__file__).resolve().parents[1]==Path.cwd().resolve(),"Run only installed frozen checkout")
    require(source_identity(root,a["python"],a["plans"])==a["source"],"Frozen source differs")
    protected={str(root/f"agents/sherlock/weights/agent_p{i}.pth"):V14_SHA for i in (0,1)}
    protected[str(root/"Gruppe15.zip")]=ZIP_SHA
    require(a["protected"]==protected and hashes(protected)==protected and hashes(a["inputs"])==a["inputs"],"Input/V14/ZIP changed")
    config=bound(a["inputs"],a["config_manifest"])
    require(config["source_sha256"]==V14_SHA and a["config"]==dict(config["source_config"],frozen=False),"Inference config differs")
    out=Path(a["out"]).resolve();base=root/"experiments/analysis"/PROFILE
    require(out.parent==base and out.name==("technical_v1" if stage=="technical" else "performance_v1"),"Fixed exclusive output required")
    require(all(out!=Path(p) and out not in Path(p).parents for p in a["inputs"]),"Input/output overlap")
    if stage=="performance":
        seeds=bound(a["inputs"],a["seed_acceptance"])
        require(seeds.get("status")=="PASS" and seeds.get("profile")==PROFILE and seeds.get("cohorts")==COHORTS
                and seeds.get("no_observed_conflicts") is True and bool(seeds.get("limitations"))
                and bool(seeds.get("files")),"Fixed seed audit not accepted")
        require(all(a["inputs"].get(p)==h==digest(p) for p,h in seeds["files"].items()),"Unbound seed evidence")
        tech=bound(a["inputs"],a["technical_receipt"])
        require(tech.get("status")=="complete" and tech.get("profile")==PROFILE and tech.get("stage")=="technical"
                and tech.get("source")==a["source"] and tech.get("config")==a["config"]
                and bool(tech.get("files")),"Technical receipt source/config differs")
        check_technical(tech["games"])
        require(all(a["inputs"].get(p)==h==digest(p) for p,h in tech["files"].items()),"Unbound raw technical proof")
    return a


def make_agent(a,enabled):
    from scripts.par_eval import build_cfg
    from scripts.rank_mean_agent import RankMeanAgent
    weights=str(Path(a["root"])/"agents/sherlock/weights/agent_p0.pth")
    cfg=build_cfg(weights,["frozen=false"])
    require(vars(cfg)==a["config"],"Actual checkpoint config differs")
    agent=RankMeanAgent("player_0",agent_path=weights,cfg=cfg,train=False,seed=0,rank_enabled=enabled)
    agent.set_to_eval_mode();agent.autosave_on_terminate=False
    require(not agent.training and agent.epsilon==0 and not agent.cfg.frozen and agent.learn_enabled is False
            and len(agent.aggregation_members)==36 and len({id(m) for m in agent.aggregation_members})==36
            and agent.rank_enabled is enabled and agent.feat_dim==79 and agent.n_actions==6
            and agent.cnn_policy is None,"Wrong actual V14 inference role")
    return agent


def as_array(value):
    import numpy as np
    if hasattr(value,"detach"):value=value.detach().cpu().numpy()
    return np.asarray(value).copy()


def numpy_rank_mean(member_q,masks):
    """Independent integer midrank reconstruction; no prototype/Torch helper."""
    import numpy as np
    q=np.asarray(member_q);masks=np.asarray(masks)
    require(q.ndim==3 and q.shape[0]>0 and q.shape[2]==6 and masks.shape==q.shape[1:]
            and masks.dtype==np.bool_ and np.isfinite(q).all() and masks.any(axis=1).all(),
            "Invalid Q values or legal masks")
    out=np.full(masks.shape,-1.0)
    for row,mask in enumerate(masks):
        legal=np.flatnonzero(mask);count=len(legal)
        if count==1:out[row,legal]=.5;continue
        selected=q[:,row,:][:,legal]
        for action in legal:
            values=q[:,row,action,None]
            numerator=2*int((selected<values).sum())+int((selected==values).sum())-q.shape[0]
            out[row,action]=numerator/(q.shape[0]*2*(count-1))
    return out


def check_aggregation(agent,captured,sid,ms):
    """Validate genuine instance outputs and current decision cache, no forwards."""
    import numpy as np
    records=captured["members"]
    require(len(records)==36,"Expected36 original network captures")
    empty=dict(ids=[],masks=[],member_q=[],features=[],raw_mean=[],rank_mean=[],raw_greedy=[],
               rank_greedy=[],proposal_changes=0,active=False)
    if ms==0:
        require(not any(records) and not captured["aggregate"] and agent.aggregation_last is None,
                "Reset unexpectedly ran a network or retained diagnostics")
        return empty
    cache=agent._cache
    require(cache is not None and cache[0]==sid and cache[1]["step"]==sid
            and cache[1]["match_step"]==ms and agent._prev_ctx is cache[1],"Stale decision cache")
    _,ctx,ids,feat_map,mask_map,_=cache
    if not ids:
        require(not any(records) and not captured["aggregate"] and agent.aggregation_last is None,
                "No-unit frame unexpectedly ran a network or retained diagnostics")
        return empty
    require(len(set(ids))==len(ids) and len(agent.aggregation_members)==36,"Invalid member/UID count")
    features=np.stack([feat_map[u] for u in ids]).astype(np.float32)
    masks=np.stack([mask_map[u] for u in ids])
    outputs=[]
    for module,record in zip(agent.aggregation_members,records):
        require(len(record)==1,"Missing/extra member forward")
        actual,output=record[0]
        require(actual.shape==(len(ids),module.feat_dim) and np.array_equal(actual,features[:,:module.feat_dim])
                and output.shape==(len(ids),6),"Member features/order/output shape differ")
        outputs.append(output)
    member_q=np.stack(outputs)
    require(masks.shape==(len(ids),6) and masks.dtype==np.bool_ and masks.any(axis=1).all()
            and np.isfinite(member_q).all(),"Invalid Q values or legal masks")
    raw=member_q.mean(axis=0)
    record=dict(ids=list(ids),masks=masks,member_q=member_q,features=features,raw_mean=raw,
                rank_mean=[],raw_greedy=[],rank_greedy=[],proposal_changes=0,active=True)
    if not agent.rank_enabled:
        require(not captured["aggregate"] and agent.aggregation_last is None,"OFF aggregation path changed")
        return plain(record)
    rank=numpy_rank_mean(member_q,masks)
    require(len(captured["aggregate"])==1,"Missing/extra rank aggregate forward")
    aggregate_input,aggregate_output=captured["aggregate"][0]
    require(np.array_equal(aggregate_input,features) and aggregate_output.shape==rank.shape
            and np.array_equal(aggregate_output,rank.astype(aggregate_output.dtype)),"Actual rank aggregate differs")
    diag=agent.aggregation_last
    require(isinstance(diag,dict) and diag.get("step")==sid and list(diag.get("ids",[]))==list(ids),
            "Aggregation diagnostic IDs/step differ")
    require(np.array_equal(as_array(diag["masks"]),masks) and np.array_equal(as_array(diag["member_q"]),member_q),
            "Aggregation diagnostic masks/member outputs differ")
    actual_raw=as_array(diag["raw_mean"]);actual_rank=as_array(diag["rank_mean"])
    require(actual_raw.shape==raw.shape and np.allclose(actual_raw,raw,rtol=1e-5,atol=1e-6)
            and np.array_equal(actual_rank,rank.astype(actual_rank.dtype)),"Aggregation diagnostic means differ")
    # Raw mean is the actual Torch reduction, as in V14. NumPy reduction can
    # round differently near a raw-Q tie; do not invent a different baseline.
    raw_greedy=np.where(masks,actual_raw,-np.inf).argmax(axis=1)
    rank_greedy=rank.argmax(axis=1)
    require(np.array_equal(as_array(diag["raw_greedy"]),raw_greedy)
            and np.array_equal(as_array(diag["rank_greedy"]),rank_greedy),"Legal greedy diagnostic differs")
    record.update(raw_mean=actual_raw,rank_mean=rank,raw_greedy=raw_greedy,rank_greedy=rank_greedy,
                  proposal_changes=int((raw_greedy!=rank_greedy).sum()))
    return plain(record)


@contextmanager
def hook_audit(agent,guard,technical=False):
    """Passive hooks only on this instance; never patch a class or call a net."""
    import numpy as np
    members=tuple(agent.aggregation_members)
    require(len(members)==36 and len({id(m) for m in members})==36,"Original36 unique members required")
    originals={name:(name in vars(agent),vars(agent).get(name),getattr(agent,name)) for name in ("act","_act")}
    captured={};handles=[]
    audit=dict(frames=0,proposal_changed_steps=0,proposal_changes=0,calls=0,last=None)
    def member_hook(index):
        def capture(module,args,output):
            require(len(args)==1,"Unexpected member forward inputs")
            captured["members"][index].append((as_array(args[0]),as_array(output)))
        return capture
    def aggregate_hook(module,args,output):
        require(len(args)==1,"Unexpected aggregate inputs")
        captured["aggregate"].append((as_array(args[0]),as_array(output)))
    def core(step,obs):
        captured["core_calls"]+=1
        result=originals["_act"][2](step,obs)
        captured["core_final"]=as_array(result)
        return result
    def act(step,obs):
        guard();captured.clear();captured.update(members=[[] for _ in members],aggregate=[],core_calls=0)
        result=originals["act"][2](step,obs)
        require(captured["core_calls"]==1 and agent.caught_errors==0
                and np.array_equal(result,captured["core_final"]),"Original action pipeline differs or failed")
        require(np.array_equal(agent.param_est._prev["act"],result),"Original remember lacks submitted command")
        sid=int(np.asarray(obs["steps"]));ms=int(np.asarray(obs["match_steps"]))
        require(tuple(agent.aggregation_members)==members,"Original members changed during game")
        record=check_aggregation(agent,captured,sid,ms)
        changes=record["proposal_changes"];changed=changes>0
        audit["frames"]+=1;audit["proposal_changed_steps"]+=int(changed);audit["proposal_changes"]+=changes
        audit["calls"]+=int(agent.rank_enabled and record["active"])
        require(all(agent.aggregation_stats.get(k,0)==audit[k] for k in
                    ("calls","proposal_changes","proposal_changed_steps")),"Aggregation counters differ")
        if not technical:
            record.pop("member_q");record.pop("features")
        audit["last"]=dict(step=sid,final=plain(result),proposal_changed=changed,aggregation=record)
        return result
    try:
        for index,module in enumerate(members):handles.append(module.register_forward_hook(member_hook(index)))
        if agent.rank_enabled:handles.append(agent.q.register_forward_hook(aggregate_hook))
        agent._act=core;agent.act=act
        yield audit
    finally:
        for handle in reversed(handles):handle.remove()
        for name,(owned,value,_) in originals.items():
            if owned:setattr(agent,name,value)
            elif name in vars(agent):delattr(agent,name)


class RecordedEnv:
    def __init__(self,env,side,audit,stream,technical):
        self.env,self.side,self.audit,self.stream,self.technical=env,side,audit,stream,technical
        self.action_hash=hashlib.sha256();self.matches=[];self.frames=0;self.resets=0
    def reset(self,seed):
        obs,info=self.env.reset(seed=seed);self.obs=obs;return obs,info
    def step(self,actions):
        import numpy as np
        from scripts.targeting_probe import action_bytes
        from scripts.scoring import match_points_after_step
        self.action_hash.update(action_bytes(actions))
        record=self.audit["last"]
        require(record["step"]==self.frames and record["final"]==np.asarray(actions[self.side]).tolist(),"Hook/engine command mismatch")
        if self.technical or record["proposal_changed"]:
            self.stream.write(json.dumps(record,allow_nan=False)+"\n");self.stream.flush()
        self.resets+=int(self.obs[self.side]["match_steps"]==0)
        next_obs,reward,terminated,truncated,info=self.env.step(actions)
        points=match_points_after_step(self.obs[self.side],next_obs[self.side],info)
        done=bool(np.asarray(terminated[self.side])) or bool(np.asarray(truncated[self.side]))
        if int(next_obs[self.side]["match_steps"])==0 or done:
            self.matches.append(dict(match_idx=len(self.matches),points=plain(points),cumulative_wins=plain(next_obs[self.side]["team_wins"])))
        self.obs=next_obs;self.frames+=1
        return next_obs,reward,terminated,truncated,info


def one_game(a,seed,side,enabled,direct,trace,guard,technical):
    from scripts.common import make_opponent,play_game
    from luxai_s3.wrappers import LuxAIS3GymEnv
    guard(force=True)
    from scripts.experiment import limit_threads
    limit_threads()
    agent=make_agent(a,enabled)
    opponent=make_agent(a,False) if direct else make_opponent("solution92",f"player_{1-int(side[-1])}")
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        with Path(trace).open("x") as stream,hook_audit(agent,guard,technical) as audit, \
                (hook_audit(opponent,guard) if direct else nullcontext()):
            wrapped=RecordedEnv(env,side,audit,stream,technical)
            row=play_game(wrapped,agent,opponent,seed,side,False)
            require(row["steps"]==audit["frames"]==wrapped.frames==303 and wrapped.resets==3
                    and len(wrapped.matches)==3 and agent.caught_errors==0
                    and getattr(opponent,"caught_errors",0)==0,"Incomplete/failed game")
            row.update(caught_errors=0,aggregation=dict(agent.aggregation_stats),
                       observed_proposal_changed_steps=audit["proposal_changed_steps"],
                       action_sha256=wrapped.action_hash.hexdigest(),matches=wrapped.matches)
    finally:env.close()
    guard(force=True)
    return row


def historical(a,seed,side):
    path=Path(a["root"])/"experiments/analysis/continuation_20261102/targeting/manifest.json"
    require(digest(path)==HISTORY_SHA,"Historical manifest changed")
    doc=bound(a["inputs"],path)
    found=[g for g in doc["games"] if (g["key"]["seed"],g["key"]["side"])==(seed,side)]
    require(len(found)==1 and found[0]["complete"] is True,"Historical game missing")
    g=found[0];trace=path.parent/g["trace"]["path"]
    require(a["inputs"].get(str(trace))==g["trace"]["sha256"]==digest(trace),"Historical trace unbound")
    with gzip.open(trace,"rt") as stream:frames=[json.loads(line) for line in stream]
    require(len(frames)==303 and all(f["key"]["obs_step"]==i and f["key"]["seed"]==seed
            and f["key"]["side"]==side for i,f in enumerate(frames)),"Historical frame sequence differs")
    return g["observed"],frames


def run(a,path,sha,owner_path,job,argv):
    from scripts.early_curriculum_study import hashes
    out=Path(a["out"]);base=out.parent
    guard=Guard(a,path,sha,owner_path,job,argv)
    guard(force=True)
    if job=="technical":
        # Validate both old inputs before the first model is constructed.
        histories={key:historical(a,*key) for key in TECH_KEYS}
    base.mkdir(parents=True,exist_ok=True)
    write(base/f"{job}_launch.json",dict(profile=PROFILE,admission_sha256=sha,argv=argv,pid=os.getpid()))
    target=out/job;target.mkdir(parents=True,exist_ok=False)
    games=[]
    try:
        with (target/"games.jsonl").open("x") as raw:
            selected=[(mode,seed,side) for mode in (False,True) for seed,side in TECH_KEYS] if job=="technical" else [
                (job!="off_solution",seed,side) for seed,side in keys(job)]
            for index,(mode,seed,side) in enumerate(selected):
                trace=target/f"events_{index:02}.jsonl"
                row=one_game(a,seed,side,mode,job=="on_direct",trace,guard,job=="technical")
                row.update(mode=mode,off_reproduced=False)
                if job=="technical":
                    expected,frames=histories[(seed,side)]
                    current=[json.loads(line) for line in trace.read_text().splitlines()]
                    require(len(current)==303,"Technical native frame count differs")
                    row["native_divergent_frames"]=sum(c["final"]!=f["native_actions"] for c,f in zip(current,frames))
                    if not mode:
                        require(all(row[k]==expected[k] for k in ("seed","side","steps","our_wins","opp_wins","result",
                            "our_points","opp_points","point_counting_version","matches","action_sha256")),"OFF historical game mismatch")
                        require(row["native_divergent_frames"]==0,"OFF historical native arrays differ")
                        row["off_reproduced"]=True
                raw.write(json.dumps(plain(row),allow_nan=False)+"\n");raw.flush();games.append(row)
        if job=="technical":check_technical(games)
        else:require(len(games)==40,"Fixed job incomplete")
        guard(force=True)
        receipt=dict(profile=PROFILE,status="complete",stage=a["stage"],job=job,admission_sha256=sha,
            source=a["source"],config=a["config"],command=argv,games=games,
            files=hashes(p for p in target.iterdir() if p.is_file()))
        write(target/"receipt.json",receipt)
        return receipt
    except BaseException as exc:
        write(target/"failed.json",dict(status="failed",error=f"{type(exc).__name__}: {exc}",completed_games=len(games)))
        raise


def check_closed_state(state,sha):
    require(state.get("profile")==PROFILE and state.get("status")=="complete"
            and state.get("active")==[] and state.get("admission_sha256")==sha
            and set(state.get("jobs",{}))==set(JOBS)
            and all(type(j.get("returncode")) is int and j["returncode"]==0
                    and j.get("finished_at") is not None for j in state["jobs"].values()),
            "All owned jobs must be successfully closed")


def analyze(a,sha,state_path):
    state_path=Path(state_path).resolve();state_hash=digest(state_path)
    state=json.loads(state_path.read_text());check_closed_state(state,sha)
    require(type(state.get("allow_battery")) is bool and all(state.get(k)==a[k] for k in
            ("root","out","source","protected","allow_battery")),"Closed state provenance differs")
    rows={};receipts={}
    for job in JOBS:
        folder=Path(a["out"])/job;receipt=json.loads((folder/"receipt.json").read_text())
        require(receipt.get("status")=="complete" and receipt.get("profile")==PROFILE
                and receipt.get("job")==job and receipt.get("stage")=="performance"
                and receipt.get("admission_sha256")==sha and receipt.get("source")==a["source"]
                and receipt.get("config")==a["config"] and len(receipt.get("files",{}))==41,"Incomplete/unbound job receipt")
        expected={str(folder/"games.jsonl"),*(str(folder/f"events_{i:02}.jsonl") for i in range(40))}
        require(set(receipt["files"])==expected and all(digest(p)==h for p,h in receipt["files"].items()),"Raw job files missing/changed")
        receipt_path=str(folder/"receipt.json");receipts[receipt_path]=digest(receipt_path)
        require(state["jobs"][job]["argv"]==receipt["command"] and state.get("receipts",{}).get(job)==
                dict(path=receipt_path,sha256=receipts[receipt_path]),"Owner command/receipt binding differs")
        data=[json.loads(line) for line in (folder/"games.jsonl").read_text().splitlines()]
        require(data==receipt["games"],"Receipt/raw rows differ")
        for i,row in enumerate(data):
            events=[json.loads(line) for line in (folder/f"events_{i:02}.jsonl").read_text().splitlines()]
            require(len(events)==row["observed_proposal_changed_steps"] and all(e["proposal_changed"] is True for e in events)
                    and len({e["step"] for e in events})==len(events),"Actual change events/count differ")
        rows[job]=data
    result=summarize(rows)
    require(digest(state_path)==state_hash,"Final ownership state changed during analysis")
    result["input_sha256"]=dict(admission=sha,state={str(state_path):state_hash},receipts=receipts)
    return result


def main():
    for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ[name]="1"
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("technical","run","analyze"))
    parser.add_argument("--admission",type=Path,required=True)
    parser.add_argument("--admission-sha",required=True)
    parser.add_argument("--owner-state",type=Path)
    parser.add_argument("--job",choices=JOBS)
    args=parser.parse_args()
    a=admission(args.admission,args.admission_sha,"technical" if args.command=="technical" else "performance")
    if args.command=="analyze":
        require(args.owner_state is not None and args.job is None,"Analysis requires closed owner state; cannot launch workers")
        result=analyze(a,args.admission_sha,args.owner_state)
        admission(args.admission,args.admission_sha,"performance")
        write(Path(a["out"])/"summary.json",result)
    else:
        require(args.owner_state is not None and (args.job is None if args.command=="technical" else args.job in JOBS),"Exact job/owner state required")
        argv=[sys.executable,*sys.orig_argv[1:]]
        run(a,args.admission.resolve(),args.admission_sha,args.owner_state,
            "technical" if args.command=="technical" else args.job,argv)


if __name__=="__main__":main()
