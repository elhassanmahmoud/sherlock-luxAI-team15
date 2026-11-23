"""720 vorab festgelegte neue Spiele des unveränderten kombinierten Agenten."""
import argparse
import json
import os
from pathlib import Path

from technik import HERE,STUDY,MIDDLE,sha,model,games,manifest
from scripts.experiment import limit_threads
from scripts.fetch_kaggle3 import TARGET,WEIGHT_SHA256,verify


def panel():
    return [(s,p,o,a) for s in range(160386000,160386080) for p in ("player_0","player_1")
            for o in (("solution92","kaggle3","v16") if s<160386040 else ("solution92","kaggle3"))
            for a in (("beide",) if o=="v16" else ("aus","beide"))]


def contract():
    source=manifest()
    for f in (HERE/"auswerten.py",Path(__file__),HERE/"technik"/"ergebnis.json",HERE/"lauf.sh",
              HERE/"paritaet.py",HERE/"technik/paritaet_0.json",HERE/"technik/paritaet_1.json",HERE/"seedpruefung.json",HERE/"kartenpruefung.py",
              STUDY.parents[3]/"agents/sherlock/geometry.py",STUDY.parents[3]/"agents/sherlock/features.py",
              STUDY.parents[3]/"scripts/kaggle3_opponent.py",STUDY.parents[3]/"scripts/fetch_kaggle3.py",
              *(TARGET/n for n in WEIGHT_SHA256),*sorted(TARGET.rglob("*.py"))):
        source[str(f.relative_to(STUDY.parents[3]))]=sha(f)
    if not verify():raise ValueError("Falscher Kaggle-Gegner")
    return source


def main():
    ap=argparse.ArgumentParser();ap.add_argument("shard",type=int,choices=(0,1));args=ap.parse_args()
    report=json.loads((HERE/"technik"/"ergebnis.json").read_bytes())
    if report["n"]!=44 or not report["gate"]:raise ValueError("Bekannte Stufe erfüllt Kriterien nicht")
    checked=[r for i in (0,1) for r in json.loads((HERE/"technik"/f"paritaet_{i}.json").read_bytes())]
    if len(checked)!=4 or {(r["side"],r["arm"]) for r in checked}!={(p,a) for p in ("player_0","player_1") for a in ("mitte","signal")} or any(r["identical_observations_and_commands"]!=303 for r in checked):
        raise ValueError("Eingefrorene Einzelmodule nicht an allen 1.212 Mannschaftsbefehlen bestätigt")
    limit_threads();net=model();stamp=contract()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    env=LuxAIS3GymEnv(numpy_output=True)
    folder=HERE/"frisch";folder.mkdir(exist_ok=True)
    rec=folder/f"quellen_{args.shard}.json"
    if rec.exists() and json.loads(rec.read_text())!=stamp:raise ValueError("Abweichende Quellen")
    rec.write_text(json.dumps(stamp,indent=2,sort_keys=True)+"\n")
    out=folder/f"worker_{args.shard}.jsonl"
    keys=[k for k in panel() if k[0]%2==args.shard]
    old=[(r["seed"],r["side"],r["opponent"],r["arm"]) for r in (map(json.loads,out.read_text().splitlines()) if out.exists() else [])]
    if old!=keys[:len(old)]:raise ValueError("Falsches Teilarchiv")
    for seed,side,opp,a in keys[len(old):]:
        r=games(env,seed,side,a,net,opp)
        with out.open("a") as s:
            s.write(json.dumps(r,separators=(",",":"))+"\n");s.flush();os.fsync(s.fileno())
        print(seed,side,opp,a,flush=True)
    if contract()!=stamp:raise ValueError("Unbeabsichtigter Quellenwechsel")


if __name__=="__main__": main()
