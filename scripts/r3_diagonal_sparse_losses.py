"""Replay both Solution defeats from the independent two-view panel on their shared map."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

SEED = 7286137
PANEL = Path("experiments/analysis/movement_reflection_20261115")
CHECKPOINT = Path("experiments/candidates/movement_dagger_20261115/r3_soft.pth")
SCORE = {"result":"game_win","wins":"our_wins","losses":"opp_wins","points":"our_points",
         "opp_points":"opp_points","steps":"steps"}
SEATS = ("player_0", "player_1")


def losses(repo):
    prior = {}
    for arm in ("diagonal", "v14"):
        file = repo / PANEL / "confirm" / arm / "games.jsonl"
        rows = [json.loads(line) for line in file.read_text().splitlines()]
        assert len(rows) == 240
        solution = [row for row in rows if row["opponent"] == "solution92"]
        if arm == "diagonal":
            assert {(r["seed"],r["side"]) for r in solution if not r["result"]} == {(SEED,s) for s in SEATS}
        prior[arm] = {r["side"]:r for r in solution if r["seed"] == SEED}
    return prior


def run(args):
    import torch
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts import final_battle_compare as battle
    from scripts.common import make_opponent, play_game
    from scripts.experiment import limit_threads
    from scripts.par_eval import require_no_agent_errors
    from scripts.solution_passive import ScoreObserver, game_summary

    limit_threads()
    torch.manual_seed(0)
    prior = losses(args.repo)
    if args.arm in ("v14", "diagonal"):
        from scripts import r3_diagonal_games as original
        model = args.repo / CHECKPOINT
        options = SimpleNamespace(archive=args.repo / PANEL / "paired_validation.json", model=model)
        source = original.manifest(options, "confirm", args.arm)
        recorded = json.loads((args.repo/PANEL/"confirm"/args.arm/"manifest.json").read_bytes())
        if source != recorded:
            raise ValueError("Different original independent confirmation actor")
        policy = "v14" if args.arm == "v14" else "selective_movement"
        battle.POLICIES[policy] = original.ACTORS[args.arm]
        battle.init_worker(policy, None if args.arm == "v14" else str(model))
        player, env = battle.evaluate.agent, battle.evaluate.env
    else:
        from scripts.r3_v4_contact_study import binding
        from scripts.r3_v4_contact_agent import make_r3, make_v4
        source, _ = binding(args.repo)
        player = (make_r3 if args.arm == "r3" else make_v4)(SEATS[0])
        env = LuxAIS3GymEnv(numpy_output=True)
    try:
        for index, side in enumerate(SEATS):
            observer = ScoreObserver(env)
            opponent = make_opponent("solution92", SEATS[1-index])
            result = play_game(observer, player, opponent, SEED, side, False)
            require_no_agent_errors(player,opponent)
            if args.arm == "v4":
                require_no_agent_errors(player.v14, player.student)
            expected = {dest: prior[args.arm][side][key] for key,dest in SCORE.items()} if args.arm in prior else {}
            if any(result[name] != value for name,value in expected.items()):
                raise ValueError("Parent failed to reproduce its archived score")
            summary = game_summary(observer.frames, result, expected)
            assert len(observer.frames) == 303 and len(summary["matches"]) == 3
            label = args.arm+"_"+side
            timeline = gzip.compress(json.dumps(observer.frames,separators=(",",":")).encode(),mtime=0)
            (args.out/(label+".json.gz")).write_bytes(timeline)
            report = dict(arm=args.arm, seed=SEED, side=side, score={k:result[k] for k in SCORE.values()},
                          source=source, matched_prior=bool(expected), matches=summary["matches"],
                          timeline_sha256=hashlib.sha256(timeline).hexdigest())
            (args.out/(label+".json")).write_text(json.dumps(report,indent=2)+"\n")
            print(label,report["score"],flush=True)
    finally:
        env.close()


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm", choices=("v14","diagonal","r3","v4"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    run(args)
