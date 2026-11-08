"""Pure, synthetic checks; these tests never load a model or run a game."""
import copy
import json

import numpy as np
import pytest

from scripts import holder_learning as h


def candidate(energy=200.0):
    energy_map = np.zeros((5, 5)).tolist()
    energy_map[1][1], energy_map[2][1] = -10, 40
    nebula = np.zeros((5, 5), bool).tolist()
    nebula[2][1] = True
    return dict(uid=0, proposal=2, q=[4., 2., 6., None, None, None],
                mask=[True, True, True, False, False, False], features=['unused'],
                public=dict(ally_pos=[[1, 1]], ally_ene=[energy], move_cost=3,
                            sap_cost=50, sap_range=1, match_step=20, max_match_steps=100,
                            own_points=10, opp_points=10, energy_map=energy_map, nebula=nebula,
                            enemy_coords=[[1, 1], [2, 1], [1, 2], [1, 1]],
                            enemy_energies=[50, 100, 20, -1]))


def provenance():
    return dict(baseline_sha256='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8',
                source_identity={'scripts/a.py': 'a' * 64}, training_manifest_sha256='b' * 64,
                training_artifacts={'pairs.json': 'c' * 64})


def rows(nmaps=12, per_map=8):
    return [dict(seed=s, side=f'player_{i % 2}', candidate=candidate(100 if i % 2 == 0 else 300),
                 label=2. if i % 2 == 0 else -1.)
            for s in range(nmaps) for i in range(per_map)]


def neutral_head():
    head, _ = h.fit_head(rows(), provenance=provenance())
    head['coefficients'] = [0.] * 16
    head['intercept'] = 0.
    return head


def test_features_use_exact_public_formulas_and_float64():
    actual = h.feature_vector(candidate())
    expected = [.5, .5, .6, 1., .81, 0., -.5, 1., 0., 1.,
                2 / 16, 2 / 16, 120 / 6400, 50 / 6400, 50 / 6400, 100 / 6400]
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-15)
    assert actual.dtype == np.float64


def test_features_ignore_hidden_and_nonpublic_candidate_fields():
    a, b = candidate(), candidate()
    b.update(seed='secret', side='secret', label=1e9, branch=object(), features=object())
    b['public'].update(nebula_estimate=object(), sensor_mask=object(), energy_observation_age=object())
    np.testing.assert_array_equal(h.feature_vector(a), h.feature_vector(b))
    # Canonical observations of either side carry the same information, regardless of UID.
    b['uid'] = 1
    b['public']['ally_pos'].append([1, 1])
    b['public']['ally_ene'].append(200)
    np.testing.assert_array_equal(h.feature_vector(a), h.feature_vector(b))


def test_features_clip_only_specified_fields_and_handle_zero_q_span():
    c = candidate(1000)
    c['q'] = [2., 2., 2., None, None, None]
    c['public'].update(move_cost=10, sap_cost=100, own_points=30, opp_points=10)
    x = h.feature_vector(c)
    np.testing.assert_allclose(x[:6], [0., 1., 2., 2., .81, np.tanh(1)])


@pytest.mark.parametrize('mutation', ['legal_none', 'illegal_finite', 'nan', 'stay', 'proposal', 'outside'])
def test_feature_rejects_malformed_q_or_invalid_move(mutation):
    c = candidate()
    if mutation == 'legal_none': c['q'][0] = None
    if mutation == 'illegal_finite': c['q'][3] = 5.
    if mutation == 'nan': c['q'][1] = float('nan')
    if mutation == 'stay': c['mask'][0] = False; c['q'][0] = None
    if mutation == 'proposal': c['proposal'] = 5
    if mutation == 'outside': c['public']['ally_pos'][0] = [4, 1]
    with pytest.raises(ValueError): h.feature_vector(c)


