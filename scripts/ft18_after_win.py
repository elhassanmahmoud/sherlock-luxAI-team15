"""Lock the late FT18 movement choice to our public first-match outcome."""
import csv
from pathlib import Path

from agents.sherlock.main import Agent_x
from scripts.ft18_movement import FT18MovementAgent
from scripts.solution_passive import ROOT, sha


REFERENCE = ROOT / "experiments/analysis/final_battle_20261103/performance_confirmation/confirmation/baseline_panel.csv"
REFERENCE_SHA = "bc281d528a10acbd22c8156db68dc0bf7a1afd7b0ac6354e30b6449b60295847"
SIDES = ("player_0", "player_1")


class FT18AfterWinAgent(FT18MovementAgent):
    def _reset_study(self):
        super()._reset_study()
        self.first_won = None

    def _act(self, step, obs):
        # At the start of match two, including its reset frame, only the first result is known.
        if self.first_won is None and sum(obs["team_wins"]) == 1:
            self.first_won = bool(obs["team_wins"][self.team_id])
        return super()._act(step, obs)

    def _network_values(self, features):
        if self.first_won:
            return super()._network_values(features)
        return Agent_x._network_values(self, features)

    def _policy_greedy(self, ctx, ids, masks, greedy):
        if self.first_won:
            return super()._policy_greedy(ctx, ids, masks, greedy)
        return Agent_x._policy_greedy(self, ctx, ids, masks, greedy)


def reference_panel(path=REFERENCE):
    if sha(path) != REFERENCE_SHA:
        raise ValueError("Historical V14 baseline changed")
    with Path(path).open() as stream:
        rows = [r for r in csv.DictReader(stream) if r["opponent"] == "solution92"]
    lookup = {(int(r["seed"]),r["side"]):r for r in rows}
    seeds = range(852000,852400)
    if len(lookup)!=len(rows) or set(lookup)!={(s,p) for s in seeds for p in SIDES}:
        raise ValueError("Historical reference is incomplete")
    losses = {s for s in seeds if any(lookup[s,p]["game_win"]=="0" for p in SIDES)}
    selected = sorted([s for s in seeds if s in losses][:12] + [s for s in seeds if s not in losses][:12])
    if len(selected)!=24:
        raise ValueError("Expected 12 historical loss maps and 12 protection maps")
    return {(s,p):lookup[s,p] for s in selected for p in SIDES}
