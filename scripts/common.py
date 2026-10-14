"""Gemeinsame Bausteine fuer Training und Evaluation.

Wichtig: Wir nutzen das Env DIREKT (LuxAIS3GymEnv) statt lux/runner.py, weil der
Runner pro Spiel neue Agenten erzeugt und save_agent() VOR dem Spiel aufruft -
damit wuerde nie etwas Gelerntes gespeichert und Replay Buffer/Epsilon waeren
nach jedem Spiel weg (siehe CLAUDE.md, "Bekannte Probleme im Template").
"""
from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

import numpy as np

from scripts.scoring import POINT_COUNTING_VERSION, match_points_after_step

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OPPONENTS = ("default", "solution92", "dqn", "random", "self")


class RandomAgent:
    """Trivialer Gegner (Sanity-Check / Aufwaermen)."""

    def __init__(self, player: str, name: str = "RandomAgent") -> None:
        self.player = player
        self.name = name
        self.team_id = 0 if player == "player_0" else 1
        self.env_cfg = {"max_units": 16}
        self.rng = np.random.default_rng(0)

    def set_env_cfg(self, env_cfg) -> None:
        self.env_cfg = env_cfg

    def act(self, step: int, obs) -> np.ndarray:
        n = int(self.env_cfg["max_units"])
        a = np.zeros((n, 3), dtype=int)
        a[:, 0] = self.rng.integers(0, 5, size=n)
        return a


_SOL92_DEFAULTS = None


def _reset_solution92() -> None:
    """Solution_92 haelt seinen Zustand in Klassenvariablen (Global.*), die
    zwischen Spielen NICHT zurueckgesetzt werden. Ohne Reset wachsen
    Global.REWARD_RESULTS unbegrenzt und alte Relic-Infos verfaelschen das
    naechste Spiel."""
    global _SOL92_DEFAULTS
    from agents.Solution_92_Kaggle.base import Global

    if _SOL92_DEFAULTS is None:
        _SOL92_DEFAULTS = {
            k: copy.deepcopy(v)
            for k, v in vars(Global).items()
            if not k.startswith("__") and not callable(v)
        }
    for k, v in _SOL92_DEFAULTS.items():
        setattr(Global, k, copy.deepcopy(v))


def make_opponent(kind: str, player: str, self_play_path: str | None = None):
    """Gegner erzeugen. `self` laedt einen eingefrorenen Snapshot unseres Agenten."""
    if kind == "default":
        from agents.default.default import DefaultAgent
        return DefaultAgent(player)
    if kind == "solution92":
        _reset_solution92()
        from agents.Solution_92_Kaggle.agent import Agent
        return Agent(player)
    if kind == "dqn":
        from agents.DQN.main import Agent
        return Agent(player, agent_path="agents/DQN/agent.pth")
    if kind == "random":
        return RandomAgent(player)
    if kind == "self":
        from agents.sherlock.main import Agent_x
        opp = Agent_x(player, agent_path=self_play_path, name="Self-Play Snapshot", train=False)
        opp.set_to_eval_mode()
        return opp
    raise ValueError(f"Unbekannter Gegner `{kind}`. Erlaubt: {OPPONENTS}")


def play_game(env, agent, opp, seed: int, our_side: str, train: bool) -> dict:
    """Ein komplettes Spiel (3 Matches). Gibt Ergebnis + Kennzahlen zurueck.

    Globale Zufallsquellen (np.random/random - genutzt von default und Prof-DQN)
    werden mit dem Spiel-Seed gesetzt, damit jedes Spiel reproduzierbar ist.
    """
    import random

    from scripts.metrics import GameTracker

    opp_side = "player_1" if our_side == "player_0" else "player_0"
    t0 = time.time()

    if hasattr(agent, "new_game"):
        agent.new_game(our_side)
    if hasattr(opp, "new_game"):
        opp.new_game(opp_side)

    random.seed(seed)
    np.random.seed(seed % (2**32))
    obs, info = env.reset(seed=seed)
    env_cfg = info["params"]
    for a in (agent, opp):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(env_cfg)
    team = 0 if our_side == "player_0" else 1
    tracker = GameTracker(team, env_cfg)

    step = 0
    done = False
    last_obs = obs
    totals = np.zeros(2, dtype=np.int64)
    while not done:
        actions = {
            our_side: agent.act(step=step, obs=obs[our_side]),
            opp_side: opp.act(step=step, obs=obs[opp_side]),
        }
        tracker.record(obs[our_side], actions[our_side])
        next_obs, reward, terminated, truncated, info = env.step(actions)
        done = bool(np.asarray(terminated[our_side])) or bool(np.asarray(truncated[our_side]))
        if train and hasattr(agent, "update"):
            agent.update(
                step=step,
                obs=obs[our_side],
                reward=float(np.asarray(reward[our_side]).reshape(-1)[0]),
                action=actions[our_side],
                terminated=done,
                next_obs=next_obs[our_side],
            )
        points = match_points_after_step(obs[our_side], next_obs[our_side], info)
        totals += points - np.asarray(obs[our_side]["team_points"])
        obs = next_obs
        last_obs = next_obs
        step += 1

    o = last_obs[our_side]
    wins = np.asarray(o["team_wins"]).tolist()
    our_w, opp_w = int(wins[team]), int(wins[1 - team])
    result = 1.0 if our_w > opp_w else (0.0 if our_w < opp_w else 0.5)
    our_p, opp_p = int(totals[team]), int(totals[1 - team])
    row = dict(
        seed=seed, side=our_side, steps=step,
        our_wins=our_w, opp_wins=opp_w,
        our_points=our_p, opp_points=opp_p,
        point_counting_version=POINT_COUNTING_VERSION,
        result=result,
        game_win=int(our_w > opp_w),
        point_win=1.0 if our_p > opp_p else (0.0 if our_p < opp_p else 0.5),
        secs=round(time.time() - t0, 2),
    )
    row.update(tracker.summary())
    extra = agent.episode_stats() if hasattr(agent, "episode_stats") else {}
    row["relics_found"] = extra.get("relics_found", row["relics_seen"])
    row["known_point_tiles"] = extra.get("known_point_tiles", float("nan"))
    row["greedy_masked_frac"] = extra.get("greedy_masked_frac", float("nan"))
    row["belief_contradictions"] = extra.get("belief_contradictions", float("nan"))
    return row