def test_fit_map_weights_population_normalization_and_unpenalized_intercept():
    data = rows()
    # One map has twice as many observations, but retains exactly 1/12 of total weight.
    data += copy.deepcopy(data[:8])
    head, report = h.fit_head(data, provenance=provenance())
    assert report['pairs'] == 104
    assert report['represented_maps'] == 12
    assert report['positive_labels'] == 52
    assert head['mean'][1] == pytest.approx(.5)
    assert head['scale'][1] == pytest.approx(.25)
    assert head['scale'][0] == 1.
    # y=.5-1.5*z; weighted ridge solution shrinks coefficient by 1/1.1.
    assert head['intercept'] == pytest.approx(.5)
    assert head['coefficients'][1] == pytest.approx(-1.5 / 1.1)
    assert head['provenance'] == provenance()
    assert h.validate_head(json.loads(json.dumps(head))) == head


def test_map_weights_do_not_allow_one_dense_map_to_dominate():
    data = rows()
    for row in data: row['candidate'] = candidate()
    for row in data: row['label'] = 12. if row['seed'] == 0 else 1.
    data += copy.deepcopy(data[:8]) * 20
    head, _ = h.fit_head(data, provenance=provenance())
    assert head['intercept'] == pytest.approx(23 / 12)
    assert np.max(np.abs(head['coefficients'])) < 1e-20


@pytest.mark.parametrize('kind', ['pairs', 'maps', 'positive_labels', 'positive_maps'])
def test_fixed_training_minima_reject_insufficient_data(kind):
    data = rows()
    if kind == 'pairs': data = data[:-1]
    if kind == 'maps': data = rows(nmaps=11, per_map=10)
    if kind == 'positive_labels':
        for i, row in enumerate(data): row['label'] = float(i < 11)
    if kind == 'positive_maps':
        for row in data: row['label'] = float(row['seed'] < 5)
    with pytest.raises(h.InsufficientTrainingData): h.fit_head(data, provenance=provenance())


def test_zero_and_negative_labels_are_kept_in_fit():
    data = rows()
    for row in data:
        row['candidate'] = candidate()
        row['label'] = [2., 0., -4., 2.][row['seed'] % 4]
    head, report = h.fit_head(data, provenance=provenance())
    assert head['intercept'] == pytest.approx(0.)
    assert report['pairs'] == 96


def test_fit_is_detached_from_validation_and_provenance_objects():
    data, prov = rows(), provenance()
    first, _ = h.fit_head(data, provenance=prov)
    validation = rows(nmaps=8)
    for row in validation: row['label'] *= -1000
    second, _ = h.fit_head(data, provenance=prov)
    assert second == first
    prov['source_identity']['scripts/a.py'] = 'changed'
    assert first['provenance'] == provenance()


def test_predict_uses_training_scaling_clips_z_and_zero_head_is_neutral():
    head = neutral_head()
    assert h.predict_gain(head, candidate()) == 0.
    head['coefficients'][1] = 2.
    head['scale'][1] = .01
    assert h.predict_gain(head, candidate(400)) == 10.


@pytest.mark.parametrize('key,value', [
    ('schema_version', 2), ('feature_version', 'wrong'), ('feature_names', ['bad'] * 16),
    ('eligibility_version', 'wrong'), ('cadence', {}), ('horizon', 13),
    ('mean', [float('nan')] * 16), ('scale', [0.] * 16),
    ('coefficients', [0.] * 15), ('intercept', float('inf')),
    ('ridge_alpha', .2), ('threshold', 0.), ('baseline_sha256', 'bad'),
])
def test_malformed_head_is_rejected(key, value):
    head = neutral_head()
    head[key] = value
    with pytest.raises(ValueError): h.validate_head(head)


def test_head_rejects_missing_unknown_or_false_baseline_provenance():
    head = neutral_head()
    del head['mean']
    with pytest.raises(ValueError): h.validate_head(head)
    head = neutral_head()
    head['unknown'] = 1
    with pytest.raises(ValueError): h.validate_head(head)
    for value in ['bad', None]:
        prov = provenance(); prov['baseline_sha256'] = value
        with pytest.raises(ValueError): h.fit_head(rows(), provenance=prov)


