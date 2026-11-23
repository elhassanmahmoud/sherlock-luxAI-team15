"""Condition a real complete continuation on the true first-two-match sequence."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.entscheidungsspiel.spieler import Decider
from experiments.analysis.relictsuche_20261123.folgewahl.sammeln import OLD
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,Monitor,PACKAGE,common_source,sha,stamp,write_once
from scripts.r3_package import r3_package_agent
from scripts.par_eval import require_no_agent_errors
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads

HERE=Path(__file__).resolve().parent


class Watch(Monitor):
    def __init__(self,env,t):
        super().__init__(env,t,"discovery");self.actions=[];self.prefix=None

    def step(self,cmd):
        self.actions.append(cmd[self.side].copy())
        result=super().step(cmd)
        if self.turn==202:self.prefix=self.digest.hexdigest()
        return result


def play(env,s,t,opp,arm):
    side=f"player_{t}";other=f"player_{1-t}"
    actor=Decider(side) if arm=="neu" else r3_package_agent(side,PACKAGE)
    rival=make_opponent(opp,other) if opp=="solution92" else r3_package_agent(other,PACKAGE)
    rec=Watch(env,t)
    raw=play_game(rec,actor,rival,s,side,False)
    require_no_agent_errors(getattr(actor,"base",actor),rival)
    chosen=arm=="neu" and actor.chosen
    assert arm!="neu" or chosen==(rec.matches[0]["win"]==1 and rec.matches[1]["win"]==0)
    if chosen:require_no_agent_errors(actor.r3,rival)
    assert rec.turn==303 and raw["game_win"]==int(sum(m["win"] for m in rec.matches)>=2)
    return dict(chosen=chosen,matches=rec.matches,win=raw["game_win"],hash=rec.digest.hexdigest(),prefix=rec.prefix,
                sight=rec.first_sight,credit=rec.first_credit),np.stack(rec.actions)


def known(env,token):
    examples=json.loads((HERE.parent/"entscheidende_matches/ergebnis.json").read_text())["games"]
    cases=[]
    for e in (r for r in examples if r["kind"]=="v16"):
        s,t=e["seed"],e["team"]
        a,cmd=play(env,s,t,"solution92","v16");b,new=play(env,s,t,"solution92","neu")
        assert b["chosen"] and a["hash"]==e["hash"] and a["matches"]==e["matches"] and a["matches"][:2]==b["matches"][:2]
        assert a["prefix"]==b["prefix"] and np.array_equal(cmd[:202],new[:202])
        cases.append(dict(seed=s,team=t,base=a,decider=b))
    assert len(cases)==2
    write_once(HERE/"technik.json",dict(source=token,passed=any(r["decider"]["win"] for r in cases),cases=cases))


def recorded(env,file,token):
    m=json.loads(file.read_text());s,t,o=m["seed"],m["team"],m["opponent"]
    score=[v if t==0 else v[::-1] for v in m["matches"]]
    eligible=score[0][0]>=score[0][1] and score[1][0]<=score[1][1]
    path=file.parent/m["public"]
    assert sha(path)==m["public_sha"]
    common=dict(seed=s,team=t,opponent=o,source=token,base=m["win"],original_points=score,public=m["public_sha"])
    if not eligible:return dict(**common,win=m["win"],chosen=False,replayed=False)
    b,actual=play(env,s,t,o,"neu")
    with np.load(path) as saved:
        assert np.array_equal(actual[:202],saved["commands"][:202])
        if not b["chosen"]:assert np.array_equal(actual,saved["commands"])
    assert [v["points"] for v in b["matches"][:2]]==score[:2]
    if not b["chosen"]:assert b["win"]==m["win"] and [v["points"] for v in b["matches"]]==score
    return dict(**common,win=b["win"],chosen=b["chosen"],replayed=True,actual=b)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("archive",type=Path);p.add_argument("folder",type=Path)
    p.add_argument("stage",choices=("tech","train","valid"));p.add_argument("op",choices=("play","score"),nargs="?",default="play")
    p.add_argument("lane",type=int,nargs="?",default=0);p.add_argument("stride",type=int,nargs="?",default=1)
    a=p.parse_args();limit_threads()
    src=[HERE/"PLAN.md",HERE/"spieler.py",Path(__file__)]+[HERE.parent/f for f in ("folgewahl/politik.py","r3_folge/berater.py")]
    token=stamp(dict(common=common_source(),r3=sha(OLD),files={str(p.relative_to(HERE.parent)):sha(p) for p in src}))
    if a.stage=="tech":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:known(env,token)
        finally:env.close()
        return
    gate=json.loads((HERE/("technik.json" if a.stage=="train" else "train.json")).read_text())
    assert gate["passed"] and gate["source"]==token
    files=sorted((a.archive/a.stage).glob("*.json"));assert len(files)==(160 if a.stage=="train" else 48)
    def dest(f):return a.folder/a.stage/f.name
    if a.op=="play":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for f in files[a.lane::a.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                if dest(f).exists():assert json.loads(dest(f).read_text())["source"]==token
                else:write_once(dest(f),recorded(env,f,token))
        finally:env.close()
        return
    allrows=[json.loads(dest(f).read_text()) for f in files]
    assert all(r["source"]==token for r in allrows)
    groups={}
    for opp in ("solution92","v16"):
        rows=[r for r in allrows if r["opponent"]==opp]
        groups[opp]={k:sum(r[k] for r in rows) for k in ("chosen","win","base","replayed")}
        groups[opp]["cards"]=len(rows)
    deltas=[r["win"]-r["base"] for r in groups.values()]
    passes=min(deltas)>=0 and max(deltas)>0 and (a.stage=="valid" or sum(r["chosen"] for r in allrows)>=8)
    write_once(HERE/f"{a.stage}.json",dict(source=token,groups=groups,cards=len(allrows),passed=passes))
    payload="\n".join(json.dumps(r,separators=(",",":")) for r in allrows)+"\n"
    (HERE/f"{a.stage}_karten.jsonl.gz").write_bytes(gzip.compress(payload.encode(),mtime=0))


if __name__=="__main__":main()
