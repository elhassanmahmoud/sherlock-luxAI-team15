"""Three fixed styles, 24 preregistered cards, both seats, frozen V14 vs. packed V15."""
import argparse
import csv
from hashlib import sha256
from importlib import metadata, util
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

ROOT = Path(__file__).resolve().parents[1]
MAPS = range(7170040, 7170064)
SEATS = ("player_0", "player_1")
OPPONENTS = ("sol92_sq", "rush", "dqn")
V14 = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
V15 = "20f8af0dee4711b566cc83309111fceb32ee176aa86c7fd9398bf52c330a017e"
DQN = "2678d4e5409645ec16236545c5b84dbb32108a02d3140ea40aad1444089a4981"
SOURCES = "453d627d4957ae9e30b0c2cdf650c0101417e8ee8a450f9b7f6f8418308656a7"
ENGINE = {"env.py":"cc1b2657e1b56df21ec890bc78eab75539575e16529b8b8e5a1e8d1b4865a469",
          "params.py":"74511d1415879ca65ffa9b4e6b3918e8f85d711ae47b458425bebe39694df666",
          "wrappers.py":"79ce95b43c8e78a1dada485266d71d210dc9065e89e4880f1af95504b76bcf26"}
SCHEDULE = [(opp, seed, side) for seed in MAPS for opp in OPPONENTS for side in SEATS]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def sources():
    files = list((ROOT / "agents").rglob("*.py")) + list((ROOT / "lux").glob("*.py"))
    files += [ROOT/"scripts"/(file+".py") for file in
              ("common","experiment","par_eval","protocol","scoring","variants","metrics","style_opponents",
               "check_candidate_runner","xversion_replay","variant_compare")]
    files += [ROOT / "Paths.csv", ROOT / "agents/DQN/agent.yaml"]
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(files)}


