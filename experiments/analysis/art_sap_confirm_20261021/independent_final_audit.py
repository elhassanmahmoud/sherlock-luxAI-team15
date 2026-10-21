"""Independent final audit of six Art3 jobs; stdlib/NumPy only.

The unavailable predecessor left an extension of independent_development_audit.py
and a provisional independent_results.json. The replacement final reviewer read
both, strengthened the checks below, and reran this companion from raw artifacts.
No supplied analyzer, model, engine, pickle loader, or project module is imported.
Only independent_results.json is written. Git is used solely to read HEAD.
"""
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
STATE_BYTES_AT_START = (STUDY / 'execution_state.json').read_bytes()
CSV_FIELDS = ['seed', 'side', 'opponent', 'result', 'game_win', 'point_win',
              'our_wins', 'opp_wins', 'our_points', 'opp_points',
              'point_counting_version', 'wait_frac', 'invalid_frac',
              'greedy_masked_frac', 'sap_attempts', 'sap_hits', 'stack_frac',
              'relics_found', 'relics_seen', 'known_point_tiles',
              'belief_contradictions', 'unit_steps', 'steps', 'secs']
INTEGER_FIELDS = {'seed', 'game_win', 'our_wins', 'opp_wins', 'our_points',
                  'opp_points', 'point_counting_version', 'sap_attempts',
                  'sap_hits', 'relics_found', 'relics_seen', 'known_point_tiles',
                  'belief_contradictions', 'unit_steps', 'steps'}


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
assert counts == {'source_hashes': 83, 'input_hashes': 5, 'protected_hashes': 8}
assert STATE['root'] == str(ROOT)

identity = json.loads(Path(STATE['candidate_identity']).read_text())
assert identity['source'] == STATE['v3_weights']
assert identity['candidate'] == STATE['candidate_weights']
assert identity['baseline_sha256'] == sha(STATE['v3_weights'])
assert identity['candidate_sha256'] == sha(STATE['candidate_weights'])
assert identity['baseline_sha256'] == 'aac1c9101c6639e3e085398267d0bc448a4e47b482e68bfe8b01374d5288d935'
assert identity['candidate_sha256'] == 'e392f20c60d51817591ee4c0061bc8150e7ec8aa312b42e704004538ead45497'
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
assert len(storages) == 264

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
    assert len(rows) == len(required_keys) and columns == CSV_FIELDS
    assert {key(row) for row in rows} == required_keys
    assert len({key(row) for row in rows}) == len(rows)
    for row in rows:
        assert set(row) == set(CSV_FIELDS)
        for field, raw in row.items():
            if field in ('side', 'opponent'):
                continue
            number = float(raw)
            assert math.isfinite(number) and number >= 0, (field, raw)
            if field in INTEGER_FIELDS:
                assert number == int(number), (field, raw)
            if field.endswith('_frac'):
                assert number <= 1
        assert float(row['steps']) == 303
        assert float(row['point_counting_version']) == 2
        assert float(row['invalid_frac']) == 0
        assert float(row['result']) in (0, 0.5, 1)
        assert float(row['point_win']) in (0, 0.5, 1)
        assert 0 <= float(row['sap_hits']) <= float(row['sap_attempts']) <= float(row['unit_steps'])
        assert float(row['unit_steps']) <= 303 * 16
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
    assert not any(k in job for k in ('error', 'cleanup_error'))
    assert job['pid'] == job['pgid'] > 0 and job['owner_pid'] > 0
    assert job['cleanup'] == {'group_clear': True, 'sigkill_sent': False, 'sigterm_sent': False}
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

# Independently audit the remaining fixed course/fresh phases.
from datetime import datetime
labels = ['development_v3', 'development_candidate', 'direct_development',
          'course', 'fresh_v3', 'fresh_candidate']
assert [job['label'] for job in STATE['jobs']] == labels
assert STATE['active'] is None
assert not Path(STATE['outputs']['direct_fresh']).exists()
limits = {'development_v3': 3600, 'development_candidate': 3600,
          'direct_development': 1200, 'course': 600, 'fresh_v3': 3600,
          'fresh_candidate': 3600, 'direct_fresh': 2400}
