import math

import numpy as np
import pytest
import torch

from scripts.collect_combat_advice import file_sha
from scripts.imitate import movement_distillation_loss
from scripts.selective_dagger import mapped_part


def test_original_and_traced_archives_share_board_indices_and_only_eligible_movements(tmp_path):
    n = 12
    arrays = dict(planes=np.zeros((2, 16, 24, 24), np.int8), global_step=np.array([7, 9]),
                  step=np.array([0] * (n - 1) + [1]), pos=np.zeros((n, 2), np.int8),
                  feats=np.zeros((n, 79), np.float16), mask=np.ones((n, 6), bool),
                  act=np.ones(n, np.int8), sdx=np.zeros(n, np.int8), sdy=np.zeros(n, np.int8),
                  base_act=np.zeros(n, np.int8))
    # Raw maxima for an illegal move and for SAP must both be ignored.
    scores = np.tile(np.array([0, 2, 1, 70, -1, 90], np.float32), (n, 1))
    arrays["mask"][:, 3] = False
    selected = np.ones(n, np.int8)
    selected[1] = 0
    selected[2] = -1
    arrays["base_act"][3] = 5
    arrays["act"][4] = 5
    arrays["mask"][5, 1] = False
    scores[6, 2] = 3   # legal raw winner differs from the final teacher action
    scores[7, 5] = np.nan
    scores[8, 0] = np.inf
    arrays["mask"][9, :5] = False
    scores[10, 2] = 2  # argmax uses the first of equal maxima
    status = np.zeros(303, np.int8)
    status[7], status[9] = 1, -1

    old, raw = tmp_path / "old.npz", tmp_path / "raw.npz"
    np.savez(old, **arrays)
    np.savez(raw, **arrays, teacher_action_scores=scores, teacher_selected=selected, teacher_frame_status=status)
    records = [dict(path=str(p), sha256=file_sha(p)) for p in (old, raw)]
    _, hard, _ = mapped_part(records, tmp_path / "hard")
    _, soft, _ = mapped_part(records, tmp_path / "soft", distill_movement=True)
    assert set(soft) - set(hard) == {"distill_ok", "movement_scores"}
    for key in hard:
        np.testing.assert_array_equal(soft[key], hard[key])
    assert np.flatnonzero(soft["distill_ok"]).tolist() == [n, n + 10]
    np.testing.assert_array_equal(soft["movement_scores"][soft["distill_ok"]], scores[[0, 10], :5])
    assert np.isfinite(soft["movement_scores"]).all()
    assert not soft["movement_scores"][~soft["distill_ok"]].any()


def test_temperature_scaled_kl_direction_legal_support_and_no_sap_gradient():
    teacher = torch.tensor([[2 * math.log(3), 0., 6., 7., 8.], [15., 18., 19., 0., 90.]])
    student = torch.tensor([[0., 0., 35., 40., 45., 100.], [28., 99., 2., 14., 1., -100.]],
                           requires_grad=True)
    legal = torch.tensor([[1, 1, 0, 0, 0], [0, 0, 0, 1, 0]], dtype=torch.bool)
    loss = movement_distillation_loss(student[:, :5], teacher, legal, temperature=2.)
    # KL([.75,.25] || [.5,.5]) for the first row; the singleton support contributes zero.
    expected = 4 * (.75 * math.log(1.5) + .25 * math.log(.5)) / 2
    assert loss.item() == pytest.approx(expected, rel=1e-6)
    loss.backward()
    np.testing.assert_allclose(student.grad[0].numpy(), [-.25, .25, 0, 0, 0, 0], atol=1e-6)
    assert not student.grad[1].any()


def test_identical_or_empty_policies_have_finite_zero_loss_and_gradient():
    student = torch.tensor([[0., -torch.inf, 1., -torch.inf, -2.]], requires_grad=True)
    legal = torch.isfinite(student)
    loss = movement_distillation_loss(student, student.detach(), legal, temperature=2.)
    empty = movement_distillation_loss(student[:0], student.detach()[:0], legal[:0], temperature=2.)
    assert loss.item() == 0 and empty.item() == 0
    (loss + empty).backward()
    torch.testing.assert_close(student.grad, torch.zeros_like(student.grad), atol=1e-7, rtol=0)
