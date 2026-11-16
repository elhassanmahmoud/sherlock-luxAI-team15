"""The remaining two opponents in the V15 night comparison. One sequential process; fixed 80 games."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re
import sys

from scripts import v15_style_panel as prior

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "experiments/analysis/final_battle_20261103/performance_confirmation"
PLAN = ROOT / "experiments/analysis/umbau_20261115/robustness_ft18_random/PLAN.md"
FT18 = "2993091df0524478146dd21aaf5c10a47429c7f18bcc7ce78c4bc994e317d576"
ORIGINAL = "7c906e16943ff7217afe1eae392834439cc76634"
MANIFEST = "20d6b784a4ad94199642a386ee67793d5a008e413616ea66f87df28de9fa44b7"
FREEZE = "3b3bdbe8de396e5762fd542d2337c26334246424986f2ccb80e83bcda19ae73c"
PLAN_HASH = "7bd64ece9b0fa22f22cd09f5d96f78c530836ecced6ba70c5f2a82ce18947362"
MAPS = {"ft18": range(7170064,7170076), "random": range(7170076,7170084)}
SEATS = ("player_0","player_1")
KEYS = [(opp,seed,side) for opp,maps in MAPS.items() for seed in maps for side in SEATS]
SCORES = ("seed","side","result","game_win","our_wins","opp_wins","our_points","opp_points","steps","point_counting_version")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def contract(ft18_path,v15_path):
    p=HISTORY/"admission/candidate_manifest.json"
    require(prior.digest(p)==MANIFEST and prior.digest(HISTORY/"freeze.json")==FREEZE and
            prior.digest(PLAN)==PLAN_HASH, "Different pre-registered evidence")
    historical=read(HISTORY/"freeze.json")
    roster=read(p)
    ft=roster["candidates"]["FT18"]
    require(prior.digest(ft18_path)==ft["sha256"]==FT18 and roster["source_sha256"]==prior.V14 and
            historical["expected_head"]==historical["identity"]["source"]["head"]==ORIGINAL and
            ft["source_indices"]==list(range(18,36)) and ft["ordered_tensor_sha256"]==roster["source_component_sha256"][18:]
            and len(set(roster["source_component_sha256"]))==36 and ft["net_count"]==ft["unique_tensor_count"]==18
            and ft["weighting"]=="equal 1/18" and not ft["new_training"] and not ft["replaced_indices"],
            "FT18 archive or historical member list differs")
    source={k.split("/agents/sherlock/")[1]:v for k,v in historical["identity"]["source"]["files"].items()
            if "/agents/sherlock/" in k and k.endswith(".py")}
    actual={p.name:prior.digest(p) for p in (ROOT/"ft18_historical").glob("*.py")}
    require(actual==source and len(source)==16,"Historical Agent_x package differs")
    previous=prior.contract(v15_path)
    return dict(plan_sha256=PLAN_HASH, runner_sha256=prior.digest(Path(__file__)), style_source=prior.SOURCES,
                style_runner_sha256=prior.digest(Path(prior.__file__)), native_course_sources=previous["sources"],
                engine=previous["engine"],versions=previous["versions"], python=sys.version,
                v14=prior.V14,v15=prior.V15,ft18=FT18,historical_commit=ORIGINAL,ft18_sources=source,
                historical_manifest=MANIFEST,historical_freeze=FREEZE,ft18_members=ft["ordered_tensor_sha256"],
                digest_helper=prior.digest(ROOT/"scripts/final_battle_candidates.py"),keys=KEYS)


class RandomStream:
    """Passively verify this exact instance's real world commands against the seeded native generator."""
    def __init__(self,rival):
        import numpy as np
        self.expected=np.random.default_rng(0)
        self.stream=hashlib.sha256()
        self.calls=0
        actual=rival.act
        def record(step,obs):
            actions=actual(step,obs)
            expected=self.expected.integers(0,5,size=16)
            require(step==self.calls and actions.shape==(16,3) and actions.dtype.kind in "iu" and
                    np.array_equal(actions[:,0],expected) and not actions[:,1:].any(),"Unexpected random opponent stream")
            self.stream.update(actions.astype("<i2").tobytes())
            self.calls+=1
            return actions
        rival.act=record


