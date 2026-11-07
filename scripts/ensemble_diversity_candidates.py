"""Assemble fixed November rosters only from six complete training receipts.

Inference artifacts contain no optimizer or replay continuation. Their normalized
counters are not a claim about training history, which remains in the receipts.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path

import torch

from agents.sherlock.config import AgentConfig
from scripts.final_battle_candidates import file_sha256, tensor_sha256, _validate_state
from scripts.network_breadth_candidates import load_checkpoint
from scripts.output_paths import checked_output

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
ARMS = ('A0', 'B0', 'A1', 'B1', 'A2', 'B2')
PARENTS = dict(zip(ARMS, (18, 18, 24, 24, 30, 30)))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def training_config(cfg):
    return dict(AgentConfig.from_dict(cfg).to_dict(), frozen=False, lr=5e-5,
                rules_in_training=True, rules_in_training_all=True, rescue_in_training=True)


def validate_arm(path, arm):
    from scripts.ensemble_diversity_train import validate_final_receipt
    return validate_final_receipt(path, arm=arm)


def build(source, training_state, out):
    source, training_state = (Path(p).resolve(strict=True) for p in (source, training_state))
    lexical = Path(out).absolute()
    require(not any(p.is_symlink() for p in (lexical, *lexical.parents)), 'Symlink output')
    out = checked_output(lexical, ROOT/'agents/sherlock/weights')
    require(out == (ROOT/'experiments/candidates/ensemble_diversity_20261107').resolve(),
            'Unexpected candidate destination')
    if out.exists():
        raise FileExistsError(out)
    require(source.is_relative_to(ROOT) and training_state.is_relative_to(ROOT), 'Inputs outside checkout')
    input_hashes = {str(p):file_sha256(p) for p in (source, training_state)}
    require(input_hashes[str(source)] == SOURCE_SHA, 'V14 SHA mismatch')
    cp, base, base_hashes, _ = load_checkpoint(source, 36)
    state = json.loads(training_state.read_text())
    require(state.get('status') == 'complete' and state.get('active') == [] and state.get('queue') == []
            and set(state.get('receipts', {})) == set(ARMS)
            and set(state.get('jobs', {})) == set(ARMS)
            and all(x.get('returncode') == 0 for x in state['jobs'].values()), 'Incomplete training wave')
    trained, arm_info = [], {}
    for arm in ARMS:
        entry = state['receipts'][arm]
        path = Path(entry['path']).resolve(strict=True)
        require(path.is_relative_to(ROOT) and file_sha256(path) == entry['sha256'], 'Receipt hash/path mismatch')
        receipt = validate_arm(path, arm)
        require(receipt['pins']['git_commit'] == state['expected_head'], 'Training source head mismatch')
        require(receipt['config'] == training_config(cp['cfg']), 'Training configuration mismatch')
        require(receipt['initial_tensor_sha256'] == base_hashes[PARENTS[arm]], 'Training parent mismatch')
        weights = path.parent/'weights/agent.pth'
        require(file_sha256(weights) == entry['final_checkpoint_sha256'], 'Final checkpoint hash mismatch')
        end = torch.load(weights, map_location='cpu', weights_only=True)
        _validate_state(end['q'], 256)
        require(end.get('feature_dim') == 79 and end.get('n_actions') == 6
                and end['cfg'] == training_config(cp['cfg']), 'Final model semantics mismatch')
        trained.append(end['q'])
        arm_info[arm] = dict(receipt=str(path.relative_to(ROOT)), receipt_sha256=entry['sha256'],
                             checkpoint=str(weights.relative_to(ROOT)), checkpoint_sha256=entry['final_checkpoint_sha256'],
                             tensor_sha256=tensor_sha256(end['q']), parent_index=PARENTS[arm])
        input_hashes.update({str(path):entry['sha256'], str(weights):entry['final_checkpoint_sha256']})
    all_states = base + trained
    all_hashes = [tensor_sha256(x) for x in all_states]
    require(len(set(all_hashes)) == 42, 'Duplicate tensor members after training')
    rosters = dict(A39=list(range(36))+[36,38,40], B39=list(range(36))+[37,39,41],
                   ALL42=list(range(42)),
                   REPLACE36=[i for i in range(36) if i not in (0,6,12,18,24,30)]+list(range(36,42)))
    manifest = dict(schema_version=1, status='admitted', created_utc=datetime.now(timezone.utc).isoformat(),
                    training_state=str(training_state.relative_to(ROOT)), training_state_sha256=input_hashes[str(training_state)],
                    training_head=state['expected_head'], arms=arm_info, non_nominable=['V14','REPLACE36'],
                    roles={'V14':dict(path=str(source.relative_to(ROOT)), sha256=SOURCE_SHA, net_count=36)},
                    source_hashes=input_hashes, builder_sha256=file_sha256(__file__),
                    counters='Inference normalization only; training evidence is in six complete receipts')
    out.mkdir(parents=True, exist_ok=False)
    for name, indices in rosters.items():
        selected = [all_states[i] for i in indices]
        artifact = dict(q=copy.deepcopy(selected[0]), target_q=copy.deepcopy(selected[0]),
                        ensemble=copy.deepcopy(selected[1:]), ensemble_dims=[79]*(len(selected)-1),
                        cfg=copy.deepcopy(cp['cfg']), feature_dim=79, n_actions=6, env_steps=60000, learn_steps=0)
        target = out/f'{name}.pth'
        with target.open('xb') as handle:
            torch.save(artifact, handle)
        saved, _, observed, _ = load_checkpoint(target, len(indices))
        require(observed == [all_hashes[i] for i in indices] and saved['cfg'] == cp['cfg']
                and tensor_sha256(saved['target_q']) == observed[0], 'Candidate reload differs')
        manifest['roles'][name] = dict(path=str(target.relative_to(ROOT)), sha256=file_sha256(target),
             net_count=len(indices), ordered_tensor_sha256=observed, roster_indices=indices,
             weighting=f'equal 1/{len(indices)}')
    require(all(file_sha256(p) == sha for p,sha in input_hashes.items()), 'Input changed during assembly')
    with (out/'manifest.json').open('x') as handle:
        json.dump(manifest, handle, indent=2, allow_nan=False)
        handle.write('\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'training-state', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    result = build(args.source, args.training_state, args.out)
    print(json.dumps({k:v['net_count'] for k,v in result['roles'].items()}))


if __name__ == '__main__':
    main()
