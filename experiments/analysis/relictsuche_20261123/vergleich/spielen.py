"""Resumable deterministic full-game comparison. No score readout while a stage is running."""
import argparse
from datetime import datetime
import fcntl
import hashlib
from importlib import metadata, util
import json
import os
from pathlib import Path
import platform
import random
import re
import sys
from zoneinfo import ZoneInfo

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from scripts.common import make_opponent, play_game
from scripts.par_eval import require_no_agent_errors
from scripts.r3_package import r3_package_agent
from scripts.scoring import match_points_after_step

PACKAGE = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
RELEASE = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"
SCRATCH = Path("/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/experiments/imitation/relictsuche_20261123/vergleich")
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS")
CUTOFF = datetime(2026, 11, 23, 16, 0, tzinfo=ZoneInfo("Europe/Berlin"))
HIST = ROOT / "experiments/analysis/v16_finalwoche_20261122/eroeffnung_lehrer"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_once(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with tmp.open("w") as f:
        json.dump(obj, f, sort_keys=True, separators=(",", ":"), allow_nan=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    try:
        os.link(tmp, path)
    except FileExistsError:
        require(json.loads(path.read_text()) == obj, f"Existing identity or data differs: {path}")
    finally:
        tmp.unlink(missing_ok=True)


def common_source():
    require(sha(PACKAGE) == RELEASE, "Wrong V16 package")
    eng = Path(util.find_spec("luxai_s3").origin).parent
    support = [ROOT / "scripts" / (k + ".py") for k in ("common", "metrics", "r3_package", "par_eval", "xversion_replay", "scoring", "experiment")]
    support += sorted((ROOT / "agents/Solution_92_Kaggle").glob("*.py"))
    support += [HERE / f for f in ("PLAN.md", "spielen.py", "panel.py", "karten.json")]
    return {"release": RELEASE, "python": platform.python_version(),
            "libraries": {n: metadata.version(n) for n in ("luxai-s3", "jax", "jaxlib", "torch", "numpy", "scipy", "flax")},
            "support": {str(f.relative_to(ROOT)): sha(f) for f in support},
            "engine": {str(f.relative_to(eng)): sha(f) for f in sorted(eng.rglob("*.py"))},
            "threads": {k: os.environ.get(k) for k in THREADS}, "pythonhashseed": os.getenv("PYTHONHASHSEED")}


def inputs(path, dependencies):
    require(path.is_absolute() and path.is_file(), "Candidate must be an existing absolute file")
    files = [path.resolve(), *(p.resolve(strict=True) for p in dependencies)]
    require(len(files) == len(set(files)), "Duplicate candidate input")
    def label(p):
        return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
    return {"module": label(files[0]), "files": {label(p): sha(p) for p in files}}


def load_factory(path):
    spec = util.spec_from_file_location("relic_run_candidate", path)
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module.create


class Monitor:
    """Checks each submitted command against a copy of the unmodified, actual V16 proposal."""
    def __init__(self, env, team, phase, actor=None):
        self.env = env
        self.team = team
        self.side = f"player_{team}"
        self.phase = phase
        self.actor = actor
        self.proposal = None
        self.turn = 0
        self.first_sight = self.first_credit = 101
        self.after_70 = None
        self.matches = []
        self.events = []
        self.digest = hashlib.sha256()
        self.counts = [0, 0]
        if actor is not None:
            from scripts.r3_package import _module_for
            _, course = _module_for(PACKAGE.resolve())
            require(type(actor.base) is course.Agent_x, "Candidate must expose its actual V16 instance as .base")
            raw = actor.base.act
            def exact(*args, **kwargs):
                require(self.proposal is None, "Multiple calls to V16 in one turn")
                command = raw(*args, **kwargs)
                self.proposal = np.asarray(command).copy()
                return command
            actor.base.act = exact

    def reset(self, **kwargs):
        result = self.env.reset(**kwargs)
        self.old = result[0][self.side]
        self.sensor = int(result[1]["params"]["unit_sensor_range"])
        require(self.phase == "general" or self.sensor == 1, "Unexpected public sensor range at real reset")
        return result

    def step(self, actions):
        t, ms = self.turn, self.turn % 101
        require(int(self.old["match_steps"]) == ms, "Incorrect continuity")
        for team in (0, 1):
            a = np.asarray(actions[f"player_{team}"])
            require(a.shape == (16, 3) and np.issubdtype(a.dtype, np.integer), "Malformed command array")
            require(np.all((a[:, 0] >= 0) & (a[:, 0] <= 5)), "Unknown action")
            self.digest.update(a.astype("<i4", copy=False).tobytes())
            self.counts[team] += 1
        if self.actor is not None:
            require(self.proposal is not None, "Candidate skipped V16 proposal")
            played = np.asarray(actions[self.side])
            delta = np.flatnonzero(np.any(played != self.proposal, axis=1))
            require(len(delta) <= 1, "More than one modified ship")
            if len(delta):
                uid = int(delta[0])
                before, after = self.proposal[uid], played[uid]
                require(t < 101 and self.sensor == 1, "Change outside low-vision match one")
                require(0 <= before[0] <= 4 and 1 <= after[0] <= 4 and after[0] != before[0] and not after[1:].any(), "Expected a distinct scout movement")
                require(bool(self.old["units_mask"][self.team, uid]), "Scout not alive")
                self.events.append([t, uid, int(before[0]), int(after[0])])
            require(int(self.actor.changes) == len(self.events), "Policy count disagrees with submitted commands")
            self.proposal = None
        if t <= 100 and self.first_sight == 101 and np.asarray(self.old["relic_nodes_mask"]).any():
            self.first_sight = t
        out = self.env.step(actions)
        new = out[0][self.side]
        if t <= 100 or ms == 100:
            scores = match_points_after_step(self.old, new, out[4])
            points = [int(scores[self.team]), int(scores[1 - self.team])]
            if t <= 100 and self.first_credit == 101 and points[0]:
                self.first_credit = t
            if t == 70:
                self.after_70 = points
            if ms == 100:
                wins = np.asarray(new["team_wins"]) - np.asarray(self.old["team_wins"])
                require(sorted(wins.tolist()) == [0, 1] and int(new["match_steps"]) == 0, "Bad match boundary")
                self.matches.append({"points": points, "win": int(wins[self.team])})
        self.turn += 1
        self.old = new
        return out


def technical_reference(row):
    sources = (HIST / "teil_0.jsonl", HIST / "teil_1.jsonl")
    old = [v for p in sources for line in p.read_text().splitlines() if (v := json.loads(line))["arm"] == "v16"
           and v["seed"] == row["seed"] and v["side"] == f"player_{row['team']}"]
    require(len(old) == 1, "Missing historical control")
    old = old[0]
    m = row["matches"][0]
    expected = [old[k] if old[k] is not None else 101 for k in ("first_relic", "first_own_score", "after_70", "match_score", "match_win")]
    require(expected == [row["sight"], row["credit"], row["after_70"], m["points"], m["win"]], "Historical V16 opening disagrees")


def validate(row, key, source):
    phase, seed, team, ident, opponent = key
    require([row[k] for k in ("phase", "seed", "team", "id", "opponent")] == list(key) and row["source"] == source, f"Wrong game identity {key}")
    require(row["steps"] == 303 and row["actions_checked"] == [303, 303] and row["caught_errors"] == [0, 0]
            and row["point_counting_version"] == 2 and len(row["matches"]) == 3, f"Incomplete game {key}")
    matches = row["matches"]
    require(row["wins"] == sum(m["win"] for m in matches) and int(row["wins"] >= 2) == row["win"], "Wrong winner")
    require(row["points"] == [sum(m["points"][i] for m in matches) for i in (0, 1)], "Wrong game points")
    require(all(0 <= row[f] <= 101 for f in ("sight", "credit")), "Invalid event time")
    require((row["credit"] == 101) == (matches[0]["points"][0] == 0), "Incorrect first credit")
    require(all(0 <= x <= y for x, y in zip(row["after_70"], matches[0]["points"], strict=True)), "Invalid score after turn 70")
    require(phase == "general" or row["sensor"] == 1, "Wrong sensor")
    require(ident != "reference" or not row["events"], "Reference modified an action")
    ts = [e[0] for e in row["events"]]
    require(ts == sorted(set(ts)) and all(0 <= t < 101 and 0 <= u < 16 and 0 <= a <= 4 and 1 <= b <= 4 and b != a
            and row["sensor"] == 1 for t, u, a, b in row["events"]), "Invalid changed actions")
    require(len(row["action_hash"]) == 64, "Invalid action trace")
    if phase == "technical" and ident == "reference":
        technical_reference(row)


def play(env, key, source, factory):
    import torch
    phase, seed, team, ident, opponent = key
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    side, other = f"player_{team}", f"player_{1-team}"
    actor = factory(side) if factory else r3_package_agent(side, PACKAGE)
    rival = r3_package_agent(other, PACKAGE) if opponent == "v16" else make_opponent("solution92", other)
    monitor = Monitor(env, team, phase, actor if factory else None)
    raw = play_game(monitor, actor, rival, seed, side, False)
    require_no_agent_errors(actor, rival)
    if factory:
        require_no_agent_errors(actor.base, rival)
    row = dict(zip(("phase", "seed", "team", "id", "opponent"), key, strict=True), source=source,
               sensor=monitor.sensor, sight=monitor.first_sight, credit=monitor.first_credit, after_70=monitor.after_70,
               matches=monitor.matches, events=monitor.events, steps=monitor.turn, actions_checked=monitor.counts,
               caught_errors=[0, 0], point_counting_version=raw["point_counting_version"], wins=raw["our_wins"],
               win=raw["game_win"], points=[raw["our_points"], raw["opp_points"]], action_hash=monitor.digest.hexdigest())
    require(raw["steps"] == monitor.turn and raw["our_wins"] + raw["opp_wins"] == 3, "Runner disagrees with monitor")
    validate(row, key, source)
    return row


def run(args):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.experiment import limit_threads

    require(os.getenv("PYTHONHASHSEED") == "0" and all(os.getenv(k) == "1" for k in THREADS), "Unpinned randomness/threads")
    require(bool(args.candidate) == (args.id != "reference") and re.fullmatch("[a-z][a-z0-9_-]*", args.id), "Invalid policy identity")
    require(not args.dependency or args.candidate, "Reference has no candidate dependencies")
    require(args.phase != "technical" or args.id == "reference", "Technical games are historical reference anchors")
    limit_threads()
    common = common_source()
    source = {"common": stamp(common), "id": args.id, "candidate": inputs(args.candidate, args.dependency) if args.candidate else None}
    write_once(args.work / "common.json", common)
    write_once(args.work / "sources" / (args.id + ".json"), source)
    if args.phase != "technical":
        anchors = json.loads((HERE / "karten.json").read_text())["technical"]
        for seed in anchors:
            for team in (0, 1):
                k = ("technical", seed, team, "reference", "solution92")
                r = args.work / "technical" / "reference" / f"{seed}_{team}_solution92.json"
                ref_source = json.loads((args.work / "sources/reference.json").read_text())
                require(ref_source["common"] == source["common"], "Technical sources changed")
                validate(json.loads(r.read_text()), k, stamp(ref_source))
    factory = load_factory(args.candidate) if args.candidate else None
    cards = json.loads((HERE / "karten.json").read_text())[args.phase]
    opponents = ["solution92", "v16"] if factory else ["solution92"]
    jobs = [(args.phase, seed, team, args.id, opp) for seed in cards for team in (0, 1) for opp in opponents]
    offset = (args.worker * 37) % len(jobs)
    path = args.work / args.phase / args.id
    locks = path / ".leases"
    locks.mkdir(parents=True, exist_ok=True)
    env = LuxAIS3GymEnv(numpy_output=True)
    completed = 0
    try:
        for key in jobs[offset:] + jobs[:offset]:
            if datetime.now(CUTOFF.tzinfo) >= CUTOFF and not args.reproduction:
                break
            stem = f"{key[1]}_{key[2]}_{key[4]}"
            dest = path / (stem + ".json")
            if dest.exists():
                continue
            with (locks / (stem + ".lock")).open("a+") as lease:
                try:
                    fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    continue
                if dest.exists():
                    continue
                data = play(env, key, stamp(source), factory)
                write_once(dest, data)
                completed += 1
                if completed % 10 == 0:
                    print(f"{args.phase} {args.id} worker={args.worker} additional_games={completed}", flush=True)
    finally:
        env.close()
    require(common_source() == common and (not args.candidate or inputs(args.candidate, args.dependency) == source["candidate"]), "Sources drifted during execution")
    print(f"{args.phase} {args.id} worker={args.worker} completed={completed}", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=("technical", "discovery", "confirm", "general"))
    p.add_argument("--id", default="reference")
    p.add_argument("--candidate", type=Path)
    p.add_argument("--dependency", type=Path, action="append", default=[])
    p.add_argument("--worker", type=int, default=0)
    p.add_argument("--work", type=Path, default=SCRATCH)
    p.add_argument("--reproduction", action="store_true", help="After the study deadline, use a separate new working directory for historical reproduction")
    args = p.parse_args()
    require(not args.reproduction or args.work.resolve() != SCRATCH.resolve(), "Reproduction requires separate storage")
    run(args)
