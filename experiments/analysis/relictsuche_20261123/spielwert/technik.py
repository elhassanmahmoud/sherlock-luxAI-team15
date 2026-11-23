"""Check that budget zero reproduces release actions for both opponents and seats."""
import argparse
import json
from pathlib import Path
from luxai_s3.wrappers import LuxAIS3GymEnv
from gruppen import HERE, path, schedule
from spielen import play, require
from scripts.experiment import limit_threads


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    args=p.parse_args()
    limit_threads()
    jobs=[key for key in schedule("train") if key[-1]=="b0"][:4]
    if len({(t,o) for _,t,o,_ in jobs})!=4:
        raise ValueError("Expected both sides and opponents")
    env=LuxAIS3GymEnv(numpy_output=True)
    checked=[]
    try:
        for key in jobs:
            seed,team,opp,_=key
            forced=json.loads(path(args.folder,"train",key).read_text())
            pure=play(env,("train",seed,team,"reference",opp),forced["source"],None)
            for name in ("action_hash","matches","sight","credit","wins","points","caught_errors","after_70","events"):
                require(pure[name]==forced[name],f"Unaltered candidate changed {name}")
            checked.append(dict(seed=seed,team=team,opp=opp,commands_both_teams=303*16*2,
                                digest=pure["action_hash"]))
    finally:
        env.close()
    (HERE/"technik.json").write_text(json.dumps(checked,indent=2)+"\n")


if __name__=="__main__":
    main()
