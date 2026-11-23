"""A hidden opponent can contribute points; newly spawning pairs can re-open formerly empty cells."""
from experiments.analysis.relictsuche_20261123.punktspeicher.beweise import PAIR
from experiments.analysis.relictsuche_20261123.punktgrenzen.grenzen import PublicBounds


def observation(t,our=(),theirs=(),score=0,rival=0,relics=()):
    return dict(step=t,ms=t%101,occupied=our,rivals=theirs,points=score,rival_points=rival,
                epoch_seen=any(i%3==t//101 for i,_ in relics),relics=relics)


def test_visible_enemy_subset_provides_a_cap_not_a_total():
    a,b=25,72
    with_zero=PublicBounds(geometry=False)
    with_hidden=PublicBounds(geometry=False)
    for m in (with_zero,with_hidden):
        m.observe(observation(0))
    with_zero.observe(observation(1,(a,b),(b,),1,0))
    assert with_zero.positive>>PAIR[a]&1 and with_zero.negative>>PAIR[b]&1
    with_hidden.observe(observation(1,(a,b),(b,),1,1))
    assert not with_hidden.positive and not with_hidden.negative


def test_outside_known_geometry_can_become_positive_in_a_later_match():
    a,b=49,275
    m=PublicBounds(opponents=False)
    m.observe(observation(0))
    m.observe(observation(1,(a,b),(),1,0,[(0,(2,2))]))
    assert m.positive>>PAIR[a]&1 and m.negative>>PAIR[b]&1
    for t in range(2,101):
        m.observe(observation(t,score=1))
    m.observe(observation(101))
    assert not (m.negative>>PAIR[b]&1)
    m.observe(observation(102,(b,),(),1,0,[(1,(11,11))]))
    assert m.positive>>PAIR[b]&1 and not(m.negative>>PAIR[b]&1)


def test_unsighted_current_pair_does_not_create_a_geometric_zero():
    m=PublicBounds(opponents=False)
    m.observe(observation(0))
    m.observe(observation(1,(49,275),(),1))
    assert not m.negative and not m.positive
