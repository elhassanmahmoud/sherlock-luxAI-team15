"""One opt-in test on published R3: progress toward this unit's assigned confirmed target."""
import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock.rules import PathCache
from scripts.combat_teacher_counterfactual import live_ids, native_order
from scripts.selective_advice_agent import SelectiveAdviceAgent


def canonical_end(pos, world_action, mirrored, shape):
    direction = geo.mirror_dir(world_action) if mirrored else world_action
    return (int(np.clip(pos[0] + geo.DIR_DX[direction], 0, shape[0] - 1)),
            int(np.clip(pos[1] + geo.DIR_DY[direction], 0, shape[1] - 1)))


def proposals(actor, obs, base, advice):
    ctx = actor._prev_ctx
    if (ctx is None or ctx["match_idx"] not in (1, 2) or ctx["match_step"] == 0 or ctx["own_points"] != 0
            or not np.any(ctx["point_tiles"])):
        return []
    team = actor.team_id
    energies = np.asarray(obs["units"]["energy"])[team].reshape(-1)
    positions = np.asarray(obs["units"]["position"])[team]
    tiles = np.asarray(obs["map_features"]["tile_type"])
    mirrored = actor.belief.mirrored
    events = []
    for uid in map(int, live_ids(obs, team)):
        v14, r3 = int(base[uid, 0]), int(advice[uid, 0])
        target = ctx["assigned"].get(uid)
        if target is None or v14 not in range(1, 5) or r3 not in range(5) or v14 == r3:
            continue
        target = tuple(map(int, target))
        if (not all(0 <= c < n for c, n in zip(target, tiles.shape)) or
                not ctx["point_tiles"][target] or not ctx["passable"][target]):
            continue
        # Only an R3 order the native substitute would actually play is a possible reversion.
        if any(not native_order(plan[uid], positions[uid], energies[uid], actor.env_cfg, tiles)
               for plan in (base, advice)):
            continue
        pos = tuple(map(int, ctx["ally_pos"][uid]))
        dist = actor.route_paths.get(ctx["step"], ctx["passable"], target)
        base_end = canonical_end(pos, v14, mirrored, dist.shape)
        r3_end = canonical_end(pos, r3, mirrored, dist.shape)
        start, with_v14, with_r3 = map(int, (dist[pos], dist[base_end], dist[r3_end]))
        if not (0 <= with_v14 < start <= with_r3):
            continue
        world_goal = geo.mirror_xy(*target, *dist.shape) if mirrored else target
        events.append(dict(step=ctx["step"], match=ctx["match_idx"] + 1, match_step=ctx["match_step"], uid=uid,
                           world_origin=positions[uid].tolist(), world_target=list(world_goal),
                           distances=[start, with_v14, with_r3], v14_world=base[uid].tolist(),
                           r3_world=advice[uid].tolist(), energy=int(energies[uid])))
    return events


class RestartRouteAgent(SelectiveAdviceAgent):
    restore = False

    def _reset_episode_state(self):
        super()._reset_episode_state()
        self.route_events = []
        # Use V14's exact four-neighbour shortest paths without mutating its ordinary policy cache.
        self.route_paths = PathCache()

    def _finish_advice(self, obs, base, advice):
        events = proposals(self, obs, base, advice)
        if events and self.restore:
            advice = advice.copy()
            for e in events:
                advice[e["uid"]] = base[e["uid"]]
        # Exactly one normal legality/bookkeeping pass, followed by normal _act_est.remember.
        played = super()._finish_advice(obs, base, advice)
        for e in events:
            e["applied"] = bool(self.restore)
            if played[e["uid"]].tolist() != e["v14_world" if self.restore else "r3_world"]:
                raise ValueError("Registered reversion differs from the final world order")
        self.route_events.extend(events)
        return played
