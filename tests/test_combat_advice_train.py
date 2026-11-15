import numpy as np
import pytest
import torch

from scripts.train_combat_advice import (batch_loss, build_inputs, commands_match, frame_batches, increment,
                                        input_index, make_plan, metrics, publish, totals)


def mock_game():
    p = np.zeros((3,16,24,24), np.int8)
    p[0,10,2,3] = 127
    p[1,0,4,3] = 127
    feat = np.zeros((4,79), np.float16)
    feat[:,2] = 30/400
    feat[:,7] = 30/50
    feat[:,8] = 1/7
    feat[1,2] = 29/400
    return dict(planes=p, global_step=np.array([5,6,9]), step=np.array([0,1,1,2]),
                mstep=np.array([5,6,6,9]), uid=np.array([0,0,1,0]), feats=feat,
                pos=np.array([[3,3],[3,3],[3,3],[3,3]]), act=np.array([5,5,5,5]),
                sdx=np.array([0,0,2,1]), sdy=np.array([0,0,0,1]),
                base_act=np.array([5,2,2,0]), base_sdx=np.zeros(4,int), base_sdy=np.zeros(4,int))


def test_records_use_only_immediate_previous_frame_keep_center_and_check_target():
    game = build_inputs(mock_game())
    assert np.all(game['boards'][0,16:] == 0) and np.all(game['boards'][2,16:] == 0)
    assert game['boards'][1,16,2,3] == 1
    assert game['affordable'].tolist() == [True,False,True,True]
    assert game['legal_shot'].tolist() == [True,False,False,True]
    assert game['protected'].tolist() == [False,True,True,False]
    frames, rows, inv = next(frame_batches(game, 32, None))
    assert rows.tolist() == [0,1,2,3] and frames[inv].tolist() == [0,1,1,2]
    shuffled = list(frame_batches(game, 1, np.random.default_rng(2)))
    assert sorted(np.concatenate([part[1] for part in shuffled]).tolist()) == [0,1,2,3]


def test_unweighted_bce_uses_every_row_ce_only_legal_shots():
    fire = torch.tensor([2.,-2.,1.], requires_grad=True)
    target = torch.tensor([[[3.,0.]], [[-torch.inf,0.]], [[1.,9.]]], requires_grad=True)
    loss, _, _ = batch_loss(fire, target, torch.tensor([5,0,5]), torch.tensor([0,0,99]),
                            torch.tensor([True,False,False]))
    want = (torch.nn.functional.binary_cross_entropy_with_logits(fire, torch.tensor([1.,0.,1.]))
            + torch.nn.functional.cross_entropy(target[:1].flatten(1), torch.tensor([0])))
    assert torch.allclose(loss, want)
    loss.backward()
    assert torch.all(fire.grad != 0)
    assert not target.grad[1:].any()


def test_all_rows_in_joint_and_real_gated_changes_can_be_measured():
    data = build_inputs(mock_game())
    # Baseline correct on unit 0; head aims at a different field. Last unit is a new exact shot.
    rows = np.arange(4)
    fire = np.array([1.,1.,1.,.95])
    confidence = np.array([.8,.9,.9,.51])
    targets = np.array([4*24+3,3*24+3,3*24+3,4*24+4])
    before = set()
    for mode in ['aim','fire']:
        count = totals()
        increment(count, data, rows, fire, confidence, targets, mode)
        before.add(count['base_joint_exact'])
        assert count['units'] == 4 and count['aim_changes'] == 1
        assert count['harmed'] == 1 and count['base_sap_teacher_legal'] == 1
        assert count['new_saps'] == int(mode == 'fire')
        result = metrics(count)
        if mode == 'fire':
            assert result['new_sap_precision'] == 1 and count['helped'] == 1
        else:
            assert result['new_sap_precision'] is None
    assert before == {1}
    assert commands_match(2, 0, 0, 2, 1, 1)


def test_technical_ranges_are_explicit_and_existing_artifact_is_never_overwritten(tmp_path):
    plan = make_plan(7271000, 32, 7271032, 8)
    assert len(plan['train']) == 64 and len(plan['val']) == 16
    with pytest.raises(ValueError):
        make_plan(4,2,5,1)
    with pytest.raises(ValueError):
        input_index([tmp_path], plan)
    p = tmp_path/'out.json'
    publish(p, lambda tmp: tmp.write_text("first"))
    with pytest.raises(FileExistsError):
        publish(p, lambda tmp: tmp.write_text("second"))
    assert p.read_text() == "first"
