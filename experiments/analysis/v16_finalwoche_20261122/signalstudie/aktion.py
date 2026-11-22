"""Gepaarte Spiele des einmalig festgelegten signalgesteuerten Kundschafters."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

from kandidat import SignalScout
from messen import ROOT, HERE, SEEDS, DIGEST, GroundTruth, source_hashes, SCORES
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads


def bound_sources():
    hashes=source_hashes()
    for filename in (HERE/"kandidat.py",Path(__file__),HERE.parent/"kundschafter"/"kandidat.py",HERE/"AKTION.md"):
        hashes[str(filename.relative_to(ROOT))]=sha256(filename.read_bytes()).hexdigest()
    return hashes


def baseline_data():
    rows=[]
    for shard in (0,1):
        rows.extend(map(json.loads,(HERE/"beobachtung"/f"worker_{shard}.jsonl").read_text().splitlines()))
    return {(r["seed"],r["side"]):r for r in rows}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("shard",type=int,choices=(0,1))
    args=ap.parse_args()
    report=json.loads((HERE/"beobachtung"/"ergebnis.json").read_bytes())
    if not report["gate"] or report["all"]["maps"]!=48 or report["all"]["sides"]!=96:
        raise RuntimeError("Die vollständige Beobachtung muss den Suchversuch eröffnen")
    hashes=bound_sources()
    base=baseline_data()
    keys=[(seed,side,opp) for seed in SEEDS if seed%2==args.shard for side in ("player_0","player_1")
          for opp in ("solution92","v16")]
    if len(base)!=96 or len(keys)!=96: raise ValueError("Unvollständiges Panel")
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    env=LuxAIS3GymEnv(numpy_output=True)
    directory=HERE/"aktion"
    directory.mkdir(exist_ok=True)
    manifest=directory/f"quellen_{args.shard}.json"
    if manifest.exists() and json.loads(manifest.read_bytes())!=hashes:
        raise ValueError("Quellen seit Anlauf verändert")
    manifest.write_text(json.dumps(hashes,sort_keys=True,indent=2)+"\n")
    out=directory/f"worker_{args.shard}.jsonl"
    saved=list(map(json.loads,out.read_text().splitlines())) if out.exists() else []
    done=[(r["seed"],r["side"],r["opponent"]) for r in saved]
    if done!=keys[:len(done)]: raise ValueError("Unpassende Teilergebnisse")
    for seed,side,opp in keys[len(done):]:
        me=SignalScout(side,True)
        rival="player_1" if side=="player_0" else "player_0"
        enemy=SignalScout(rival,False) if opp=="v16" else make_opponent(opp,rival)
        trace=GroundTruth(env)
        res=play_game(trace,me,enemy,seed,side,False)
        checks=[me,enemy] if opp=="v16" else [me]
        if any(a.base.caught_errors or getattr(a.base._imitation,"caught_errors",0) for a in checks):
            raise ValueError("Ein Paketagent musste auf einen Ersatzbefehl zurückgreifen")
        if res["steps"]!=303 or len(trace.match_winners)!=3 or me.fields_third is None:
            raise ValueError("Unvollständige Partie")
        baseline=base[seed,side]
        if opp=="solution92":
            expected=baseline["first"]
            if expected and expected["turn"]>79: expected=None
            if me.first_signal!=expected:
                raise ValueError(f"Öffentliche Erstmeldung weicht vor dem ersten Eingriff ab: {seed}/{side}")
            if not me.changes and (any(res[k]!=baseline[k] for k in SCORES)
                                   or me.sighting!=baseline["known_second"] or trace.match_winners!=baseline["match_winners"]):
                raise ValueError(f"Abweichung trotz identischer Aktionen: {seed}/{side}")
        if me.changes and (me.first_signal is None or me.start<me.first_signal["turn"]
                          or len({c[1] for c in me.changes})!=1 or max(c[0] for c in me.changes)>79):
            raise ValueError("Suchauftrag außerhalb seiner Bedingungen")
        row=dict(seed=seed,side=side,opponent=opp,**{k:res[k] for k in SCORES},
                 match_winners=trace.match_winners,match2_win=trace.match_winners[1]==int(side[-1]),
                 first=me.first_signal,start=me.start,uid=me.uid,stop=me.reason,changes=me.changes,
                 known_second=me.sighting,fields_match3_step0=me.fields_third,
                 fields_match3_step1=me.known_at_third)
        with out.open("a") as sink:
            sink.write(json.dumps(row,separators=(",",":"))+"\n")
            sink.flush()
            os.fsync(sink.fileno())
        print(seed,side,opp,flush=True)
    if bound_sources()!=hashes: raise ValueError("Unbemerkte Quellenänderung")


if __name__=="__main__":
    main()
