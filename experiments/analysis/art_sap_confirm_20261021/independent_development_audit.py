"""Read-only independent development audit. No project/model imports or games."""
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import zipfile

import numpy as np

STUDY = Path(__file__).resolve().parent
ROOT = STUDY.parents[2]
STATE = json.loads((STUDY / 'execution_state.json').read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def storage_hashes(path):
    # No unpickling/model loading. Verify every serialized tensor storage directly.
    result = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            relative = name.split('/', 1)[1]
            if relative.startswith('data/'):
                digest = hashlib.sha256()
                with archive.open(name) as source:
                    while block := source.read(1024 * 1024):
                        digest.update(block)
                result[relative] = digest.hexdigest()
    assert result
    return result


HEAD = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert HEAD == STATE['head'] == '9c1efc7fe4e09e1738ff489292786fa535670174'
counts = {}
for group in ('source_hashes', 'input_hashes', 'protected_hashes'):
    for path, expected in STATE[group].items():
        assert sha(path) == expected, path
    counts[group] = len(STATE[group])

identity = json.loads(Path(STATE['candidate_identity']).read_text())
assert identity['source'] == STATE['v3_weights']
assert identity['candidate'] == STATE['candidate_weights']
assert identity['baseline_sha256'] == sha(STATE['v3_weights'])
assert identity['candidate_sha256'] == sha(STATE['candidate_weights'])
assert identity['changed_saved_config'] == {'art_sap': True, 'art_min_hits': 3}
assert identity['loaded_network_count'] == 18
assert identity['loaded_tensors_identical'] is True
assert identity['all_other_checkpoint_fields_identical'] is True
for key, value in {'art_sap': True, 'art_min_hits': 3, 'art_safe': True,
                   'art_reserve': 0, 'siege': False, 'threat_feats': False,
                   'joint_moves': False}.items():
    assert identity['effective_config'][key] == value, key
storages = storage_hashes(STATE['v3_weights'])
assert storages == storage_hashes(STATE['candidate_weights'])

freeze_fields = ('root', 'python', 'head', 'deadline', 'source_hashes',
                 'protected_hashes', 'input_hashes', 'v3_weights',
                 'candidate_weights', 'candidate_identity', 'historical_csvs',
                 'outputs', 'job_limits_seconds')
freeze_id = hashlib.sha256(json.dumps({k: STATE[k] for k in freeze_fields},
                                    sort_keys=True, separators=(',', ':')).encode()).hexdigest()
assert STATE['deadline'] == 1792638900
expected_keys = {(opp, seed, side) for opp in ('default', 'solution92')
                 for seed in range(500720, 500780)
                 for side in ('player_0', 'player_1')}


def key(row):
    return row['opponent'], int(row['seed']), row['side']


def load(path, required_keys=expected_keys):
    with Path(path).open(newline='') as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames
        rows = list(reader)
    assert len(rows) == len(required_keys) and len(columns) == 24
    assert {key(row) for row in rows} == required_keys
    assert len({key(row) for row in rows}) == len(rows)
    for row in rows:
        for field, raw in row.items():
            if field in ('side', 'opponent'):
                continue
            number = float(raw)
            assert math.isfinite(number) and number >= 0, (field, raw)
            if field.endswith('_frac'):
                assert number <= 1
        assert float(row['steps']) == 303
        assert float(row['point_counting_version']) == 2
        assert float(row['invalid_frac']) == 0
        ours, theirs = float(row['our_wins']), float(row['opp_wins'])
        assert ours == int(ours) and theirs == int(theirs) and ours + theirs <= 3
        assert float(row['result']) == (1 if ours > theirs else 0 if ours < theirs else 0.5)
        assert float(row['game_win']) == int(ours > theirs)
        ours, theirs = float(row['our_points']), float(row['opp_points'])
        assert float(row['point_win']) == (1 if ours > theirs else 0 if ours < theirs else 0.5)
    return columns, {key(row): row for row in rows}


tables = {}
comparisons = {}
job_checks = {}
for role in ('v3', 'candidate'):
    label = 'development_' + role
    path = STATE['outputs'][label]
    weights = STATE['v3_weights'] if role == 'v3' else STATE['candidate_weights']
    jobs = [job for job in STATE['jobs'] if job['label'] == label]
    assert len(jobs) == 1
    job = jobs[0]
    expected_argv = [STATE['python'], '-B', '-m', 'scripts.par_eval', '--weights',
                     weights, '--first', '720', '--n', '60', '--workers', '2',
                     '--opponents', 'default,solution92', '--out', path]
    assert job['argv'] == expected_argv
    assert job['returncode'] == 0 and job['rows'] == 240
    assert job['output'] == path
    assert job['output_sha256'] == job['observed_output_sha256_at_finish'] == sha(path)
    assert job['freeze_id'] == freeze_id
    assert job['verified_inputs_after'] is True and job['cleanup']['group_clear'] is True
    assert job['process_check_before'] == {'foreign_model_jobs': [], 'evaluation_workers': 0}
    assert 0 < job['finished_at'] - job['started_at'] <= 3600
    assert job['finished_at'] < STATE['deadline']
    fields, rows = load(path)
    old_fields, old_rows = load(STATE['historical_csvs'][role])
    assert fields == old_fields
    non_time = [field for field in fields if field != 'secs']
    assert len(non_time) == 23
    for row_key, row in rows.items():
        for field in non_time:
            assert row[field] == old_rows[row_key][field], (role, row_key, field)
    tables[role] = rows
    comparisons[role] = {'rows': 240, 'non_time_fields': 23,
                         'matched_values': 240 * 23, 'historical_exact': True,
                         'historical_sha256': sha(STATE['historical_csvs'][role]),
                         'new_sha256': sha(path)}
    job_checks[label] = {'argv': expected_argv, 'returncode': 0,
                         'elapsed_seconds': job['finished_at'] - job['started_at'],
                         'freeze_id': freeze_id, 'output_sha256': sha(path)}

statistics = {}
for opp in ('default', 'solution92'):
    counts_by_role = {}
    for role, table in tables.items():
        results = [float(row['result']) for row_key, row in table.items() if row_key[0] == opp]
        counts_by_role[role] = dict(zip(('wins', 'draws', 'losses'),
                                       (results.count(1), results.count(0.5), results.count(0))))
    # Whole-map pairing of true win indicators, not result score or individual rows.
    differences = []
    for seed in range(500720, 500780):
        sides = []
        for side in ('player_0', 'player_1'):
            candidate = float(tables['candidate'][(opp, seed, side)]['result']) == 1
            baseline = float(tables['v3'][(opp, seed, side)]['result']) == 1
            sides.append(int(candidate) - int(baseline))
        differences.append(sum(sides) / 2)
    differences = np.asarray(differences)
    rng = np.random.default_rng(0)
    draws = rng.choice(differences, size=(5000, 60), replace=True).mean(axis=1)
    statistics[opp] = {'maps': 60, 'games_per_agent': 120, **counts_by_role,
                       'true_win_delta': float(differences.mean()),
                       'paired_95_ci': np.percentile(draws, [2.5, 97.5]).tolist()}

passed = (statistics['solution92']['candidate']['wins'] >= 108 and
          statistics['solution92']['candidate']['wins'] - statistics['solution92']['v3']['wins'] >= 6 and
          statistics['default']['candidate']['wins'] == 120)
assert passed
direct_label = 'direct_development'
direct_path = STATE['outputs'][direct_label]
direct_jobs = [job for job in STATE['jobs'] if job['label'] == direct_label]
assert len(direct_jobs) == 1
direct_job = direct_jobs[0]
direct_opponent = 'self:' + STATE['v3_weights']
direct_argv = [STATE['python'], '-B', '-m', 'scripts.par_eval', '--weights',
               STATE['candidate_weights'], '--first', '720', '--n', '60',
               '--workers', '2', '--opponents', direct_opponent, '--out', direct_path]
assert direct_job['argv'] == direct_argv
assert direct_job['returncode'] == 0 and direct_job['rows'] == 120
assert direct_job['output'] == direct_path
assert direct_job['output_sha256'] == direct_job['observed_output_sha256_at_finish'] == sha(direct_path)
assert direct_job['freeze_id'] == freeze_id
assert direct_job['verified_inputs_after'] is True and direct_job['cleanup']['group_clear'] is True
assert direct_job['process_check_before'] == {'foreign_model_jobs': [], 'evaluation_workers': 0}
assert 0 < direct_job['finished_at'] - direct_job['started_at'] <= 1200
assert direct_job['finished_at'] < STATE['deadline']
direct_keys = {(direct_opponent, seed, side) for seed in range(500720, 500780)
               for side in ('player_0', 'player_1')}
direct_fields, direct_rows = load(direct_path, direct_keys)
assert direct_fields == fields
direct_results = [float(row['result']) for row in direct_rows.values()]
map_results = [sum(float(direct_rows[(direct_opponent, seed, side)]['result'])
                   for side in ('player_0', 'player_1')) / 2
               for seed in range(500720, 500780)]
rng = np.random.default_rng(0)
direct_draws = rng.choice(map_results, size=(5000, 60), replace=True).mean(axis=1)
direct_summary = dict(maps=60, games=120, wins=direct_results.count(1),
                      draws=direct_results.count(.5), losses=direct_results.count(0),
                      mean_result=float(np.mean(map_results)),
                      whole_map_95_ci=np.percentile(direct_draws, [2.5, 97.5]).tolist(),
                      output_sha256=sha(direct_path), argv=direct_argv,
                      elapsed_seconds=direct_job['finished_at'] - direct_job['started_at'],
                      returncode=0, development_direct_gate_passed=float(np.mean(map_results)) >= .5)
assert direct_summary['development_direct_gate_passed']
output = dict(head=HEAD, freeze_id=freeze_id, hash_checks=counts,
              candidate_sha256=identity['candidate_sha256'],
              candidate_receipt_sha256=sha(STATE['candidate_identity']),
              identical_serialized_tensor_storages=len(storages),
              identity_receipt_checks=True, comparisons=comparisons,
              jobs=job_checks, statistics=statistics, development_opponent_gate_passed=passed,
              direct_development=direct_summary, course_outside_this_audit=True,
              fresh_confirmation_outside_this_audit=True)
(STUDY / 'development_data_review.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps(output, indent=2))
