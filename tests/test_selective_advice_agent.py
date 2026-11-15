from collections import Counter
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.imitation_net import ImitationNet
from agents.sherlock.main import Agent_x
from scripts import selective_advice_agent as selective


def test_reads_the_standard_student_checkpoint_and_legacy_own_tile_flag(tmp_path):
    net = ImitationNet(feat_dim=79, ch=4, blocks=1, hidden=8)
    ckpt = {"kind": "imitation", "arch": net.arch, "policy": net.state_dict()}
    path = tmp_path / "student.pth"
    torch.save(ckpt, path)
    members, own_tile = selective.load_heads(path)
    assert len(members) == 1 and not own_tile and not members[0].training
    assert all(torch.equal(a, b) for a, b in zip(members[0].parameters(), net.parameters()))
    ckpt.update(sap_own_tile=True, imitation_ensemble=[{"arch": net.arch, "policy": net.state_dict()}])
    torch.save(ckpt, path)
    members, own_tile = selective.load_heads(path)
    assert len(members) == 2 and own_tile


@pytest.mark.parametrize("mode", ["movement", "combat"])
def test_selective_agent_uses_final_v14_cache_and_updates_native_orders(monkeypatch, mode):
    # Kanonische Position (5,8) entspricht fuer player_1 dem Weltfeld (15,18).
    pos = np.repeat([[5, 8]], 7, axis=0)
    world = 23 - pos[:, ::-1]
    energy = np.array([51, 52, 53, 54, 55, 1, -1])
    tiles = np.zeros((24, 24), int)
    public = dict(steps=4, match_steps=4, units={"position": np.stack([world, world]),
                  "energy": np.stack([energy, energy])}, units_mask=np.ones((2, 7), bool),
                  sensor_mask=np.ones_like(tiles, bool), map_features={"tile_type":tiles})
    ctx = dict(ally_pos=pos, ally_ene=energy, enemy_coords=np.array([[5,8]]), enemy_energies=np.array([30]),
               sap_range=2, sap_cost=30, H=24)
    # UID 1 ist ein V14-Schuss, alle anderen bleiben vor der Beratung stehen.
    base = np.zeros((7, 3), int)
    base[1] = [5, 1, 0]
    agent = object.__new__(selective.SelectiveAdviceAgent)
    agent.mode, agent.sap_own_tile, agent.training = mode, True, False
    agent.belief = SimpleNamespace(mirrored=True)
    agent.team_id, agent._imitation = 1, None
    agent.env_cfg = dict(unit_move_cost=3, unit_sap_cost=30, unit_sap_range=2)
    agent.cfg = SimpleNamespace(nebula_avoid=True, dodge_shape=False, dodge_distrust=0, dodge_verify=False)
    agent.selective_counts = Counter()
    remembered = []
    agent.param_est = SimpleNamespace(observe=lambda *a: None, remember=lambda o,t,a: remembered.append(a.copy()))
    ids = list(range(7))
    features = {u: np.zeros(79, np.float32) for u in ids}
    masks = {u: np.ones(6, dtype=bool) for u in ids}
    for m in masks.values():
        m[geo.SAP] = False  # die Imitationsmaske erlaubt bezahlbare Blindschuesse
    masks[5][1:5] = False  # zu wenig Energie

    def v14(self, step, obs):
        self._prev_ctx = ctx
        self._cache = (4, ctx, ids, features, masks, {})
        self._prev_actions = {u:int(a) for u,a in enumerate(base[:, 0])}
        self._sap_hits = {1: 1}
        self._sap_unknown = {1}
        self.ep_stats = {"sap_attempts": 1, "sap_hits_est": 1}
        return base.copy()

    class FixedStudent:
        def forward_all(self, boards, idx, positions, feats):
            assert boards.shape == (1, 16, 24, 24) and feats.shape == (6, 79)
            logits = torch.zeros((6, 6))
            logits[0, geo.RIGHT] = logits[1, geo.UP] = logits[2, geo.SAP] = 12
            logits[3, geo.SAP] = 12  # fuer diesen Schuetzen ist das Top-Ziel ausser Reichweite
            logits[5, geo.SAP] = 12  # unbezahlbar
            target = torch.zeros((1, 24, 24))
            target[0,5,8] = 12  # Eigenfeld von UID 2
            return logits, None, target

    pos[3] = [14, 14]
    public["units"]["position"][1,3] = 23 - pos[3, ::-1]
    agent.members = [FixedStudent()]
    monkeypatch.setattr(Agent_x, "_act", v14)
    monkeypatch.setattr(selective, "map_planes", lambda ctx: np.zeros((16,24,24), np.float32))
    played = agent._act_est(4, public)
    expected = base.copy()
    if mode == "movement":
        expected[0] = [geo.UP, 0, 0]
        assert agent._prev_actions[0] == geo.RIGHT
    else:
        expected[1] = [geo.RIGHT, 0, 0]
        expected[2] = [geo.SAP, 0, 0]
        assert agent._prev_actions[1] == geo.UP and agent._sap_hits == {2:1} and not agent._sap_unknown
        assert agent.ep_stats["sap_attempts"] == agent.ep_stats["sap_hits_est"] == 1
    np.testing.assert_array_equal(played, expected)
    assert len(remembered) == 1
    np.testing.assert_array_equal(remembered[0], expected)
    # Training erhaelt den unveraenderten Originalbefehl.
    agent.training = True
    np.testing.assert_array_equal(agent._act(4, public), base)
