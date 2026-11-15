from hashlib import sha256
from types import SimpleNamespace

import pytest

from scripts import r3_course_entry as entry


def test_weight_identity_and_policy_are_checked_before_inference(monkeypatch):
    data = {"kind": entry.KIND, "v14": b"base", "r3": b"student"}
    monkeypatch.setattr(entry, "V14_SHA", sha256(data["v14"]).hexdigest())
    monkeypatch.setattr(entry, "R3_SHA", sha256(data["r3"]).hexdigest())
    entry.check_payload(data)
    for change in ({"v14": data["r3"]}, {"r3": data["v14"]}, {"kind": "hybrid"}):
        with pytest.raises(ValueError):
            entry.check_payload({**data, **change})


def test_train_course_updates_never_feed_next_observation_or_save():
    actor = entry.Agent_x.__new__(entry.Agent_x)
    observed = []
    actor._actor = SimpleNamespace(act=lambda step, obs: observed.append((step, obs)) or "order")
    for step in (0, 1, 101, 202):
        assert actor.act(step, "public") == "order"
        actor.update(step, "public", 2, "order", False, "next_public")
        actor.save_agent()
    assert observed == [(step, "public") for step in (0, 1, 101, 202)]


def test_final_zip_layout_registers_both_seats_and_contains_a_single_bundle():
    from scripts.build_r3_course_candidate import final_layout

    files = final_layout({"__init__.py": "", "main.py": "class Agent_x: pass"}, b"weights")
    assert set(files) == {"paths.csv", "sherlock/__init__.py", "sherlock/main.py",
                          "sherlock/agents.yaml", "sherlock/weights/agent.pth"}
    assert files["sherlock/__init__.py"] == ""
    cls, weight = "agents.sherlock.main.Agent_x", "agents/sherlock/weights/agent.pth"
    assert files["paths.csv"].splitlines() == ["Moodle Gruppe;Import_Path;Load_Path_P0;Load_Path_P1",
                                                f"15;{cls};{weight};{weight}"]
    assert files["sherlock/agents.yaml"].splitlines()[-3:] == [
        f"IMPORT_PATH: '{cls}'", f"LOAD_PATH_P0: '{weight}'", f"LOAD_PATH_P1: '{weight}'"]
