"""Fixed SAP-motion technical/screen worker; never orchestrates other workers."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
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
PROFILE = "sap_motion_screen_20261109"
V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
ZIP_SHA = "88dfbe320cc1df076366e43d928f76a230690d6b96b573eefd583d7979dff9d6"
HISTORY_SHA = "90324b008945da4a054a0559a108ee0023cf572d754b20af844160dfe4ebc435"
COHORTS = {"panel":list(range(9942000,9942020)),"direct":list(range(9942100,9942120))}


def require(ok, message="SAP screen contract failed"):
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
    start = 9942100 if job == "on_direct" else 9942000
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
            changes=r["leading"].get("changes",0)
            require(type(changes) is int and 0<=changes<=300 and changes==r["observed_changes"]
                    and (job!="off_solution" or changes==0),"Invalid intervention count")
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
    exposure=sum(any(normalized["on_solution"][(seed,side)]["leading"].get("changes",0)>0
                     for side in ("player_0","player_1")) for seed in panel)
    doubled=lambda job:2*reports[job]["W"]+reports[job]["D"]
    gates=dict(exposure=exposure>=5,solution=doubled("on_solution")>=doubled("off_solution"),
               direct=doubled("on_direct")>=48)
    return dict(status="complete_descriptive",games=120,exposed_panel_maps=exposure,
                solution={k:reports[k] for k in JOBS[:2]},direct=reports["on_direct"],
                solution_delta=float(differences.mean()),solution_delta_ci95=list(_bootstrap(differences)),
                gates=gates,eligible_for_separate_design=all(gates.values()),promotion=False,
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
            and sum(r["observed_changes"] for r in games if r["mode"])>0,
            "Four technical proofs with OFF reproduction and actual ON intervention required")


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
    from scripts.sap_motion_agent import SapMotionAgent
    weights=str(Path(a["root"])/"agents/sherlock/weights/agent_p0.pth")
    cfg=build_cfg(weights,["frozen=false"])
    require(vars(cfg)==a["config"],"Actual checkpoint config differs")
    agent=SapMotionAgent("player_0",agent_path=weights,cfg=cfg,train=False,seed=0,lead_enabled=enabled)
    agent.set_to_eval_mode();agent.autosave_on_terminate=False
    require(not agent.training and agent.epsilon==0 and not agent.cfg.frozen and agent.learn_enabled is False
            and len(agent.extra_q)==35 and agent.feat_dim==79 and agent.n_actions==6
            and agent.cnn_policy is None,"Wrong actual V14 inference role")
    return agent


def book(agent):
    return copy.deepcopy(dict(hits=agent._sap_hits,unknown=sorted(agent._sap_unknown),stats=agent.ep_stats,
        prev=agent._prev_actions,pred=agent._pred_pending,shape=agent._shape_pending,
        feats=agent._prev_feats,masks=agent._prev_masks))


def check_change(before,after,old,new,remembered,*,expected,calls):
    import numpy as np
    require(calls==1 and np.array_equal(after,expected),"Wrong hook output or core-call count")
    changed=np.flatnonzero(np.any(before!=after,axis=1))
    require(len(changed)<=1 and np.array_equal(before[:,0],after[:,0])
            and (not len(changed) or after[changed[0],0]==5),"More than one SAP offset changed")
    require(np.array_equal(remembered,after),"Original remember lacks submitted command")
    if len(changed):
        uid=int(changed[0]); wanted=copy.deepcopy(old)
        wanted["hits"][uid]=new["hits"][uid]
        wanted["unknown"]=[u for u in old["unknown"] if u!=uid]
        wanted["stats"]["sap_hits_est"]+=int(new["hits"][uid]>0)-int(old["hits"][uid]>0)
        require(plain(new)==plain(wanted),"SAP bookkeeping delta or pending state differs")
    else:require(plain(new)==plain(old),"No-change hook altered productive bookkeeping")


def observe_motion(history,current,counts,move_cost):
    """Independently count completed public transitions, including non-target units."""
    counts=list(counts)
    if current is None:return [],counts
    if history and (history[-1][0]+1,history[-1][1]+1,*history[-1][2:4])!=current[:4]:history=[]
    sequence=[*history,current]
    if len(sequence)>=3:
        first,middle,last=sequence[-3:]
        for uid in sorted(set(first[4]) & set(middle[4]) & set(last[4])):
            p0,_=first[4][uid];p1,e1=middle[4][uid];p2,e2=last[4][uid]
            heading=(p1[0]-p0[0],p1[1]-p0[1]);delta=(p2[0]-p1[0],p2[1]-p1[1])
            if (abs(heading[0])+abs(heading[1])!=1 or abs(delta[0])+abs(delta[1])>1
                    or not (math.isfinite(e1) and math.isfinite(e2) and e1>=0 and e1>=move_cost and e2>=0)):continue
            dx,dy=heading
            relative=((dx,dy),(-dy,dx),(-dx,-dy),(dy,-dx),(0,0))
            counts[relative.index(delta)]+=1
    return sequence[-2:],counts


def motion_estimate(ctx,sensor,enemy,old,target,delta,drop,counts):
    """Public five-class geometry and Dirichlet moments; no agent helpers."""
    dx,dy=delta;positions=[];blocked=[];unknown=[]
    def hit(center,position):
        distance=max(abs(center[0]-position[0]),abs(center[1]-position[1]))
        return 1.0 if distance==0 else float(drop) if distance==1 else 0.0
    for i,(mx,my) in enumerate(((dx,dy),(-dy,dx),(-dx,-dy),(dy,-dx),(0,0))):
        p=(old[0]+mx,old[1]+my)
        if not (0<=p[0]<ctx["W"] and 0<=p[1]<ctx["H"]) or (sensor[p] and not ctx["passable"][p]):
            blocked.append(i);p=old
        elif not sensor[p]:unknown.append(i)
        positions.append(list(p))
    gains=[hit(target,p)-hit(old,p) for p in positions]
    other=sum(hit(target,p)-hit(old,p) for uid,p,energy in
              zip(ctx["enemy_vis_ids"],ctx["enemy_coords"],ctx["enemy_energies"])
              if int(uid)!=enemy and math.isfinite(float(energy)) and energy>=0)
    n=sum(counts);mass=n+5;prob=[(c+1)/mass for c in counts]
    focus=sum(p*g for p,g in zip(prob,gains));mean=other+focus
    variance=max(0.0,(sum(p*g*g for p,g in zip(prob,gains))-focus*focus)/(mass+1))
    return dict(sample_count=n,counts=list(counts),probabilities=prob,focus_gains=gains,
        other_gain=other,mean=mean,variance=variance,lower_bound=mean-2*math.sqrt(variance),
        next_positions=positions,blocked_classes=blocked,unknown_classes=unknown)


def expected_action(before,ctx,sensor,previous,current,drop,enabled,mirrored,counts):
    """Independent public rule reconstruction, never the prototype's _candidate."""
    import numpy as np
    out=before.copy();eligible=[]
    if not enabled or ctx is None or previous is None or sum(counts)<32 or not (0<=drop<1):return out,eligible
    step,ms,mi=current[:3]
    if (previous[0]+1,previous[1]+1,*previous[2:4])!=current[:4]:return out,eligible
    prior=previous[4]
    for uid in sorted(map(int,ctx["ally_ids"])):
        if before[uid,0]!=5 or not (math.isfinite(float(ctx["ally_ene"][uid])) and ctx["ally_ene"][uid]>=ctx["sap_cost"]):continue
        x,y=map(int,ctx["ally_pos"][uid]);dx,dy=map(int,before[uid,1:])
        if mirrored:dx,dy=-dy,-dx
        old=(x+dx,y+dy)
        def legal(p):return 0<=p[0]<ctx["W"] and 0<=p[1]<ctx["H"] and max(abs(p[0]-x),abs(p[1]-y))<=ctx["sap_range"]
        if not legal(old):continue
        found=[j for j,p in enumerate(ctx["enemy_coords"]) if tuple(map(int,p))==old]
        if len(found)!=1:continue
        index=found[0];enemy=int(ctx["enemy_vis_ids"][index]);energy=float(ctx["enemy_energies"][index])
        if enemy not in prior:continue
        oldpos,oldenergy=prior[enemy];delta=(old[0]-oldpos[0],old[1]-oldpos[1])
        if abs(delta[0])+abs(delta[1])!=1 or not (math.isfinite(oldenergy) and math.isfinite(energy)
                and oldenergy>=0 and energy>=0 and energy>=ctx["move_cost"]):continue
        target=(old[0]+delta[0],old[1]+delta[1])
        if not legal(target) or not sensor[target] or not ctx["passable"][target]:continue
        estimate=motion_estimate(ctx,sensor,enemy,old,target,delta,drop,counts)
        if estimate["lower_bound"]>0:
            eligible.append(dict(uid=uid,enemy_uid=enemy,target=target,old_center=old,new_center=target,**estimate))
    if eligible:
        item=eligible[0];uid=item["uid"];delta=np.asarray(item["target"])-ctx["ally_pos"][uid]
        out[uid,1:]=(-delta[1],-delta[0]) if mirrored else delta
    return out,eligible


