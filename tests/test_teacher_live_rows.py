import json

import numpy as np

from scripts.imitate import SideRecord


def test_record_keeps_zero_energy_and_aligns_features_actions_and_frames(tmp_path):
    record = SideRecord()
    ids = [3, 0, 7]
    energy = np.zeros(16, dtype=np.int16)
    actions = np.zeros((16, 3), dtype=np.int8)
    actions[3] = [2, 0, 0]
    actions[7] = [5, -1, 1]
    feats = np.zeros((3, 79), dtype=np.float32)
    feats[:, 0] = [0.25, 0.5, 0.75]
    pos = np.array([[3, 3], [0, 2], [7, 1]])
    mask = np.ones((3, 6), dtype=bool)
    planes = np.zeros((16, 24, 24), dtype=np.float32)
    ctx = {"ally_ene": energy, "match_step": 12}
    fz = ctx, ids, feats, mask, {}, planes, pos

    energy[ids] = -1
    record.add(fz, actions, False)
    assert not record.planes

    energy[ids] = [-1, 0, 1]
    record.add(fz, actions, False)
    dest = tmp_path / "seat.npz"
    assert record.save(dest, {}) == 2
    with np.load(dest, allow_pickle=False) as rows:
        assert json.loads(rows["meta"].item())["row_filter"] == "unit_energy>=0"
        assert rows["uid"].tolist() == [0, 7]
        assert rows["step"].tolist() == [0, 0]
        assert rows["act"].tolist() == [0, 5]
        assert rows["sdx"].tolist() == [0, -1]
        assert rows["sdy"].tolist() == [0, 1]
        assert rows["feats"][:, 0].tolist() == [0.5, 0.75]
        assert rows["pos"].tolist() == [[0, 2], [7, 1]]
