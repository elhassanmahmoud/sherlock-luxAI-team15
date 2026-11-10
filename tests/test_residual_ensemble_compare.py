import copy
import pytest
from scripts.residual_ensemble_compare import fixed_jobs, summarize, validate_rows


def rows_for(job, wins):
    return [dict(seed=k['seed'],side=k['side'],steps=303,point_counting_version=2,
                 our_wins=2 if i<wins else 1,opp_wins=1 if i<wins else 2,
                 result=1. if i<wins else 0.,game_win=int(i<wins),caught_errors=0,
                 our_points=5,opp_points=4)
            for i,k in enumerate(job['keys'])]


def test_exact_budgets_and_shared_keys():
    jobs=fixed_jobs('selection')
    assert sum(len(j['keys']) for j in jobs)==200
    assert jobs[0]['keys']==jobs[1]['keys']==jobs[2]['keys']
    confirm=fixed_jobs('confirmation','R61')
    assert sum(len(j['keys']) for j in confirm)==600
    assert len({k['seed'] for j in confirm for k in j['keys']})==180


def test_incomplete_duplicate_invalid_score_and_counting_fail():
    j=fixed_jobs('selection')[0]
    rows=rows_for(j,39)
    validate_rows(j,rows)
    for bad in [rows[:-1],rows+rows[:1],rows[:-1]+rows[:1]]:
        with pytest.raises(ValueError): validate_rows(j,bad)
    for key,value in [('point_counting_version',1),('steps',302),('game_win',0),('result',.5),('caught_errors',1)]:
        bad=copy.deepcopy(rows);bad[0][key]=value
        with pytest.raises(ValueError): validate_rows(j,bad)


def test_both_starts_required_rank_direct_before_solution_and_no_draw_wins():
    jobs=fixed_jobs('selection')
    data={j['name']:rows_for(j,n) for j,n in zip(jobs,[39,40,38,25,24])}
    s=summarize('selection',jobs,data)
    assert s['nominee']=='R61'
    data[jobs[4]['name']]=rows_for(jobs[4],23)
    assert summarize('selection',jobs,data)['nominee'] is None
    draw=data[jobs[4]['name']][23]
    draw.update(our_wins=1,opp_wins=1,result=.5,game_win=0)
    assert summarize('selection',jobs,data)['nominee'] is None


def test_confirmation_all_guards_and_cluster_uncertainty():
    jobs=fixed_jobs('confirmation','R61')
    data={j['name']:rows_for(j,len(j['keys'])) for j in jobs}
    assert summarize('confirmation',jobs,data)['qualified']
    direct=next(j for j in jobs if j['name']=='R61_direct')
    data[direct['name']]=rows_for(direct,102)
    report=summarize('confirmation',jobs,data)
    assert not report['qualified']
    assert report['direct_interval'][0] < .5
    default=next(j for j in jobs if j['name']=='R61_default')
    data[default['name']]=rows_for(default,19)
    assert not summarize('confirmation',jobs,data)['gates']['default_perfect']
