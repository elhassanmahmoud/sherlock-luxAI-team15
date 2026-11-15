import numpy as np
import pytest
import torch

from scripts import imitate


def test_action_loss_uses_union_once_and_normalizes_by_weight_sum():
    # V14-only SAP, teacher-only SAP, both, neither.
    base = torch.tensor([5, 1, 5, 2])
    teacher = torch.tensor([1, 5, 5, 2])
    logits = torch.arange(24, dtype=torch.float32).reshape(4, 6) / torch.tensor([[2.],[4.],[8.],[16.]])
    individual = torch.nn.functional.cross_entropy(logits, teacher, reduction="none")
    expected = (3*individual[0] + 3*individual[1] + 3*individual[2] + individual[3]) / 10
    assert imitate.action_loss(logits, teacher, base).item() == pytest.approx(expected.item())
    assert imitate.action_loss(logits, teacher).item() == pytest.approx(individual.mean().item())


def test_fixed_data_preserves_seat_pairs_offsets_and_baseline_actions(tmp_path, monkeypatch):
    from scripts import train_combat_advice

    seen = {}
    def fake_index(dirs, plan):
        seen.update(plan)
        p = tmp_path/'game.npz'
        return {name: [dict(path=str(p), sha256="a", seed=seed, side=side) for seed,side in rows]
                for name, rows in plan.items()}
    np.savez(tmp_path/'game.npz', planes=np.zeros((1,16,24,24),np.int8), step=np.array([0,0]),
             pos=np.zeros((2,2)), feats=np.zeros((2,79)), mask=np.ones((2,6),bool),
             act=np.array([1,5]), sdx=np.array([0,1]), sdy=np.array([0,0]), base_act=np.array([5,3]))
    monkeypatch.setattr(train_combat_advice, "input_index", fake_index)
    train, val, nt, nv, inputs = imitate.selective_data([str(tmp_path)])
    assert (nt,nv) == (64,16) and len(inputs["val"]) == 16
    assert seen["train"] == [(i, side) for i in range(7271000,7271032) for side in ("player_0","player_1")]
    assert seen["val"] == [(i, side) for i in range(7271032,7271040) for side in ("player_0","player_1")]
    for part, n in ((train,nt),(val,nv)):
        assert np.array_equal(part[1]["step"], np.repeat(np.arange(n),2))
        assert np.array_equal(part[1]["base_act"], np.tile([5,3],n))
