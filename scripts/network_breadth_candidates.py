"""Build exactly SOLO28 and FO42, preserving raw V14 inference configuration.

Trusted local checkpoints only. Sources are read-only; outputs are new inference
artifacts, never optimizer/replay continuations or new training histories.
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
from scripts.output_paths import checked_output

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = '98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
HIDDEN = 256
PLAY_KEYS = ('hidden', 'dueling', 'use_sap', 'use_belief', 'canonical', 'mask_actions', 'threat_feats')


def load_checkpoint(path, count):
    cp = torch.load(path, map_location='cpu', weights_only=True)
    if (not isinstance(cp, dict) or cp.get('feature_dim') != 79 or cp.get('n_actions') != 6
            or not isinstance(cp.get('cfg'), dict) or not isinstance(cp.get('ensemble'), list)
            or len(cp['ensemble']) != count - 1):
        raise ValueError(f'Expected {count} members with 79 features and six actions')
    cfg = AgentConfig.from_dict(cp['cfg']).to_dict()
    if (type(cfg['hidden']) is not int or cfg['hidden'] != HIDDEN or cfg['dueling'] is not True
            or cfg['threat_feats'] is not False):
        raise ValueError('Incompatible DuelingDQN architecture/feature semantics')
    if cp.get('ensemble_dims') not in (None, []) and cp['ensemble_dims'] != [79] * (count - 1):
        raise ValueError('Incompatible ensemble feature dimensions')
    states = [cp['q'], *cp['ensemble']]
    for state in states:
        _validate_state(state, HIDDEN)
    hashes = [tensor_sha256(state) for state in states]
    if len(set(hashes)) != count:
        raise ValueError('Duplicate checkpoint members')
    return cp, states, hashes, cfg


def output_path(out, sources):
    lexical = Path(out).expanduser().absolute()
    allowed = ROOT / 'experiments/ensembles/network_breadth_20261104'
    resolved = checked_output(lexical, ROOT / 'agents/sherlock/weights')
    if not lexical.is_relative_to(allowed.absolute()) or not resolved.is_relative_to(allowed.resolve()):
        raise ValueError('Output must be new and under experiments/ensembles/network_breadth_20261104')
    if any(path.is_symlink() for path in (lexical, *lexical.parents)):
        raise ValueError('Symlink output path')
    if resolved.exists():
        raise FileExistsError(resolved)
    if any(source.is_relative_to(resolved) for source in sources):
        raise ValueError('Output directory contains a source')
    return resolved


def build(source, out, *, fo_source):
    source, fo_source = (Path(path).resolve(strict=True) for path in (source, fo_source))
    out = output_path(out, (source, fo_source))
    input_hashes = {str(path): file_sha256(path) for path in (source, fo_source)}
    if input_hashes[str(source)] != SOURCE_SHA:
        raise ValueError('V14 source SHA mismatch')
    cp, states, hashes, cfg = load_checkpoint(source, 36)
    fo, extra, extra_hashes, fo_cfg = load_checkpoint(fo_source, 24)
    if any(cfg[key] != fo_cfg[key] for key in PLAY_KEYS):
        raise ValueError('FO play-feature semantics differ from V14')
    if (cfg['cand_rescue'] is not True or cfg['rescue_after'] != 30
            or any(cfg[key] for key in ('zone_rescue', 'point_pair_swap', 'art_move_guard', 'rescue_in_training'))):
        raise ValueError('Unexpected raw V14 configuration')
    rosters = {'SOLO28': [(source, 28, states[28])],
               'FO42': [(source, i, state) for i, state in enumerate(states)]
                       + [(fo_source, i, extra[i]) for i in range(18, 24)]}
    if len(set(hashes + extra_hashes[18:24])) != 42:
        raise ValueError('FO42 must have 42 distinct tensor members')
    manifest = dict(schema_version=1, status='BUILT_VERIFIED',
                    created_utc=datetime.now(timezone.utc).isoformat(),
                    sources=input_hashes, source_component_sha256={str(source): hashes, str(fo_source): extra_hashes},
                    builder_sha256=file_sha256(__file__),
                    training_history='Inference only; normalized counters are not training history',
                    candidates={})
    # Validate every source and roster before creating any output.
    out.mkdir(parents=True, exist_ok=False)
    for name, roster in rosters.items():
        selected = [state for _, _, state in roster]
        ordered = [tensor_sha256(state) for state in selected]
        artifact = dict(q=copy.deepcopy(selected[0]), target_q=copy.deepcopy(selected[0]),
                        ensemble=copy.deepcopy(selected[1:]), ensemble_dims=[79] * (len(selected) - 1),
                        cfg=copy.deepcopy(cp['cfg']), feature_dim=79, n_actions=6,
                        env_steps=60000, learn_steps=0)
        target = out / f'{name}.pth'
        with target.open('xb') as handle:
            torch.save(artifact, handle)
        reloaded, _, actual, _ = load_checkpoint(target, len(selected))
        if (actual != ordered or reloaded['cfg'] != cp['cfg']
                or tensor_sha256(reloaded['target_q']) != ordered[0]
                or reloaded['ensemble_dims'] != [79] * (len(selected) - 1)):
            raise ValueError(f'{name}: reload identity mismatch')
        manifest['candidates'][name] = dict(path=str(target), sha256=file_sha256(target),
            net_count=len(selected), unique_tensor_count=len(set(ordered)), ordered_tensor_sha256=ordered,
            members=[dict(source=str(path), index=index, tensor_sha256=ordered[i])
                     for i, (path, index, _) in enumerate(roster)],
            configuration=copy.deepcopy(cp['cfg']), new_training=False, weighting=f'equal 1/{len(selected)}')
    if any(file_sha256(path) != expected for path, expected in input_hashes.items()):
        raise ValueError('A source changed during construction')
    with (out / 'manifest.json').open('x') as handle:
        json.dump(manifest, handle, indent=2, allow_nan=False)
        handle.write('\n')
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'fo-source', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args(argv)
    torch.set_num_threads(1)
    result = build(args.source, args.out, fo_source=args.fo_source)
    print(json.dumps({'manifest': str(args.out / 'manifest.json'),
                      'candidates': {k: v['net_count'] for k, v in result['candidates'].items()}}))


if __name__ == '__main__':
    main()
