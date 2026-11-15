from unittest.mock import patch
import numpy as np
from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from scripts.final_pressure import PressureAgent


def test_pressure_requires_repeated_comparable_observations_and_resets():
    agent = PressureAgent.__new__(PressureAgent)
    agent.cfg = AgentConfig()
    with patch.object(Agent_x, '_reset_episode_state'):
        agent._reset_episode_state()
        ctx = dict(ally_ene=np.array([110,100]), enemy_energies=np.array([180,190]), step=41)
        with patch.object(Agent_x, '_decide', return_value=(ctx, [0,1], {}, {}, {})):
            for observed in ([180], [180,190], [], [180,190]):
                ctx['enemy_energies'] = np.array(observed); agent._decide({})
                assert not agent.cfg.charge
            ctx['enemy_energies'] = np.array([205,220]); agent._decide({})
            assert agent.cfg.charge and agent.cfg.focus_sap and agent.study_stats['switch_step']==41
            ctx['enemy_energies'] = np.array([]); agent._decide({})
            assert agent.study_stats['active_steps']==2
        agent._reset_episode_state()
        assert not agent.cfg.charge and not agent.cfg.focus_sap and agent.study_stats['switch_step']==-1