def check_motion(agent,counts,candidates,current,drop,actions):
    """Bind actual diagnostics to independently reconstructed public decisions."""
    import numpy as np
    require(np.array_equal(agent.motion_counts,counts),"Public motion counts differ")
    require(agent.leading_stats.get("motion_labels",0)==sum(counts) and all(
        agent.leading_stats.get("motion_"+name,0)==count for name,count in
        zip(("forward","right","backward","left","stay"),counts)),"Motion label totals differ")
    if not candidates:
        require(agent.leading_last is None,"Unexpected motion decision diagnostic")
        return
    expected={k:v for k,v in candidates[0].items() if k!="target"}
    expected.update(step=current[0],match_step=current[1],match_idx=current[2],dropoff=drop,
                    native_action=actions[expected["uid"]].tolist())
    observed=plain(agent.leading_last)
    require(isinstance(observed,dict) and set(observed)==set(expected),"Motion diagnostic fields differ")
    floats={"probabilities","focus_gains","other_gain","mean","variance","lower_bound","dropoff"}
    for key,value in expected.items():
        if key in floats:
            require(np.allclose(observed[key],value,rtol=1e-12,atol=1e-12),"Motion posterior/uncertainty differs: "+key)
        else:require(observed[key]==plain(value),"Motion decision differs: "+key)


