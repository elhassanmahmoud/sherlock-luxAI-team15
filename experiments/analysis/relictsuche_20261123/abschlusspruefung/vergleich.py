"""One untouched release comparison. Bind the selected player before opening the cards."""
import argparse
from datetime import datetime
import gzip
import json
from pathlib import Path

import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv

from experiments.analysis.relictsuche_20261123.punktwissen.spiele import decoded
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import MIRROR
from experiments.analysis.relictsuche_20261123.punktwissen.kandidat import PACKAGE
from experiments.analysis.relictsuche_20261123.vergleich.spielen import CUTOFF,Monitor,common_source,sha,stamp,write_once
from scripts.common import play_game,make_opponent
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import point_tile_map

HERE=Path(__file__).resolve().parent
STUDY=HERE.parent
FILES={
    "kontextsuche": ("duelle.json", ("kontextsuche","netzvertrauen","flottenblick","zielschaetzer")),
    "ortundflotte": ("duelle.json", ("ortundflotte","flottenblick","zielschaetzer")),
    "spielwert": ("ganze_spiele.json", ("spielwert","zielschaetzer")),
    "punktgrenzen": ("duell.json", ("punktgrenzen","punktwissen","punktspeicher")),
    "fehlmarkierung": ("duelle.json", ("fehlmarkierung","punktgrenzen","punktspeicher")),
    "folgewahl": ("duell.json", ("folgewahl","r3_folge")),
    "r3_folge": ("pilotpruefung/ergebnis.json", ("r3_folge",)),
    "halteprobe": ("leistung.json", ("halteprobe","feldprobe")),
    "entscheidungsspiel": ("duell.json", ("entscheidungsspiel","folgewahl","r3_folge")),
    "suche_und_wissen": ("duelle.json", ("suche_und_wissen","zielschaetzer","punktgrenzen","punktwissen","punktspeicher")),
}


def make(label,side):
    if label=="v16":return r3_package_agent(side,PACKAGE)
    if label=="solution92":return make_opponent(label,side)
    if label=="punktgrenzen":
        from experiments.analysis.relictsuche_20261123.punktgrenzen.politik import AreaKnowledge
        return AreaKnowledge(r3_package_agent(side,PACKAGE))
    if label=="r3_folge":
        from experiments.analysis.relictsuche_20261123.r3_folge.berater import create
        return create(side)
    if label=="entscheidungsspiel":
        from experiments.analysis.relictsuche_20261123.entscheidungsspiel.spieler import Decider
        return Decider(side)
    if label=="suche_und_wissen":
        from experiments.analysis.relictsuche_20261123.suche_und_wissen.spieler import make_player
        return make_player(side,"beide")
    if label=="folgewahl":
        from experiments.analysis.relictsuche_20261123.folgewahl.politik import Switch
        return Switch(side)
    from importlib import import_module
    name={"spielwert":"politik","fehlmarkierung":"korrektur"}.get(label,"kandidat")
    return import_module(f"experiments.analysis.relictsuche_20261123.{label}.{name}").create(side)


def nomination(label):
    gate,groups=FILES[label]
    check=STUDY/label/gate
    result=json.loads(check.read_text())
    assert result.get("passed",result.get("qualified",False))
    files={HERE/"PLAN.md",Path(__file__),check}
    for group in groups:
        folder=STUDY/group
        files.update(folder.glob("*.py"))
        files.update(folder.glob("*.npz"))
        for f in ("modell.json","ort.json","valid.json","technik.json"):
            if (folder/f).exists(): files.add(folder/f)
    if label in ("folgewahl","r3_folge","entscheidungsspiel"):
        from experiments.analysis.relictsuche_20261123.folgewahl.sammeln import OLD
        files.add(OLD)
        files.add(STUDY.parent/"v16_finalwoche_20261122/fruehuebergabe/staffel.py")
    if label=="halteprobe":
        extra=STUDY/label/"gegenpruefung_leistung.json"
        assert extra.exists() and json.loads(extra.read_text())["archive_sha"]==result["archive_sha"]
        files.add(extra)
    return dict(player=label,sources={str(f.relative_to(STUDY.parents[2])):sha(f) for f in sorted(files)},base=common_source())


class Referee(Monitor):
    def __init__(self,env,team,subject,label):
        super().__init__(env,team,"general")
        self.subject=subject
        self.label=label
        self.commands=[]
        self.evidence=[]

    def step(self,actions):
        self.commands.append(np.stack([actions[f"player_{n}"] for n in (0,1)]).astype(np.int8))
        if self.label in ("punktgrenzen","fehlmarkierung"):
            rows=self.subject.events[len(self.evidence):]
            if rows:
                truth=point_tile_map(self.env.state)
                positive=self.label=="punktgrenzen"
                for item in rows:
                    k=item["world"] if positive else item["pair"]
                    assert item["t"]==self.turn and all(bool(truth[divmod(p,24)])==positive for p in (k,MIRROR[k]))
                    self.evidence.append(item)
        return super().step(actions)