def build_rival(name,side,ft18_path,ft_state,members):
    from scripts.common import RandomAgent,make_opponent
    if name=="random":
        rival=make_opponent("random",side)
        require(type(rival) is RandomAgent and rival.player==side,"Incorrect random opponent")
        return rival,RandomStream(rival)
    from ft18_historical.main import Agent_x
    from ft18_historical.config import AgentConfig
    from scripts.final_battle_candidates import tensor_sha256
    from ft18_historical import main as original_module
    require(Path(original_module.__file__).resolve()==ROOT/"ft18_historical/main.py","Incorrect FT18 import")
    cfg=AgentConfig.from_dict(ft_state["cfg"])
    rival=Agent_x(side,agent_path=str(ft18_path),cfg=cfg,train=False,seed=0)
    rival.set_to_eval_mode()
    rival.autosave_on_terminate=False
    live=[rival.q,*rival.extra_q]
    require(type(rival) is Agent_x and rival.player==side and not rival.training and not rival.q.training
            and rival.cnn_policy is None and rival.cfg.to_dict()==cfg.to_dict()
            and [tensor_sha256(net.state_dict()) for net in live]==members,"Incorrect loaded historical FT18")
    return rival,None


def validate_row(row,key):
    opp,seed,side=key
    w,l=row["our_wins"],row["opp_wins"]
    require((row["opponent"],row["seed"],row["side"])==key and row["steps"]==303 and
            row["point_counting_version"]==2 and all(type(row[k]) is int for k in
            ("seed","steps","our_wins","opp_wins","our_points","opp_points")) and 0<=w<=3 and w+l==3
            and row["result"]==row["game_win"]==int(w>l) and min(row["our_points"],row["opp_points"])>=0,
            "Invalid native final score")
    require(row["opponent_source"]==("historical_ft18_18_35" if opp=="ft18" else "scripts.common.RandomAgent") and
            (row["random_stream_sha256"] is None if opp=="ft18" else
             bool(re.fullmatch("[0-9a-f]{64}",row["random_stream_sha256"]))),"Invalid opponent evidence")


def existing_rows(d,arm,pin):
    require(read(d/"manifest.json")==json.loads(json.dumps(dict(pin,arm=arm))),"Different existing run manifest")
    file=d/"games.jsonl"
    if not file.is_file():
        return []
    raw=file.read_bytes()
    require(not raw or raw.endswith(b"\n"),"Incomplete saved row; inspect the original journal")
    rows=[json.loads(line) for line in raw.splitlines()]
    require(len(rows)<=len(KEYS),"Too many recorded games")
    for key,row in zip(KEYS,rows):
        validate_row(row,key)
    return rows


def play(mode,out,ft18,v15):
    from scripts.experiment import limit_threads
    limit_threads()
    import torch
    from agents.sherlock.main import Agent_x
    from scripts.check_candidate_runner import verify_loaded
    from scripts.common import play_game
    from scripts.par_eval import require_no_agent_errors
    from luxai_s3.wrappers import LuxAIS3GymEnv
    pin=contract(ft18,v15)
    d=out/mode
    if not d.exists():
        d.mkdir()
        prior.publish(d/"manifest.json",dict(pin,arm=mode))
    recorded=existing_rows(d,mode,pin)
    if (d/"complete.json").exists():
        require(len(recorded)==len(KEYS) and read(d/"complete.json")=={n:prior.digest(d/n) for n in
                ("manifest.json","games.jsonl")},"Retained completed arm differs")
        return
    torch.manual_seed(0)
    weight=v15 if mode=="v15" else ROOT/"agents/sherlock/weights/agent_p0.pth"
    state=torch.load(weight,map_location="cpu",weights_only=False)
    candidate=Agent_x("player_0",agent_path=str(weight),train=False,seed=0)
    verify_loaded(candidate,state)
    candidate.set_to_eval_mode()
    candidate.autosave_on_terminate=False
    if mode=="v15":
        hybrid=candidate._imitation
        require(hybrid.mode=="mixed" and hybrid.combat_radius==5 and hybrid.student.cfg.imit_stay_bias==1.5
                and hybrid.student.cfg.imit_unstack is True,"Incorrect V15 switches")
    ft_state=torch.load(ft18,map_location="cpu",weights_only=True)
    receipt=read(HISTORY/"admission/candidate_manifest.json")["candidates"]["FT18"]
    require(ft_state["cfg"]==receipt["configuration"],"Historical FT18 config changed")
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        with (d/"games.jsonl").open("a") as stream:
            for key in KEYS[len(recorded):]:
                opp,seed,side=key
                rival,observer=build_rival(opp,SEATS[1-SEATS.index(side)],ft18,ft_state,pin["ft18_members"])
                game=play_game(env,candidate,rival,seed,side,train=False)
                require_no_agent_errors(candidate,rival)
                require(observer is None or observer.calls==303,"Incomplete random opponent stream")
                row={k:game[k] for k in SCORES}
                row.update(opponent=opp,opponent_source="scripts.common.RandomAgent" if observer else "historical_ft18_18_35",
                           random_stream_sha256=observer.stream.hexdigest() if observer else None)
                validate_row(row,key)
                stream.write(json.dumps(row,allow_nan=False)+"\n")
                stream.flush()
                if side=="player_1":
                    print(mode,opp,seed,"both seats complete",flush=True)
    finally:
        env.close()
    require(pin==contract(ft18,v15),"Source changed during collection")
    prior.publish(d/"complete.json",{n:prior.digest(d/n) for n in ("manifest.json","games.jsonl")})