assert STATE['job_limits_seconds'] == limits
counts_per_job = {'development_v3': 240, 'development_candidate': 240,
                  'direct_development': 120, 'course': 8,
                  'fresh_v3': 800, 'fresh_candidate': 800, 'direct_fresh': 400}
all_planned = labels + ['direct_fresh']
previous_finish = 0
all_jobs = {}
for index, job in enumerate(STATE['jobs']):
    label = job['label']
    path = STATE['outputs'][label]
    weights = STATE['v3_weights'] if label in ('development_v3','fresh_v3') else STATE['candidate_weights']
    argv = [STATE['python'], '-B', '-m']
    if label == 'course':
        argv += ['scripts.check_candidate_runner', '--weights', weights, '--out', path]
    else:
        first, n = ('23000', '200') if label.startswith('fresh') else ('720', '60')
        opponents = 'self:' + STATE['v3_weights'] if label == 'direct_development' else 'default,solution92'
        argv += ['scripts.par_eval', '--weights', weights, '--first', first, '--n', n,
                 '--workers', '2', '--opponents', opponents, '--out', path]
    assert job['argv'] == argv
    assert job['output'] == path
    assert job['returncode'] == 0 and job.get('games',job.get('rows')) == counts_per_job[label]
    assert job['output_sha256'] == job['observed_output_sha256_at_finish'] == sha(path)
    assert job['freeze_id'] == freeze_id
    assert job['verified_inputs_after'] is True and job['cleanup']['group_clear'] is True
    assert not any(k in job for k in ('error', 'cleanup_error'))
    assert job['pid'] == job['pgid'] > 0 and job['owner_pid'] > 0
    assert job['cleanup'] == {'group_clear': True, 'sigkill_sent': False, 'sigterm_sent': False}
    assert Path(job['log']) == STUDY / (label + '.log') and Path(job['log']).is_file()
    assert job['process_check_before'] == {'foreign_model_jobs': [], 'evaluation_workers': 0}
    assert job['started_at'] > previous_finish
    assert 0 < job['finished_at'] - job['started_at'] <= limits[label]
    assert job['finished_at'] < STATE['deadline']
    admission = job['admission']
    assert admission['historical_v3_sha256'] == comparisons['v3']['historical_sha256']
    assert admission['historical_max_secs'] == 4.94 and admission['reserve_factor'] == 1.2
    assert admission['startup_allowance_per_job_seconds'] == 60
    estimates = {remaining: math.ceil(4.94*counts_per_job[remaining]/(1 if remaining=='course' else 2)*1.2+60)
                 for remaining in all_planned[index:]}
    assert admission['remaining_job_estimates_seconds'] == estimates
    assert job['started_at'] + sum(estimates.values()) + 300 < STATE['deadline']
    assert job['started_at'] + limits[label] + 300 < STATE['deadline']
    previous_finish = job['finished_at']
    all_jobs[label] = {'argv':argv, 'games':counts_per_job[label], 'returncode':0,
                       'elapsed_seconds':job['finished_at']-job['started_at'],
                       'output_sha256':sha(path), 'freeze_id':freeze_id,
                       'started_at': job['started_at'], 'finished_at': job['finished_at'],
                       'cleanup': job['cleanup'], 'process_check_before': job['process_check_before'],
                       'pid': job['pid'], 'pgid': job['pgid'], 'owner_pid': job['owner_pid'],
                       'admission_all_remaining_jobs_fit':True}

course = json.loads(Path(STATE['outputs']['course']).read_text())
assert set(course) == {'status', 'games', 'unchanged_sha256', 'course_time_limit',
                       'max_rss_bytes_macos', 'notes'}
assert course['status'] == 'passed' and len(course['games']) == 8
assert isinstance(course['max_rss_bytes_macos'], int) and course['max_rss_bytes_macos'] > 0
course_keys = {(opp,seed,side) for opp in ('default','solution92')
               for seed in (500720,500721) for side in ('player_0','player_1')}
assert {key(row) for row in course['games']} == course_keys
for row in course['games']:
    assert set(row) == {'side', 'opponent', 'seed', 'fresh_belief',
                        'loaded_model_verified', 'steps', 'act_ms'}
    assert type(row['seed']) is int and type(row['steps']) is int
    assert row['fresh_belief'] is True and row['loaded_model_verified'] is True
    assert row['steps'] == 303
    assert set(row['act_ms']) == {'median','p95','max'}
    median,p95,maximum = (row['act_ms'][k] for k in ('median','p95','max'))
    assert all(math.isfinite(x) for x in (median,p95,maximum))
    assert 0 <= median <= p95 <= maximum
    assert p95 <= 50 and maximum <= 250
