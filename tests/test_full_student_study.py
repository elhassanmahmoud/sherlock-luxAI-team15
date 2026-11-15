import json
from collections import Counter

import numpy as np
import pytest

from scripts import full_student_study as study
from scripts.imitation_storage import store_partition


def test_fixed_roster_and_three_shared_diagnostic_groups():
    plan = study.roster()
    ids = {(cohort, seed, split) for (cohort, seed, _), (split, _) in plan.items()}
    assert len(ids) == len({seed for _, seed, _ in ids}) == 424
    assert Counter((c, split) for c, _, split in ids) == {
        ("v14", "train"): 32, ("v14", "val"): 8, ("mixed", "train"): 120,
        ("mixed", "val"): 24, ("expert", "train"): 216, ("expert", "val"): 24}
    records = [dict(cohort=c, seed=s, side=p, split=split, rows=2)
               for (c, s, p), (split, _) in plan.items()]
    control, val1, g1 = study.arm_inputs(records, "historical")
    plus, val2, g2 = study.arm_inputs(records, "plus_teacher")
    assert len(control) == 304 and len(plus) == 608
    assert val1 == val2 and g1 == g2 == [("v14", 0, 32), ("mixed", 32, 128), ("expert", 128, 194)]
    assert {r["seed"] for r in val1}.isdisjoint(r["seed"] for r in plus)
    receipt = {}
    study.put(receipt, ("expert", study.FIRST, "player_1"), "first")
    with pytest.raises(ValueError, match="Duplicate"):
        study.put(receipt, ("expert", study.FIRST, "player_1"), "copy")


def test_new_side_archives_and_ordinary_own_target_energy_mask(tmp_path):
    seed, side, opponent = 7280000, "player_0", "kaggle3"
    path = tmp_path / f"g{seed}_{side}_{opponent}.npz"
    n = 4
    feats = np.zeros((n, 79), dtype=np.float16)
    feats[:, 2] = np.array([40, 39, 80, 60]) / 400
    feats[:, 7:9] = [40/50, 3/7]
    mask = np.ones((n, 6), dtype=bool)
    mask[:, 5] = [False, True, True, True]
    meta = json.dumps(dict(seed=seed, side=side, opponent=opponent))
    np.savez_compressed(path, planes=np.zeros((1,16,24,24), dtype=np.int8),
                        step=np.zeros(n, dtype=np.int32), uid=np.arange(n, dtype=np.int8),
                        pos=np.zeros((n,2), dtype=np.int8), feats=feats, mask=mask,
                        act=np.array([5,5,5,0], dtype=np.int8), sdx=np.array([0,0,-1,0], dtype=np.int8),
                        sdy=np.zeros(n, np.int8), meta=meta, base_act=np.zeros(n, np.int8))
    assert study.archive_rows(path, seed, side, opponent) == n
    with pytest.raises(ValueError, match="identity"):
        study.archive_rows(path, seed, "player_1", opponent)
    _, rows = store_partition([path], tmp_path / "mapped", study.imitate.prepare_labels)
    assert "base_act" not in rows
    np.testing.assert_array_equal(rows["mask"][:, 5], [True, False, True, True])
    np.testing.assert_array_equal(rows["sap_label"], [True, False, False, False])
    np.testing.assert_array_equal(rows["admitted"], [True, False, False, True])
    assert rows["tgt"][0] == 0


def test_fits_seed_global_numpy_and_publish_full_student(tmp_path, monkeypatch):
    import torch
    from agents.sherlock import ppo_agent
    from scripts import imitation_storage

    monkeypatch.setattr(study, "sha256", lambda path: study.V14_DIGEST)
    frames = np.zeros((1,16,1,1), dtype=np.int8)
    monkeypatch.setattr(imitation_storage, "store_partition", lambda paths, *args:
                        (frames, {"step": np.arange(len(paths))}))
    monkeypatch.setattr(study.imitate, "v14_cfg", lambda: object())
    saved, permutations = [], []
    def fake_train(*args):
        _, _, options, _ = args
        permutations.append(np.random.permutation(20).tolist())
        assert options.sap_weight == .5
        options.validation_report.update({key: {"rows": stop-start} for key,start,stop in options.validation_groups})
        return object()
    def fake_save(path, net, cfg, extra):
        saved.append(extra)
        from pathlib import Path
        Path(path).write_text("self-trained dummy")
    monkeypatch.setattr(study.imitate, "train_student", fake_train)
    monkeypatch.setattr(ppo_agent, "save_policy", fake_save)
    monkeypatch.setattr(torch, "set_num_threads", lambda *args: None)
    files = [dict(cohort=c, split=split, file="synthetic", rows=1)
             for c in study.COHORTS for split in ("train","val")]
    for i, arm in enumerate(("historical","plus_teacher")):
        np.random.seed(999-i)
        opts = study.SimpleNamespace(out=tmp_path/f"{arm}.pth", device="cpu", arm=arm)
        study.fit(opts, {"files": files}, "frozen", {c:tmp_path for c in study.COHORTS})
    assert permutations == [np.random.RandomState(2711).permutation(20).tolist()] * 2
    assert all(x["kind"] == "imitation" and x["sap_own_tile"] for x in saved)
    for obj in saved:
        info = obj["full_policy_study"]
        assert info["manifest_sha256"] == "frozen" and set(info["validation"]) == set(study.COHORTS)
