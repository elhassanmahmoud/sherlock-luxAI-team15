import pytest

from scripts import combined_movement as combined


@pytest.mark.parametrize("net,hurt,expected", [
    (17481, 2343, False), (17482, 2343, True), (17481, 2342, True),
    (17480, 2000, False), (17500, 2344, False),
])
def test_gate_requires_one_strict_gain_while_preserving_both_controls(net, hurt, expected):
    controls = {"r3": {"hurt": 2343}, "r5": {"net": 17481}}
    assert all(combined.offline_gate({**controls, "r7": {"net": net, "hurt": hurt}}).values()) == expected


def test_published_outputs_are_rejected_through_symlink(tmp_path):
    root = tmp_path / "checkout"
    live = root / "agents/sherlock/weights"
    live.mkdir(parents=True)
    area = tmp_path / "alias"
    area.symlink_to(live, target_is_directory=True)
    for path in [area / "new.pth", root / "experiments/candidates/x/new.pth",
                 root / "experiments/releases/saved/new.pth"]:
        with pytest.raises(ValueError, match="experiment"):
            combined.check_output(path)
    combined.check_output(tmp_path / "experiments/imitation/fresh/student.pth")


def test_both_inputs_are_opt_in_and_mapped_together(tmp_path):
    import hashlib
    import numpy as np
    from scripts import selective_dagger as dagger

    file = tmp_path / "sample.npz"
    np.savez(file, planes=np.zeros((2, 16, 24, 24), np.int8), global_step=[17, 18],
             step=np.arange(2), uid=np.array([2,2]), mstep=np.array([17,18]),
             pos=np.array([[3,3],[4,3]]), feats=np.zeros((2,79), np.float16),
             mask=np.ones((2,6), bool), act=np.array([2,2]), base_act=np.array([1,1]),
             played_act=np.array([2,0]), sdx=np.zeros(2,int), sdy=np.zeros(2,int),
             teacher_action_scores=np.array([[0.,0.,4.,2.,1.,0.]]*2, np.float32),
             teacher_selected=np.ones(2, np.int8), teacher_frame_status=np.ones(19, np.int8))
    record = {"path": file, "sha256": hashlib.sha256(file.read_bytes()).hexdigest()}
    with pytest.raises(ValueError):
        dagger.mapped_part([record], tmp_path/"old", own_commands=True,distill_movement=True)
    _, rows, _ = dagger.mapped_part([record],tmp_path/"new",own_commands=True,
                                    distill_movement=True, combined_movement=True)
    assert rows["feats"].shape == (2,85)
    assert not rows["feats"][0,79:].any()
    assert rows["feats"][1,81] == 1
    assert rows["distill_ok"].tolist() == [True,True]
    assert rows["movement_scores"][1].tolist() == [0.,0.,4.,2.,1.]

def test_fixed_teacher_population_checked_before_fit():
    recorded = {"temperature": 2., "weight": .5, "eligible_train_rows": 656134,
                "rows_with_multiple_legal_moves": 631325}
    combined.verify_targets(recorded)
    for key in recorded:
        with pytest.raises(ValueError, match="coverage"):
            combined.verify_targets({**recorded, key: 0})


def test_model_checkpoint_and_aggregate_are_bound_to_file_bytes(tmp_path):
    from hashlib import sha256
    path = tmp_path / "weights"
    path.write_bytes(b"snapshot")
    expected = sha256(path.read_bytes()).hexdigest()
    combined.check_digest(path, expected)
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Changed"):
        combined.check_digest(path, expected)
