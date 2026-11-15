"""One fixed, paired Solution_92 development study. Run as python -m scripts.ft18_movement_study --out NEW_DIR."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.scoring import match_points_after_step
from scripts.solution_passive import ROOT, SOURCE, SOURCE_SHA, V14_SHA, WEIGHTS, sha

HISTORICAL_MANIFEST = ROOT / "experiments/analysis/final_battle_20261103/performance_confirmation/admission/candidate_manifest.json"
MANIFEST_SHA = "20d6b784a4ad94199642a386ee67793d5a008e413616ea66f87df28de9fa44b7"
SIDES = ("player_0", "player_1")
SEEDS = (7150000, 7150001, 7150002, 7150003, 7150004, 7150011, 7150035, 7150037, 7150045,
         7150052, 7150060, 7150067, 7150079, 7150096)


def references():
    if sha(SOURCE) != SOURCE_SHA:
        raise ValueError("Historical Dev A CSV changed")
    with SOURCE.open() as f:
        rows = [r for r in csv.DictReader(f) if r["opponent"] == "solution92"]
    keys = {(int(r["seed"]), r["side"]): r for r in rows}
    if len(keys) != len(rows) or set(keys) != {
            (s, side) for s in range(7150000, 7150100) for side in SIDES}:
        raise ValueError("Incomplete or duplicate Dev A Solution results")
    seeds = sorted({s for s, _ in keys})
    losses = [s for s in seeds if any(keys[s, side]["game_win"] == "0" for side in SIDES)]
    wins = [s for s in seeds if s not in losses][:4]
    if sorted(losses + wins) != list(SEEDS):
        raise ValueError("Historical panel selection differs from preregistered keys")
    return {(s, side): keys[s, side] for s in SEEDS for side in SIDES}


def provenance():
    from luxai_s3 import env as engine, wrappers
    if sha(HISTORICAL_MANIFEST) != MANIFEST_SHA or sha(WEIGHTS) != V14_SHA:
        raise ValueError("Historical roster or actual V14 weights differ")
    m = json.loads(HISTORICAL_MANIFEST.read_text())
    ft = m["candidates"]["FT18"]
    if (m["source_sha256"] != V14_SHA or ft["source_indices"] != list(range(18, 36))
            or ft["ordered_tensor_sha256"] != m["source_component_sha256"][18:]
            or ft["weighting"] != "equal 1/18" or ft["new_training"] or ft["replaced_indices"]):
        raise ValueError("FT18 roster cannot be linked to the pinned V14 checkpoint")
    paths = set((ROOT / "agents/sherlock").rglob("*.py")) | set((ROOT / "agents/Solution_92_Kaggle").rglob("*.py"))
    paths.update(ROOT / "scripts" / (name + ".py") for name in (
        "ft18_movement", "ft18_movement_study", "common", "scoring", "metrics", "par_eval", "experiment",
        "solution_passive", "protocol", "final_battle_candidates"))
    return dict(v14_sha256=V14_SHA, historical_csv_sha256=SOURCE_SHA, roster_manifest_sha256=MANIFEST_SHA,
                archived_ft18_sha256=ft["sha256"], indices=ft["source_indices"],
                tensor_sha256=m["source_component_sha256"], seeds=SEEDS, sides=SIDES,
                source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)},
                engine_sha256=sha(Path(engine.__file__)), wrapper_sha256=sha(Path(wrappers.__file__)),
                prefix_format="101 consecutive steps (0..100), player_0 then player_1, 16x3 little-endian int64 per team",
                comparison="Proposal matrix rows=V14, columns=FT18 in canonical action order. M1 native, not evaluated.")


def action_bytes(actions):
    chunks = []
    for side in SIDES:
        a = np.asarray(actions[side])
        if a.shape != (16,3) or not np.issubdtype(a.dtype, np.integer):
            raise ValueError("Unexpected submitted action shape or dtype")
        chunks.append(a.astype("<i8", copy=False).tobytes(order="C"))
    return b"".join(chunks)


class PrefixObserver:
    def __init__(self, env):
        self.env = env

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.before = obs["player_0"]
        self.digest = hashlib.sha256()
        self.n = 0
        self.final = None
        return obs, info

    def step(self, actions):
        if self.final is not None:
            return self.env.step(actions)
        if (int(self.before["steps"]) != self.n or int(self.before["match_steps"]) != self.n
                or np.asarray(self.before["team_wins"]).sum() != 0):
            raise ValueError("Unexpected pre-action position in first-match prefix")
        data = action_bytes(actions)  # copy the actual world commands, before the engine sees them
        result = self.env.step(actions)
        after, info = result[0]["player_0"], result[-1]
        self.digest.update(data)
        self.n += 1
        if int(after["match_steps"]) == 0:
            wins = np.asarray(after["team_wins"], int).tolist()
            if self.n != 101 or wins not in ([1,0],[0,1]):
                raise ValueError("First match did not award one win after 101 actions")
            points = match_points_after_step(self.before, after, info).tolist()
            self.final = dict(steps=self.n, actions_sha256=self.digest.hexdigest(),
                              points_world=points, wins_world=wins)
        self.before = after
        return result

    def first_match(self):
        if self.final is None:
            raise ValueError("Missing first-match endpoint")
        return self.final


def run(out):
    from agents.sherlock.main import Agent_x
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.common import make_opponent, play_game
    from scripts.experiment import limit_threads
    from scripts.final_battle_candidates import tensor_sha256
    from scripts.ft18_movement import FT18MovementAgent
    from scripts.par_eval import build_cfg, require_no_agent_errors

    limit_threads()
    history, manifest = references(), provenance()
    out.mkdir(parents=True, exist_ok=False)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    agents = {}
    for arm, cls in (("v14", Agent_x), ("ft18_movement", FT18MovementAgent)):
        agent = cls("player_0", agent_path=str(WEIGHTS), cfg=build_cfg(str(WEIGHTS), []), train=False, seed=0)
        agent.set_to_eval_mode()
        agent.autosave_on_terminate = False
        loaded = [tensor_sha256(m.state_dict()) for m in [agent.q, *agent.extra_q]]
        if loaded != manifest["tensor_sha256"] or agent.cnn_policy is not None:
            raise ValueError(f"{arm}: loaded policy differs from the historical ordered V14 roster")
        agents[arm] = agent
    env = LuxAIS3GymEnv(numpy_output=True)
    observer = PrefixObserver(env)
    try:
        with (out / "games.jsonl").open("x") as games, (out / "pairs.jsonl").open("x") as pairs:
            for (seed, side), expected in history.items():
                trial = {}
                for arm, agent in agents.items():
                    opp = make_opponent("solution92", SIDES[1-int(side[-1])])
                    row = play_game(observer, agent, opp, seed, side, train=False)
                    require_no_agent_errors(agent, opp)
                    mismatch = []
                    if arm == "v14":
                        mismatch = [k for k in expected if k not in {"seed","side","opponent","secs"}
                                    and not np.isclose(row[k], float(expected[k]), atol=1e-10, rtol=0)]
                    entry = dict(arm=arm, opponent="solution92", **row, first_match=observer.first_match(),
                                 interventions=0 if arm == "v14" else sum(
                                     r["before_rules_changed"] for r in agent.study_stats),
                                 movement_by_match=agent.movement_statistics() if arm != "v14" else [],
                                 historical_v14_differences=mismatch if arm == "v14" else None)
                    games.write(json.dumps(entry, allow_nan=False) + "\n")
                    games.flush()
                    trial[arm] = entry
                    if row["steps"] != 303 or mismatch:
                        raise ValueError(f"Invalid {arm} on {seed}/{side}: steps={row['steps']}, differences={mismatch}")
                b, a = trial.values()
                same = b["first_match"] == a["first_match"]
                pair = dict(seed=seed, side=side, same_first_match=same,
                            historical_v14={k: expected[k] for k in ("game_win","our_wins","opp_wins","our_points","opp_points")},
                            v14_result=b["result"], ft18_result=a["result"], interventions=a["interventions"])
                pairs.write(json.dumps(pair) + "\n")
                pairs.flush()
                if not same:
                    raise ValueError(f"First-match comparison failed for {seed}/{side}")
                print(seed, side, "paired", flush=True)
    finally:
        env.close()
    if provenance() != manifest:
        raise ValueError("A source changed during the study")
    (out / "completed.json").write_text(json.dumps(dict(games=2*len(history), pairs=len(history),
        games_sha256=sha(out/"games.jsonl"), pairs_sha256=sha(out/"pairs.jsonl"),
        manifest_sha256=sha(out/"manifest.json")), indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    run(parser.parse_args().out)
