"""Messe frühes öffentliches Kartenwissen und Ein-Schritt-Besetzungen in 16 Archivpartien."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from replays import MatchRecord, PACKAGES, limit_threads, make_opponent, play_game, r3_package_agent
from scripts.scoring import point_tile_map

DIRS = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))
MIRROR = (0, 2, 1, 4, 3)


def measure_options(obs, side, inner, actions, old_true):
    team = int(side[-1])
    mirror = inner.belief.mirrored
    known = np.asarray(inner.belief.point_tiles, dtype=bool)
    if mirror:
        known = known[::-1, ::-1].T
    sensor = np.asarray(obs["sensor_mask"], dtype=bool)
    alive = np.asarray(obs["units_mask"]) & (np.asarray(obs["units"]["energy"]).reshape(2, -1) >= 0)
    pos = np.asarray(obs["units"]["position"])
    own = {tuple(p) for p in pos[team, alive[team]]}
    enemy = {tuple(p) for p in pos[1 - team, alive[1 - team]]}
    visible_empty = {tuple(p) for p in np.argwhere(known & sensor)} - own - enemy
    stats = Counter(frames=1, known=int(known.sum()), known_true=int((known & old_true).sum()),
                    known_occupied=sum(bool(known[p]) for p in own), known_visible_free=len(visible_empty),
                    actual_occupied=sum(bool(old_true[p]) for p in own))
    adjacent, legal, ordered, safe_origin, terrain, affordable = (set() for _ in range(6))
    if not alive[team].any():
        return stats, legal, ordered
    cache = inner._cache
    if cache is None or cache[0] != int(obs["steps"]):
        raise ValueError("Aktuelle originale Aktionsmaske nicht im Cache")
    _, ctx, _, _, masks, _ = cache
    for uid in np.flatnonzero(alive[team]):
        x, y = map(int, pos[team, uid])
        if known[x, y]:
            continue
        cp = np.asarray(ctx["ally_pos"][uid])
        expected = np.array((len(known)-1-y, len(known)-1-x) if mirror else (x, y))
        if not np.array_equal(cp, expected):
            raise ValueError("Fehler bei der Sitztransformation")
        for direction, (dx, dy) in enumerate(DIRS[1:], start=1):
            p = (x + dx, y + dy)
            if p not in visible_empty:
                continue
            adjacent.add(p)
            canon_p = (len(known)-1-p[1], len(known)-1-p[0]) if mirror else p
            if ctx["passable"][canon_p]:
                terrain.add(p)
                if ctx["ally_ene"][uid] >= ctx["move_cost"]:
                    affordable.add(p)
            canon_dir = MIRROR[direction] if mirror else direction
            if masks[uid][canon_dir]:
                legal.add(p)
                if not old_true[x, y]:
                    safe_origin.add(p)
                if int(actions[uid][0]) == direction:
                    ordered.add(p)
    stats.update(adjacent=len(adjacent), passable=len(terrain), affordable=len(affordable),
                 legal=len(legal), actual_non_scoring_origin=len(safe_origin), ordered=len(ordered))
    return stats, legal, ordered


class PublicRecord(MatchRecord):
    def __init__(self, env, side, agent, arm):
        super().__init__(env)
        self.side = side
        self.inner = agent._actor if arm == "r3" else agent._imitation
        self.by_match = [[Counter() for _ in range(3)] for _ in range(3)]

    def reset(self, **kwargs):
        obs, info = super().reset(**kwargs)
        self.all_obs = obs
        return obs, info

    def step(self, actions):
        n = len(self.frames)
        m, t = divmod(n, 101)
        obs = self.all_obs[self.side]
        if t != int(obs["match_steps"]):
            raise ValueError("Unerwartete Zugnummer")
        if 1 <= t <= 70:
            stats, legal, ordered = measure_options(obs, self.side, self.inner, actions[self.side],
                                                   point_tile_map(self.env.state))
        result = super().step(actions)
        self.all_obs = result[0]
        if 1 <= t <= 70:
            scored = self.frames[-1][int(self.side[-1])]
            stats.update(legal_scored=len(legal & scored), ordered_scored=len(ordered & scored))
            self.by_match[m][int(t > 30) + int(t > 50)].update(stats)
        return result


def run(arm, out):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    limit_threads()
    pkg, sha = PACKAGES[arm]
    if hashlib.sha256(pkg.read_bytes()).hexdigest() != sha:
        raise ValueError("Abweichendes Abgabepaket")
    previous = json.loads((HERE.parent / "replays.json").read_text())
    env = LuxAIS3GymEnv(numpy_output=True)
    games = []
    for ref in previous["arms"][arm]:
        seed, side = ref["seed"], ref["side"]
        agent = r3_package_agent(side, pkg)
        opponent = make_opponent("solution92", "player_1" if side == "player_0" else "player_0")
        tape = PublicRecord(env, side, agent, arm)
        actual = play_game(tape, agent, opponent, seed, side, train=False)
        if not (ref["verified"] and len(tape.frames) == 303 and
                all(actual[k] == v for k, v in ref["expected"].items())):
            raise ValueError(f"Abweichendes Ergebnis bei {arm}/{seed}")
        if tape.match_winners != [int(side[-1]) if r["win"] else 1-int(side[-1]) for r in ref["matches"]]:
            raise ValueError("Matchausgang weicht ab")
        for idx, ms in enumerate(tape.by_match):
            if [b["frames"] for b in ms] != [30, 20, 20]:
                raise ValueError("Fehlende Zugdaten")
            for b in ms:
                order = [b[k] for k in ("known_visible_free", "adjacent", "passable", "affordable", "legal", "ordered", "ordered_scored")]
                if any(a < c for a, c in zip(order, order[1:])):
                    raise ValueError("Inkonsistente Erreichbarkeit")
        games.append({"seed": seed,"side": side,"group": ref["expected_outcome_group"],
                      "win": [m["win"] for m in ref["matches"]], "match_blocks": tape.by_match})
        print(arm, seed, side, "OK", flush=True)
    out.write_text(json.dumps(games) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", choices=PACKAGES)
    p.add_argument("--out", type=Path, default=HERE / "daten.json")
    args = p.parse_args()
    if args.arm:
        return run(args.arm, args.out)
    with tempfile.TemporaryDirectory() as td:
        data = {}
        for a in PACKAGES:
            path = Path(td) / (a + ".json")
            subprocess.run([sys.executable, __file__, "--arm", a, "--out", str(path)], check=True)
            data[a] = json.loads(path.read_text())
    args.out.write_text(json.dumps({"blocks": [[1,30],[31,50],[51,70]], "arms": data}, indent=2) + "\n")


if __name__ == "__main__":
    main()
