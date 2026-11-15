import numpy as np
import pytest

from agents.sherlock.geometry import mirror_xy
from scripts.v4_holder_assess import tech
from scripts.v4_sole_holder import choose


def decision(pos, v14, student, *, team=0, energy=None, live=None, points=None, walls=(), guard=True,
             route=None, foe=None):
    n = len(pos)
    xy = np.zeros((2, n, 2), dtype=int)
    xy[team] = pos
    power = np.full((2, n, 1), 50, dtype=int)
    power[team, :, 0] = [50]*n if energy is None else energy
    mask = np.zeros((2, n), dtype=bool)
    mask[team] = [True]*n if live is None else live
    tiles = np.zeros((24, 24), dtype=int)
    for p in walls:
        tiles[p] = 2
    obs = dict(units={"position":xy, "energy":power}, units_mask=mask, map_features={"tile_type":tiles})
    canon = [mirror_xy(*p) if team else p for p in pos]
    first = {}
    for uid, p in enumerate(canon):
        if mask[team, uid] and power[team, uid, 0] >= 0:
            first.setdefault(p, uid)
    known = np.zeros((24, 24), dtype=bool)
    for p in ([pos[0]] if points is None else points):
        known[mirror_xy(*p) if team else p] = True
    ctx = dict(ally_pos=canon, first_on_tile=first, enemy_coords=[canon[0] if foe is None else foe])
    a, b = np.array(v14, dtype=int), np.array(student, dtype=int)
    routed = [True]*n if route is None else route
    baseline = np.where(np.asarray(routed)[:, None], b, a)
    return choose(obs, team, ctx, known, routed, a, b, baseline, cost=3, guard=guard)


stay, up, right, left = (0,0,0), (1,0,0), (2,0,0), (4,0,0)
sap = (5,-2,1)


@pytest.mark.parametrize("seat", [0, 1])
def test_full_world_sap_command_and_orientation_at_both_seats(seat):
    observed, original = decision([(8,4)], [sap], [right], team=seat, guard=False)
    played, events = decision([(8,4)], [sap], [right], team=seat)
    assert observed[0].tolist() == list(right) and original[0]["eligible"]
    assert played[0].tolist() == list(sap) and events[0]["restored"]
    assert events[0]["canonical"] == (list(mirror_xy(8,4)) if seat else [8,4])
    assert events[0]["world"] == events[0]["planned_end"] == [8,4]


def test_no_override_without_usable_v14_anchor_or_mixed_trigger():
    for opts in ({"energy":[2]}, {"walls":[(5,4)]}, {"points":[]}, {"route":[False]}, {"foe":(10,10)}):
        played, events = decision([(4,4)], [stay], [right], **opts)
        assert not any(e["restored"] for e in events)
        expected = stay if opts.get("route") == [False] else right
        assert played[0].tolist() == list(expected)
    # V14 would leave as well, or the two SAP targets differ: neither is an outgoing holder.
    assert not decision([(4,4)], [up], [right])[1][0]["eligible"]
    assert not decision([(4,4)], [(5,0,-2)], [(5,-1,-1)])[1][0]["eligible"]
    # V14's blocked move can be a valid holding command; preserve the original world order.
    assert decision([(4,4)], [left], [right], walls=[(3,4)])[0][0].tolist() == list(left)
    assert decision([(0,4)], [left], [right])[0][0].tolist() == list(left)


def test_living_and_able_teammate_replaces_holder():
    pos = [(5,4),(6,4)]
    assert not decision(pos, [stay,stay], [up,left])[1][0]["eligible"]
    for opts in ({"live":[True,False]}, {"energy":[50,-1]}, {"energy":[50,2]}):
        assert decision(pos, [stay,stay], [up,left], **opts)[1][0]["restored"]
    assert not decision([(5,4),(5,4)], [stay,stay], [up,right])[1][0]["eligible"]


def test_joint_swaps_hold_both_fields_and_failed_replacement_cascades():
    points = [(2,2),(3,2)]
    swap, events = decision(points, [stay,stay], [right,left], points=points)
    assert swap.tolist() == [list(right),list(left)] and not any(e["restored"] for e in events)
    protected, events = decision(points, [stay,stay], [left,left], points=points)
    assert protected.tolist() == [list(stay),list(stay)]
    assert [r["other_planned_before"] for r in events] == [1,0]
    assert all(r["restored"] and not r["other_planned_final"] for r in events)


def test_direct_compare_checks_actions_from_both_seats_and_per_match():
    seat = (7150068, "player_1", "solution92")
    rows = {(*seat, arm): dict(orders_sha256=["a","b"], game={}, matches=[], events=[])
            for arm in ("native_mixed","native_points","mixed","points")}
    assert tech(rows)["actual_player1_parity"] == {"mixed": True, "points": True}
    rows[*seat,"native_mixed"]["orders_sha256"] = ["other","b"]
    rows[*seat,"native_points"]["matches"] = [1]
    assert tech(rows)["actual_player1_parity"] == {"mixed": False, "points": False}