def validation_rows():
    return [dict(seed=s, side=f'player_{i % 2}', candidate=candidate(), label=2.)
            for s in range(8) for i in range(4)]


def test_validation_all_maps_bootstrap_mse_and_fixed_gates():
    head = neutral_head(); head['intercept'] = 2.
    report = h.validation_report(head, validation_rows(), list(range(8)))
    assert report['passed'] is True
    assert report['selected'] == 32
    assert report['selected_positive'] == 32
    assert report['selected_zero'] == report['selected_negative'] == 0
    assert report['total_selected_gain'] == 64.
    assert report['selected_mean_gain'] == 2.
    assert report['map_gains'] == [{'seed': i, 'gain': 4.} for i in range(8)]
    assert report['mean_map_gain'] == report['bootstrap_lower_025'] == 4.
    assert report['weighted_mse'] == report['unweighted_mse'] == 0.


def test_validation_strict_threshold_and_zero_pair_maps_count_as_zero():
    head = neutral_head(); head['intercept'] = 1.
    report = h.validation_report(head, validation_rows(), range(8))
    assert report['selected'] == 0
    assert report['selected_mean_gain'] is None
    assert report['passed'] is False
    head['intercept'] = 1.000001
    data = validation_rows()
    for row in data: row['seed'] %= 4
    for row in data: row['label'] = 2.
    report = h.validation_report(head, data, range(8))
    assert report['selected_maps'] == 4
    assert [m['gain'] for m in report['map_gains']] == [8., 8., 8., 8., 0., 0., 0., 0.]
    assert report['mean_map_gain'] == 4.
    assert report['bootstrap_lower_025'] == 1.
    assert report['passed'] is True


def test_validation_retains_negative_zero_unselected_and_does_not_change_head():
    head = neutral_head(); head['intercept'] = 2.
    before = copy.deepcopy(head)
    data = validation_rows()
    for i, row in enumerate(data): row['label'] = [2., 0., -1., 3.][i % 4]
    report = h.validation_report(head, data, range(8))
    assert report['selected_positive'] == 16
    assert report['selected_zero'] == report['selected_negative'] == 8
    assert report['total_selected_gain'] == 32.
    assert report['weighted_mse'] == report['unweighted_mse'] == 3.5
    assert head == before


@pytest.mark.parametrize('kind', ['seven_maps', 'duplicate_map', 'unknown_seed', 'bad_side', 'nonfinite_label'])
def test_validation_rejects_bad_keys_and_labels(kind):
    data, seeds = validation_rows(), list(range(8))
    if kind == 'seven_maps': seeds = seeds[:-1]
    if kind == 'duplicate_map': seeds[-1] = 0
    if kind == 'unknown_seed': data[0]['seed'] = 99
    if kind == 'bad_side': data[0]['side'] = 'wrong'
    if kind == 'nonfinite_label': data[0]['label'] = float('nan')
    with pytest.raises(ValueError): h.validation_report(neutral_head(), data, seeds)


def test_no_visible_enemy_and_flat_q_produce_zero_enemy_features():
    c = candidate()
    c['public'].update(enemy_coords=[], enemy_energies=[])
    x = h.feature_vector(c)
    np.testing.assert_array_equal(x[10:], np.zeros(6))


def test_enemy_features_use_chebyshev_for_range_and_manhattan_for_adjacency():
    c = candidate()
    c['public'].update(enemy_coords=[[0, 0], [3, 2], [1, 2], [1, 1]],
                       enemy_energies=[50, 50, 49, -100])
    x = h.feature_vector(c)
    # (0,0) can shoot current p diagonally; (3,2) can shoot destination diagonally.
    np.testing.assert_allclose(x[10:], [1 / 16, 1 / 16, 49 / 6400, 0., 0., 0.])


