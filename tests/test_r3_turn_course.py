"""The turn course package must wrap exactly the researched policy and preserve both model byte streams."""
import ast
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts import build_r3_diagonal_course_candidate as builder
from scripts import r3_course_entry


def policy_body(source):
    return [ast.dump(node) for node in ast.parse(source).body if not isinstance(node, (ast.Import, ast.ImportFrom))]


def test_turn_derivative_preserves_real_policy_and_all_support_files(tmp_path, monkeypatch):
    base = tmp_path / "basis.zip"
    support = {"sherlock/weights/agent.pth": b"frozen test bundle", "sherlock/orders.py": b"# native commands",
               "paths.csv": b"unchanged registration"}
    with ZipFile(base, "w") as z:
        z.write(r3_course_entry.__file__, "sherlock/main.py")
        for name, content in support.items():
            z.writestr(name, content)
    monkeypatch.setattr(builder, "STANDARD_ZIP", sha256(base.read_bytes()).hexdigest())
    out = tmp_path / "richtungs-kandidat.zip"
    builder.build(base, out, turn_advice=True)
    policy_file = Path(builder.__file__).with_name("r3_turn_advice.py")
    raw = policy_file.read_bytes()
    assert sha256(raw).hexdigest() == builder.TURN_SOURCE
    with ZipFile(out) as z:
        assert set(z.namelist()) == {*support, "sherlock/main.py", "sherlock/r3_turn_advice.py"}
        assert all(z.read(name) == data for name, data in support.items())
        main = z.read("sherlock/main.py").decode()
        assert "from .r3_turn_advice import TurnAdviceAgent" in main
        assert "actor = TurnAdviceAgent(" in main
        source = z.read("sherlock/r3_turn_advice.py")
        assert policy_body(raw) == policy_body(source)
        assert b"from scripts." not in source and b"from agents." not in source
    with pytest.raises(ValueError):
        builder.build(base, out, turn_advice=True)
    with pytest.raises(ValueError):
        builder.build(base, tmp_path / "agent.zip", turn_advice=True)
    with pytest.raises(ValueError):
        builder.build(base, tmp_path / "other-kandidat.zip", turn_advice=True, after_loss=True)
