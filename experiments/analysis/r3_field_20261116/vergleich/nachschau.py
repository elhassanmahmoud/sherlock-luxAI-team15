"""Inspect the three verified policies after noticing a fresh discordant result."""
import argparse
import gzip
import json
from pathlib import Path
from wiederholung import STUDY, PRIOR, Observer, match_summary, play, require, spiele, verify_runtime


def run(runtime, out):
    verify_runtime(runtime, json.loads((PRIOR / "laufzeit.json").read_bytes()))
    out.mkdir(parents=True, exist_ok=False)
    spiele.initialize(runtime)
    from feldwahl import Field
    env = spiele.env
    seat, seed = "player_0", 7426119
    traces = {}
    for arm in ("r3", "blend", "field"):
        folder = "candidate" if arm == "field" else "parents"
        reference, = (r for r in map(json.loads, (STUDY / folder / "games.jsonl").read_bytes().splitlines())
                      if (r["arm"], r["opponent"], r["seed"], r["seat"]) == (arm, "solution", seed, seat))
        if arm == "field":
            spiele.actors[arm] = Field(seat)
        actor = spiele.actor(arm, seat)
        observer = Observer(env, actor if arm == "r3" else actor.r3, "r3", seat)
        spiele.env = observer
        try:
            got = play((arm, "solution", seed, seat))
        finally:
            spiele.env = env
        require(got == reference and len(observer.frames) == 303, "Reproduction failed")
        traces[arm] = observer.frames
        result = dict(game=got, frames=observer.frames)
        (out / f"{arm}.json.gz").write_bytes(gzip.compress(json.dumps(result, separators=(",", ":")).encode(), mtime=0))
    env.close()
    result = {arm: [match_summary(frames[i:i+101]) for i in (0,101,202)] for arm, frames in traces.items()}
    for reference in ("r3", "blend"):
        result["first_different_orders_vs_" + reference] = []
        for start in (0, 101, 202):
            events = []
            for step in range(start, start+101):
                own = traces["field"][step]
                other = traces[reference][step]
                uids = [u for u in range(16) if own["own_orders"][u] != other["own_orders"][u]]
                if uids:
                    events.append(dict(turn=step-start, units=uids, coordinate_equal=own["own"] == other["own"],
                                       field=[own["own_orders"][u] for u in uids], ref=[other["own_orders"][u] for u in uids],
                                       confirmed=len(own["confirmed"]), state=own["before"]))
                    break
            result["first_different_orders_vs_" + reference].append(events)
    (out / "verlauf.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("runtime","out"):
        parser.add_argument("--" + arg, type=lambda s: Path(s).resolve(), required=True)
    args = parser.parse_args()
    run(args.runtime, args.out)