def compare_scores(v14,v15,opp):
    import numpy as np
    from scripts.variant_compare import boot
    keys=[k for k in KEYS if k[0]==opp]
    def groups(rows,k):
        return np.array([rows[key][k] for key in keys],dtype=int).reshape(-1,2)
    result={}
    for label,field,per in (("games","game_win",1),("matches","our_wins",3)):
        a,b=groups(v14,field),groups(v15,field)
        diff=(b-a).mean(axis=1)/per
        result[label]=dict(v14=int(a.sum()),v15=int(b.sum()),total=len(keys)*per,
                           delta=float(diff.mean()),ci95=boot(diff,np.random.default_rng(2711)))
    result["gained"]=[k[1:] for k in keys if v15[k]["game_win"]>v14[k]["game_win"]]
    result["lost"]=[k[1:] for k in keys if v15[k]["game_win"]<v14[k]["game_win"]]
    if opp=="random":
        require(len({rows[k]["random_stream_sha256"] for rows in (v14,v15) for k in keys})==1,
                "Random opponent differed across games")
    return result


def assess(out,ft18,v15):
    pin=contract(ft18,v15)
    groups,files={},{}
    for arm in ("v14","v15"):
        d=out/arm
        files[arm]={n:prior.digest(d/n) for n in ("manifest.json","games.jsonl")}
        require(files[arm]==read(d/"complete.json") and read(d/"manifest.json")==json.loads(json.dumps(dict(pin,arm=arm))),
                "Changed arm or seals")
        lines=(d/"games.jsonl").read_bytes().splitlines()
        groups[arm]={}
        for k,line in zip(KEYS,lines,strict=True):
            r=json.loads(line)
            validate_row(r,k)
            groups[arm][k]=r
    result=dict(games=80,files=files,opponents={o:compare_scores(groups["v14"],groups["v15"],o) for o in MAPS})
    target=out/"assessment.json"
    if target.exists():
        require(read(target)==json.loads(json.dumps(result)),"Different stored assessment")
    else:
        prior.publish(target,result)


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode",choices=("check","run","assess"))
    cli.add_argument("--out",type=Path)
    cli.add_argument("--ft18",type=Path,default=ROOT/"inputs/FT18.pth")
    cli.add_argument("--v15",type=Path,default=ROOT/"inputs/V15.pth")
    args=cli.parse_args()
    if args.mode=="check":
        contract(args.ft18,args.v15)
        print("Course bindings, both checkpoints, historical subset and 16 FT18 source files verified.")
    elif args.out is None:
        cli.error("--out is required for game collection/assessment")
    else:
        if args.mode=="run":
            args.out.mkdir(parents=True,exist_ok=True)
        with (args.out/".run.lock").open("a" if args.mode=="run" else "rb") as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if args.mode=="run":
                for arm in ("v14","v15"):
                    play(arm,args.out,args.ft18,args.v15)
            assess(args.out,args.ft18,args.v15)