def run(env,key,token):
    import base64,hashlib,zlib
    seed,t,arm,opp=key
    actor=make(arm,f"player_{t}");rival=make(opp,f"player_{1-t}")
    rec=Referee(env,t,actor,arm)
    r=play_game(rec,actor,rival,seed,f"player_{t}",False)
    require_no_agent_errors(getattr(actor,"base",actor),rival)
    assert rec.turn==r["steps"]==303 and r["game_win"]==int(sum(m["win"] for m in rec.matches)>=2)
    if arm in ("punktgrenzen","fehlmarkierung"):assert actor.events==rec.evidence
    cmds=np.stack(rec.commands)
    assert hashlib.sha256(cmds.astype("<i4").tobytes()).hexdigest()==rec.digest.hexdigest()
    return dict(key=list(key),source=token,sensor=rec.sensor,matches=rec.matches,win=r["game_win"],sight=rec.first_sight,
                credit=rec.first_credit,evidence=rec.evidence,digest=rec.digest.hexdigest(),
                tape=base64.b64encode(zlib.compress(cmds.tobytes())).decode())


def score(rows,label):
    vals=[]
    for seed in range(164300000,164300160):
        direct=[rows[seed,t,label,"v16"] for t in (0,1)]
        for t in (0,1):
            ref,new=rows[seed,t,"v16","solution92"],rows[seed,t,label,"solution92"]
            assert ref["sensor"]==new["sensor"]==direct[t]["sensor"]
            diff=np.flatnonzero(np.any(decoded(ref)!=decoded(new),axis=(1,2,3)))
            if not len(diff):assert ref["matches"]==new["matches"] and ref["win"]==new["win"]
            if ref["sensor"]!=1:
                assert not len(diff) and direct[0]["digest"]==direct[1]["digest"] and direct[0]["win"]+direct[1]["win"]==1
            vals.append((ref["win"],new["win"],direct[t]["win"],new["win"]-ref["win"],ref["sight"]-new["sight"],
                         ref["credit"]-new["credit"],int(bool(len(diff))),new["sensor"]))
    x=np.array(vals).reshape(160,2,8)
    draw=np.random.default_rng(231123).integers(0,160,(20000,160))
    mean=x.mean(1)
    ci=np.quantile(mean[draw].mean(1),[.025,.975],axis=0)
    sums=x.sum((0,1))
    a=ci[0,3]>0 and sums[2]>=160 and ci[0,2]>=.45
    b=ci[0,2]>.5 and ci[0,3]>=-.01
    return dict(player=label,games=len(rows),cards=160,original=int(sums[0]),candidate=int(sums[1]),direct=int(sums[2]),
                solution_gain_ci=ci[:,3].tolist(),direct_ci=ci[:,2].tolist(),changed_seats=int(sums[6]),sight1=int((x[:,:,7]==1).sum()),
                sight_gain=float(mean[:,4].mean()),credit_gain=float(mean[:,5].mean()),way_a=bool(a),way_b=bool(b),qualified=bool(a or b))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path);p.add_argument("stage",choices=("nominate","play","score"))
    p.add_argument("label",choices=FILES);p.add_argument("lane",type=int,nargs="?",default=0);p.add_argument("stride",type=int,nargs="?",default=1)
    args=p.parse_args();limit_threads()
    label=args.label
    note=HERE/"nominierung.json"
    if args.stage=="nominate":
        write_once(note,nomination(label));return
    record=json.loads(note.read_text())
    assert record==nomination(label)
    token=stamp(record)
    keys=[(s,t,a,o) for s in range(164300000,164300160) for t in (0,1) for a,o in (("v16","solution92"),(label,"solution92"),(label,"v16"))]
    def dest(k):return args.folder/"alle"/("_".join(map(str,k))+".json")
    if args.stage=="play":
        env=LuxAIS3GymEnv(numpy_output=True)
        try:
            for k in keys[args.lane::args.stride]:
                if datetime.now(CUTOFF.tzinfo)>=CUTOFF:break
                if dest(k).exists():assert json.loads(dest(k).read_text())["source"]==token
                else:write_once(dest(k),run(env,k,token))
        finally:env.close()
        return
    rows={k:json.loads(dest(k).read_text()) for k in keys}
    assert len(rows)==960 and all(r["source"]==token and tuple(r["key"])==k for k,r in rows.items())
    out=score(rows,label)
    write_once(HERE/"ergebnis.json",dict(source=token,**out))
    payload="\n".join(json.dumps(r,separators=(",",":")) for r in rows.values())+"\n"
    (HERE/"partien.jsonl.gz").write_bytes(gzip.compress(payload.encode(),mtime=0))


if __name__=="__main__":main()
