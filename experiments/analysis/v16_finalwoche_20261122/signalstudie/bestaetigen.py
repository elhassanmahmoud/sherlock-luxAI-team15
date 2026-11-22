"""Unberührte Bestätigungs- und Gegnerkontrollkarten; je Lauf eine vorab festgelegte Teilmenge."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

from aktion import HERE, ROOT, SignalScout, GroundTruth, SCORES, bound_sources
from scripts.common import make_opponent, play_game
from scripts.experiment import limit_threads


def panel(phase):
    if phase=="haupt":
        return [(seed,side,opponent,arm)
                for seed in range(160344000,160344200) for side in ("player_0","player_1")
                for opponent in (("solution92","v16") if seed<160344050 else ("solution92",))
                for arm in (("v16","signal") if opponent=="solution92" else ("signal",))]
    if phase=="kaggle":
        return [(seed,side,"kaggle3",arm) for seed in range(160344200,160344400)
                for side in ("player_0","player_1") for arm in ("v16","signal")]
    raise ValueError("Unbekannte Phase")


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def frozen(phase):
    data=bound_sources()
    include=[Path(__file__),HERE/"BESTAETIGUNG.md",HERE/"aktionsbilanz.py",HERE/"aktion"/"ergebnis.json",
             HERE/"publikumspruefung.py",ROOT/"scripts/scoring.py"]
    if phase=="kaggle":
        include.append(HERE/"haupt"/"ergebnis.json")
        from scripts.fetch_kaggle3 import TARGET, WEIGHT_SHA256, verify
        if not verify(TARGET): raise ValueError("Unerwartete Kaggle-Gewichte")
        include.append(ROOT/"scripts/kaggle3_opponent.py")
        include.append(ROOT/"scripts/fetch_kaggle3.py")
        include.extend(Path(TARGET).rglob("*.py"))
        include.extend(Path(TARGET)/name for name in WEIGHT_SHA256)
    for f in include: data[str(f.relative_to(ROOT))]=sha(f)
    return data


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("phase",choices=("haupt","kaggle"))
    ap.add_argument("shard",type=int,choices=(0,1))
    args=ap.parse_args()
    phase=args.phase
    decision=HERE/("aktion" if phase=="haupt" else "haupt")/"ergebnis.json"
    report=json.loads(decision.read_bytes())
    if not report["gate"]: raise ValueError("Vorherige vollständige Stufe hat keinen weiteren Test eröffnet")
    hashes=frozen(phase)
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    env=LuxAIS3GymEnv(numpy_output=True)
    directory=HERE/phase
    directory.mkdir(exist_ok=True)
    manifest=directory/f"quellen_{args.shard}.json"
    if manifest.exists() and json.loads(manifest.read_bytes())!=hashes:
        raise ValueError("Quellen der ersten Aufnahme stimmen nicht mehr")
    manifest.write_text(json.dumps(hashes,sort_keys=True,indent=2)+"\n")
    out=directory/f"worker_{args.shard}.jsonl"
    jobs=[key for key in panel(phase) if key[0]%2==args.shard]
    done=[(r["seed"],r["side"],r["opponent"],r["arm"])
          for r in (map(json.loads,out.read_text().splitlines()) if out.exists() else [])]
    if done!=jobs[:len(done)]: raise ValueError("Falsche oder doppelte angeschnittene Aufzeichnung")
    for seed,side,opponent,arm in jobs[len(done):]:
        other="player_1" if side=="player_0" else "player_0"
        agent=SignalScout(side,arm=="signal")
        enemy=SignalScout(other,False) if opponent=="v16" else make_opponent(opponent,other)
        trace=GroundTruth(env)
        result=play_game(trace,agent,enemy,seed,side,False)
        bundle=[agent,enemy] if opponent=="v16" else [agent]
        if any(a.base.caught_errors or getattr(a.base._imitation,"caught_errors",0) for a in bundle):
            raise ValueError("Ersatzentscheidung eines Agenten")
        if result["steps"]!=303 or len(trace.match_winners)!=3 or agent.fields_third is None:
            raise ValueError("Unvollständiger Spielverlauf")
        if agent.changes and (arm!="signal" or agent.first_signal is None or agent.start<agent.first_signal["turn"]
                or len({c[1] for c in agent.changes})!=1 or max(c[0] for c in agent.changes)>79):
            raise ValueError("Unerlaubte Aktionsänderung")
        row=dict(seed=seed,side=side,opponent=opponent,arm=arm,
                 **{k:result[k] for k in SCORES},match_winners=trace.match_winners,first=agent.first_signal,
                 changes=agent.changes,start=agent.start,uid=agent.uid,known_second=agent.sighting,
                 fields_step0=agent.fields_third,fields_step1=agent.known_at_third)
        with out.open("a") as sink:
            sink.write(json.dumps(row,separators=(",",":"))+"\n")
            sink.flush()
            os.fsync(sink.fileno())
        print(seed,side,opponent,arm,flush=True)
    if frozen(phase)!=hashes: raise ValueError("Unbeabsichtigte Quellenänderung")


if __name__=="__main__":
    main()