@contextmanager
def hook_audit(agent,guard):
    """Instance-scoped passive wrapper; restores class and instance on all exits."""
    import numpy as np
    from agents.sherlock.main import Agent_x
    from agents.sherlock.geometry import mirror_map
    original=Agent_x._act;original_act=agent.act
    own_act="act" in vars(agent);old_act=vars(agent).get("act")
    audit=dict(frames=0,changes=0,last=None);captured={};history=[];counts=[0]*5
    def core(self,step,obs):
        result=original(self,step,obs)
        if self is agent:
            captured["calls"]=captured.get("calls",0)+1
            captured.update(before=result.copy(),book=book(self))
        return result
    def act(step,obs):
        nonlocal history,counts
        guard();captured.clear();result=original_act(step,obs)
        require(captured.get("calls")==1 and agent.caught_errors==0,"Caught/extra/missing core action")
        ms=int(np.asarray(obs["match_steps"]));sid=int(np.asarray(obs["steps"]))
        cache=agent._cache
        ctx=cache[1] if (ms and cache is not None and cache[0]==sid and cache[1]["step"]==sid
            and cache[1]["match_step"]==ms and agent._prev_ctx is cache[1]) else None
        sensor=np.asarray(obs["sensor_mask"],bool)
        mirrored=bool(agent.belief.mirrored)
        if mirrored:sensor=mirror_map(sensor)
        cfg=agent.cfg
        estimator_active=cfg.nebula_avoid or cfg.dodge_auto or cfg.sap_dropoff_est or cfg.art_splash or cfg.sap_still_splash
        drop=agent.param_est.dropoff(default=1.0,min_conf=.9) if estimator_active else 1.0
        current=None if ctx is None else (sid,ms,int(ctx["match_idx"]),mirrored,
            {int(u):(tuple(map(int,p)),float(e)) for u,p,e in zip(ctx["enemy_vis_ids"],ctx["enemy_coords"],ctx["enemy_energies"])})
        prior_history=list(history);previous=history[-1] if history else None
        history,counts=observe_motion(history,current if agent.lead_enabled else None,counts,
                                      ctx["move_cost"] if ctx is not None else 0)
        expected,candidates=expected_action(captured["before"],ctx,sensor,previous,current,drop,agent.lead_enabled,mirrored,counts)
        check_motion(agent,counts,candidates,current,drop,result)
        afterbook=book(agent)
        check_change(captured["before"],result,captured["book"],afterbook,agent.param_est._prev["act"],
                     expected=expected,calls=captured["calls"])
        if candidates:
            uid=candidates[0]["uid"];target=np.array(candidates[0]["target"])
            hits=int((np.max(np.abs(ctx["enemy_coords"]-target),axis=1)<=1).sum())
            require(agent._sap_hits[uid]==hits and agent.leading_last["uid"]==uid,"New target hit count/UID differs")
        changed=not np.array_equal(result,captured["before"])
        audit["frames"]+=1;audit["changes"]+=int(changed)
        require(agent.leading_stats.get("changes",0)==audit["changes"],"Recorded exposure differs from real commands")
        public=None if ctx is None else {k:ctx[k] for k in ("step","match_step","match_idx","W","H","ally_ids","ally_pos","ally_ene",
            "enemy_vis_ids","enemy_coords","enemy_energies","passable","sap_cost","sap_range","move_cost")}
        audit["last"]=plain(dict(step=sid,core=captured["before"],final=result,changed=changed,eligible=candidates,
            public=public,sensor=sensor,previous=previous,motion_history=prior_history,motion_counts=counts,
            motion_decision=agent.leading_last,dropoff=drop,posterior_log=agent.param_est.log_drop,
            parameter_samples=agent.param_est.n_drop,mirrored=mirrored,book_before=captured["book"],book_after=afterbook))
        return result
    Agent_x._act=core;agent.act=act
    try:yield audit
    finally:
        Agent_x._act=original
        if own_act:agent.act=old_act
        else:delattr(agent,"act")


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
        if self.technical or record["changed"]:
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
        with Path(trace).open("x") as stream,hook_audit(agent,guard) as audit:
            wrapped=RecordedEnv(env,side,audit,stream,technical)
            row=play_game(wrapped,agent,opponent,seed,side,False)
            require(row["steps"]==audit["frames"]==wrapped.frames==303 and wrapped.resets==3
                    and len(wrapped.matches)==3 and agent.caught_errors==0
                    and getattr(opponent,"caught_errors",0)==0,"Incomplete/failed game")
            row.update(caught_errors=0,leading=dict(agent.leading_stats),observed_changes=audit["changes"],
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
                if job=="technical" and not mode:
                    expected,frames=histories[(seed,side)]
                    require(all(row[k]==expected[k] for k in ("seed","side","steps","our_wins","opp_wins","result",
                        "our_points","opp_points","point_counting_version","matches","action_sha256")),"OFF historical game mismatch")
                    current=[json.loads(line) for line in trace.read_text().splitlines()]
                    require(len(current)==303 and all(c["final"]==f["native_actions"] for c,f in zip(current,frames)),"OFF historical native arrays differ")
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
            require(len(events)==row["observed_changes"] and all(e["changed"] is True for e in events)
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