@pytest.mark.parametrize('field', ['schema_version', 'horizon', 'threshold', 'ridge_alpha', 'intercept'])
def test_head_rejects_boolean_numeric_fields(field):
    head = neutral_head()
    head[field] = True
    with pytest.raises(ValueError): h.validate_head(head)


def test_head_rejects_float_cadence_integer_fields_and_bool_array_elements():
    head = neutral_head()
    head['cadence']['max_opportunities'] = 8.0
    with pytest.raises(ValueError): h.validate_head(head)
    head = neutral_head()
    head['mean'][0] = True
    with pytest.raises(ValueError): h.validate_head(head)


def test_provenance_requires_finite_exact_json_without_silent_key_conversion():
    prov = provenance(); prov['source_identity'] = {1: 'would change into string'}
    with pytest.raises(ValueError): h.fit_head(rows(), provenance=prov)
    prov = provenance(); prov['metadata'] = float('nan')
    with pytest.raises(ValueError): h.fit_head(rows(), provenance=prov)


def test_validation_empty_is_failed_screen_with_eight_zero_map_gains():
    report = h.validation_report(neutral_head(), [], range(8))
    assert report['passed'] is False
    assert report['pairs'] == report['selected'] == 0
    assert report['weighted_mse'] is report['unweighted_mse'] is None
    assert [m['gain'] for m in report['map_gains']] == [0.] * 8
    assert report['bootstrap_lower_025'] == 0.


def test_validation_mse_map_weighting_and_all_unselected_rows_remain_in_report():
    head = neutral_head()
    data = validation_rows()
    for row in data: row['label'] = 0.
    data += [dict(seed=0, side='player_0', candidate=candidate(), label=4.)] * 4
    report = h.validation_report(head, data, range(8))
    assert report['pairs'] == 36
    assert report['selected'] == 0
    assert report['weighted_mse'] == 1.
    assert report['unweighted_mse'] == pytest.approx(16 / 9)


@pytest.mark.parametrize('kind,gate', [('pairs', 'minimum_pairs'), ('maps', 'minimum_maps'),
                                     ('selected', 'minimum_selected'), ('selected_maps', 'minimum_selected_maps'),
                                     ('negative', 'positive_mean_map_gain'), ('uncertain', 'positive_bootstrap_lower')])
def test_validation_each_predeclared_gate_can_fail_independently(kind, gate):
    head = neutral_head(); head['intercept'] = 2.
    data = validation_rows()
    if kind == 'pairs': data = data[:-1]
    if kind in ('maps', 'selected_maps'):
        for row in data: row['seed'] %= 3
    if kind == 'selected': head['intercept'] = 1.
    if kind == 'negative':
        for row in data: row['label'] = -1.
    if kind == 'uncertain':
        for row in data: row['label'] = 100. if row['seed'] == 0 else -1.
    report = h.validation_report(head, data, range(8))
    assert report['gates'][gate] is False
    assert report['passed'] is False


def test_exact_positive_label_and_map_minima_are_accepted():
    data = rows()
    for i, row in enumerate(data):
        row['label'] = float(row['seed'] < 6 and i % 8 < 2)
    head, report = h.fit_head(data, provenance=provenance())
    assert report['positive_labels'] == 12
    assert report['positive_maps'] == 6
    assert report['passed'] is True
    assert np.isfinite(head['intercept'])


@pytest.mark.parametrize('variation,expected_scale', [(.0001, 1.), (.0008, .000002)])
def test_training_population_std_uses_scale_one_only_below_one_micro(variation, expected_scale):
    data = rows()
    for i, row in enumerate(data):
        row['candidate'] = candidate(200 + (variation if i % 2 else -variation))
    head, _ = h.fit_head(data, provenance=provenance())
    assert head['mean'][1] == pytest.approx(.5)
    assert head['scale'][1] == pytest.approx(expected_scale)