for path, expected in course['unchanged_sha256'].items():
    assert sha(path) == expected
expected_course_paths = {str(ROOT/'agents/sherlock/weights/agent_p0.pth'),
                         str(ROOT/'agents/sherlock/weights/agent_p1.pth'),
                         STATE['candidate_weights'],str(ROOT/'Paths.csv'),str(ROOT/'lux/runner.py')}
assert set(course['unchanged_sha256']) == expected_course_paths
course_summary = dict(games=8, complete_keys=True, all_steps_303=True,
                      exact_top_level_and_game_schemas=True,
                      all_fresh_belief=True, all_loaded_verified=True,
                      max_p95_ms=max(r['act_ms']['p95'] for r in course['games']),
                      max_action_ms=max(r['act_ms']['max'] for r in course['games']),
                      fixed_time_gates_passed=True, hash=sha(STATE['outputs']['course']),
                      limitation=course['course_time_limit'], notes=course['notes'])

fresh_keys = {(opp,seed,side) for opp in ('default','solution92')
              for seed in range(523000,523200) for side in ('player_0','player_1')}
fresh_tables = {}
for role in ('v3','candidate'):
    fresh_fields, fresh_rows = load(STATE['outputs']['fresh_'+role], fresh_keys)
    assert fresh_fields == fields
    fresh_tables[role] = fresh_rows
fresh_stats = {}
for opp in ('default','solution92'):
    totals = {}
    for role,table in fresh_tables.items():
        values = [float(row['result']) for k,row in table.items() if k[0]==opp]
        totals[role] = dict(wins=values.count(1), draws=values.count(.5), losses=values.count(0))
    deltas = []
    flips = {'loss_or_draw_to_win':0,'win_to_loss_or_draw':0}
    for seed in range(523000,523200):
        sides=[]
        for side in ('player_0','player_1'):
            candidate=int(float(fresh_tables['candidate'][(opp,seed,side)]['result'])==1)
            baseline=int(float(fresh_tables['v3'][(opp,seed,side)]['result'])==1)
            delta=candidate-baseline
            sides.append(delta)
            if delta==1:flips['loss_or_draw_to_win']+=1
            if delta==-1:flips['win_to_loss_or_draw']+=1
        deltas.append(sum(sides)/2)
    rng=np.random.default_rng(0)
    samples=rng.choice(deltas,size=(5000,200),replace=True).mean(axis=1)
    fresh_stats[opp]=dict(maps=200,games_per_agent=400,**totals,
                          true_win_delta=float(np.mean(deltas)),
                          paired_95_ci=np.percentile(samples,[2.5,97.5]).tolist(),flips=flips)
sol=fresh_stats['solution92'];default=fresh_stats['default']
gates=dict(solution_delta_at_least_5pp=sol['true_win_delta']>=.05,
           solution_lower_bound_strictly_positive=sol['paired_95_ci'][0]>0,
           default_winrate_at_least_99pct=default['candidate']['wins']/400>=.99,
           default_delta_at_least_minus1pp=default['true_win_delta']>=-.01)
assert not all(gates.values())
seed_audit=json.loads((STUDY/'seed_audit_pre_fresh.json').read_text())
assert seed_audit['seed_interval']==[523000,523399]
assert seed_audit['hits']==[] and seed_audit['errors']==[]
assert seed_audit['reserved_by_mahmoud']==[503220,503819]
assert datetime.fromisoformat(seed_audit['at_utc']).timestamp()<STATE['jobs'][4]['started_at']
assert STATE['jobs'][3]['finished_at'] < datetime.fromisoformat(seed_audit['at_utc']).timestamp()

