"""Regeln vom 19.10.2026: relic_filter, subset_infer, BFS-Wege."""
import numpy as np

from agents.sherlock import geometry as geo
from agents.sherlock import rules
from agents.sherlock.belief import Belief


def _units(*tiles):
    pos = np.full((16, 2), -1, dtype=np.int32)
    mask = np.zeros(16, dtype=bool)
    for i, (x, y) in enumerate(tiles):
        pos[i] = (x, y)
        mask[i] = True
    return pos, np.full(16, 100, dtype=np.int32), mask


def test_subset_difference_proves_new_tile():
    b = Belief(0, subset_infer=True)
    pos, ene, mask = _units((5, 5), (5, 6))
    b._infer_point_tiles(pos, ene, mask, gain=1, match_step=60)
    assert not b.point_tiles.any()  # 1 von 2 -> offen
    pos, ene, mask = _units((5, 5), (5, 6), (6, 6))
    b._infer_point_tiles(pos, ene, mask, gain=2, match_step=61)
    assert b.point_tiles[6, 6]
    assert not b.point_tiles[5, 5] and not b.point_tiles[5, 6]


def test_without_subset_infer_tile_stays_open():
    b = Belief(0, subset_infer=False)
    for tiles, gain, ms in ((((5, 5), (5, 6)), 1, 60), (((5, 5), (5, 6), (6, 6)), 2, 61)):
        pos, ene, mask = _units(*tiles)
        b._infer_point_tiles(pos, ene, mask, gain=gain, match_step=ms)
    assert not b.point_tiles.any()


def test_relic_filter_ignores_units_far_from_relics():
    b = Belief(0, relic_filter=True, symmetry=True)
    b._add_relic(5, 5)
    b._add_relic(geo.mirror_xy(5, 5)[0], geo.mirror_xy(5, 5)[1])
    assert b.known_pairs() == 1  # Match 0: alle Paare bekannt
    pos, ene, mask = _units((5, 6), (0, 0))  # (0, 0) liegt ausserhalb jeder 5x5-Zone
    b._infer_point_tiles(pos, ene, mask, gain=1, match_step=60)
    assert b.point_tiles[5, 6]
    assert not b.point_tiles[0, 0]


def test_relic_filter_off_keeps_ambiguity():
    b = Belief(0, relic_filter=False, symmetry=True)
    b._add_relic(5, 5)
    pos, ene, mask = _units((5, 6), (0, 0))
    b._infer_point_tiles(pos, ene, mask, gain=1, match_step=60)
    assert not b.point_tiles.any()


def test_relic_filter_unknown_pair_before_step_50_has_no_zone():
    b = Belief(0, relic_filter=True)
    b.match_idx, b.match_step = 1, 30  # Match 1, Paar 2 unbekannt, Spawnfenster offen
    b._add_relic(5, 5)
    assert b._possible_point_zone() is None


def test_relic_filter_unseen_tiles_stay_possible_after_step_50():
    b = Belief(0, relic_filter=True)
    b.match_idx, b.match_step = 1, 60
    b._add_relic(5, 5)
    b.last_seen[:] = 60
    b.last_seen[20, 20] = -1000  # dort koennte noch ein Relic liegen
    zone = b._possible_point_zone()
    assert zone[5, 7] and zone[18, 22] and not zone[0, 0]


def test_bfs_first_step_goes_around_asteroid():
    passable = np.ones((5, 5), dtype=bool)
    passable[1, 0] = False  # direkt rechts vom Start
    dist = rules.distance_map(passable, (2, 0))
    mask = np.array([True, True, False, True, True, False])  # rechts gesperrt
    step = rules.first_step(dist, (0, 0), mask)
    assert step == geo.DOWN
    assert dist[0, 0] == 4


def _ctx(pos, ene, ids, match_step=60, assigned=None):
    W = H = 24
    pt = np.zeros((W, H), bool)
    pt[5, 5] = True
    first = {}
    for u in ids:
        first.setdefault((int(pos[u][0]), int(pos[u][1])), u)
    return dict(ally_ids=np.array(ids), ally_pos=np.array(pos), ally_ene=np.array(ene, dtype=float),
                W=W, H=H, point_tiles=pt, first_on_tile=first, assigned=assigned or {},
                own_wins=0.0, opp_wins=0.0, match_step=match_step,
                belief=type("B", (), {"newly_explored": 0, "newly_proven": 0})())


def test_reward_fix_treats_reused_id_as_death():
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.reward import surviving, unit_rewards
    cfg = AgentConfig(reward_fix=True)
    ctx = _ctx([[10, 10]], [100], [0])
    nxt = _ctx([[0, 0]], [100], [0])  # gleiche ID, aber am Spawn neu entstanden
    assert surviving(cfg, ctx, nxt) == set()
    r = unit_rewards(cfg, ctx, nxt, {0: 0}, {})
    assert r[0] == -cfg.w_death
    old = AgentConfig(reward_fix=False)
    assert surviving(old, ctx, nxt) == {0}


def test_reward_fix_no_point_reward_with_negative_energy():
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.reward import unit_rewards
    cfg = AgentConfig(reward_fix=True, w_energy=0.0, w_shape=0.0)
    ctx = _ctx([[5, 5]], [10], [0])
    nxt = _ctx([[5, 5]], [-5], [0])
    assert unit_rewards(cfg, ctx, nxt, {0: 0}, {})[0] == 0.0


