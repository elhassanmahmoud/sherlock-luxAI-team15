"""Trace five published R3 defeats and three prespecified R3 rescues on the shared Dev A development panel."""
import argparse
from collections import Counter
import csv
from importlib.util import find_spec
import json
from pathlib import Path

from scripts import final_battle_compare as battle
from scripts.final_battle_select import SEATS, checked_run_files
from scripts.r3_solution_observation import SECTIONS, ships
from scripts.r3_solution_retrace import reproduce
from scripts.solution_passive import ScoreObserver

MAPS = range(7150000, 7150100)
LOSSES = ((7150011, "player_0"), (7150011, "player_1"), (7150035, "player_0"),
          (7150079, "player_1"), (7150096, "player_0"))
CONTROLS = ((7150003, "player_0"), (7150035, "player_1"), (7150037, "player_1"))
CASES = LOSSES + CONTROLS
POLICY = {"v14": "v14", "r3": "selective_movement"}
R3_FILES = {"games_sha256": "7d407d4fd7322f65d6ae5d27a87a157e2cf0a144b9eac303a93c86db9fea27ae",
            "manifest_sha256": "06452ab615c2dd35f1b4e63261ce0f3d5014dabe8c35840b3113fef705e67dde"}
V14_TABLE = "589ebf326adbb2535bd0079b603d914a47b7b2987b2bdf8dd83ba9c2bcefb25f"
TRACE_SOURCES = {"r3_solution_observation.py": "d222c99ba383ce8858b2aac328964329c0ccfecbc11fdd6af803d7f1bdb145ad",
                 "r3_solution_retrace.py": "380e8c9557457b0dd8c9e426549b5b07ff70f7f5256a757d05b122da4995c501",
                 "solution_passive.py": "926a0ed1d20578780b6043408048ba442023cc6c2195e224678ba054af3b74f3",
                 "final_battle_select.py": "8fbb96e068fdf5c581766202272b061987efe5bed6b6b337dc31f042a1e831f4"}


def inputs(analysis):
    study = analysis / "movement_soft_20261115/dev_a_solution"
    rows, manifest, files = checked_run_files(study / "r3", POLICY["r3"], MAPS, ("solution92",))
    table = analysis / "kaggle3_20261115/v14_ref_devA.csv"
    if files != R3_FILES or battle.digest(table) != V14_TABLE:
        raise ValueError("Changed historical Dev A files")
    r3 = {(seed, side): row for (_, seed, side), row in rows.items()}
    v14 = {}
    with table.open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["opponent"] != "solution92":
                continue
            seed, side = int(row["seed"]), row["side"]
            if (seed, side) in v14:
                raise ValueError("Duplicate published seat")
            v14[seed, side] = dict(candidate="v14", opponent="solution92", seed=seed, side=side,
                                  result=int(row["game_win"]), wins=int(row["our_wins"]), losses=int(row["opp_wins"]),
                                  points=int(row["our_points"]), opp_points=int(row["opp_points"]), steps=int(row["steps"]))
    if v14.keys() != r3.keys() or set(r3) != {(seed, side) for seed in MAPS for side in SEATS}:
        raise ValueError("Unpaired or incomplete 200 published seats")
    losses = tuple(sorted(key for key, row in r3.items() if not row["result"]))
    rescues = sorted(key for key, row in r3.items() if row["result"] and not v14[key]["result"])
    first_per_map = {}
    for key in rescues:
        first_per_map.setdefault(key[0], key)
    if losses != LOSSES or tuple(first_per_map.values())[:3] != CONTROLS:
        raise ValueError("Historical selection no longer reproduces the preregistered cases")
    return {"v14": v14, "r3": r3}, manifest, {**files, "v14_table_sha256": V14_TABLE}


class PublicScoreObserver(ScoreObserver):
    """Append public own occupancy; the existing observer measures the true scores post-step."""
    def __init__(self, env, side):
        super().__init__(env)
        self.side = side
        self.team = int(side[-1])
        self.public_occupancy = []

    def step(self, actions):
        before = self.previous[self.side]
        result = super().step(actions)
        after = self.previous[self.side]
        counts = []
        for obs in (before, after):
            _, _, pos, live = ships(obs, self.team)
            counts.append(Counter(tuple(map(int, xy)) for xy in pos[live]))
        self.public_occupancy.append(counts)
        return result


