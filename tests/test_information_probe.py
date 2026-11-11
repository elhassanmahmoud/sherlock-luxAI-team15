"""Public-only inference and joint-action opportunity tests, no models/games."""
from copy import deepcopy

import pytest

from scripts.information_probe import (
    PublicEquation, PublicHistory, advance_public_history, choose_probe,
    public_frame, scan_frames,
    validate_archive_manifest,
)


def grid(value=False):
    return [[value for _ in range(8)] for _ in range(8)]


def situation():
    p = dict(W=8, H=8, step=60, match_idx=0, match_step=60,
             own_points=5, ally_ids=[0, 1], ally_pos=[[2, 2], [3, 2]],
             ally_ene=[20, 20], point_tiles=grid(), candidate=grid(),
             sensor_mask=grid(True), passable=grid(True), nebula=grid(),
             enemy_coords=[], move_cost=2, sap_range=3,
             assigned={'0': [1, 2], '1': [3, 2]})
    p['candidate'][2][2] = p['candidate'][3][2] = True
    h = PublicHistory(match_idx=0, records=[PublicEquation(((2, 2), (3, 2)), 1, 59)],
                      zeros={(1, 2)})
    return p, h, [[True, False, False, False, True], [True, False, False, False, False]]


def test_isolate_a_from_a_plus_b():
    p, h, masks = situation()
    proposal = choose_probe(p, [0, 1], masks, [0, 0], h)
    assert proposal is not None
    assert proposal['x'] == [2, 2]
    assert proposal['changes'] == [[0, 4]]
    assert proposal['previous_unknown'] == [[2, 2], [3, 2]]
    assert proposal['projected_unknown'] == [[3, 2]]
    assert choose_probe(p, [0, 1], masks, [0, 0], h) == proposal


@pytest.mark.parametrize('change', ['holder', 'hidden', 'nebula', 'energy', 'enemy', 'cost', 'sap', 'masked', 'late', 'early', 'second_match'])
def test_reject_unsafe_or_out_of_scope(change):
    p, h, masks = situation(); greedy = [0, 0]
    if change == 'holder': p['point_tiles'][2][2] = True
    if change == 'hidden': p['sensor_mask'][1][2] = False
    if change == 'nebula': p['nebula'][1][2] = True
    if change == 'energy': p['ally_ene'][0] = 3
    if change == 'enemy': p['enemy_coords'] = [[4, 2]]
    if change == 'cost': p.pop('move_cost')
    if change == 'sap': greedy[0] = 5; masks[0].append(True)
    if change == 'masked': masks[0][4] = False
    if change == 'late': p['match_step'] = 81
    if change == 'early': p['match_step'] = 49
    if change == 'second_match': p['match_idx'] = 1
    assert choose_probe(p, [0, 1], masks, greedy, h) is None


def test_original_already_identifies_x():
    p, h, masks = situation()
    assert choose_probe(p, [0, 1], masks, [4, 0], h) is None


def test_non_candidate_is_not_a_known_zero():
    p, h, masks = situation(); h.zeros.clear()
    assert not p['candidate'][1][2]
    assert choose_probe(p, [0, 1], masks, [0, 0], h) is None


def test_history_current_occupancy_stacks_and_negative_energy():
    p, _, _ = situation()
    prev = deepcopy(p); prev.update(step=59, match_step=59, own_points=4)
    prev['ally_pos'] = [[0, 0], [0, 1]]
    p['ally_ids'] = [0, 1, 2]
    p['ally_pos'] = [[2, 2], [2, 2], [7, 7]]
    p['ally_ene'] = [5, 5, -1]
    h = advance_public_history(prev, p, PublicHistory())
    assert h.records == [PublicEquation(((2, 2),), 1, 60)]


def test_known_point_contribution_and_distinct_symmetric_tiles():
    p, h, masks = situation()
    p['ally_ids'].append(2); p['ally_pos'].append([5, 5]); p['ally_ene'].append(20)
    p['point_tiles'][5][5] = True
    h.records = [PublicEquation(((2, 2), (3, 2), (5, 5)), 2, 59)]
    masks.append([True, False, False, False, False])
    result = choose_probe(p, [0, 1, 2], masks, [0, 0, 0], h)
    assert result and result['previous_residual'] == 1
    assert result['projected_known_points'] == [[5, 5]]


def test_reset_gap_and_pre50_history():
    p, h, _ = situation(); prev = deepcopy(p)
    prev.update(step=48, match_step=48)
    p.update(step=49, match_step=49)
    h = advance_public_history(prev, p, h)
    assert not h.records and not h.zeros
    p.update(step=50, match_step=50); prev.update(step=49, match_step=49)
    h = advance_public_history(prev, p, h)
    assert h.records and h.zeros == {(2, 2), (3, 2)}
    prev = deepcopy(p); p.update(step=52, match_step=52)
    h = advance_public_history(prev, p, h)
    assert not h.records and not h.zeros
    p.update(match_idx=1, step=102, match_step=0)
    assert not advance_public_history(prev, p, h).records


