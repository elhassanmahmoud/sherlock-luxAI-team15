"""Gegner mit anderen Spielweisen fuer Robustheitstests (22.10.2026, nur Auswertung, kein Training).

Andere Teams bauen vermutlich auf denselben Kursvorlagen auf (Solution_92, Prof-DQN). Deshalb:

- `Sol92Variant(square=True)`: wie Solution_92, schiesst aber im ganzen Sap-Quadrat (Chebyshev, so
  wie die Engine es erlaubt) statt nur in der Manhattan-Raute.
- `Sol92Variant(weakest=True)`: wie Solution_92, zielt aber auf den schwaechsten Gegner in Reichweite
  (Abschuesse) statt auf den mit der hoechsten ID.
- `RushBot`: einfache Regel-KI, laeuft mit allen Units in die gegnerische Haelfte und sappt jeden
  sichtbaren Gegner im Sap-Quadrat (der schwaechste zuerst).
"""
from __future__ import annotations

import numpy as np

from agents.Solution_92_Kaggle.agent import Agent as Sol92Agent
from agents.Solution_92_Kaggle.agent import Node
from agents.Solution_92_Kaggle.base import ActionType, Global
from agents.Solution_92_Kaggle.pathfinding import (
    astar,
    create_weights,
    estimate_energy_cost,
    find_closest_target,
    path_to_actions,
)


class Sol92Variant(Sol92Agent):
    """Solution_92 mit geaenderter Sap-Zielwahl der Sammler (sonst unveraendert)."""

    def __init__(self, player: str, square: bool = False, weakest: bool = False) -> None:
        super().__init__(player)
        self.square = square
        self.weakest = weakest
        self.name = "Solution_92" + ("_sq" if square else "") + ("_weak" if weakest else "")

    def _dist(self, a, b) -> int:
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        return max(dx, dy) if self.square else dx + dy

    def harvest(self):
        def set_task(ship, target_node):
            if ship.node == target_node:
                best = None
                if ship.energy >= Global.UNIT_SAP_COST:
                    for enemy in self.opp_fleet.ships:
                        if enemy.node is None:
                            continue
                        if self._dist(ship.coordinates, enemy.node.coordinates) > Global.UNIT_SAP_RANGE:
                            continue
                        if best is None or not self.weakest or enemy.energy < best.energy:
                            best = enemy  # Original: letzter Gegner in Reichweite
                if best is not None:
                    ship.task = "sap"
                    ship.target = Node(best.node.x - ship.coordinates[0], best.node.y - ship.coordinates[1])
                    ship.action = ActionType.sap
                else:
                    ship.task = "harvest"
                    ship.target = target_node
                    ship.action = ActionType.center
                return True

            path = astar(create_weights(self.space), start=ship.coordinates, goal=target_node.coordinates)
            energy = estimate_energy_cost(self.space, path)
            actions = path_to_actions(path)
            if not actions or ship.energy < energy:
                return False
            ship.task = "harvest"
            ship.target = target_node
            ship.action = actions[0]
            return True

        booked_nodes = set()
        for ship in self.fleet:
            if ship.task == "sap":
                ship.task = "harvest"
                ship.target = Node(ship.coordinates[0], ship.coordinates[1])
                booked_nodes.add(ship.target)
            if ship.task == "harvest":
                if ship.target is None:
                    ship.task = None
                    continue
                if set_task(ship, ship.target):
                    if ship.task == "sap":
                        booked_nodes.add(Node(ship.coordinates[0], ship.coordinates[1]))
                    else:
                        booked_nodes.add(ship.target)
                else:
                    ship.task = None
                    ship.target = None

        targets = set()
        for n in self.space.reward_nodes:
            if n.is_walkable and n not in booked_nodes:
                targets.add(n.coordinates)
        if not targets:
            return
        for ship in self.fleet:
            if ship.task:
                continue
            target, _ = find_closest_target(ship.coordinates, targets)
            if target and set_task(ship, self.space.get_node(*target)):
                targets.remove(target)
            else:
                ship.task = None
                ship.target = None


class RushBot:
    """Laeuft in die gegnerische Haelfte und sappt alles im Sap-Quadrat (schwaechster zuerst)."""

    DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # up right down left -> Aktion 1..4

    def __init__(self, player: str) -> None:
        self.player = player
        self.team_id = 0 if player == "player_0" else 1
        self.name = "RushBot"
        self.env_cfg = None
        self.rng = np.random.default_rng(0)

    def set_env_cfg(self, env_cfg) -> None:
        self.env_cfg = env_cfg

    def act(self, step: int, obs, remainingOverageTime: int = 60):
        cfg = self.env_cfg or {}
        n = int(cfg.get("max_units", 16))
        W, H = int(cfg.get("map_width", 24)), int(cfg.get("map_height", 24))
        R, cost = int(cfg.get("unit_sap_range", 4)), int(cfg.get("unit_sap_cost", 40))
        move = int(cfg.get("unit_move_cost", 2))
        actions = np.zeros((n, 3), dtype=int)
        me, op = self.team_id, 1 - self.team_id
        pos = np.asarray(obs["units"]["position"])
        ene = np.asarray(obs["units"]["energy"])
        mask = np.asarray(obs["units_mask"]).astype(bool)
        tiles = np.asarray(obs["map_features"]["tile_type"])
        goal = (W - 1, H - 1) if me == 0 else (0, 0)
        enemies = [(int(pos[op][j][0]), int(pos[op][j][1]), int(ene[op][j])) for j in np.nonzero(mask[op])[0]]
        for i in np.nonzero(mask[me])[0]:
            x, y, e = int(pos[me][i][0]), int(pos[me][i][1]), int(ene[me][i])
            if e >= cost:
                inr = [t for t in enemies if max(abs(t[0] - x), abs(t[1] - y)) <= R]
                if inr:
                    tx, ty, _ = min(inr, key=lambda t: t[2])
                    actions[i] = [5, tx - x, ty - y]
                    continue
            if e < move:
                continue
            tgt = min(enemies, key=lambda t: abs(t[0] - x) + abs(t[1] - y))[:2] if enemies else goal
            best, best_d = 0, abs(tgt[0] - x) + abs(tgt[1] - y)
            for k, (dx, dy) in enumerate(self.DIRS, start=1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H and tiles[nx, ny] != 2:
                    d = abs(tgt[0] - nx) + abs(tgt[1] - ny) + self.rng.random() * 0.1
                    if d < best_d:
                        best, best_d = k, d
            actions[i] = [best, 0, 0]
        return actions
