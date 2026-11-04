"""Small real checkpoints exercise order, compatibility and read-only sources."""
import copy
import json
from pathlib import Path

import pytest
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet
from scripts import network_breadth_candidates as builder


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, 'ROOT', tmp_path)
    monkeypatch.setattr(builder, 'HIDDEN', 8)
    cfg = AgentConfig(hidden=8).to_dict()
    cfg.update(cand_rescue=True, rescue_after=30)
    template = QNet(79, 6, hidden=8, dueling=True).state_dict()
    states = [{key: torch.full_like(tensor, (i + 1) / 100)
               for key, tensor in template.items()} for i in range(42)]
    def checkpoint(members, config):
        return dict(q=members[0], ensemble=members[1:], cfg=config, feature_dim=79,
                    n_actions=6, ensemble_dims=[79] * (len(members) - 1),
                    optimizer={'stale': 1}, env_steps=999999, learn_steps=700)
    base = checkpoint(states[:36], cfg)
    fo = checkpoint(states[:18] + states[36:], dict(cfg, cand_rescue=False, far_opp=6))
    source, extra = tmp_path / 'v14.pth', tmp_path / 'all24fo.pth'
    torch.save(base, source)
    torch.save(fo, extra)
    monkeypatch.setattr(builder, 'SOURCE_SHA', builder.file_sha256(source))
    out = tmp_path / 'experiments/ensembles/network_breadth_20261104'
    return source, extra, out, base, fo, states


def test_exact_members_and_config_survive_reload_without_stale_training(inputs):
    source, extra, out, base, fo, states = inputs
    before = source.read_bytes(), extra.read_bytes()
    manifest = builder.build(source, out, fo_source=extra)
    assert set(manifest['candidates']) == {'SOLO28', 'FO42'}
    for name, indices in [('SOLO28', [28]), ('FO42', list(range(42)))]:
        cp = torch.load(out / f'{name}.pth', weights_only=True)
        members = [cp['q'], *cp['ensemble']]
        assert len(members) == len(indices)
        assert len({builder.tensor_sha256(state) for state in members}) == len(indices)
        for state, index in zip(members, indices):
            assert all(torch.equal(value, states[index][key]) for key, value in state.items())
        assert builder.tensor_sha256(cp['target_q']) == builder.tensor_sha256(cp['q'])
        assert cp['cfg'] == base['cfg']
        assert cp['ensemble_dims'] == [79] * (len(indices) - 1)
        assert cp['env_steps'] == 60000 and cp['learn_steps'] == 0
        assert 'optimizer' not in cp and 'replay' not in cp
        assert manifest['candidates'][name]['net_count'] == len(indices)
    assert before == (source.read_bytes(), extra.read_bytes())
    assert json.loads((out / 'manifest.json').read_text()) == manifest


@pytest.mark.parametrize('change', ['shape', 'duplicate', 'width', 'actions', 'hidden', 'semantic', 'nan'])
def test_bad_fo_input_fails_before_outputs(inputs, change):
    source, extra, out, _, fo, _ = inputs
    if change == 'shape': fo['ensemble'][17]['adv.2.bias'] = torch.zeros(5)
    if change == 'duplicate': fo['ensemble'][18] = copy.deepcopy(fo['ensemble'][17])
    if change == 'width': fo['feature_dim'] = 80
    if change == 'actions': fo['n_actions'] = 5
    if change == 'hidden': fo['cfg']['hidden'] = 16
    if change == 'semantic': fo['cfg']['canonical'] = False
    if change == 'nan': fo['ensemble'][17]['adv.2.bias'][0] = float('nan')
    torch.save(fo, extra)
    with pytest.raises(ValueError): builder.build(source, out, fo_source=extra)
    assert not out.exists()


def test_bad_v14_digest_and_protected_outputs_fail_without_write(inputs, monkeypatch):
    source, extra, out, *_ = inputs
    monkeypatch.setattr(builder, 'SOURCE_SHA', '0' * 64)
    with pytest.raises(ValueError, match='SHA'): builder.build(source, out, fo_source=extra)
    assert not out.exists()
    with pytest.raises(ValueError): builder.build(source, source.parent / 'other', fo_source=extra)


def test_existing_output_and_symlink_are_never_overwritten(inputs):
    source, extra, out, *_ = inputs
    out.mkdir(parents=True)
    sentinel = out / 'SOLO28.pth'
    sentinel.write_bytes(b'preserve')
    with pytest.raises(FileExistsError): builder.build(source, out, fo_source=extra)
    assert sentinel.read_bytes() == b'preserve'
    alias = out.parent / 'alias'
    alias.symlink_to(out, target_is_directory=True)
    with pytest.raises(ValueError): builder.build(source, alias / 'new', fo_source=extra)
