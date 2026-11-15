"""Four fixed Dev A V14/Solution_92 games. Observe scoring only, never send engine state to agents."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.scoring import match_points_after_step, point_tile_map

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/analysis/kaggle3_20261115/v14_devA.csv"
SOURCE_SHA = "4af3e6712e217e679d5393e03f61db5d8fe820a79f16523e05de347ba8c62e78"
WEIGHTS = ROOT / "agents/sherlock/weights/agent_p0.pth"
V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
KEYS = [(seed, f"player_{side}") for seed in (7150052, 7150096) for side in (0,1)]
OUTCOMES = ("steps","our_wins","opp_wins","game_win","result","our_points","opp_points","point_win",
            "point_counting_version")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def occupied(state):
    """Distinct active scoring cells for each team, after all engine updates. Coordinates are world x,y."""
    tiles = point_tile_map(state)
    pos = np.asarray(state.units.position)
    energy = np.asarray(state.units.energy)[...,0]
    mask = np.asarray(state.units_mask, bool)
    fields, raw_energy = [], []
    for team in (0,1):
        units = pos[team, mask[team] & (energy[team] >= 0)]
        cells = {(int(x), int(y)) for x,y in units if tiles[x,y]}
        fields.append(sorted(cells))
        # Exactly the engine's tie-break sum; point eligibility uses a different energy predicate.
        raw_energy.append(int(energy[team, mask[team]].sum(dtype=np.int64)))
    return fields, raw_energy


def finish_match(before_wins, after_wins, points, energy):
    diff = np.asarray(after_wins, int) - np.asarray(before_wins, int)
    if tuple(diff) not in ((1,0),(0,1)):
        raise ValueError("A match must award exactly one win")
    winner = int(np.argmax(diff))
    reason = ("points" if points[0] != points[1] else
              "energy_tiebreak" if energy[0] != energy[1] else "engine_lot_after_double_tie")
    if reason != "engine_lot_after_double_tie":
        criterion = points if reason == "points" else energy
        if winner != int(np.argmax(criterion)):
            raise ValueError("Observed winner disagrees with the engine's match criterion")
    return dict(winner=winner, decided_by=reason, final_energy=energy)


def score_frame(before, after, info):
    """The Gym wrapper has auto_reset=False. At a match reset its public score is already zero."""
    b, a = before["player_0"], after["player_0"]
    state = info["final_state"]
    pre = np.asarray(b["team_points"], int)
    points = match_points_after_step(b, a, info)
    fields, energy = occupied(state)
    gain = np.array([len(s) for s in fields])
    if (not np.array_equal(points - pre, gain)
            or not np.array_equal(np.asarray(state.team_wins), a["team_wins"])):
        raise ValueError("Post-step scoring fields do not reproduce actual score/wins")
    frame = dict(step=int(b["steps"]), match=int(np.asarray(b["team_wins"]).sum()) + 1,
                 match_step=int(b["match_steps"]), points_before=pre.tolist(), points_after=points.tolist(),
                 points_gained=gain.tolist(), scoring_cells=fields)
    if int(a["match_steps"]) == 0:
        frame["match_end"] = finish_match(b["team_wins"], a["team_wins"], points.tolist(), energy)
    return frame


class ScoreObserver:
    """Same reset/step results and RNG consumption as the unwrapped game."""
    def __init__(self, env):
        self.env = env
        self.previous = None
        self.frames = []

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.previous = obs
        self.frames.clear()
        return obs, info

    def step(self, actions):
        result = self.env.step(actions)
        after, _, _, _, info = result
        self.frames.append(score_frame(self.previous, after, info))
        self.previous = after
        return result


def game_summary(frames, row, reference):
    if len(frames) != 303 or [f["step"] for f in frames] != list(range(303)):
        raise ValueError("Incomplete course game")
    team = int(row["side"][-1])
    order = [team, 1-team]
    totals = np.zeros(2, int)
    wins = np.zeros(2, int)
    matches = []
    for mid in (1,2,3):
        trace = [f for f in frames if f["match"] == mid]
        if [f["match_step"] for f in trace] != list(range(101)) or [
            i for i,f in enumerate(trace) if "match_end" in f] != [100]:
            raise ValueError("Incomplete course match")
        last = trace[-1]
        score = np.asarray(last["points_after"])
        gains = np.array([f["points_gained"] for f in trace])
        if not np.array_equal(gains.sum(0), score):
            raise ValueError("Sum of step gains does not reproduce the final match score")
        totals += score
        wins[last["match_end"]["winner"]] += 1
        gap = np.array([f["points_after"][team]-f["points_after"][1-team] for f in trace])
        # An exact descriptive timestamp. No causal attribution for why a cell changed hands.
        lead = np.flatnonzero(gap > 0)
        nonbehind = np.flatnonzero(gap >= 0)
        first = [next((f["match_step"] for f in trace if f["points_gained"][i] > 0), None) for i in order]
        end = last["match_end"]
        matches.append(dict(match=mid, points_before_last=np.asarray(last["points_before"])[order].tolist(),
                            final_gain=gains[-1,order].tolist(), final_points=score[order].tolist(),
                            tie_energy=np.asarray(end["final_energy"])[order].tolist(), won=end["winner"] == team,
                            decided_by=end["decided_by"], first_scoring_action_step=first,
                            last_lead_after_action=int(lead[-1]) if lead.size else None,
                            last_nonbehind_after_action=int(nonbehind[-1]) if nonbehind.size else None))
    if wins[order].tolist() != [row["our_wins"],row["opp_wins"]] or totals[order].tolist() != [
            row["our_points"],row["opp_points"]]:
        raise ValueError("Observer and official play_game totals disagree")
    # Treat runner speed separately. Match the game result and separately check the other summary columns.
    comparison = {k: dict(current=row[k], historical=float(reference[k])) for k in reference
                  if k not in ("seed","side","opponent","secs")}
    mismatches = [k for k, v in comparison.items() if abs(float(v["current"]) - v["historical"]) > 1e-10]
    return dict(seed=int(row["seed"]), side=row["side"], matches=matches, compared=comparison,
                outcome_reproduced=not any(k in OUTCOMES for k in mismatches),
                discrepant_metrics=mismatches)


def main():
    from luxai_s3 import env as engine
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game
    from scripts.experiment import limit_threads
    from scripts.par_eval import build_cfg, require_no_agent_errors

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if sha(SOURCE) != SOURCE_SHA or sha(WEIGHTS) != V14_SHA:
        raise ValueError("Historical data or V14 identity changed")
    with SOURCE.open() as f:
        original = {(int(r["seed"]),r["side"]):r for r in csv.DictReader(f)
                    if r["opponent"] == "solution92" and (int(r["seed"]),r["side"]) in KEYS}
    if set(original) != set(KEYS):
        raise ValueError("Four historical references required")
    args.out.mkdir(parents=True, exist_ok=False)
    limit_threads()
    env = LuxAIS3GymEnv(numpy_output=True)
    observer = ScoreObserver(env)
    agent = Agent_x("player_0", agent_path=str(WEIGHTS), cfg=build_cfg(str(WEIGHTS), []), train=False, seed=0)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    games = []
    try:
        for seed, side in KEYS:
            opp = make_opponent("solution92", f"player_{1-int(side[-1])}")
            row = play_game(observer, agent, opp, seed, side, train=False)
            require_no_agent_errors(agent, opp)
            summary = game_summary(observer.frames, row, original[seed,side])
            trace = args.out / f"{seed}_{side}.jsonl.gz"
            with gzip.open(trace, "xt") as stream:
                for frame in observer.frames:
                    stream.write(json.dumps(frame, separators=(",",":")) + "\n")
            summary.update(trace=trace.name, trace_sha256=sha(trace))
            games.append(summary)
            print(seed, side, "outcome reproduced:", summary["outcome_reproduced"],
                  "mismatches:", summary["discrepant_metrics"], flush=True)
    finally:
        env.close()
    result = dict(outcome_reproduced=all(g["outcome_reproduced"] for g in games), games=games,
                  trace_team_order=["player_0","player_1"], summary_team_order=["V14","Solution_92"],
                  action_step="Pre-step match_steps, 0 through 100; points_after includes that action.",
                  v14_sha256=V14_SHA, historical_sha256=SOURCE_SHA, engine_sha256=sha(Path(engine.__file__)))
    with (args.out/"summary.json").open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    if not result["outcome_reproduced"]:
        raise SystemExit("Results preserved; at least one historical game outcome differs")


if __name__ == "__main__":
    main()
