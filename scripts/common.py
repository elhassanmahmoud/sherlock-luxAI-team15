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
        from agents.team_lux.main import Agent_x
        opp = Agent_x(player, agent_path=self_play_path, name="Self-Play Snapshot", train=False)
        opp.set_to_eval_mode()
        return opp
    raise ValueError(f"Unbekannter Gegner `{kind}`. Erlaubt: {OPPONENTS}")


def play_game(env, agent, opp, seed: int, our_side: str, train: bool) -> dict:
    """Ein komplettes Spiel (3 Matches). Gibt Statistiken zurueck."""
    opp_side = "player_1" if our_side == "player_0" else "player_0"
    t0 = time.time()

    if hasattr(agent, "new_game"):
        agent.new_game(our_side)
    if hasattr(opp, "new_game"):
        opp.new_game(opp_side)

    obs, info = env.reset(seed=seed)
    env_cfg = info["params"]
    for a in (agent, opp):
        if hasattr(a, "set_env_cfg"):
            a.set_env_cfg(env_cfg)

    step = 0
    done = False
    last_obs = obs
    # Punkte werden pro Match zurueckgesetzt -> Matchmaxima aufsummieren
    totals = [0, 0]
    cur = [0, 0]
    while not done:
        actions = {
            our_side: agent.act(step=step, obs=obs[our_side]),
            opp_side: opp.act(step=step, obs=obs[opp_side]),
        }
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
        pts_now = np.asarray(next_obs[our_side]["team_points"]).tolist()
        for t in (0, 1):
            if pts_now[t] < cur[t]:          # neues Match begonnen
                totals[t] += cur[t]
            cur[t] = int(pts_now[t])
        obs = next_obs
        last_obs = next_obs
        step += 1
    totals = [totals[t] + cur[t] for t in (0, 1)]

    o = last_obs[our_side]
    team = 0 if our_side == "player_0" else 1
    wins = np.asarray(o["team_wins"]).tolist()
    our_w, opp_w = int(wins[team]), int(wins[1 - team])
    result = 1.0 if our_w > opp_w else (0.0 if our_w < opp_w else 0.5)
    return dict(
        seed=seed, side=our_side, steps=step,
        our_wins=our_w, opp_wins=opp_w,
        our_points=int(totals[team]), opp_points=int(totals[1 - team]),
        result=result, secs=round(time.time() - t0, 2),
        known_point_tiles=int(agent.belief.point_tiles.sum()) if hasattr(agent, "belief") else 0,
        relics_found=len(agent.belief.relic_positions) if hasattr(agent, "belief") else 0,
    )
