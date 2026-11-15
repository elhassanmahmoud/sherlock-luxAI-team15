"""Regressionen fuer Schusszielmaske und vollstaendige Befehle (keine Spielausfuehrung)."""
import numpy as np
import torch

from agents.sherlock.imitation_agent import ImitationAgent
from agents.sherlock.imitation_net import ImitationNet, masked_sap_logits
from scripts.imitate import prepare_labels, agreement


def fixed_rows():
    # Rechteckig: ein ungueltiges y=H darf nicht im flachen Index als (x+1,0) erscheinen.
    W, H = 4, 3
    acts = [5, 5, 5, 5, 5, 5, 2]
    n = len(acts)
    feats = torch.zeros((n, 79), dtype=torch.float16)
    feats[:, 2], feats[:, 7], feats[:, 8] = 30/400, 30/50, 1/7
    feats[1, 2] = 29/400
    mask = torch.ones((n, 6), dtype=torch.bool)
    mask[:, 5] = False   # Basismaske ohne sichtbares Gegnerziel
    mask[6, 2] = False  # Eine im Spiel gesperrte Bewegung
    r = dict(feats=feats.float(), act=torch.tensor(acts), mask=mask,
             pos=torch.tensor([[1,1],[1,1],[0,1],[1,2],[0,0],[2,1],[1,1]]),
             sdx=torch.tensor([0,0,-1,0,2,1,0]), sdy=torch.tensor([0,0,0,1,0,1,0]))
    return W, H, r


def test_fit_uses_observed_legality_without_teacher_exception_or_index_alias():
    w, h, r = fixed_rows()
    prepare_labels(r, w, h)
    assert r["mask"][:,5].tolist() == [True, False, True, True, True, True, True]
    assert not r["mask"][6,2]
    assert r["admitted"].tolist() == [True, False, False, False, False, True, False]
    assert r["sap_label"].tolist() == [True, False, False, False, False, True, False]
    assert r["tgt"][[0,5]].tolist() == [4, 11]


def test_class_and_full_command_accuracy_keep_different_denominators():
    # Teacher examples: stay, correct shot, wrong target, shot predicted as stay,
    # impossible teacher target. Only first two are exact complete commands.
    y = torch.tensor([0, 5, 5, 5, 5])
    lg = torch.full((5,6), -10.0)
    lg[torch.arange(5), [0,5,5,0,5]] = 0
    valid = torch.tensor([False, True, True, True, False])
    target_logits = torch.tensor([[9.,0.,0.],[0.,9.,0.],[0.,0.,9.]])
    matches, exact, near = agreement(lg, y, valid, target_logits, torch.tensor([0,2,2]), 3)
    assert (int(matches), int(exact), int(near)) == (2,2,3)


def test_shared_logits_include_own_tile_and_chebyshev_corner_without_leaking_targets():
    smap = torch.arange(2 * 4 * 3, dtype=torch.float32).reshape(2, 4, 3)
    pos = torch.tensor([[0,0],[2,1]])
    smap[1,0,0] = 1000
    masked = masked_sap_logits(smap, torch.tensor([1,0]), pos, torch.tensor([1,1]))
    assert masked.argmax(1).tolist() == [0, 11]
    assert int(torch.isfinite(masked[0]).sum()) == 4
    assert not torch.isfinite(masked[0, 2])
    assert not torch.isfinite(masked[1, 2])


def test_actor_accepts_center_and_mirrors_diagonal_using_same_scores(monkeypatch):
    from types import SimpleNamespace
    from agents.sherlock import imitation_agent

    smap = torch.zeros((1,4,3))
    smap[0,0,0], smap[0,3,2] = 15, 20
    def scores(*unused):
        lg = torch.zeros((3,6))
        lg[:, 5] = 100
        return lg, None, smap
    ctx = dict(ally_ene=np.array([30,30,29]), sap_cost=30, sap_range=1, W=4, H=3)
    pos = np.array([[0,0],[2,1],[1,1]])
    fz = (ctx, [0,1,2], np.zeros((3,79),np.float32), np.ones((3,6),bool), {},
          np.zeros((16,4,3),np.float32), pos)
    agent = ImitationAgent.__new__(ImitationAgent)
    agent.env_cfg = {"max_units": 3}
    agent.cfg = SimpleNamespace(focus_sap=False)
    agent.has_sap_head = True
    agent.belief = SimpleNamespace(mirrored=True)
    agent.net = SimpleNamespace(forward_all=scores)
    agent.extra_nets = []
    monkeypatch.setattr(imitation_agent, "featurize", lambda *_: fz)
    assert agent.act(1, {}).tolist() == [[5,0,0],[5,-1,-1],[0,0,0]]

    # Ein zweites Ensemblemitglied beguenstigt ein anderes legales Ziel.
    extra = ImitationNet.__new__(ImitationNet)
    torch.nn.Module.__init__(extra)
    another = torch.zeros_like(smap)
    another[0,3,1] = 80
    extra.forward_all = lambda *unused: (torch.zeros((3,6)), None, another)
    agent.extra_nets = [extra]
    assert agent.act(2, {}).tolist() == [[5,0,0],[5,0,-1],[0,0,0]]
