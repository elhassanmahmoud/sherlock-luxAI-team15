from scripts.r3_turn_advice_audit import OPPONENTS,gates,summary


def card(rows,net):
    gained=max(net,0);lost=max(-net,0)
    return dict(rows=rows,gained=gained,lost=lost,neutral=0,changed=gained+lost,
                r3_correct=rows//2,candidate_correct=rows//2+net)


def test_bootstrap_resamples_two_complete_maps_and_respects_their_different_sizes():
    # One map with a short loss and a much larger map with a win.
    # Resampling entire cards gives a negative lower bound, although the net is positive.
    x=summary([card(20,-2),card(200,8)])
    assert x["net"]==6 and x["difference_pp"]==600/220
    assert x["paired_ci95_pp"]==[-10.0,4.0] and x["counts"]["changed"]==10


def test_each_cohort_must_have_a_strict_positive_lower_bound_and_each_new_foe_a_nonnegative_sum():
    def cohort(low):
        return dict(overall=dict(paired_ci95_pp=[low,2.0]),opponents={k:dict(net=0) for k in OPPONENTS})
    a,b=cohort(0.125),cohort(0.25)
    assert all(gates(dict(old_validation=a,new_validation=b)).values())
    assert not all(gates(dict(old_validation=cohort(0.0),new_validation=b)).values())
    b["opponents"]["kaggle3"]["net"]=-1
    assert not all(gates(dict(old_validation=a,new_validation=b)).values())
