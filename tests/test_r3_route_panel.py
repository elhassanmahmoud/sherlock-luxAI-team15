import pytest

from scripts import r3_route_assess as assess
from scripts import r3_route_games as games


def test_solution_admission_ties_r3_and_must_beat_v14():
    def rows(wins):
        return {i: {"result": int(i < wins)} for i in range(120)}
    assert games.solution_gate({"v14": rows(118), "r3": rows(119), "route": rows(119)})[1]
    assert not games.solution_gate({"v14": rows(119), "r3": rows(118), "route": rows(119)})[1]
    assert not games.solution_gate({"v14": rows(118), "r3": rows(120), "route": rows(119)})[1]


def test_report_pairs_sides_and_lists_both_flips(monkeypatch):
    seen = []
    monkeypatch.setattr(assess.audit, "bounds", lambda values: seen.append(list(values)) or (0, 0))
    seeds = range(12, 14)
    def make(index):
        return {("solution92", n, "player_"+str(s)): {"result": int(s == index), "wins": 2 if s == index else 1}
                for n in seeds for s in (0, 1)}
    r = assess.paired(make(0), make(1), seeds)
    assert r["wins"] == {"reference": 2, "route": 2} and seen == [[0, 0]]
    assert len(r["gained"]) == len(r["lost"]) == 2 and r["matches"]["route"] == 6
    with pytest.raises(KeyError):
        assess.paired({}, make(1), seeds)


def test_retro_rejects_replacing_a_known_result_with_a_new_execution():
    k = ("solution92", 7273116, "player_0")
    prior = {k: {"origin": "archived", "result": 1}}
    with pytest.raises(ValueError, match="archived"):
        assess.check_origins({k: {"origin": "fresh", "result": 1}}, prior)
    with pytest.raises(ValueError, match="archived"):
        assess.check_origins({k: {"origin": "archived", "result": 0}}, prior)
    with pytest.raises(ValueError, match="archived"):
        assess.check_origins({}, prior)
    assess.check_origins(prior, prior)
