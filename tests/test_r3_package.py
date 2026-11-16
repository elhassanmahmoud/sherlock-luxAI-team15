"""R3-Finalpaket als Spieler/Gegner in scripts.par_eval (16.11.2026)."""
from pathlib import Path

import numpy as np
import pytest

from scripts import r3_package

ROOT = Path(__file__).resolve().parents[1]
R3ZIP = ROOT / "experiments/releases/20261116_r3_finale/agent.zip"
R3_SHA = "8aabdc732143a1e3f5babdd6edb6272e166b54671ee397e50e02083261c4a64d"


def test_spec_recognition():
    assert r3_package.is_spec("r3zip:experiments/releases/20261116_r3_finale/agent.zip")
    assert not r3_package.is_spec("self:agents/sherlock/weights/agent_p0.pth")
    assert not r3_package.is_spec("solution92")


@pytest.mark.skipif(not R3ZIP.is_file(), reason="R3-Paket fehlt")
def test_package_agent_acts_on_real_observation():
    from luxai_s3.wrappers import LuxAIS3GymEnv

    assert r3_package.zip_sha256(R3ZIP) == R3_SHA
    env = LuxAIS3GymEnv(numpy_output=True)
    obs, info = env.reset(seed=4242)
    agents = {side: r3_package.r3_package_agent(side, R3ZIP) for side in ("player_0", "player_1")}
    for side, agent in agents.items():
        agent.new_game(side)
        agent.set_env_cfg(info["params"])
    for step in range(3):
        actions = {side: np.asarray(agent.act(step=step, obs=obs[side])) for side, agent in agents.items()}
        for action in actions.values():
            assert action.shape == (16, 3)
            assert np.all((action[:, 0] >= 0) & (action[:, 0] <= 5))
        obs, *_ = env.step(actions)
    for agent in agents.values():
        assert getattr(agent, "caught_errors", 0) == 0
    env.close()


def test_par_eval_rejects_switches_for_package(tmp_path, monkeypatch):
    import sys

    from scripts import par_eval

    seeds = tmp_path / "s.json"
    seeds.write_text("[4242]")
    monkeypatch.setattr(sys, "argv", ["par_eval", "--weights", f"r3zip:{R3ZIP}", "--set", "end_sap=3",
                                      "--seed-list", str(seeds), "--out", str(tmp_path / "x.csv")])
    with pytest.raises(SystemExit, match="r3zip"):
        par_eval.main()
