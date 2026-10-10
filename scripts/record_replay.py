"""Ein bestimmtes Spiel erneut spielen und als Replay speichern (fuer die Praesi).

    python -m scripts.record_replay --run experiments/runs/20261010_full_s0 \
        --opponent default --seed 900003 --side player_1 --name bester_sieg

Die Testspiele sind deterministisch (Seeds + eps=0), das Replay zeigt also
genau das Spiel aus eval.csv. Ohne --seed/--side wird automatisch gewaehlt:
  --pick best    hoechste Punktedifferenz unter den Siegen
  --pick typical Niederlage mit Median-Punktedifferenz
Ansehen: https://s3vis.lux-ai.org/ (JSON-Datei hochladen).
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import pandas as pd

from scripts.common import ROOT, make_opponent, play_game
from scripts.experiment import Learners

OUT = ROOT / "docs" / "presentation" / "replays"


def pick_game(run: Path, opponent: str, how: str):
    e = pd.read_csv(run / "eval.csv")
    e = e[e["opponent"] == opponent].assign(pdiff=lambda d: d.our_points - d.opp_points)
    if how == "best":
        pool = e[e.game_win == 1].sort_values("pdiff", ascending=False)
        if pool.empty:
            pool = e.sort_values("pdiff", ascending=False)
        row = pool.iloc[0]
    else:
        pool = e[e.result == 0].sort_values("pdiff")
        if pool.empty:
            pool = e.sort_values("pdiff")
        row = pool.iloc[len(pool) // 2]
    return int(row.seed), str(row.side), row


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--opponent", default="default", choices=["default", "solution92"])
    ap.add_argument("--seed", type=int)
    ap.add_argument("--side", choices=["player_0", "player_1"])
    ap.add_argument("--pick", choices=["best", "typical"], default="best")
    ap.add_argument("--name", default=None)
    args = ap.parse_args()

    from luxai_s3.wrappers import LuxAIS3GymEnv, RecordEpisode

    run = Path(args.run)
    man = json.loads((run / "manifest.json").read_text())
    if args.seed is None or args.side is None:
        seed, side, row = pick_game(run, args.opponent, args.pick)
        print(f"gewaehlt ({args.pick}): seed {seed} {side}: {row.our_wins}-{row.opp_wins}, "
              f"Punkte {row.our_points}:{row.opp_points}")
    else:
        seed, side = args.seed, args.side

    learners = Learners(man["variant"], run, man["run_seed"], load=True)
    learners.eval_mode()
    with tempfile.TemporaryDirectory() as tmp:
        env = RecordEpisode(LuxAIS3GymEnv(numpy_output=True), save_dir=tmp,
                            save_on_close=True, save_on_reset=False)
        opp_side = "player_1" if side == "player_0" else "player_0"
        r = play_game(env, learners.agents[side], make_opponent(args.opponent, opp_side),
                      seed, side, train=False)
        env.close()
        src = next(Path(tmp).glob("*.json"))
        j = json.loads(src.read_text())
        names = {side: f"sherlock[{man['variant']}]", opp_side: args.opponent}
        j.setdefault("metadata", {})["players"] = names
        OUT.mkdir(parents=True, exist_ok=True)
        name = args.name or f"{run.name}_{args.opponent}_{seed}_{side}"
        dst = OUT / f"{name}.json"
        dst.write_text(json.dumps(j))
    print(f"{r['our_wins']}-{r['opp_wins']} Punkte {r['our_points']}:{r['opp_points']} -> {dst} "
          f"({dst.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
