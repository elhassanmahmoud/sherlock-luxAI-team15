"""Diagnose vom 26.10.2026: Netz-Stimmen, Maske und Regeln (scripts/decision_trace.py)."""
from scripts.decision_trace import _seed_list, example_kind, summarize


def _r(**kw):
    base = dict(step=1, match=1, uid=0, n_legal=6, sap_legal=False, raw=1, greedy=1, final=1,
                agree=18, top_vote=18, masked_raw=False, rules=[], on_point=False)
    base.update(kw)
    return base


def test_summarize_counts_mask_votes_and_rules():
    rec = [
        _r(),                                                      # Netz allein, alle einig
        _r(raw=3, greedy=2, final=2, masked_raw=True, agree=12, top_vote=12),  # Maske
        _r(greedy=0, final=5, rules=["pt_sap"], on_point=True, agree=8, top_vote=10),  # Regel
        _r(greedy=3, final=4, rules=["path_fix"], agree=13, top_vote=13),
    ]
    s = summarize(rec, 18)
    assert s["unit_steps"] == 4
    assert s["masked_raw_frac"] == 0.25
    assert s["masked_raw_by_action"] == {"down": 0.25}
    assert s["all_agree_frac"] == 0.25
    assert s["majority_is_choice_frac"] == 0.75
    assert s["net_alone_frac"] == 0.5
    assert s["rule_changed_frac"] == 0.5
    assert s["rule_change_kinds"] == {"stay->sap": 0.25, "move->move": 0.25}
    assert s["rule_fired_frac"] == {"pt_sap": 0.25, "path_fix": 0.25}


def test_example_kind_categories():
    assert example_kind(_r(), 8) == "einig"
    assert example_kind(_r(match=0), 8) is None
    assert example_kind(_r(raw=3, greedy=2, masked_raw=True, agree=12), 8) == "maske"
    assert example_kind(_r(greedy=0, final=5, rules=["pt_sap"], on_point=True), 8) == "regel_pt_sap"
    assert example_kind(_r(rules=["path_fix"], agree=13), 8) == "regel_path_fix"
    assert example_kind(_r(agree=6, n_legal=4), 8) == "uneinig"


def test_seed_list():
    assert _seed_list("690000-690002") == [690000, 690001, 690002]
    assert _seed_list("5,7") == [5, 7]