def contract(v15):
    source = sources()
    source_hash = sha256(json.dumps(source,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    nets = {"v14":digest(ROOT / "agents/sherlock/weights/agent_p0.pth"), "v15":digest(v15),
            "dqn":digest(ROOT / "agents/DQN/agent.pth")}
    engine_dir = Path(util.find_spec("luxai_s3").origin).parent
    if (source_hash != SOURCES or nets != {"v14":V14,"v15":V15,"dqn":DQN}
            or {n:digest(engine_dir / n) for n in ENGINE} != ENGINE):
        raise ValueError("Different frozen course sources, engine or weights")
    with (ROOT / "Paths.csv").open(encoding="cp1252",newline="") as f:
        entries = [r for r in csv.DictReader(f,delimiter=";") if r["Moodle Gruppe"]=="3"]
    if (len(entries)!=1 or entries[0]["Import_Path"]!="agents.DQN.main.Agent"
            or any(entries[0]["Load_Path_P"+str(i)]!="agents/DQN/agent.pth" for i in (0,1))):
        raise ValueError("The original group 3 DQN is not the registered opponent")
    return dict(inputs=nets,sources=source,engine=ENGINE,first=MAPS.start,last=MAPS.stop-1,
                opponents=OPPONENTS,study_sha256=digest(Path(__file__)),
                versions={k:metadata.version(k) for k in ("torch","numpy","jax","jaxlib","luxai-s3")})


def publish(path, data):
    with NamedTemporaryFile(dir=path.parent, mode="w", delete=False) as f:
        temp=Path(f.name)
        try:
            json.dump(data,f,allow_nan=False,indent=2)
            f.write("\n")
            f.flush()
            os.link(temp,path)
        finally:
            temp.unlink(missing_ok=True)


def opponent(name, side, dqn_path, native_state):
    import torch
    from scripts.common import make_opponent
    if name != "dqn":
        from scripts.style_opponents import RushBot, Sol92Variant
        obj = make_opponent(name,side)
        if (name=="rush" and type(obj) is not RushBot or
                name=="sol92_sq" and (type(obj) is not Sol92Variant or not obj.square or obj.weakest)):
            raise ValueError(f"Unexpected registered style: {name}")
        return obj
    from agents.DQN.main import Agent
    # The course loader sets eval mode; the general par_eval helper otherwise leaves this class at epsilon=0.1.
    obj=Agent(side,agent_path=str(dqn_path))
    obj.set_to_eval_mode()
    actual=obj.q.state_dict()
    if (obj.epsilon!=0 or obj.q.training or obj.state_dim!=17 or obj.n_actions!=5 or
            actual.keys()!=native_state.keys() or any(a.dtype!=native_state[k].dtype or
            a.shape!=native_state[k].shape or not torch.equal(a.cpu().contiguous().view(torch.uint8),
            native_state[k].cpu().contiguous().view(torch.uint8)) for k,a in actual.items())):
        raise RuntimeError("Professor DQN failed live bitwise identity or evaluation mode")
    return obj


def play(a):
    from scripts.experiment import limit_threads
    limit_threads()
    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.common import play_game
    from scripts.par_eval import require_no_agent_errors
    from scripts.check_candidate_runner import verify_loaded
    from agents.sherlock.main import Agent_x
    os.chdir(ROOT)
    v15=a.v15.resolve()
    pin=contract(v15)
    dest=a.out/a.arm
    dest.mkdir(parents=True,exist_ok=False)
    publish(dest/"manifest.json",dict(pin,arm=a.arm))
    weight=v15 if a.arm=="v15" else ROOT/"agents/sherlock/weights/agent_p0.pth"
    dqn_path=ROOT/"agents/DQN/agent.pth"
    state=torch.load(dqn_path,map_location="cpu",weights_only=True)
    torch.manual_seed(0)
    agent=Agent_x("player_0",agent_path=str(weight),train=False,seed=0)
    verify_loaded(agent,torch.load(weight,map_location="cpu",weights_only=False))
    agent.set_to_eval_mode()
    agent.autosave_on_terminate=False
    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        with (dest/"games.jsonl").open("x") as stream:
            for opp,seed,side in SCHEDULE:
                other="player_1" if side=="player_0" else "player_0"
                rival=opponent(opp,other,dqn_path,state)
                record=play_game(env,agent,rival,seed,side,train=False)
                require_no_agent_errors(agent,rival)
                row={k:record[k] for k in ("seed","side","result","game_win","our_wins","opp_wins",
                                            "our_points","opp_points","steps","point_counting_version")}
                row["opponent"]=opp
                row["dqn_weights_checked"]=opp=="dqn"
                check_row(row,(opp,seed,side))
                stream.write(json.dumps(row,allow_nan=False)+"\n")
                stream.flush()
                if opp==OPPONENTS[-1] and side==SEATS[-1]:
                    print(a.arm,seed,"complete",flush=True)
    finally:
        env.close()
    if contract(v15)!=pin:
        raise ValueError("Source, weights or execution environment changed")
    publish(dest/"complete.json",{n:digest(dest/n) for n in ("manifest.json","games.jsonl")})


def check_row(row, key):
    if ((row["opponent"],row["seed"],row["side"])!=key or row["steps"]!=303 or row["point_counting_version"]!=2
            or any(type(row[k]) is not int for k in ("seed","steps","our_wins","opp_wins","our_points","opp_points"))
            or row["our_wins"] not in range(4) or row["our_wins"]+row["opp_wins"]!=3
            or row["result"]!=row["game_win"] or row["game_win"]!=int(row["our_wins"]>row["opp_wins"])
            or min(row["our_points"],row["opp_points"])<0 or row["dqn_weights_checked"] is not (key[0]=="dqn")):
        raise ValueError(f"Inconsistent game: {key}")


def compare(a):
    import numpy as np
    from scripts.variant_compare import boot
    pin=contract(a.v15)
    by_arm,hashes={},{}
    for arm in ("v14","v15"):
        d=a.out/arm
        hashes[arm]=json.loads((d/"complete.json").read_bytes())
        if (hashes[arm]!={n:digest(d/n) for n in ("manifest.json","games.jsonl")}
                or json.loads((d/"manifest.json").read_bytes())!=json.loads(json.dumps(dict(pin,arm=arm)))):
            raise ValueError(f"Unexpected {arm} artifacts")
        data=[json.loads(line) for line in (d/"games.jsonl").read_text().splitlines()]
        by_arm[arm]={}
        for key,row in zip(SCHEDULE,data,strict=True):
            check_row(row,key)
            by_arm[arm][key]=row
    result={}
    for opp in OPPONENTS:
        stats={}
        rates={}
        seat_wins={}
        for arm in ("v14","v15"):
            maps=[[by_arm[arm][opp,s,side] for side in SEATS] for s in MAPS]
            seat_wins[arm]=np.array([[r["game_win"] for r in pair] for pair in maps],dtype=int)
            matches=np.array([sum(r["our_wins"] for r in pair) for pair in maps],dtype=int)
            rates[arm]=[seat_wins[arm].mean(axis=1),matches/6.]
            stats[arm]=dict(game_wins=int(seat_wins[arm].sum()),games=48,match_wins=int(matches.sum()),matches=144)
        delta=seat_wins["v15"]-seat_wins["v14"]
        for i,label in enumerate(("game","match")):
            diffs=rates["v15"][i]-rates["v14"][i]
            stats[label+"_delta"]=float(diffs.mean())
            stats[label+"_map_ci95"]=boot(diffs,np.random.default_rng(2711))
        result[opp]=dict(stats,gained_seats=int((delta>0).sum()),lost_seats=int((delta<0).sum()),
                         maps_with_changed_seat=int((delta!=0).any(axis=1).sum()))
    publish(a.out/"assessment.json",dict(opponents=result,files=hashes,maps=24,full_games=288,
           intervals="Paired map bootstrap, both seats, 4000 draws, unadjusted 95% per opponent. "
                     "A degenerate interval can be caused by identical observed outcomes on all 24 maps."))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("arm",choices=("v14","v15","compare"))
    p.add_argument("--v15",type=lambda p:Path(p).resolve(),required=True)
    p.add_argument("--out",type=lambda p:Path(p).resolve(),required=True)
    args=p.parse_args()
    if args.arm=="compare":
        compare(args)
    else:
        play(args)
