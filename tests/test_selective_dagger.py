from types import SimpleNamespace

import numpy as np
import pytest

from agents.sherlock import cnn_model
from scripts import collect_combat_advice as collect
from scripts import selective_dagger as d
from tests.test_combat_advice_collect import Actor, Course, Teacher


def test_mixed_uses_one_action_preserves_three_commands_and_syncs_real_history(monkeypatch):
    monkeypatch.setattr(cnn_model, "map_planes", lambda ctx: np.zeros((16,24,24),np.float32))
    class Recorded(Actor):
        calls = 0
        def act(self, step, public):
            self.calls += 1
            played = super().act(step, public)
            self.v14_command = played.copy()
            if played[1,0] == 1:
                self.v14_command[1,0] = 4
            return played
    actor, teacher = Recorded(), Teacher()
    opp = SimpleNamespace(set_env_cfg=lambda _:None, act=lambda step, public:np.zeros((3,3),int))
    data, _ = collect.play(Course(),actor,opp,teacher,7272000,"player_1",record=d.MixedRecord())
    assert actor.calls == 303 and len(teacher.played) == 303
    assert data["act"][:2].tolist() == [5,5] and data["sdx"][:2].tolist() == [2,2]
    assert data["base_act"][:2].tolist() == [5,3]    # world LEFT -> canonical DOWN
    assert data["played_act"][:2].tolist() == [5,2]  # world UP -> canonical RIGHT
    assert data["base_sdx"][0] == data["played_sdx"][0] == -3
    assert (teacher.played[2][1] == [1,0,0]).all()


def test_three_commands_digested_and_parent_and_mode_enforced(tmp_path,monkeypatch):
    from tests.test_combat_advice_collect import run
    arrays, game = run(Course(),Teacher(),monkeypatch)
    for name in ("act","sdx","sdy"):
        arrays["played_"+name] = arrays["base_"+name].copy()
    seed, side = 7272000, "player_1"
    meta = dict(seed=seed,side=side,steps=303,opponent=collect.opponent_for(seed),protocol_sha256="fixed",
                teacher="kaggle3",policy="selective_movement",teacher_history="played_selective_actions",
                student_sha256="student",**game)
    path = tmp_path/collect.filename(seed,side)
    def save():
        meta["arrays_sha256"] = collect.array_digest(arrays)
        np.savez_compressed(path,meta=collect.canonical_json(meta).decode(),**arrays)
    save()
    assert collect.check_archive(path,seed,side,"fixed",student_sha="student") == 300
    with pytest.raises(ValueError,match="identity"):
        collect.check_archive(path,seed,side,"fixed",student_sha="other")
    with pytest.raises(ValueError,match="identity"):
        collect.check_archive(path,seed,side,"fixed")
    arrays["played_sdx"][0] = -1
    save()
    with pytest.raises(ValueError,match="SAP"):
        collect.check_archive(path,seed,side,"fixed",student_sha="student")


def test_disk_board_arrays_and_disjoint_card_splits(tmp_path):
    a = SimpleNamespace(train_first=7272000, train_count=120, val_first=7272200, val_count=24)
    base,mixed = d.plans(a)
    assert (len(base["train"]),len(base["val"]),len(mixed["train"]),len(mixed["val"])) == (64,16,240,48)
    a.val_first = 7271000
    with pytest.raises(ValueError):
        d.plans(a)
    arrays = dict(planes=np.zeros((2,16,24,24),np.int8),global_step=[1,2],step=[0,1,1],
                  pos=np.zeros((3,2)), feats=np.zeros((3,79)), mask=np.ones((3,6),bool),
                  act=[0,1,2],sdx=[0,0,0],sdy=[0,0,0],base_act=[1,1,2])
    path = tmp_path/"g.npz"
    np.savez_compressed(path,**arrays)
    rec = dict(path=str(path),sha256=collect.file_sha(path))
    boards,rows,sizes = d.mapped_part([rec,rec],tmp_path/"boards.int8")
    assert isinstance(boards,np.memmap) and boards.shape == (4,16,24,24) and sizes == [3,3]
    assert rows["step"].tolist() == [0,1,1,2,3,3]
    assert rows["base_act"].tolist() == [1,1,2,1,1,2]