def annotate(report, observer):
    """Use only measurement data after each action; never expose diagnostics to either agent."""
    frames, occupancy = observer.frames, observer.public_occupancy
    ours = report["observation"]["team"]
    if len(occupancy) != 303 or [f["step"] for f in frames] != list(range(303)):
        raise ValueError("Incomplete score/occupancy timeline")
    for event in report["changed_orders"]:
        at = event["global_step"]
        origin = tuple(event["origin"])
        pre, post = occupancy[at]
        # At the final transition the match is over; there is no following action to repair a vacancy.
        if not event["leaves_holder_v14_would_keep"] or event["match_step"] in (0, 100) or pre[origin] != 1:
            continue
        end = (at // 101 + 1) * 101
        reoccupied = next((t for t in range(at, end) if occupancy[t][1][origin]), None)
        event["observed_holder_outcome"] = dict(vacant_after=post[origin] == 0,
            empty_step_ends=(end if reoccupied is None else reoccupied) - at,
            right_censored_by_match_end=reoccupied is None)
    for match in report["observation"]["matches"]:
        start = (match["match"] - 1) * 101
        part = frames[start:start + 101]
        if [f["match_step"] for f in part] != list(range(101)) or part[-1]["points_after"] != match["final"]["team_points"]:
            raise ValueError("External score observer and historical match observer disagree")
        deltas = [f["points_after"][ours] - f["points_after"][1 - ours] for f in part]
        last_nonnegative = max((t for t, margin in enumerate(deltas) if margin >= 0), default=-1)
        match["lasting_deficit_from"] = last_nonnegative + 1 if deltas[-1] < 0 else None
        match["own_lead_max"] = max(0, *deltas)
        match["own_deficit_max"] = max(0, -min(deltas))
        match["first_rival_point_gain"] = next((f["match_step"] for f in part if f["points_gained"][1 - ours]), None)
        for label, (lo, hi) in zip(SECTIONS, ((0,0), (1,33), (34,66), (67,100)), strict=True):
            window = part[lo:hi + 1]
            phases = match["sections"][label]
            phases["points_gained"] = [sum(f["points_gained"][side] for f in window) for side in (ours, 1 - ours)]
            phases["closing_score"] = [window[-1]["points_after"][side] for side in (ours, 1 - ours)]
            phases["steps_behind"] = sum(m < 0 for m in deltas[lo:hi + 1])
        match["point_trace_own_rival"] = [[f["points_after"][i] for i in (ours, 1 - ours)] for f in part]


def verify_runtime(manifest, model):
    for name, expected in manifest["sources"].items():
        if battle.digest(battle.ROOT / name) != expected:
            raise ValueError(f"Historical evaluation source differs: {name}")
    for name, expected in TRACE_SOURCES.items():
        if battle.digest(battle.ROOT / "scripts" / name) != expected:
            raise ValueError(f"Historical observer differs: {name}")
    engine = Path(find_spec("luxai_s3").origin).parent
    if ({name: battle.digest(engine / name) for name in manifest["engine"]} != manifest["engine"]
        or battle.digest(battle.WEIGHTS) != manifest["weights"] or (model and battle.digest(model) != manifest["model"])):
        raise ValueError("Different engine or policy weights")


def dump(path, obj):
    with path.open("x") as stream:
        json.dump(obj, stream, separators=(",", ":"), allow_nan=False)
        stream.write("\n")


def run(a, expected, manifest, hashes):
    model = str(a.r3.resolve()) if a.r3 else None
    verify_runtime(manifest, model)
    dest = a.out / a.arm
    dest.mkdir(parents=True, exist_ok=False)
    files = {}
    battle.init_worker(POLICY[a.arm], model)
    original_env = battle.evaluate.env
    try:
        for seed, side in CASES:
            observer = PublicScoreObserver(original_env, side)
            battle.evaluate.env = observer
            report = reproduce(a.arm, model, seed, side, expected[a.arm][seed, side], hashes)
            annotate(report, observer)
            name = f"{seed}_{side}.json"
            dump(dest / name, report)
            if not report["reproduced"]:
                raise ValueError(f"{name}: historical reproduction failed: {report['differences']}")
            files[name] = battle.digest(dest / name)
            print(a.arm, seed, side, "reproduced", flush=True)
    finally:
        battle.evaluate.env = original_env
        original_env.close()
    verify_runtime(manifest, model)
    dump(dest / "complete.json", dict(files=files, inputs=hashes, tool_sha256=battle.digest(__file__)))


def compact_match(report, match):
    team = report["observation"]["team"]
    final = match["final"]
    def first(key):
        item = match[key]
        return None if item is None else item["match_step"]
    departures = [event["observed_holder_outcome"] for event in report["changed_orders"]
                  if event["match"] == match["match"] and "observed_holder_outcome" in event]
    return dict(match=match["match"], result="W" if final["own_won"] else "L", decided_by=final["decided_by"],
        final_points=[final["team_points"][i] for i in (team, 1-team)], opening_known=match["opening_known_cells"],
        first_confirmed=first("first_confirmed"), first_scored=first("first_own_point_gain"),
        first_rival_score=match["first_rival_point_gain"], first_confirmed_occupied=first("first_known_occupied_after"),
        own_lead_max=match["own_lead_max"], own_deficit_max=match["own_deficit_max"],
        lasting_deficit_from=match["lasting_deficit_from"], sole_holder_interventions=len(departures),
        immediate_vacancies=sum(e["vacant_after"] for e in departures),
        empty_step_ends_per_intervention=[e["empty_step_ends"] for e in departures],
        censored_interventions=sum(e["right_censored_by_match_end"] for e in departures),
        sections={label:{k:sec[k] for k in ("steps", "closing_score", "points_gained", "steps_behind",
                     "known_occupied_cell_steps", "mean_active_units", "plausible_uid_departures")}
                  for label,sec in match["sections"].items()})


def compare(out, expected, hashes):
    cases = []
    for_complete = {}
    expected_names = {f"{seed}_{side}.json" for seed, side in CASES}
    for arm in POLICY:
        done = json.loads((out / arm / "complete.json").read_bytes())
        if (set(done["files"]) != expected_names or done["inputs"] != hashes
                or done["tool_sha256"] != battle.digest(__file__)):
            raise ValueError(f"Incomplete or unbound {arm} reproduction")
        for_complete[arm] = done["files"]
    for seed, side in CASES:
        item = dict(seed=seed, side=side, group="loss" if (seed, side) in LOSSES else "rescued_control", arms={})
        for arm in POLICY:
            name = f"{seed}_{side}.json"
            path = out / arm / name
            if battle.digest(path) != for_complete[arm][name]:
                raise ValueError(f"Changed {path}")
            report = json.loads(path.read_bytes())
            row = expected[arm][seed, side]
            if (report["arm"] != arm or report["side"] != side or report["seed"] != seed or report["original_files"] != hashes
                    or report["historical"] != row or not report["reproduced"] or report["differences"]
                    or any(v != report["game"].get(k) for k,v in row.items() if k != "secs")):
                raise ValueError(f"Unreproduced {name}/{arm}")
            item["arms"][arm] = [compact_match(report, m) for m in report["observation"]["matches"]]
        cases.append(item)
    dump(out / "comparison.json", dict(cases=cases, inputs=hashes, files=for_complete,
        interpretation="Each arm follows its own history. Holder alternatives are observed on R3's pre-action state; "
                       "subsequent vacancy duration and scores describe only the played trajectory."))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm", choices=("v14", "r3", "compare"))
    parser.add_argument("--analysis", type=Path, required=True, help="Project experiments/analysis directory")
    parser.add_argument("--out", type=Path, required=True, help="New study output root; each arm and comparison is single-use")
    parser.add_argument("--r3", type=Path)
    args = parser.parse_args()
    if bool(args.r3) != (args.arm == "r3"):
        parser.error("--r3 must be supplied exactly for the r3 arm")
    expected, manifest, hashes = inputs(args.analysis)
    if args.arm == "compare":
        compare(args.out, expected, hashes)
    else:
        run(args, expected, manifest, hashes)
