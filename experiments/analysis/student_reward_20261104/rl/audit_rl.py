"""Read-only independent completed-run audit. Execute ONLY after data-ready signal."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from collections import Counter

for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[key] = '1'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--prepared', type=Path, required=True)
    ap.add_argument('--output-prefix', type=Path, required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(args.root.resolve()))
    import numpy as np
    import torch
    torch.set_num_threads(1)
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.model import QNet
    from scripts.experiment import state_sha256
    from scripts.night_train_pilot import tensor_sha256
    report = dict(status='running', checks=[], findings=[], arms={}, scope='Technical training audit; no gameplay strength claim')

    def check(ok, label):
        report['checks'].append(dict(name=label, passed=bool(ok)))
        if not ok:
            report['findings'].append(label)

    def finite(value):
        if isinstance(value, torch.Tensor):
            return bool(torch.isfinite(value).all())
        if isinstance(value, dict):
            return all(finite(x) for x in value.values())
        if isinstance(value, (tuple, list)):
            return all(finite(x) for x in value)
        if isinstance(value, float):
            return math.isfinite(value)
        return True

    try:
        base = args.prepared.resolve()
        manifest = read(base / 'manifest.json')
        check(sha(manifest['student']) == manifest['student_sha256'], 'Immutable student file SHA matches prepared source')
        for name, digest in manifest['pins']['code'].items():
            check(sha(args.root / name) == digest, f'Frozen source pin: {name}')
        for name, digest in manifest['pins']['protected'].items():
            check(sha(name) == digest, f'Protected file unchanged: {name}')
        source = torch.load(manifest['student'], map_location='cpu', weights_only=True)
        source_cfg = AgentConfig(**source['cfg']).to_dict()
        source_tensor = tensor_sha256(source['q'])
        check(source_cfg == manifest['source_config'], 'Prepared source config equals effective immutable source config')
        check(source_tensor == tensor_sha256(source['target_q']), 'Source Q and target tensors match')
        check(finite(source), 'Source checkpoint finite')
        cfgs = [manifest['arms'][a]['config'] for a in ('control', 'sap0')]
        check({k for k in cfgs[0] if cfgs[0][k] != cfgs[1][k]} == {'w_sap_hit'}, 'Exactly one arm config treatment field')
        check(cfgs[0]['w_sap_hit'] == source_cfg['w_sap_hit'] and cfgs[1]['w_sap_hit'] == 0, 'Assigned control/SAP-zero reward weights')
        names = ['solution92', 'sol92_sq', 'default', 'rush']
        rng = np.random.default_rng(29 + 3000)
        expected = [dict(phase=phase, game=g, seed=200000 + 29 * 10000 + offset + g // 2,
                         side=('player_0', 'player_1')[g % 2], opponent=names[rng.choice(4, p=[.6, .2, .1, .1])])
                    for phase, count, offset in (('prefill', 40, 5000), ('train', 160, 3000)) for g in range(count)]
        expected_vals = [dict(after_games=after, opponent=opp, seed=seed, side=side)
                         for after in (0, 160) for opp in ('default', 'solution92')
                         for seed in range(500000, 500004) for side in ('player_0', 'player_1')]
        raw = {}
        for arm, cfg in zip(('control', 'sap0'), cfgs):
            run = base / 'runs' / arm
            entry = manifest['arms'][arm]
            rows, vals = lines(run / 'rollouts.jsonl'), lines(run / 'validation_games.jsonl')
            audit, receipt, status = read(run / 'training_audit.json'), read(run / 'final_receipt.json'), read(run / 'status.json')
            raw[arm] = dict(rows=rows, audit=audit, receipt=receipt)
            check(len(rows) == 200 and [{k: r[k] for k in expected[0]} for r in rows] == expected, f'{arm}: actual 40/160 seeded side/opponent chronology')
            check([{k: r[k] for k in expected_vals[0]} for r in vals] == expected_vals, f'{arm}: exact 32 known-card validations')
            check(entry['rollout_plan'] == expected and manifest['validation_plan'] == expected_vals, f'{arm}: declared plans agree with independently reconstructed plans')
            intended = dict(source_cfg, frozen=False, lr=1e-4, rules_in_training=True, rules_in_training_all=True)
            if arm == 'sap0':
                intended['w_sap_hit'] = 0.
            check(cfg == intended, f'{arm}: complete effective config has only authorized overrides')
            initpath = base / 'init' / arm / 'weights' / 'agent.pth'
            init = torch.load(initpath, map_location='cpu', weights_only=True)
            check(sha(initpath) == entry['weights_sha256'] and set(p.name for p in initpath.parent.iterdir()) == {'agent.pth'}, f'{arm}: init unchanged with no replay files')
            check(set(init) == set(source) and init['cfg'] == cfg and not {'opt', 'buffer', 'replay'} & set(init), f'{arm}: initializer preserves source contract without optimizer/replay')
            check(tensor_sha256(init['q']) == tensor_sha256(init['target_q']) == source_tensor, f'{arm}: exact identical source tensor start')
            model = QNet(79, 6, hidden=512, dueling=cfg['dueling'])
            fresh_opt = state_sha256(torch.optim.Adam(model.parameters(), lr=1e-4).state_dict())
            initial, prefill = audit['initial'], audit['prefill']
            il = initial['learning']
            check(initial['q_tensor_sha256'] == initial['target_tensor_sha256'] == source_tensor
                  and il['optimizer_sha256'] == fresh_opt and il['replay']['size'] == il['replay']['pos'] == 0
                  and il['learn_steps'] == 0 and il['env_steps'] == 60000 and il['recent_losses'] == []
                  and il['config'] == cfg and il['learn_enabled'] and not il['autosave_on_terminate'], f'{arm}: actual fresh optimizer/replay/counters/start config')
            check(prefill == rows[39]['identity'] and prefill['learning']['replay']['size'] > cfg['learn_start'], f'{arm}: complete prefill exceeded learning threshold')
            chronology_ok = actions_ok = finite_ok = True
            for i, row in enumerate(rows):
                identity, act, reward = row['identity'], row['final_action_audit'], row['reward_audit']
                state = identity['learning']
                chronology_ok &= (state['env_steps'] == 60000 + (i + 1) * 303 and state['learn_steps'] == max(0, i + 1 - 40) * 150
                                  and state['config'] == cfg and state['learn_enabled'] == (i >= 40) and not state['autosave_on_terminate'])
                if i < 40:
                    chronology_ok &= (identity['q_tensor_sha256'] == identity['target_tensor_sha256'] == source_tensor and state['optimizer_sha256'] == fresh_opt)
                actions_ok &= (row['steps'] == 303 and row['point_counting_version'] == 2 and act['act_calls'] == act['update_calls'] == 303
                               and reward['transitions'] == act['checked_replay_transitions'] and len(act['transcript_sha256']) == 64
                               and len(row['policy_transcript']['action_state_sha256']) == 64)
                finite_ok &= finite(row)
            check(chronology_ok, f'{arm}: all actual learning states match 40 frozen prefill/160 learning games')
            check(actions_ok, f'{arm}: every303-step rollout has final-action/replay agreement evidence')
            check(finite_ok, f'{arm}: raw rollout numeric evidence finite')
            check(len(audit['validations']) == 2 and all(p['before'] == p['after'] and p['after_games'] == after
                  and p['before']['learning']['env_steps'] == 72120 + after * 303
                  and p['before']['learning']['learn_steps'] == after * 150 for p, after in zip(audit['validations'], (0, 160))), f'{arm}: both validations preserve learning/RNG identities')
            check(all(v['steps'] == 303 and v['point_counting_version'] == 2 and v['config'] == cfg and v['epsilon'] == 0
                      and v['learn_enabled'] is False and v['eval_rng_seed'] == 20261104 for v in vals), f'{arm}: validation config/epsilon/no-learning evidence')
            with (run / 'train.csv').open() as f:
                csvrows = list(csv.DictReader(f))
            check(len(csvrows) == 160 and all(int(r['game']) == i and int(r['seed']) == expected[40+i]['seed']
                and r['side'] == expected[40+i]['side'] and r['opponent'] == expected[40+i]['opponent']
                and int(r['steps']) == 303 and int(r['point_counting_version']) == 2 and int(r['learn_steps']) == (i+1)*150
                and int(r['env_steps']) == 72120+(i+1)*303 and float(r['epsilon']) == .05 and math.isfinite(float(r['mean_loss']))
                for i, r in enumerate(csvrows)), f'{arm}: independent training CSV budget and finite loss check')
            cp_path = run / 'weights' / 'agent.pth'
            cp = torch.load(cp_path, map_location='cpu', weights_only=True)
            check(finite(cp) and cp['feature_dim'] == 79 and cp['n_actions'] == 6 and cp['cfg'] == cfg
                  and cp['cfg']['hidden'] == 512 and not cp.get('ensemble') and not cp.get('ensemble_dims')
                  and cp['env_steps'] == 120600 and cp['learn_steps'] == 24000, f'{arm}: finite single512 final checkpoint and fixed counters')
            qhash, thash = tensor_sha256(cp['q']), tensor_sha256(cp['target_q'])
            end = audit['end']
            check(qhash != source_tensor and qhash == end['q_tensor_sha256'] == rows[-1]['identity']['q_tensor_sha256']
                  and thash == end['target_tensor_sha256'] == rows[-1]['identity']['target_tensor_sha256'], f'{arm}: final changed tensors match raw final live state')
            check(state_sha256(cp['opt']) == end['learning']['optimizer_sha256'] == rows[-1]['identity']['learning']['optimizer_sha256']
                  and len(cp['opt']['state']) == len(list(model.parameters()))
                  and all(set(s) == {'step', 'exp_avg', 'exp_avg_sq'} and s['step'].item() == 24000 for s in cp['opt']['state'].values()), f'{arm}: real Adam moments and all24000 update counters match final live state')
            model.load_state_dict(cp['q'], strict=True)
            check(tensor_sha256(model.state_dict()) == qhash, f'{arm}: independent strict QNet reload exact')
            model.load_state_dict(cp['target_q'], strict=True)
            check(tensor_sha256(model.state_dict()) == thash and end['reload_verified'] is True, f'{arm}: independent strict target reload exact; live Agent_x reload evidence present')
            required_evidence = {'training_audit.json', 'rollouts.jsonl', 'validation_games.jsonl', 'train.csv'}
            check(set(receipt['evidence_sha256']) == required_evidence and all(sha(run / n) == digest for n, digest in receipt['evidence_sha256'].items())
                  and sha(cp_path) == receipt['final_checkpoint_sha256'] and receipt['end'] == end, f'{arm}: persisted evidence/checkpoint receipt hashes agree')
            check(status['status'] == receipt['status'] == 'done' and receipt['arm'] == arm and receipt['config'] == cfg
                  and receipt['actual_prefill_games'] == 40 and receipt['actual_train_games'] == 160 and receipt['actual_validation_games'] == 32, f'{arm}: done labels agree with independently checked raw budget')
            exposure = {}
            for phase in ('prefill', 'train'):
                selected = [r['reward_audit'] for r in rows if r['phase'] == phase]
                exposure[phase] = {key: sum(r[key] for r in selected) for key in ('calls', 'transitions', 'sap_transitions', 'estimated_positive_hits', 'estimated_misses', 'removed_signed', 'removed_absolute', 'positive_to_nonpositive', 'actual_reward', 'owned_point_unit_steps')}
            report['arms'][arm] = dict(rollouts=len(rows), prefill=40, learning=160, validations=len(vals), learn_steps=cp['learn_steps'], env_steps=cp['env_steps'], final_checkpoint_sha256=sha(cp_path), final_q_tensor_sha256=qhash, source_q_tensor_sha256=source_tensor, q_changed=qhash != source_tensor, reward_exposure=exposure, opponent_counts=dict(Counter(r['opponent'] for r in rows)), validation_note='Known training-diagnostic cards; not fresh strength evidence')
        controls, treatments = raw['control']['rows'][:40], raw['sap0']['rows'][:40]
        check(all(c['final_action_audit']['transcript_sha256'] == t['final_action_audit']['transcript_sha256']
                  and c['policy_transcript']['action_state_sha256'] == t['policy_transcript']['action_state_sha256'] for c,t in zip(controls,treatments)), 'Paired prefill final/replay actions, SAP coordinates and feature-state transcripts identical')
        check(all(math.isclose(c['reward_audit']['actual_reward']-t['reward_audit']['actual_reward'],c['reward_audit']['removed_signed'],rel_tol=1e-7,abs_tol=1e-6)
                  and all(math.isclose(c['reward_audit'][k],t['reward_audit'][k],rel_tol=1e-9,abs_tol=1e-6) for k in c['reward_audit'] if k != 'actual_reward')
                  for c,t in zip(controls,treatments)), 'Paired prefill reward differences equal removed signed SAP contribution; all exposure counters match')
        transcript = state_sha256([[r['final_action_audit']['transcript_sha256'], r['policy_transcript']['action_state_sha256']] for r in controls])
        paired = read(base / 'paired_prefill.json')
        check(paired['status'] == 'matched' and paired['prefill_games'] == 40 and paired['prefill_action_sha256'] == transcript
                  and all(raw[a]['receipt']['prefill_action_sha256'] == transcript for a in raw), 'Paired publication matches independently rebuilt prefill digest')
        check(sha(manifest['student']) == manifest['student_sha256'], 'Student source unchanged through audit')
        report['paired_prefill_action_sha256'] = transcript
        report['status'] = 'passed' if not report['findings'] else 'failed'
    except Exception as exc:
        report['status'] = 'failed'
        report['findings'].append(f'{type(exc).__name__}: {exc}')
    args.output_prefix.with_suffix('.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    md = ['# Independent RL training audit', '', f"Status: **{report['status'].upper()}**.", '', f"Checks: {sum(c['passed'] for c in report['checks'])}/{len(report['checks'])} passed.", '', 'Read-only inspection of actual raw rollout/validation rows, optimizer state, checkpoints and frozen hashes. No games or training performed by this audit. Known-card validation is not evidence of generalization or superiority.', '']
    for arm, result in report['arms'].items():
        md += [f'## {arm}', '', f"{result['prefill']} prefill + {result['learning']} learning games; {result['validations']} known validation games; {result['learn_steps']} Adam updates; env_steps={result['env_steps']}. Q tensors changed: {result['q_changed']}.", '', '| Phase | SAP transitions | Removed signed | Removed absolute | Positive→nonpositive | Actual reward |', '|---|---:|---:|---:|---:|---:|']
        for phase,e in result['reward_exposure'].items():
            md.append(f"| {phase} | {e['sap_transitions']} | {e['removed_signed']:.6f} | {e['removed_absolute']:.6f} | {e['positive_to_nonpositive']} | {e['actual_reward']:.6f} |")
        md += ['', f"Checkpoint SHA256: `{result['final_checkpoint_sha256']}`", '']
    md += ['## Findings', ''] + (['- '+s for s in report['findings']] or ['No technical discrepancies found.'])
    md += ['', 'Reload scope: independently strictly reloaded Q and target into QNet and checked exact tensor hashes; also inspected recorded live Agent_x reload identity proof. Validation isolation and action/replay agreement are runtime audit evidence, cross-checked against raw rows, not reconstructed environment games.', '']
    args.output_prefix.with_suffix('.md').write_text('\n'.join(md))
    print(json.dumps(dict(status=report['status'], checks=len(report['checks']), findings=report['findings'])))
    return int(report['status'] != 'passed')


if __name__ == '__main__':
    raise SystemExit(main())
