"""Compare every unit command to verified public game recordings through the course or native ZIP loader."""
import argparse
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CHECK = runpy.run_path(str(ROOT / 'scripts/xversion_replay.py'))['require_clean_policy']


def require(value, message):
    if not value:
        raise RuntimeError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def observations(fields, step):
    result = {}
    for key, rows in fields.items():
        if '/' in key:
            group, leaf = key.split('/')
            result.setdefault(group, {})[leaf] = rows[step].copy()
        else:
            result[key] = rows[step].copy()
    return result


def case(agent, tape, meta, events, native, weights, original_digest):
    side = meta['side']
    if native:
        agent.new_game(side)
    elif side == 'player_0':
        agent.set_to_eval_mode()
    agent.set_env_cfg(meta['cfg'])
    if not native and side == 'player_1':
        agent.save_agent()
    base_act = agent.base.act
    proposed = []

    def observe_proposal(*args, **kwargs):
        raw = base_act(*args, **kwargs)
        proposed.append(np.asarray(raw).copy())
        return raw

    agent.base.act = observe_proposal
    verified = 0
    changes = []
    with np.load(tape, allow_pickle=False) as record:
        expected = record['commands']
        fields = {k: record[k] for k in record.files if k not in ('commands', 'metadata')}
    require(expected.shape == (303, 16, 3), 'Recording does not contain one full game')
    for step, reference in enumerate(expected):
        world = observations(fields, step)
        action = np.asarray(agent.act(step=step, obs=world))
        CHECK(agent.base, side)
        require(len(proposed) == 1 and action.shape == (16, 3) and np.issubdtype(action.dtype, np.integer), 'Wrong V16 call count or command format')
        proposal = proposed.pop()
        require(np.array_equal(action, reference), f'{side} diverged at turn {step}')
        for uid in np.flatnonzero(np.any(action != proposal, axis=1)):
            changes.append([step, int(uid), int(proposal[uid, 0]), int(action[uid, 0])])
        verified += len(action)
    require(changes == events and agent.changes == len(events) == meta['changes'], 'V16 intervention trace differs')
    require(digest(weights) == original_digest, 'Weight changed during replay')
    return dict(seed=meta['seed'], seat=side, sensor=meta['cfg']['unit_sensor_range'], opponent=meta['opponent'],
                source_tape_sha256=digest(tape), same_unit_commands=verified, public_turns=len(expected),
                changes=changes, checkpoint_after_sha256=digest(weights))


def verify(kind, output):
    torch.set_num_threads(1)
    fmt = json.loads((HERE / 'pakete.json').read_text())['archives']
    native = kind == 'native'
    name = 'agent.zip' if native else 'Gruppe15.zip'
    spec = fmt[name]
    zip_path = Path(spec['path'])
    require(digest(zip_path) == spec['sha256'], 'Research ZIP differs from the repeat build')
    rows = []
    refs = [json.loads((HERE / f'referenz_p{t}.json').read_text()) for t in (0, 1)]
    normal = json.loads((HERE.parent / 'flottenblick/normalsicht.json').read_text())['seats']
    with TemporaryDirectory() as tmp:
        tmp = Path(tmp).resolve()
        if native:
            sys.path.insert(0, str(ROOT))
            from scripts.r3_package import r3_package_agent
            def load(side):
                player = r3_package_agent(side, zip_path)
                module = sys.modules[type(player).__module__]
                return player, Path(module.__file__).parent / 'weights/agent.pth'
            loader = ROOT / 'scripts/r3_package.py'
        else:
            # Isolate the original course resolver and extracted archive from every development agent.
            shutil.copytree(ROOT / 'lux', tmp / 'lux')
            (tmp / 'agents').mkdir()
            with ZipFile(zip_path) as z:
                z.extractall(tmp)
            sys.path.insert(0, str(tmp))
            os.chdir(tmp)
            from lux.runner import load_class_from_path
            cls = load_class_from_path('Gruppe15.main.Agent_x')
            require(Path(inspect.getfile(cls)).resolve() == tmp / 'Gruppe15/main.py', 'Wrong course class')
            def load(side):
                weights = tmp / 'Gruppe15/agent.pth'
                return cls(side, agent_path='Gruppe15/agent.pth'), weights
            loader = ROOT / 'lux/runner.py'
        for seed in ([164050001] if native else [164050001, 161050000]):
            for t in (0, 1):
                side = f'player_{t}'
                tape = zip_path.parent / 'tapes' / f'{seed}_{side}.npz'
                active = seed == 164050001
                source_sha = refs[t]['tape_sha256'] if active else normal[t]['source_sha256']
                events = refs[t]['events'] if active else []
                require(digest(tape) == source_sha, 'Input tape is not the verified one')
                with np.load(tape, allow_pickle=False) as z:
                    meta = json.loads(str(z['metadata']))
                require(meta['seed'] == seed and meta['side'] == side, 'Recording metadata mismatch')
                agent, weights = load(side)
                require(digest(weights) == spec['base_weight_sha256'], 'Wrong installed weight')
                rows.append(case(agent, tape, meta, events, native, weights, spec['base_weight_sha256']))
                print(f"{kind} {seed} {side} {rows[-1]['same_unit_commands']} verified", flush=True)
        if not native:
            os.chdir(HERE)
    result = dict(format=kind, python=sys.version.split()[0], torch=torch.__version__, numpy=np.__version__,
                  zip_sha256=digest(zip_path), loader_sha256=digest(loader), seats=rows,
                  same_unit_commands=sum(z['same_unit_commands'] for z in rows), all_equal=True)
    if output.exists():
        require(json.loads(output.read_text()) == result, 'Replay differs from the earlier check')
    else:
        output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind', choices=('course', 'native'))
    p.add_argument('output', type=Path)
    args=p.parse_args()
    verify(args.kind, args.output.resolve())
