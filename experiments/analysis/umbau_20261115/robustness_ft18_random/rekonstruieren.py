"""Rebuild the two frozen game-source versions from Git and copy the two historical local checkpoints."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

HERE=Path(__file__).resolve().parent
COURSE="b2bd67e43f213cd99669bf3eee759e3fdeb1c0f5"
OVERLAYS="ed1aee4313e1f370eff317886f8ecd1364e427ae"
OLD="7c906e16943ff7217afe1eae392834439cc76634"
HISTORY=Path("experiments/analysis/final_battle_20261103/performance_confirmation")
STUDY=Path("experiments/analysis/umbau_20261115/robustness_ft18_random")
COLLECTOR="36e24d1ee11468fa969879f70728cfaffb27c59ba2f77658c72a17b4126e662b"
PLAN="7bd64ece9b0fa22f22cd09f5d96f78c530836ecced6ba70c5f2a82ce18947362"


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def build(repo,dest,ft18,v15):
    local=HERE.parents[3]
    tools=Path("scripts/v15_ft18_random.py")
    if sha(local/tools)!=COLLECTOR or sha(HERE/"PLAN.md")!=PLAN:
        raise ValueError("Different registered plan or runner")
    checkpoints={"FT18":(ft18,"2993091df0524478146dd21aaf5c10a47429c7f18bcc7ce78c4bc994e317d576"),
                 "V15":(v15,"20f8af0dee4711b566cc83309111fceb32ee176aa86c7fd9398bf52c330a017e")}
    for name,(path,h) in checkpoints.items():
        if sha(path)!=h:
            raise ValueError(f"Different {name} checkpoint")
    if dest.is_relative_to(repo):
        raise ValueError("Choose a previously absent directory outside the checkout")
    dest.mkdir(exist_ok=False)
    try:
        with tempfile.TemporaryDirectory() as work:
            tar=Path(work)/"course.tar"
            subprocess.run(["git","-C",repo,"archive","-o",tar,COURSE,"--","agents","scripts","lux","Paths.csv"],check=True)
            with tarfile.open(tar) as arc:
                for m in arc.getmembers():
                    if not(m.isfile() or m.isdir()) or Path(m.name).is_absolute() or ".." in Path(m.name).parts:
                        raise ValueError("Unexpected Git archive entry")
                arc.extractall(dest, filter="data")
        def blob(commit,relative,target):
            target.parent.mkdir(parents=True,exist_ok=True)
            b=subprocess.check_output(["git","-C",repo,"show",f"{commit}:{relative}"])
            target.write_bytes(b)
        for p in ("scripts/v15_style_panel.py","scripts/par_eval.py","scripts/xversion_replay.py",
                  HISTORY/"freeze.json",HISTORY/"admission/candidate_manifest.json"):
            blob(OVERLAYS,p,dest/p)
        hist=json.loads((dest/HISTORY/"freeze.json").read_bytes())
        for p,h in hist["identity"]["source"]["files"].items():
            if "/agents/sherlock/" in p and p.endswith(".py"):
                name=p.split("/agents/sherlock/")[1]
                fn=dest/"ft18_historical"/name
                blob(OLD,"agents/sherlock/"+name,fn)
                if sha(fn)!=h:
                    raise ValueError("Historical file differs: "+name)
        (dest/"inputs").mkdir()
        for name,(path,h) in checkpoints.items():
            fn=dest/"inputs"/(name+".pth")
            shutil.copyfile(path,fn)
            if sha(fn)!=h:
                raise ValueError("Checkpoint changed during copy")
        (dest/STUDY).mkdir(parents=True)
        shutil.copyfile(HERE/"PLAN.md",dest/STUDY/"PLAN.md")
        shutil.copyfile(local/tools,dest/tools)
        tests=Path("tests/test_v15_ft18_random.py")
        if (local/tests).is_file():
            (dest/tests.parent).mkdir(exist_ok=True)
            shutil.copyfile(local/tests,dest/tests)
        print(dest)
    except BaseException:
        shutil.rmtree(dest)
        raise


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("repo","out","ft18","v15"):
        p.add_argument("--"+arg,type=Path,required=True)
    a=p.parse_args()
    build(a.repo.resolve(),a.out.resolve(),a.ft18.resolve(),a.v15.resolve())
