"""Build P from unchanged V14; PT additionally requires accepted four-arm evidence."""
from pathlib import Path
import argparse, copy, hashlib, json, sys

SOURCE_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def make_candidate(source, replacements):
    cp = copy.deepcopy(source)
    cp['cfg'].update(point_pair_swap=True, art_move_guard=True)
    for index, state in replacements.items():
        if index not in (18, 19):
            raise ValueError('Only fixed components18/19 are replaceable')
        cp['ensemble'][index-1] = copy.deepcopy(state)
    return cp


def build(root, source, audit_path, out, *, p_only=False):
    if p_only and audit_path is not None:
        raise ValueError('--p-only and a training audit are mutually exclusive')
    if not p_only and audit_path is None:
        raise ValueError('Full P/PT build requires the accepted four-arm training audit')
    import torch
    root, source, out = map(lambda p: Path(p).resolve(), (root, source, out))
    audit_path = Path(audit_path).resolve() if audit_path is not None else None
    sys.path.insert(0, str(root))
    from scripts.night_train_pilot import tensor_sha256
    from agents.sherlock.model import checkpoint_ensemble_dims
    assert sha(source) == SOURCE_SHA
    audit = None
    if not p_only:
        audit = json.loads(audit_path.read_text())
        assert audit['verdict'] == 'ACCEPTED' and not audit['failed'] and not audit['warnings']
        assert set(audit['arms']) == {'control18', 'adapt18', 'control19', 'adapt19'}
        for path, digest in audit['evidence_sha256'].items():
            assert sha(path) == digest, f'Accepted evidence changed: {path}'
    if out.exists():
        raise FileExistsError(out)
    assert not out.is_relative_to(root/'agents/sherlock/weights')
    assert out.is_relative_to(root/'experiments/ensembles')
    original = torch.load(source, map_location='cpu', weights_only=True)
    original_states = [original['q'], *original['ensemble']]
    assert len(original_states) == 36 and checkpoint_ensemble_dims(original, 79) == [79]*35
    hashes = [tensor_sha256(s) for s in original_states]
    replacements, final_hashes = {}, {}
    if not p_only:
        for index in (18, 19):
            final = root/f'experiments/runs/20261102_target_adapt{index}/weights/agent.pth'
            assert str(final) in audit['evidence_sha256'], 'Final checkpoint not independently bound'
            state = torch.load(final, map_location='cpu', weights_only=True)
            assert state['ensemble'] == [] and state['feature_dim'] == 79 and state['n_actions'] == 6
            assert state['learn_steps'] > 0
            replacements[index] = state['q']
            final_hashes[str(final)] = sha(final)
    manifest = dict(source=str(source), source_sha256=SOURCE_SHA, source_component_sha256=hashes,
                    training_audit_used=not p_only, replacement_input_sha256=final_hashes, candidates={})
    if audit is not None:
        manifest.update(audit_path=str(audit_path), audit_sha256=sha(audit_path))
    out.mkdir(parents=True, exist_ok=False)
    candidates = [('P', {})] if p_only else [('P', {}), ('PT', replacements)]
    for name, changes in candidates:
        cp = make_candidate(original, changes)
        states = [cp['q'], *cp['ensemble']]
        actual = [tensor_sha256(s) for s in states]
        assert len(states) == 36 and checkpoint_ensemble_dims(cp, 79) == [79]*35
        assert {i for i, (a, b) in enumerate(zip(hashes, actual)) if a != b} == set(changes)
        expected_cfg = dict(original['cfg'], point_pair_swap=True, art_move_guard=True)
        assert cp['cfg'] == expected_cfg
        for index, state in changes.items():
            assert actual[index] == tensor_sha256(state)
        target = out/f'{name}.pth'
        torch.save(cp, target)
        loaded = torch.load(target, map_location='cpu', weights_only=True)
        assert loaded['cfg'] == expected_cfg
        assert [tensor_sha256(s) for s in [loaded['q'], *loaded['ensemble']]] == actual
        manifest['candidates'][name] = dict(path=str(target), sha256=sha(target), components=actual,
                                           replaced_indices=list(changes), nets=36, weighting='equal 1/36',
                                           configuration=expected_cfg)
    assert sha(source) == SOURCE_SHA
    if audit is not None:
        for path, digest in audit['evidence_sha256'].items():
            assert sha(path) == digest
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False)+'\n')
    print(json.dumps({name:{'path':x['path'],'sha256':x['sha256'],'replaced_indices':x['replaced_indices']}
                      for name,x in manifest['candidates'].items()}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('root','source','out'):
        parser.add_argument('--'+flag, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--audit', help='Accepted full four-arm audit, required for the default P/PT build')
    mode.add_argument('--p-only', action='store_true', help='Build unchanged-tensor P only; no training audit or PT input')
    args = parser.parse_args()
    build(args.root,args.source,args.audit,args.out,p_only=args.p_only)


if __name__ == '__main__':
    main()
