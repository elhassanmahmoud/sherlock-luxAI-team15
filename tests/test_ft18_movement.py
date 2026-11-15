from types import SimpleNamespace

import numpy as np
import torch

from scripts.ft18_movement import FT18MovementAgent
from scripts.ft18_movement_study import PrefixObserver, action_bytes, references


def test_vote_uses_each_member_once_mask_before_argmax_and_leaves_sap():
    class Member:
        feat_dim = 2
        def __init__(self, q):
            self.q = torch.tensor(q, dtype=torch.float32)
            self.calls = 0
        def __call__(self, x):
            self.calls += 1
            return self.q

    # First row: illegal action 4 is always highest, FT18 proposes legal 2 instead of 1.
    # Other rows: FT18 would cancel or introduce a SAP; neither is an eligible swap.
    full_half = [[0,9,0,0,99,0],[0,0,0,0,0,9],[0,9,0,0,0,0]]
    ft_half = [[0,0,5,0,99,0],[0,4,0,0,0,0],[0,0,0,0,0,5]]
    members = [Member(full_half if i < 18 else ft_half) for i in range(36)]
    a = object.__new__(FT18MovementAgent)
    a.q, a.extra_q = members[0], members[1:]
    a.training, a.cnn_policy = False, None
    a.belief = SimpleNamespace(match_idx=0, mirrored=True)
    a._reset_study()
    x = torch.zeros(3,2)
    masks = np.ones((3,6), bool)
    masks[0,4] = False
    def vote():
        full = a._network_values(x).numpy()
        greedy = np.where(masks, full, -np.inf).argmax(1)
        return a._policy_greedy({'match_idx': a.belief.match_idx}, [9,5,1], masks, greedy)
    assert vote().tolist() == [1,5,1]
    assert not a._changed
    a.belief.match_idx = 1
    assert vote().tolist() == [2,5,1]
    assert [m.calls for m in members] == [2]*36
    assert a._changed == {9: (1,2)}
    assert a.study_stats[1]['before_rules_changed'] == 1
    assert np.asarray(a.study_stats[1]['proposal_pairs']).sum() == 3
    # On side 1 canonical EAST maps to world NORTH.
    world = np.zeros((16,3),int)
    world[9,0] = 1
    a._count_final(world)
    assert a.study_stats[1]['final_matches_ft18'] == 1


def test_first_match_hash_covers_both_seats_step_zero_and_boundary(monkeypatch):
    import scripts.ft18_movement_study as study
    monkeypatch.setattr(study, 'match_points_after_step', lambda *args: np.array([13,17]))
    def obs(n):
        return {'player_0': dict(steps=n, match_steps=n%101, team_wins=[0,int(n>=101)])}
    class Env:
        def reset(self, **kw):
            self.n = 0
            return obs(0), {}
        def step(self, actions):
            self.n += 1
            return obs(self.n), {}, {}, {}, {}
    def run(changed):
        e = PrefixObserver(Env())
        e.reset(seed=42)
        for step in range(102):
            a = {team: np.zeros((16,3), int) for team in ('player_1','player_0')}
            if changed and step == changed[0]:
                a[changed[1]][3,0] = 2
            e.step(a)
        return e.first_match()
    plain = run(None)
    assert plain['steps'] == 101
    assert plain['points_world'] == [13,17] and plain['wins_world'] == [0,1]
    for step, seat in [(0,'player_0'),(100,'player_1')]:
        assert run((step,seat))['actions_sha256'] != plain['actions_sha256']
    assert run((101,'player_0')) == plain
    a = np.zeros((16,3),dtype=np.int32)
    assert action_bytes({'player_0':a,'player_1':a}) == action_bytes({'player_1':a,'player_0':a})


def test_fixed_historical_panel():
    rows = references()
    assert len(rows) == 28
    assert sum(int(r['game_win']) for r in rows.values()) == 16
    assert all(r['opponent'] == 'solution92' and r['steps'] == '303' for r in rows.values())
