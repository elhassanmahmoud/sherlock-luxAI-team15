"""Pure fixtures for nomination, original control reuse and the three new arm sizes."""
from types import SimpleNamespace
from unittest.mock import patch

from scripts import r8_midpoint_diagonal_games as study


def test_new_games_only():
    layout=study.schedule("screen")
    assert {k:len(s)*len(foes)*2 for k,(s,foes) in layout.items()} == {"diagonal":64,"dual_external":64,"dual_direct":32}
    assert all(s==range(7170230,7170246) for s,_ in layout.values())
    assert set(layout).isdisjoint(study.SINGLES)


def test_parent_controls_and_v14_conditions():
    for s,d,sol,base_ok,expected in ((1,1,0,True,True),(0,3,1,True,False),
                                     (1,0,0,True,False),(1,1,-1,True,False),(1,1,0,False,False)):
        result={"gates":{"v14_requirements":base_ok}}
        def comparison(delta):
            return dict(external=dict(net_wins=delta),by_opponent={"solution92":{"net_wins":sol}})
        # R3 is reported descriptively, even when it wins more external games.
        study.screen_gates(result,{"midpoint":comparison(s),"diagonal":comparison(d),"r3":comparison(-100)})
        assert result['game_gates_pass'] is expected


def test_existing_partial_control_never_launches_duplicate(tmp_path):
    a=SimpleNamespace(out=tmp_path/"new")
    original=tmp_path/"old"
    original.mkdir()
    (original/"manifest.json").write_text("{}")
    with patch.object(study,"control_paths",return_value=(a.out/"screen/diagonal",[original])), patch.object(study,"owned") as play:
        try:
            study.diagonal(a,True)
        except ValueError as e:
            assert "incomplete" in str(e)
        else:
            raise AssertionError("Accepted a duplicate of an active control")
        play.assert_not_called()