# A separately constructed index-resampling crosscheck: reconstruct a 200x2
# binary win matrix per agent from keyed raw rows, then draw map indices. This
# uses neither the study analyzer nor the earlier deltas list.
crosscheck = {}
for opponent in ('default', 'solution92'):
    matrices = {role: np.array([[int(float(fresh_tables[role][(opponent, seed, side)]['result']) == 1)
                               for side in ('player_0', 'player_1')]
                              for seed in range(523000, 523200)], dtype=np.int64)
                for role in ('v3', 'candidate')}
    map_means = (matrices['candidate'] - matrices['v3']).mean(axis=1)
    indices = np.random.default_rng(0).integers(0, 200, size=(5000, 200))
    interval = np.percentile(map_means[indices].mean(axis=1), [2.5, 97.5]).tolist()
    assert interval == fresh_stats[opponent]['paired_95_ci']
    assert float(map_means.mean()) == fresh_stats[opponent]['true_win_delta']
    crosscheck[opponent] = {'delta': float(map_means.mean()), 'ci95': interval,
                           'method': 'independently reconstructed win matrices and resampled map indices'}

output.pop('course_outside_this_audit')
output.pop('fresh_confirmation_outside_this_audit')
output.update(jobs=all_jobs,course=course_summary,fresh=fresh_stats,fresh_gates=gates,
              total_completed_games=sum(counts_per_job[label] for label in labels),
              fresh_opponent_gate_passed=False,promotion_allowed=False,
              direct_fresh_not_started=True,direct_fresh_file_absent=True,
              direct_fresh_reserved_maps=[523200,523399],
              fresh_maps_consumed=[523000,523199],
              seed_audit_record_checked=True,
              no_retry_or_extension_per_fixed_plan=True,
              execution_state_status_at_review=STATE['status'],
              execution_state_active_is_none=True)
assert output['total_completed_games']==2208
assert (STUDY / 'execution_state.json').read_bytes() == STATE_BYTES_AT_START
for group in ('source_hashes', 'input_hashes', 'protected_hashes'):
    for path, expected in STATE[group].items():
        assert sha(path) == expected, path
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == HEAD
output.update(
    audit_status='passed; candidate fails the fixed fresh acceptance gates',
    audit_scope='all six completed jobs, 2208 games; no models, engines, games, or project imports',
    reviewer='replacement independent final reviewer art_final_data_review',
    predecessor_artifacts={
        'inspection': 'Both files existed at handoff; reviewed and strengthened, not accepted as a finished review.',
        'independent_final_audit_py_sha256_before_review': '54cc3aa5d8280ed07e41669a9f2e2cb56f5cee6ecdfd2027878dbdc724ebae5c',
        'independent_results_json_sha256_before_review': '4ace60ce9984b6b537c11d9d24faa12b68954d8099b16b598fd301796334068d',
        'authorship_limit': 'Unavailable predecessor attribution comes from handoff; files carry no authenticated author record.'},
    bootstrap={'samples': 5000, 'rng': 'numpy.default_rng(0)', 'numpy_version': np.__version__,
               'percentiles': [2.5, 97.5], 'percentile_method': 'linear',
               'unit': 'whole map, both sides retained; true-win indicator differences'},
    independent_index_resampling_crosscheck=crosscheck,
    csv_schema=CSV_FIELDS,
    execution_state_sha256=hashlib.sha256(STATE_BYTES_AT_START).hexdigest(),
    execution_state_bytes_unchanged_during_audit=True,
    final_frozen_hashes_rechecked=True,
    final_hash_details={group: STATE[group] for group in ('source_hashes', 'input_hashes', 'protected_hashes')},
    direct_fresh_gate='not evaluated; correctly skipped after failed opponent gates',
    fresh_seed_use_limit='Unused direct block is supported by job/output absence and scoped seed records, not a global external-use guarantee',
    process_evidence_limit='Historical argv/process/freeze/cleanup events are launcher records, not an independently reconstructed live trace',
    loading_evidence_limit='No independent model instantiation or unpickling; loading/structured equality use frozen receipt and inspected creation/runner code; 264 storage payloads compared independently',
    course_evidence_limit='Recorded shape/finiteness/integer action/type checks and measured times; no exhaustive semantic legality, hidden-state audit, or official course time-limit certification',
    audit_script_sha256=sha(__file__))
(STUDY/'independent_results.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'games':output['total_completed_games'],'fresh':fresh_stats,'gates':gates,
                  'course':course_summary,'hashes':counts,'jobs':{k:{z:v[z] for z in ('games','elapsed_seconds','output_sha256')} for k,v in all_jobs.items()}},indent=2))
