import pytest
from agents.sherlock.main import Agent_x
from scripts.ft18_after_win import FT18AfterWinAgent, reference_panel
from scripts.ft18_movement import FT18MovementAgent


@pytest.mark.parametrize("team,wins,expected", [(0,[1,0],True),(1,[1,0],False),(0,[0,1],False),(1,[0,1],True)])
def test_select_on_first_public_award_only(monkeypatch, team, wins, expected):
    agent = object.__new__(FT18AfterWinAgent)
    agent.team_id = team
    agent._reset_study()
    monkeypatch.setattr(FT18MovementAgent,"_act",lambda *args: None)
    monkeypatch.setattr(FT18MovementAgent,"_network_values",lambda *args:"ft18")
    monkeypatch.setattr(Agent_x,"_network_values",lambda *args:"v14")
    monkeypatch.setattr(FT18MovementAgent,"_policy_greedy",lambda *args:"ft18")
    monkeypatch.setattr(Agent_x,"_policy_greedy",lambda *args:"v14")
    for step,score,want in [(0,[0,0],None),(100,[0,0],None),(101,wins,expected),(202,[1,1],expected)]:
        agent._act(step,{"team_wins":score})
        assert agent.first_won is want
        assert agent._network_values(None)==("ft18" if want else "v14")
        assert agent._policy_greedy(None,None,None,None)==("ft18" if want else "v14")
    agent._reset_study()
    assert agent.first_won is None


def test_historical_panel_is_balanced_and_paired():
    lookup=reference_panel()
    seeds={s for s,_ in lookup}
    assert len(lookup)==48 and len(seeds)==24
    assert sum(any(lookup[s,p]["game_win"]=="0" for p in ("player_0","player_1")) for s in seeds)==12
