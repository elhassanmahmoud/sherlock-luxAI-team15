"""Paired whole-game evaluation of the November final candidates with resumable rows."""
import argparse
import concurrent.futures
import hashlib
import importlib
import json
import multiprocessing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / 'agents/sherlock/weights/agent_p0.pth'
POLICIES = {'v14': 'agents.sherlock.main:Agent_x', 'pressure': 'scripts.final_pressure:PressureAgent',
            'contact': 'scripts.contact_reserve:ContactReserveAgent', 'learned': 'scripts.final_learning_agent:EnergyReturnAgent',
            'aim': 'scripts.combat_advice_agent:CombatAdviceAgent', 'fire': 'scripts.combat_advice_agent:CombatAdviceAgent',
            'selective_combat': 'scripts.selective_advice_agent:SelectiveAdviceAgent',
            'selective_movement': 'scripts.selective_advice_agent:SelectiveAdviceAgent'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evaluate(job):
    # Reuse the JIT environment and the model per worker, clean agent/game state for each key.
    policy, opponent, seed, side, model = job
    from scripts.common import make_opponent, play_game
    from scripts.par_eval import require_no_agent_errors
    agent, env = evaluate.agent, evaluate.env
    other = 'player_1' if side == 'player_0' else 'player_0'
    rival = make_opponent('self' if opponent == 'v14' else opponent, other, self_play_path=str(WEIGHTS))
    row = play_game(env, agent, rival, seed, side, train=False)
    require_no_agent_errors(agent, rival)
    if row['steps'] != 303 or row['our_wins'] + row['opp_wins'] != 3:
        raise RuntimeError(f'Unexpected course game ending: {row}')
    extra = agent.episode_stats()
    return dict(candidate=policy, opponent=opponent, seed=seed, side=side,
                result=row['result'], wins=row['our_wins'], losses=row['opp_wins'],
                points=row['our_points'], opp_points=row['opp_points'], steps=row['steps'], secs=row['secs'],
                study=dict(getattr(agent,'study_stats',getattr(agent,'selective_counts',{}))), charge_moves=extra.get('charge_moves',0),
                focus_saps=extra.get('focus_saps',0), energy_changes=extra.get('energy_changes',0),
                energy_probes=extra.get('energy_probes',0), advice_retargeted=extra.get('advice_retargeted',0),
                advice_new_saps=extra.get('advice_new_saps',0))


def init_worker(policy, model):
    from scripts.experiment import limit_threads
    limit_threads()
    import torch
    torch.manual_seed(0)
    from scripts.par_eval import build_cfg
    from luxai_s3.wrappers import LuxAIS3GymEnv
    module, name = POLICIES[policy].split(':')
    klass = getattr(importlib.import_module(module), name)
    extra = {}
    if policy == 'learned':
        extra['model_path'] = model
    elif policy in ('aim', 'fire'):
        extra = {'advice_path': model, 'mode': policy}
    elif policy.startswith('selective_'):
        extra = {'advice_path': model, 'mode': policy.removeprefix('selective_')}
    agent = klass('player_0', agent_path=str(WEIGHTS), cfg=build_cfg(str(WEIGHTS),[]), train=False, seed=0, **extra)
    agent.set_to_eval_mode()
    agent.autosave_on_terminate = False
    evaluate.agent, evaluate.env = agent, LuxAIS3GymEnv(numpy_output=True)


def contract(args):
    tracked = list((ROOT/'agents/sherlock').glob('*.py')) + list((ROOT/'agents/Solution_92_Kaggle').glob('*.py'))
    tracked += [ROOT/'scripts'/f for f in ('final_battle_compare.py','common.py','scoring.py','par_eval.py','metrics.py','kaggle3_opponent.py','experiment.py')]
    tracked.append(ROOT/(POLICIES[args.candidate].split(':')[0].replace('.','/')+'.py'))
    if args.candidate == 'learned': tracked.extend((ROOT/'scripts').glob('final_learning_*.py'))
    if args.candidate.startswith('selective_'):
        tracked += [ROOT/'scripts'/f for f in ('combat_teacher_counterfactual.py','collect_combat_advice.py','imitate.py')]
    # Include installed opponent source/weights when that opponent is actually evaluated.
    if 'kaggle3' in args.opponents.split(','):
        from scripts.fetch_kaggle3 import TARGET, verify
        if not verify(): raise ValueError('Kaggle opponent weights missing or corrupt')
        tracked.extend(TARGET.rglob('*.py')); tracked.extend(TARGET.rglob('*.pth'))
    import importlib.util
    engine_path = Path(importlib.util.find_spec('luxai_s3').origin).parent
    return dict(candidate=args.candidate, opponents=args.opponents.split(','), first=args.first, maps=args.maps,
                model=digest(args.model) if args.model else None, weights=digest(WEIGHTS),
                sources={str(p.relative_to(ROOT)):digest(p) for p in sorted(set(tracked))},
                engine={k:digest(engine_path/k) for k in ('env.py','params.py','wrappers.py')})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',required=True,choices=list(POLICIES)); p.add_argument('--model')
    p.add_argument('--opponents',default='kaggle3,solution92'); p.add_argument('--first',type=int,required=True)
    p.add_argument('--maps',type=int,required=True); p.add_argument('--out',required=True,type=Path)
    p.add_argument('--workers',type=int,choices=[1,2],default=2)
    a = p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    if a.maps <= 0 or bool(a.model) != (a.candidate in ('learned', 'aim', 'fire', 'selective_movement', 'selective_combat')): p.error('invalid map count or model argument')
    import fcntl
    with (a.out/'.run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        config=contract(a); manifest=a.out/'manifest.json'
        if manifest.exists() and json.loads(manifest.read_text()) != config: raise ValueError('source/config change on resume')
        if not manifest.exists(): manifest.write_text(json.dumps(config,indent=2)+'\n')
        jobs=[(a.candidate,o,s,side,a.model) for s in range(a.first,a.first+a.maps)
              for o in config['opponents'] for side in ('player_0','player_1')]
        path=a.out/'games.jsonl'; completed={}
        for line in path.read_text().splitlines() if path.is_file() else []:
            row=json.loads(line); key=(a.candidate,row['opponent'],row['seed'],row['side'],a.model)
            if key not in jobs or key in completed or row['candidate']!=a.candidate or row['steps']!=303:
                raise ValueError('invalid saved game')
            completed[key]=row
        pending=[j for j in jobs if j not in completed]
        if pending:
            with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers, mp_context=multiprocessing.get_context('spawn'),
                    initializer=init_worker,initargs=(a.candidate,a.model)) as pool, path.open('a') as f:
                for row in pool.map(evaluate,pending,chunksize=1):
                    f.write(json.dumps(row)+'\n'); f.flush()
                    print(row['opponent'],row['seed'],row['side'],row['result'],flush=True)
        if config != contract(a): raise RuntimeError('bound sources changed during play')
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        assert len(rows)==len(jobs)
        summary={o:dict(played=sum(r['opponent']==o for r in rows),
                        wins=sum(r['result'] for r in rows if r['opponent']==o),
                        matches=sum(r['wins'] for r in rows if r['opponent']==o)) for o in config['opponents']}
        (a.out/'completed.json').write_text(json.dumps(dict(summary=summary,rows_sha256=digest(path)),indent=2)+'\n')
        print(summary)


if __name__=='__main__': main()