def test_contradiction_discards_zero_assumptions():
    p, h, _ = situation(); h.zeros = {(2, 2), (3, 2)}
    prev = deepcopy(p); prev.update(step=59, match_step=59, own_points=4)
    h = advance_public_history(prev, p, h)
    assert not h.records and not h.zeros and h.contradictions == 1


@pytest.mark.parametrize('old_tiles,old_value', [(((2,2),(3,2),(4,2)), 2), (((2,2),(3,2)), 2)])
def test_mutually_contradictory_records_are_discarded(old_tiles, old_value):
    p, h, _ = situation()
    p.update(ally_ids=[0,1,2], ally_pos=[[2,2],[3,2],[4,2]], ally_ene=[20]*3)
    h.records = [PublicEquation(old_tiles, old_value, 59)]; h.zeros.clear()
    previous = deepcopy(p); previous.update(step=59, match_step=59, own_points=4)
    result = advance_public_history(previous, p, h)
    assert result.records == [] and result.zeros == set() and result.contradictions == 1


def test_adapter_whitelist_and_prefix_independence():
    p, h, masks = situation()
    row = dict(status='decision', public=p, units=[dict(uid=i, mask=masks[i], masked_argmax=0) for i in range(2)],
               posthoc={'secret': 12}, events={'future': 42})
    obs, ids, mm, gg = public_frame(row)
    assert 'posthoc' not in obs and 'events' not in obs
    assert choose_probe(obs, ids, mm, gg, h)
    before = deepcopy(row); before['public'].update(step=59, match_step=59, own_points=4)
    rows = [before, row]
    a = scan_frames(rows)
    rows[0]['posthoc'] = {'secret': 'changed'}
    later = deepcopy(row); later['public'].update(step=61, match_step=61)
    b = scan_frames(rows + [later])
    assert a['frames'] == b['frames'][:len(a['frames'])]


def test_no_mutation_and_proposal_bound():
    p, h, masks = situation(); original = deepcopy((p, h, masks))
    stats = {}
    choose_probe(p, [0, 1], masks, [0, 0], h, stats=stats)
    assert (p, h, masks) == original
    assert stats['enumerated'] <= 113


def test_requires_two_coordinated_moves():
    p, h, masks = situation()
    p['ally_ids'].append(2); p['ally_pos'].append([2, 2]); p['ally_ene'].append(20)
    p['assigned']['2'] = [2, 3]; h.zeros.add((2, 3))
    masks.append([True, False, False, True, False])
    result = choose_probe(p, [0, 1, 2], masks, [0, 0, 0], h)
    assert result and result['changes'] == [[0, 4], [2, 3]]


def test_all_113_projections():
    p, h, _ = situation()
    p.update(ally_ids=[0, 1, 2, 3], ally_pos=[[2, 2], [3, 2], [4, 3], [4, 4]], ally_ene=[20]*4)
    p['assigned'].update({'2':[4, 3], '3':[4, 4]})
    stats = {}
    choose_probe(p, p['ally_ids'], [[True]*6 for _ in range(4)], [0]*4, h, stats=stats)
    assert stats['enumerated'] == 113


def test_scan_stops_at_first_proof_and_never_uses_future_or_hidden_data():
    p, _, masks = situation()
    rows = []
    for step, positions, score in [(49, [[1,2],[1,2]], 0),
                                    (50, [[1,2],[1,2]], 0),
                                    (51, [[2,2],[3,2]], 1)]:
        q = deepcopy(p); q.update(step=step, match_step=step, ally_pos=positions, own_points=score)
        mm = [[True,False,False,False,False]]*2 if step < 51 else masks
        rows.append(dict(status='decision', public=q,
                         units=[dict(uid=i, mask=mm[i], masked_argmax=0) for i in range(2)],
                         posthoc={'hidden_points': [[0,0]]}))
    result = scan_frames(rows)
    assert result['first'] and result['first']['step'] == 51
    for row in rows: row['posthoc'] = {'hidden_points': 'arbitrary conflicting truth'}
    assert scan_frames(rows + [{'status':'invalid_future_frame'}]) == result


def test_manifest_identity_checked_before_any_other_io(tmp_path):
    manifest = tmp_path/'manifest.json'; manifest.write_text('{}')
    with pytest.raises(ValueError, match='manifest identity'):
        validate_archive_manifest(manifest, tmp_path)
