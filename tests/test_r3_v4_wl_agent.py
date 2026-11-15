import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import Mock

import numpy as np
import pytest

@pytest.fixture
def experiment(monkeypatch):
    # The game snapshot ships two historical trees. The switch only needs the
    # three actor hooks in this state-machine test.
    helpers = ModuleType("scripts.r3_v4_contact_agent")
    helpers.make_r3, helpers.make_v4, helpers.sync = Mock(), Mock(), Mock()
    monkeypatch.setitem(sys.modules, helpers.__name__, helpers)
    source = Path(__file__).resolve().parents[1] / "scripts/r3_v4_wl_agent.py"
    spec = importlib.util.spec_from_file_location("tested_wl_switch", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("team",[0,1])
@pytest.mark.parametrize("first,second,should_switch",[(True,False,True),(False,True,False),(True,True,False),(False,False,False)])
def test_switch_starts_with_public_m3_and_resets(monkeypatch,experiment,team,first,second,should_switch):
    base = np.zeros((16,3),dtype=int)
    v4 = base.copy()
    v4[:2,0] = 3
    actor = experiment.SwitchAgent.__new__(experiment.SwitchAgent)
    actor.r3 = Mock(caught_errors=0)
    actor.r3.act.return_value = base
    actor.shadow = Mock(caught_errors=0, v14=Mock(caught_errors=0), student=Mock(caught_errors=0))
    actor.shadow.act.return_value = v4
    sync = Mock()
    monkeypatch.setattr(experiment,"sync",sync)
    actor.new_game(f"player_{team}")
    def observation(own,other):
        wins = [own,other] if team==0 else [other,own]
        energy=np.full((2,16),10)
        energy[team,1]=-1
        return dict(team_wins=wins,units_mask=np.ones((2,16),bool),units={"energy":energy})
    assert actor.act(0,observation(0,0)) is base
    assert actor.act(101,observation(int(first),int(not first))) is base
    own = int(first)+int(second)
    start_m3 = observation(own,2-own)
    expected=v4 if should_switch else base
    assert actor.act(202,start_m3) is expected
    assert actor.act(203,start_m3) is expected
    assert actor.episode_stats() == dict(v4_steps=2*should_switch, different_orders=4*should_switch,
                                         different_active=2*should_switch)
    assert sync.call_args.args[0] is (actor.r3 if should_switch else actor.shadow.student)
    assert sync.call_args.args[2] is expected
    actor.new_game(f"player_{1-team}")
    assert actor.first_won is None and actor.episode_stats()["v4_steps"]==0
