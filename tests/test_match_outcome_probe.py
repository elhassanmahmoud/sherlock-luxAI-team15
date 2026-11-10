"""Manifest, whole-map feasibility and source-preserving phase contracts."""
import pytest
from scripts import match_outcome_probe as p


def test_keys_technical_partition_and_total_are_fixed():
    assert len(p.KEYS)==16 and len(set(p.KEYS))==16
    assert p.KEYS[:2]==((11011017,'player_0'),(11011000,'player_0'))
    assert len(p.phase_keys('technical'))==2 and len(p.phase_keys('remaining'))==14
    assert p.phase_keys('technical')+p.phase_keys('remaining')==list(p.KEYS)


def pair(seed,n,**changes):
    return dict(seed=seed,side='player_0',candidate={'match':n},effective=True,delta_win=0,
                delta_points=2,delta_h12=1,live_verified=True,**changes)


def test_gates_count_pairs_and_whole_maps_not_unique_action_vectors():
    rows=[pair(s,n) for s in range(8) for n in range(3)]
    for i in [0,3,6]:rows[i]['delta_win']=1
    r=p.summarize_pairs(rows)
    assert r['effective_pairs']==24 and r['effective_maps']==8
    assert r['positive_flips']==3 and r['positive_maps']==3 and r['passed']
    rows[3]['delta_win']=rows[6]['delta_win']=0
    assert not p.summarize_pairs(rows)['passed']


def test_invalid_or_duplicate_pair_and_incomplete_live_verification_rejected():
    row=pair(1,0)
    with pytest.raises(ValueError):p.summarize_pairs([row,row])
    row['live_verified']=False
    with pytest.raises(ValueError):p.summarize_pairs([row])
    row['live_verified']=True;row['effective']=False;row['delta_win']=1
    with pytest.raises(ValueError):p.summarize_pairs([row])


def test_no_effect_and_negative_labels_retained():
    rows=[pair(1,0),pair(2,0),pair(3,0)]
    rows[0].update(effective=False,delta_points=0,delta_h12=0)
    rows[1]['delta_win']=-1
    r=p.summarize_pairs(rows)
    assert r['cases']==3 and r['negative_flips']==1 and r['zero_flips']==2
    assert not r['passed']


def test_remaining_admission_binds_actual_prior_artifacts(tmp_path):
    import json
    games=[]
    for i,(seed,side) in enumerate(p.FIRST):
        record={'key':{'seed':seed,'side':side},'passivity':{'trajectory':True}}
        for role in ('reference','collector'):
            files=[]
            for ext in ('frames','pairs'):
                path=tmp_path/f'{i}_{role}.{ext}';path.write_text('unchanged');files.append(path)
            record[role]={'artifacts':p.hashes(files)}
        games.append(record)
    prior={'status':'complete','phase':'technical','source':{'head':'fixed'},'games':games,
           'keys':[list(x) for x in p.FIRST],'counters':{'completed_games':4,'started_games':4}}
    path=tmp_path/'manifest.json';path.write_text(json.dumps(prior))
    accepted=tmp_path/'accepted.json';accepted.write_text(json.dumps({'status':'accepted','manifest_sha256':p.digest(path)}))
    loaded,inputs=p.load_technical(path,accepted,{'head':'fixed'})
    assert loaded==prior and len(inputs)==10
    (tmp_path/'0_collector.frames').write_text('changed after acceptance')
    with pytest.raises(ValueError,match='artifact'):p.load_technical(path,accepted,{'head':'fixed'})
    (tmp_path/'0_collector.frames').unlink()
    with pytest.raises(ValueError,match='artifact'):p.load_technical(path,accepted,{'head':'fixed'})
