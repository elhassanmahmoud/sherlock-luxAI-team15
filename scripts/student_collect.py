"""Collect exact normal-eval student decisions and raw pinned-V14 Q labels.

The instance-local forward hook copies tensors before Agent_x masks its CPU
numpy view in place. No second belief/context/decision evaluation is performed.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys
import time

import numpy as np
import torch

from agents.sherlock import geometry as geo
from agents.sherlock.config import AgentConfig
from agents.sherlock.main import Agent_x
from agents.sherlock.model import QNet
from scripts.common import make_opponent, play_game
from scripts.output_paths import checked_output
from scripts.student_distill import (_finite, _hashes, _write, load_teacher,
                                    reserve_output as _reserve_output, sha256,
                                    teacher_q, V14_SHA256)

ROOT = Path(__file__).resolve().parent.parent
PRIMARY = Path('/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15')
HISTORICAL = Path('/Users/moayedshawesh/Desktop/KI/sherlock-november-followup')
TEACHER = ROOT / 'agents/sherlock/weights/agent_p0.pth'
V13 = ROOT / 'experiments/releases/20261101_v13_neb/agent_p0.pth'
V13_SHA256 = '6d00b6c52366a613eed3b7b5b6f9c3c088802716a85c30fe192c46c57bdd8e62'
DTYPES = dict(s=np.float32, mask=np.bool_, student_q=np.float32,
              final_action=np.int8, world_action=np.int16, game_index=np.int32,
              env_seed=np.int64, side=np.int8, env_step=np.int16,
              match_step=np.int16, uid=np.int8, is_train=np.bool_)


def game_plan(seed_start: int, maps: int) -> list[dict]:
    if type(maps) is not int or not 2 <= maps <= 30:
        raise ValueError('maps must be an integer from 2 to 30 with a nonempty train split')
    if type(seed_start) is not int or not 0 <= seed_start <= np.iinfo(np.int64).max - maps:
        raise ValueError('seed_start must be a nonnegative int64 seed')
    diagnostic = max(1, maps // 6)
    opponents = ('solution92', 'solution92', 'solution92', 'default', 'self')
    return [dict(game_index=2 * index + side, env_seed=seed_start + index,
                 side=side, side_name=f'player_{side}', opponent=opponents[index % 5],
                 is_train=index < maps - diagnostic)
            for index in range(maps) for side in (0, 1)]


def reserve_output(out: Path, inputs) -> Path:
    # Include the packaging directory as well as the existing raw-weight guards.
    for base in (ROOT, PRIMARY, HISTORICAL):
        checked_output(out, base / 'agents/Gruppe15')
        if (base / 'agents/Gruppe15').resolve().is_relative_to(Path(out).expanduser().resolve()):
            raise ValueError('Output must not contain protected submission directory')
    return _reserve_output(out, inputs)


class ExactCollector:
    """Attach to exactly one agent for one or more games; restore in finally."""
    def __init__(self, agent, check=lambda: None):
        self.agent, self.check = agent, check
        self.chunks = []
        self.game = None
        self.counts = dict(act_steps=0, network_steps=0, no_network_steps=0,
                           reset_steps=0, no_unit_steps=0,
                           final_outside_network_mask_rows=0)
        self._calls = []
        self._active = False

    def set_game(self, game):
        self.game = dict(game)

    def __enter__(self):
        self._had_act = 'act' in vars(self.agent)
        self._own_act = vars(self.agent).get('act')
        self._original = self.agent.act
        self._handle = self.agent.q.register_forward_hook(self._hook)
        self.agent.act = self._act
        return self

    def __exit__(self, *exc):
        self._handle.remove()
        if self._had_act:
            self.agent.act = self._own_act
        else:
            del self.agent.act

    def _hook(self, module, inputs, output):
        if not self._active:
            raise ValueError('Student network called outside the normal act invocation')
        # .numpy() alone aliases CPU tensor storage: both copies must occur HERE.
        self._calls.append((inputs[0].detach().cpu().numpy().copy(),
                            output.detach().cpu().numpy().copy()))

    def _act(self, step: int, obs):
        self.check()
        if self.agent.training or self.agent.cfg.frozen or self.agent.autosave_on_terminate:
            raise ValueError('Collection requires fail-fast eval with autosave disabled')
        self._calls = []
        self._active = True
        try:
            actions = self._original(step=step, obs=obs)
        finally:
            self._active = False
        self.counts['act_steps'] += 1
        match_step = int(np.asarray(obs['match_steps']))
        feats = self.agent._prev_feats
        if not self._calls:
            if feats or self.agent._prev_masks:
                raise ValueError('Saved features without current network invocation')
            self.counts['no_network_steps'] += 1
            self.counts['reset_steps' if match_step == 0 else 'no_unit_steps'] += 1
            return actions
        if len(self._calls) != 1 or not feats or match_step == 0:
            raise ValueError('Expected exactly one network call for each nonreset decision')
        s, q = self._calls[0]
        ids = list(feats)
        if (s.shape != (len(ids), 79) or s.dtype != np.float32
                or q.shape != (len(ids), 6) or q.dtype != np.float32):
            raise ValueError('Network input/output must be float32 [N,79]/[N,6]')
        if not np.array_equal(s, np.stack([feats[u] for u in ids])):
            raise ValueError('Captured features do not align with saved current-decision features')
        if set(ids) != set(self.agent._prev_masks):
            raise ValueError('Saved feature/mask unit IDs do not match')
        mask = np.stack([self.agent._prev_masks[u] for u in ids]).copy()
        if mask.shape != (len(ids), 6) or mask.dtype != np.bool_ or not mask.any(axis=1).all():
            raise ValueError('Invalid or empty network mask')
        if not np.isfinite(s).all() or not np.isfinite(q).all():
            raise ValueError('Nonfinite captured feature or raw Q value')
        world_all = np.asarray(actions)
        if (world_all.ndim != 2 or world_all.shape[1] != 3 or
                not np.issubdtype(world_all.dtype, np.integer) or
                any(type(u) not in (int, np.int64, np.int32) or not 0 <= u < min(16, len(world_all)) for u in ids)):
            raise ValueError('Invalid final action array or unit IDs')
        world = world_all[ids].copy()
        if ((world < np.iinfo(np.int16).min) | (world > np.iinfo(np.int16).max)).any():
            raise ValueError('Final world action exceeds int16')
        final = world[:, 0].copy()
        if ((final < 0) | (final > 5)).any():
            raise ValueError('Final action must be in 0..5')
        if self.agent.belief.mirrored:
            moving = final < 5
            final[moving] = geo.MIRROR_DIR[final[moving]]
        self.counts['final_outside_network_mask_rows'] += int((~mask[np.arange(len(ids)), final]).sum())
        if self.game is None:
            # A failed act need not have game metadata; a retained row always must.
            raise ValueError('Set game metadata before collecting network rows')
        if not 0 <= step <= 32767 or not 0 <= match_step <= 32767:
            raise ValueError('Step does not fit dataset int16 contract')
        chunk = dict(s=s, student_q=q, mask=mask, world_action=world,
                     final_action=final, uid=np.asarray(ids))
        for key in ('game_index', 'env_seed', 'side', 'is_train'):
            chunk[key] = np.full(len(ids), self.game[key])
        chunk['env_step'] = np.full(len(ids), step)
        chunk['match_step'] = np.full(len(ids), match_step)
        self.chunks.append({key: np.asarray(value, dtype=DTYPES[key]).copy() for key, value in chunk.items()})
        self.counts['network_steps'] += 1
        return actions

    def arrays(self):
        shapes = dict(s=(0, 79), student_q=(0, 6), mask=(0, 6), world_action=(0, 3))
        return {key: (np.concatenate([chunk[key] for chunk in self.chunks]) if self.chunks
                      else np.empty(shapes.get(key, (0,)), dtype=dtype))
                for key, dtype in DTYPES.items()}


def load_student(path: Path):
    cp = torch.load(path, map_location='cpu', weights_only=True)
    fields = {'q', 'target_q', 'cfg', 'feature_dim', 'n_actions', 'ensemble',
              'ensemble_dims', 'env_steps', 'learn_steps'}
    provenance = {'distillation_updates', 'distillation_epochs', 'distillation_seed'}
    if (not isinstance(cp, dict) or not fields <= set(cp)
            or set(cp) - fields not in (set(), provenance) or cp['feature_dim'] != 79
            or cp['n_actions'] != 6 or cp['ensemble'] or cp['ensemble_dims']
            or cp['env_steps'] != 60000 or cp['learn_steps'] != 0):
        raise ValueError('Student requires one final 79/6 network without optimizer/replay')
    if provenance <= set(cp) and any(
            type(cp[name]) is not int or cp[name] < minimum
            for name, minimum in (('distillation_updates', 1),
                                  ('distillation_epochs', 1), ('distillation_seed', 0))):
        raise ValueError('Legacy distillation provenance requires positive counts and a valid seed')
    cfg = AgentConfig(**cp['cfg'])
    if cfg.hidden != 512 or not cfg.dueling or not cfg.canonical or not cfg.use_sap or cfg.threat_feats:
        raise ValueError('Student requires a single canonical 512-wide dueling 79/6 network')
    _finite(cp)
    with torch.random.fork_rng(devices=[]):
        probe = QNet(79, 6, 512, True)
        probe.load_state_dict(cp['q'], strict=True)
        probe.load_state_dict(cp['target_q'], strict=True)
    if any(not torch.equal(cp['q'][k], cp['target_q'][k]) for k in cp['q']):
        raise ValueError('Student q/target must be equal')
    return cp


def _agent(student, checkpoint):
    cfg = AgentConfig(**dict(checkpoint['cfg'], frozen=False))
    agent = Agent_x('player_0', agent_path=str(student), cfg=cfg, train=False, seed=20261104)
    agent.autosave_on_terminate = False
    agent.learn_enabled = False
    agent.set_to_eval_mode()
    agent.target_q.eval()
    if agent.extra_q or agent.cnn_policy is not None or agent.training or agent.cfg.frozen:
        raise ValueError('Real loaded student must be a fail-fast eval single network')
    for name in ('q', 'target_q'):
        actual = getattr(agent, name).state_dict()
        if set(actual) != set(checkpoint[name]) or any(
                not torch.equal(v.detach().cpu(), checkpoint[name][k]) for k, v in actual.items()):
            raise ValueError('Real loaded student differs from validated checkpoint')
    return agent


def _learning_digest(agent):
    digest = hashlib.sha256()
    def add(value):
        if isinstance(value, torch.Tensor):
            value = value.detach().cpu().contiguous()
            digest.update(str((value.dtype, tuple(value.shape))).encode())
            digest.update(value.numpy().tobytes())
        elif isinstance(value, dict):
            for key in sorted(value, key=str):
                digest.update(repr(key).encode())
                add(value[key])
        elif isinstance(value, (list, tuple)):
            for item in value:
                add(item)
        else:
            digest.update(repr(value).encode())
    add([agent.q.state_dict(), agent.target_q.state_dict(), agent.opt.state_dict(),
         agent.env_steps, agent.learn_steps, len(agent.buffer), agent.recent_losses])
    return digest.hexdigest()


def _protected_hashes():
    paths = set()
    for base in (ROOT, PRIMARY, HISTORICAL):
        for folder in ('agents/sherlock/weights', 'Gruppe15', 'agents/Gruppe15'):
            directory = base / folder
            if directory.exists():
                paths.update(p.resolve() for p in directory.rglob('*') if p.is_file())
        paths.update(p.resolve() for p in base.glob('*.zip') if p.is_file())
    return _hashes(sorted(paths))


def _pins():
    import luxai_s3
    sources = {ROOT / 'scripts' / f'{name}.py' for name in
               ('student_collect', 'student_distill', 'common', 'metrics', 'scoring', 'output_paths')}
    for directory in ('agents/sherlock', 'agents/default', 'agents/Solution_92_Kaggle'):
        sources.update((ROOT / directory).rglob('*.py'))
    sources.add(ROOT / 'lux/utils.py')
    sources.update(Path(luxai_s3.__file__).resolve().parent.rglob('*.py'))
    return dict(sources=_hashes(sorted(sources)), protected=_protected_hashes(),
                interpreter=str(Path(sys.executable).resolve()),
                interpreter_sha256=sha256(Path(sys.executable).resolve()),
                dependency_versions={name: version(name) for name in
                                     ('numpy', 'torch', 'scipy', 'jax', 'jaxlib', 'luxai-s3', 'gymnasium')})


def _env():
    from luxai_s3.wrappers import LuxAIS3GymEnv
    return LuxAIS3GymEnv(numpy_output=True)


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def collect(student: Path, out: Path, seed_start: int, maps: int, deadline: datetime) -> dict:
    if deadline.tzinfo is None:
        raise ValueError('Deadline must include a UTC offset')
    plan = game_plan(seed_start, maps)
    student = Path(student).expanduser().resolve(strict=True)
    inputs = [student, TEACHER.resolve(strict=True), V13.resolve(strict=True)]
    out = reserve_output(out, inputs)
    started = time.monotonic()
    manifest = dict(schema_version=1, status='running', teacher_sha256=V14_SHA256,
                    teacher_members=36, teacher=str(TEACHER.resolve()), student=str(student),
                    game_plan=plan, games_completed=0, rows=0, cpu_threads=1,
                    technical_test_only=maps != 30, seed_start=seed_start, maps=maps,
                    deadline_utc=deadline.astimezone(timezone.utc).isoformat(),
                    started_utc=datetime.now(timezone.utc).isoformat(),
                    exclusions='Only reset/no-unit steps with no network forward have no rows; invalid rows fail the run.',
                    limitations='Development states; teacher Q on identical observed features, not final teacher actions.')
    def check():
        if datetime.now(timezone.utc) >= deadline:
            raise TimeoutError('Collection deadline reached')
    def progress(phase):
        manifest.update(phase=phase, wall_seconds=time.monotonic() - started)
        _write(out / 'status.json', manifest)
    env = None
    try:
        progress('preflight')
        check()
        torch.set_num_threads(1)
        manifest['inputs_before'] = _hashes(inputs)
        manifest['student_sha256'] = manifest['inputs_before'][str(student)]
        if manifest['inputs_before'][str(V13.resolve())] != V13_SHA256:
            raise ValueError('V13 opponent hash does not match pinned release')
        manifest['pins_before'] = _pins()
        checkpoint = load_student(student)
        manifest['student_config'] = copy.deepcopy(checkpoint['cfg'])
        nets, cfg = load_teacher(TEACHER)
        manifest['teacher_config'] = cfg
        _write(out / 'manifest.json', manifest)
        agent = _agent(student, checkpoint)
        initial = _learning_digest(agent)
        manifest['learning_state_before'] = initial
        env = _env()
        with (out / 'games.jsonl').open('x') as log, ExactCollector(agent, check) as capture:
            for game in plan:
                check()
                capture.set_game(game)
                other = f"player_{1 - game['side']}"
                opp = make_opponent(game['opponent'], other,
                                    self_play_path=str(V13) if game['opponent'] == 'self' else None)
                if hasattr(opp, 'cfg'):
                    opp.cfg.frozen = False
                if hasattr(opp, 'autosave_on_terminate'):
                    opp.autosave_on_terminate = False
                before_rows = sum(len(c['s']) for c in capture.chunks)
                result = play_game(env, agent, opp, game['env_seed'], game['side_name'], train=False)
                if result['steps'] != 303:
                    raise ValueError('Collection requires all 303 course steps (three matches)')
                if _learning_digest(agent) != initial or agent.training or agent.q.training:
                    raise ValueError('Student learning/model/optimizer state mutated during eval')
                result.update(game_index=game['game_index'], env_seed=game['env_seed'],
                              is_train=game['is_train'], opponent=game['opponent'],
                              rows=sum(len(c['s']) for c in capture.chunks) - before_rows)
                log.write(json.dumps(_json_safe(result), allow_nan=False) + '\n')
                log.flush()
                manifest['games_completed'] += 1
                manifest['counts'] = dict(capture.counts)
                progress('collecting')
            data = capture.arrays()
        if not len(data['s']) or not data['is_train'].any() or data['is_train'].all():
            raise ValueError('Collection requires nonempty train and diagnostic rows')
        manifest['rows'] = len(data['s'])
        manifest['train_rows'] = int(data['is_train'].sum())
        manifest['diagnostic_rows'] = int((~data['is_train']).sum())
        data['teacher_q'] = np.empty((len(data['s']), 6), np.float32)
        progress('labeling')
        for start in range(0, len(data['s']), 1024):
            check()
            data['teacher_q'][start:start + 1024] = teacher_q(
                nets, torch.from_numpy(data['s'][start:start + 1024])).cpu().numpy()
        if not np.isfinite(data['teacher_q']).all():
            raise ValueError('Nonfinite teacher labels')
        manifest['teacher_gradients_absent'] = all(p.grad is None for net in nets for p in net.parameters())
        manifest['learning_state_after'] = _learning_digest(agent)
        manifest['inputs_after'] = _hashes(inputs)
        manifest['pins_after'] = _pins()
        if (manifest['learning_state_after'] != initial or
                manifest['inputs_before'] != manifest['inputs_after'] or
                manifest['pins_before'] != manifest['pins_after']):
            raise ValueError('Pinned input/source/protected/learning-state mutation detected')
        check()
        pending = out / 'dataset.pending.npz'
        np.savez_compressed(pending, **data)
        # Verify actual serialized schema and row counts before publishing success.
        with np.load(pending, allow_pickle=False) as archive:
            if set(archive.files) != set(data) or any(
                    not np.array_equal(archive[key], value) for key, value in data.items()):
                raise ValueError('Dataset serialization differs from collected rows')
        check()
        # Serialization can take time; attest the final bytes against the same freeze.
        if manifest['inputs_before'] != _hashes(inputs) or manifest['pins_before'] != _pins():
            raise ValueError('Pinned input/source/protected mutation during serialization')
        pending.replace(out / 'dataset.npz')
        manifest['files_sha256'] = {name: sha256(out / name) for name in ('dataset.npz', 'games.jsonl')}
        manifest.update(status='done', completed_utc=datetime.now(timezone.utc).isoformat())
        _write(out / 'manifest.json', manifest)
        progress('done')
        return manifest
    except BaseException as error:
        (out / 'dataset.pending.npz').unlink(missing_ok=True)
        (out / 'dataset.npz').unlink(missing_ok=True)
        manifest.update(status='failed', error=f'{type(error).__name__}: {error}')
        _write(out / 'manifest.json', manifest)
        progress('failed')
        raise
    finally:
        if env is not None and hasattr(env, 'close'):
            env.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--student', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed-start', type=int, default=865100)
    parser.add_argument('--maps', type=int, default=30)
    parser.add_argument('--deadline-utc', required=True)
    args = parser.parse_args()
    deadline = datetime.fromisoformat(args.deadline_utc.replace('Z', '+00:00'))
    result = collect(args.student, args.out, args.seed_start, args.maps, deadline)
    print(json.dumps(dict(status=result['status'], rows=result['rows'], out=str(args.out))))


if __name__ == '__main__':
    main()
