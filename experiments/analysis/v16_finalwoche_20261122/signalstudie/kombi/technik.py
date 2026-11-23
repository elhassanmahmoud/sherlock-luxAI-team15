"""Prüft alle bekannten ganzen Siegwechsel, deren Originale und die gesperrten Einzelmodule."""
import argparse
from hashlib import sha256
import gzip
import json
import os
from pathlib import Path

from kombination import HERE, STUDY, MIDDLE, Combination, model, sha, PACKAGE, V16, SOURCE, MODEL_SHA, SOURCE_SHA
from messen import GroundTruth, SCORES, source_hashes
from scripts.common import make_opponent,play_game
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors

def manifest():
    data=source_hashes()
    for f in (HERE/"PLAN.md",HERE/"kombination.py",Path(__file__),STUDY/"kandidat.py",STUDY.parent/"kundschafter/kandidat.py",
              MIDDLE/"mitte.py",MIDDLE/"optionen.py",MIDDLE/"archiv_partien.jsonl.gz",SOURCE/"berater.py",SOURCE/"wertberater.npz"):
        data[str(f.relative_to(STUDY.parents[3]))]=sha(f)
    if (sha(MIDDLE/"mitte.py")!="22f80ab0852f22adc07202da37cd6a20263570a46aa669427be08e6af5bd9620"
            or sha(MIDDLE/"optionen.py")!="c03586fe09e697b5a8ba39dba0c93ae9ffe970b1822730ec9c59a021bca7748e"
            or sha(MIDDLE/"archiv_partien.jsonl.gz")!="5bc24ce8c5d1f2bbbd543b0df46259eaea79b1c782c62965324cf40678b80c28"):
        raise ValueError("Bekannte Mitte2-Quelle stimmt nicht")
    return data


def raw(folder):return [r for f in sorted(folder.glob("worker_*.jsonl")) for r in map(json.loads,f.read_text().splitlines())]


def selection():
    cases={}
    for label,ref,cand in (("signal_pruef",raw(STUDY/"haupt"),raw(STUDY/"haupt")),
                           ("signal_entwicklung",raw(STUDY/"beobachtung"),raw(STUDY/"aktion"))):
        old={(r["seed"],r["side"]):r for r in ref if r.get("arm","v16")=="v16" and r.get("opponent","solution92")=="solution92"}
        new={(r["seed"],r["side"]):r for r in cand if r.get("arm","signal")=="signal" and r.get("opponent","solution92")=="solution92"}
        for k,o in old.items():
            n=new[k]
            if o["game_win"]!=n["game_win"]:
                cases[k]=dict(labels=[label],aus=o,signal=n)
    for r in map(json.loads,gzip.open(MIDDLE/"archiv_partien.jsonl.gz","rt")):
        o=r["original"];n=r["alternate"]
        if not n or o["scores"]["game_win"]==n["scores"]["game_win"]:continue
        k=r["seed"],r["side"]
        if k in cases:raise ValueError("Mehrfacharchiv vor Interpretation abgleichen")
        team=int(k[1][-1])
        def native(v):
            return dict(**v["scores"],match_winners=[team if w else 1-team for w in v["match_wins"]],event=v["event"])
        cases[k]=dict(labels=["mitte_archiv"],aus=native(o),mitte=native(n))
    counts={a:sum(a in x["labels"] for x in cases.values()) for a in ("signal_pruef","mitte_archiv","signal_entwicklung")}
    if counts!={"signal_pruef":3,"mitte_archiv":7,"signal_entwicklung":1}:
        raise ValueError(f"Nicht die erwarteten vollständigen Siegwechsel: {counts}")
    return cases


def games(env,seed,side,arm,net,opp="solution92"):
    other="player_1" if side=="player_0" else "player_0"
    me=Combination(side,net,arm)
    enemy=Combination(other,net,"aus") if opp=="v16" else make_opponent(opp,other)
    trace=GroundTruth(env)
    res=play_game(trace,me,enemy,seed,side,False)
    require_no_agent_errors(me.base,enemy.base if opp=="v16" else enemy)
    if me.calls!=303 or res["steps"]!=303 or len(trace.match_winners)!=3 or me.middle.changed>1:
        raise ValueError("Unvollständiger Einsatz")
    if opp=="v16" and (enemy.calls!=303 or enemy.events):raise ValueError("Falsche Direktreferenz")
    r=dict(seed=seed,side=side,arm=arm,opponent=opp,**{k:res[k] for k in SCORES},
           match_winners=trace.match_winners,signal_changes=me.scout.changes,signal_first=me.scout.first_signal,
           middle_event=me.middle.event,decisions=me.calls,events=me.events)
    if ((arm in ("aus","signal") and r["middle_event"] is not None) or (arm in ("aus","mitte") and r["signal_changes"])):
        raise ValueError("Modulsperre missachtet")
    return r


def verify_reference(r,expected):
    for k in (*SCORES,"match_winners"):
        if k in expected and r[k]!=expected[k]:raise ValueError(f"Originalarchiv weicht ab {r['seed']}/{r['side']}/{r['arm']}/{k}")
    if r["arm"]=="signal" and (r["signal_changes"]!=expected["changes"] or r["signal_first"]!=expected["first"]):
        raise ValueError("Scout-Sperre reproduziert die Einzelakte nicht")
    if r["arm"]=="mitte" and r["middle_event"]!=expected["event"]:
        raise ValueError("Mitte2-Einzelaktion weicht vom Archiv ab")


def main():
    ap=argparse.ArgumentParser();ap.add_argument("shard",type=int,choices=(0,1));args=ap.parse_args()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads();net=model();env=LuxAIS3GymEnv(numpy_output=True)
    cases=selection();sources=manifest()
    folder=HERE/"technik";folder.mkdir(exist_ok=True)
    f=folder/f"quellen_{args.shard}.json"
    if f.exists() and json.loads(f.read_text())!=sources:raise ValueError("Quellversion verschieden")
    f.write_text(json.dumps(sources,sort_keys=True,indent=2)+"\n")
    keys=[(seed,side,a) for seed,side in sorted(cases) for a in ("aus","signal","mitte","beide")][args.shard::2]
    dest=folder/f"worker_{args.shard}.jsonl"
    done=[(r["seed"],r["side"],r["arm"]) for r in (map(json.loads,dest.read_text().splitlines()) if dest.exists() else [])]
    if done!=keys[:len(done)]:raise ValueError("Doppelte oder falsche Aufnahme")
    for seed,side,a in keys[len(done):]:
        result=games(env,seed,side,a,net)
        c=cases[seed,side]
        if a in c:verify_reference(result,c[a])
        result["labels"]=c["labels"]
        with dest.open("a") as s:
            s.write(json.dumps(result,separators=(",",":"))+"\n");s.flush();os.fsync(s.fileno())
        print(seed,side,a,flush=True)
    if sources!=manifest():raise ValueError("Unbeabsichtigte Änderung")


if __name__=="__main__":main()