def test_reward_fix_terminal_potential_is_zero():
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.reward import unit_rewards
    cfg = AgentConfig(reward_fix=True, w_energy=0.0, w_point=0.0, w_stack=0.0)
    ctx = _ctx([[0, 0]], [100], [0], match_step=99, assigned={0: (10, 0)})
    nxt = _ctx([[1, 0]], [100], [0], match_step=0, assigned={0: (10, 0)})
    r = unit_rewards(cfg, ctx, nxt, {0: 2}, {})[0]
    # phi(s) = -10 * 10/48, phi(s') = 0 im Terminalzustand
    assert abs(r - cfg.w_shape * (10.0 * 10 / 48)) < 1e-9


def test_keep_dead_restores_old_null_tiles_outside_new_relic_zone():
    b = Belief(0, symmetry=True, keep_dead=True)
    b._add_relic(5, 5)
    b._add_relic(*geo.mirror_xy(5, 5))
    f = 5 * b.H + 6
    b._mark_dead(f)
    near_new = 10 * b.H + 9
    b._mark_dead(near_new)
    b.match_idx = 1
    b.reset_match()
    assert not b.dead_tiles[5, 6]  # Matchwechsel: erst verworfen
    b._add_relic(10, 10)            # neues Paar in Match 1
    b._add_relic(*geo.mirror_xy(10, 10))
    b._restore_dead()
    assert b.dead_tiles[5, 6]       # liegt nicht neben dem neuen Relic
    assert not b.dead_tiles[10, 9]  # koennte zum neuen Relic gehoeren


def test_keep_dead_waits_while_new_relic_may_still_spawn():
    b = Belief(0, symmetry=True, keep_dead=True)
    b._add_relic(5, 5)
    b._add_relic(*geo.mirror_xy(5, 5))
    b._mark_dead(5 * b.H + 6)
    b.match_idx, b.match_step = 1, 20
    b.reset_match()
    b._restore_dead()
    assert not b.dead_tiles[5, 6]


def test_opp_points_penalty_is_shared_by_team():
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.reward import unit_rewards
    cfg = AgentConfig(w_opp_points=1.0, w_energy=0.0, w_shape=0.0, w_point=0.0)
    ctx = _ctx([[1, 1], [2, 2]], [100, 100], [0, 1])
    nxt = _ctx([[1, 1], [2, 2]], [100, 100], [0, 1])
    nxt["belief"].opp_gain = 4
    r = unit_rewards(cfg, ctx, nxt, {0: 0, 1: 0}, {})
    assert r[0] == r[1] == -2.0


class _StubBelief:
    """Minimaler Belief fuer assign_targets (kanonisch, Team 0)."""
    canonical, team_id = True, 0

    def __init__(self, points, cands):
        self._p = np.array(points, np.int32).reshape(-1, 2)
        self._c = np.array(cands, np.int32).reshape(-1, 2)
        self.explored_ever = np.zeros((24, 24), bool)

    def point_coords(self):
        return self._p

    def candidate_coords(self):
        return self._c

    def explore_coords(self, stale=0):
        return np.zeros((0, 2), np.int32)

    unexplored_coords = relic_coords = lambda self: np.zeros((0, 2), np.int32)


def test_far_opp_prefers_own_candidate_over_distant_enemy_tile():
    from agents.sherlock.features import assign_targets
    b = _StubBelief(points=[(20, 20)], cands=[(5, 5)])
    unit = np.array([[2, 2]])
    assert assign_targets(b, [0], unit, 24, 24)[0] == (20, 20)
    assert assign_targets(b, [0], unit, 24, 24, far_opp=10)[0] == (5, 5)


def test_far_opp_keeps_nearby_enemy_tile():
    from agents.sherlock.features import assign_targets
    b = _StubBelief(points=[(12, 12)], cands=[(5, 5)])
    unit = np.array([[8, 8]])
    assert assign_targets(b, [0], unit, 24, 24, far_opp=10)[0] == (12, 12)


def test_sticky_keeps_previous_target_unless_clearly_better():
    from agents.sherlock.features import assign_targets
    b = _StubBelief(points=[(8, 5), (5, 7)], cands=[])
    unit = np.array([[5, 5]])
    assert assign_targets(b, [0], unit, 24, 24)[0] == (5, 7)
    assert assign_targets(b, [0], unit, 24, 24, prev={0: (8, 5)}, sticky=2.0)[0] == (8, 5)
    # Vorteil des neuen Ziels groesser als sticky -> Wechsel
    assert assign_targets(b, [0], unit, 24, 24, prev={0: (8, 5)}, sticky=0.5)[0] == (5, 7)


def test_sticky_memory_resets_between_matches():
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.main import Agent_x
    from tests.conftest import ENV_CFG, make_obs
    a = Agent_x("player_0", cfg=AgentConfig(sticky=3.0), train=False)
    a.set_env_cfg(ENV_CFG)
    a.act(5, make_obs(5, 5, units=[(2, 2, 100)], relics=[(6, 6)]))
    assert a._sticky_prev is not None and a._sticky_prev[0] == 0
    a.new_game("player_0")
    assert a._sticky_prev is None
