import json

import numpy as np
import pytest

from scripts.imitation_target_audit import audit, publish


def make_side(path, side):
    # Four simultaneous legal SAPs. The second and third both choose (5, 5).
    # The first chooses (4, 5). The fourth fires on its own field (6, 5).
    # One out-of-bounds and one unaffordable SAP are ignored as engine-invalid.
    pos = np.array([(4, 4), (5, 4), (5, 4), (6, 5), (0, 0), (4, 4), (5, 4)], np.int8)
    delta = np.array([(0, 1), (0, 1), (0, 1), (0, 0), (-1, 0), (0, 0), (-1, 2)], np.int8)
    feats = np.zeros((len(pos), 79), np.float16)
    feats[:, 2], feats[:, 7], feats[:, 8] = 30 / 400, 30 / 50, 3 / 7
    feats[5, 2] = 29 / 400
    np.savez_compressed(
        path, step=np.array([0, 0, 0, 0, 0, 0, 1]), uid=np.array([0, 1, 2, 3, 4, 5, 0]),
        mstep=np.array([1, 1, 1, 1, 1, 1, 2]), feats=feats,
        pos=pos, sdx=delta[:, 0], sdy=delta[:, 1], act=np.array([5]*7),
        planes=np.zeros((2, 16, 24, 24), np.int8),
        meta=json.dumps(dict(seed=7272000, side=side, opponent="v14", sap_range=3)))


def test_mutual_masks_individual_denominator_and_seats(tmp_path):
    make_side(tmp_path / "g0.npz", "player_0")
    make_side(tmp_path / "g1.npz", "player_1")
    result = audit([tmp_path])
    s = result["by_side"]["player_0"]
    assert s["legal_saps"] == 5 and s["invalid_saps"] == 2 and s["self_targets"] == 1
    assert s["self_targets_per_legal_sap"] == pytest.approx(0.2)
    head, engine = s["deployed"], s["engine"]
    assert (head["pairs"], head["mutual_pairs"], head["conflicts"], head["affected_saps"]) == (3, 3, 2, 3)
    assert head["affected_per_eligible_sap"] == .75 and head["affected_per_legal_sap"] == .6
    assert (engine["pairs"], engine["conflicts"], engine["affected_saps"]) == (6, 5, 4)
    assert result["total"]["legal_saps"] == 10 and len(result["map_sides"]) == 2
    assert len(result["map_sides"][0]["input_sha256"]) == 64
    assert result["map_sides"][0]["examples"]["deployed"][0]["recorded_step"] == 0


def test_excludes_cross_origin_and_out_of_range(tmp_path):
    path = tmp_path / "g0.npz"
    make_side(path, "player_1")
    with np.load(path) as f:
        data = {k: f[k] for k in f.files}
    data["sdx"][0], data["sdy"][0] = 1, 0  # first targets second/third shooters' origin
    data["pos"][2] = (12, 13)  # both cross targets out of range
    np.savez_compressed(path, **data)
    result = audit([tmp_path])["total"]
    assert result["deployed"]["conflicts"] == 0 and result["engine"]["conflicts"] > 0


def test_no_overwrite_or_duplicate_map_side(tmp_path):
    make_side(tmp_path / "g0.npz", "player_0")
    make_side(tmp_path / "g1.npz", "player_0")
    with pytest.raises(ValueError, match="Duplicate"):
        audit([tmp_path])
    out = tmp_path / "report.json"
    publish(out, {"original": True})
    with pytest.raises(FileExistsError):
        publish(out, {"replacement": True})
    assert json.loads(out.read_text()) == {"original": True}
