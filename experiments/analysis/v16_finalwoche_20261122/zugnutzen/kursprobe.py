"""Record the experimental reference commands and compare a standalone course package."""
import argparse
from collections import defaultdict
import gzip
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np
import torch

HERE=Path(__file__).resolve().parent


def record(folder, study):
    from spielen import PACKAGE, Policy, ValueNet, check_qualification
    from scripts.r3_package import r3_package_agent
    from scripts.common import make_opponent, play_game
    from scripts.experiment import limit_threads
    from scripts.par_eval import require_no_agent_errors
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    folder.mkdir(parents=True,exist_ok=True)
    if study == "late":
        source = HERE
        net = ValueNet().eval()
        with np.load(check_qualification(True), allow_pickle=False) as z:
            net.load_state_dict({k:torch.from_numpy(z[k]) for k in z.files})
        def candidate(base):
            return Policy(base, net)
    else:
        source = HERE.parent/"sichtlernen"
        sys.path.insert(0, str(source))
        from sicht import Scout, NAMES
        stored = json.loads((source/"offline.json").read_bytes())
        if not stored["eligible"] or stored["estimate"]["names"] != list(NAMES):
            raise ValueError("Incorrect visibility estimator")
        params = np.asarray(stored["estimate"]["w"], dtype=float), stored["estimate"]["bias"]
        def candidate(base):
            return Scout(base, params)
    archive=gzip.decompress((source/"auswahl_partien.jsonl.gz").read_bytes()).splitlines()
    chosen={}
    for row in sorted(map(json.loads,archive),key=lambda r:r["seed"]):
        if row["arm"]=="adviser" and row["changes"]>0 and row["opponent"]!="v16":
            chosen.setdefault((row["opponent"],row["side"]),row)
    if len(chosen)!=4: raise ValueError("Need an actually intervened game from both seats and opponents")

    class Recorder:
        def __init__(self,policy):
            self.policy=policy
            self.tape=defaultdict(list)

        def __getattr__(self,key):
            return getattr(self.policy,key)

        def set_env_cfg(self,cfg):
            self.cfg={k:np.asarray(v).tolist() for k,v in cfg.items()}
            self.policy.set_env_cfg(cfg)

        def act(self,step,obs):
            if len(self.tape["commands"])!=step:raise ValueError("Invalid chronology")
            command=self.policy.act(step,obs)
            self.tape["commands"].append(command.copy())
            for key,val in obs.items():
                if isinstance(val,dict):
                    for sub,arr in val.items():self.tape[key+"/"+sub].append(np.array(arr,copy=True))
                else:self.tape[key].append(np.array(val,copy=True))
            return command

    env=LuxAIS3GymEnv(numpy_output=True)
    try:
        for (opponent,side),r in chosen.items():
            s=r["seed"]
            receiver=Recorder(candidate(r3_package_agent(side,PACKAGE)))
            rival=make_opponent(opponent,"player_"+str(1-int(side[-1])))
            g=play_game(env,receiver,rival,s,side,train=False)
            require_no_agent_errors(receiver.policy.base,rival)
            if (g["steps"]!=303 or any(g[k]!=r[k] for k in ("our_wins","opp_wins","our_points","opp_points"))
                    or receiver.policy.changed!=r["changes"]):
                raise ValueError("Reference does not reproduce the selected game")
            meta=dict(cfg=receiver.cfg,seed=s,side=side,opponent=opponent,changes=r["changes"])
            np.savez_compressed(folder/f"{s}_{side}_{opponent}.npz",metadata=np.array(json.dumps(meta)),**{
                key:np.stack(values) for key,values in receiver.tape.items()})
            print(s,side,opponent,r["changes"],flush=True)
    finally:
        env.close()


def compare(folder,package,out):
    torch.set_num_threads(1)
    samples=sorted(folder.glob("*.npz"))
    if len(samples)!=4:raise ValueError("Incomplete reference tapes")
    results=[]
    with TemporaryDirectory() as temp:
        path=Path(temp)
        agent_dir=path/"agents"
        agent_dir.mkdir()
        (agent_dir/"__init__.py").touch()
        with ZipFile(package) as z:z.extractall(agent_dir)
        sys.path.insert(0,str(path))
        entry=importlib.import_module("agents.sherlock.main")
        if Path(entry.__file__).resolve()!=(agent_dir/"sherlock/main.py").resolve():
            raise ValueError("Wrong course module")
        for p in samples:
            with np.load(p,allow_pickle=False) as packed:
                meta=json.loads(str(packed["metadata"]))
                arrays={k:packed[k] for k in packed.files if k!="metadata"}
            side=meta["side"]
            actor=entry.Agent_x(side,agent_path=str(agent_dir/"sherlock/weights/agent.pth"))
            actor.set_to_eval_mode()
            actor.new_game(side)
            actor.set_env_cfg(meta["cfg"])
            for step,expected in enumerate(arrays["commands"]):
                obs={}
                for k,v in arrays.items():
                    if k=="commands":continue
                    if "/" in k:
                        head,leaf=k.split("/",1);obs.setdefault(head,{})[leaf]=v[step]
                    else:obs[k]=v[step]
                actual=actor.act(step,obs)
                if not np.array_equal(expected,actual):
                    raise ValueError(f"Action differs on {p.name}, turn {step}")
            if len(arrays["commands"])!=303 or actor.changed!=meta["changes"] or actor.changed<=0:
                raise ValueError("Incorrect intervention count or length")
            results.append(dict(seed=meta["seed"],side=side,opponent=meta["opponent"],changes=actor.changed,
                                steps=303,commands=303*16,tape_sha256=sha256(p.read_bytes()).hexdigest()))
    report=dict(python=sys.version.split()[0],torch=str(torch.__version__),numpy=np.__version__, release_sha256=sha256(package.read_bytes()).hexdigest(),
                games=results, action_matrices=1212, unit_commands=19392, differences=0)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(report["python"],report["unit_commands"],"identical",flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    subs=p.add_subparsers(dest="mode",required=True)
    a=subs.add_parser("record");a.add_argument("folder",type=Path);a.add_argument("--study",choices=("late","visibility"),default="late")
    a=subs.add_parser("compare");a.add_argument("folder",type=Path);a.add_argument("package",type=Path);a.add_argument("out",type=Path)
    a=p.parse_args()
    if a.mode=="record":record(a.folder, a.study)
    else:compare(a.folder,a.package,a.out)
