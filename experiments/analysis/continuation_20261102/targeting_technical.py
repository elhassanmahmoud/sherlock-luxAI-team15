"""Fixed known-game compatibility/smoke checks; no strength selection."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, os, sys, subprocess, time, re
ROOT=Path('/Users/moayedshawesh/Desktop/KI/sherlock-v10-mechanics')
PY='/Users/moayedshawesh/Desktop/KI/sherlock-luxAI-team15/.venv/bin/python'
PRIVATE=Path('/tmp/sherlock-continue-20261102')
OUT=ROOT/'experiments/analysis/continuation_20261102/prototype_technical'
sys.path.insert(0,str(ROOT))
from scripts.early_curriculum_study import source_identity,hashes
from scripts.targeting_probe import action_bytes

def now():return datetime.now(timezone.utc).isoformat()

def main():
    if OUT.exists():raise FileExistsError(OUT)
    weights=ROOT/'experiments/releases/20261101_v14_baseline/agent_p0.pth'
    assert hashlib.sha256(weights.read_bytes()).hexdigest()=='98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8'
    keysfile=ROOT/'experiments/analysis/continuation_20261102/diagnostic_keys.json'
    oldfile=ROOT/'experiments/analysis/continuation_20261102/targeting/manifest.json'
    keys=json.loads(keysfile.read_text())['keys']
    old={(r['key']['seed'],r['key']['side']):r['unobserved'] for r in json.loads(oldfile.read_text())['games']}
    active=[(831006,'player_1'),(831029,'player_0'),(831042,'player_0'),(831043,'player_1')]
    modes={'off':{},'art':{'art_move_guard':True},'swap':{'point_pair_swap':True},
           'pair':{'art_move_guard':True,'point_pair_swap':True}}
    jobs=[('off',k['seed'],k['side']) for k in keys]+[(m,s,p) for m in ('art','swap','pair') for s,p in active]
    plans=[ROOT/'docs/superpowers/plans/2026-11-02-targeting-technical-games.md',
           ROOT/'docs/superpowers/specs/2026-11-02-targeting-prototypes-design.md',keysfile,oldfile,Path(__file__).resolve()]
    protected=[weights,*(ROOT/f'agents/sherlock/weights/agent_p{i}.pth' for i in (0,1)),
               *(ROOT/f'experiments/releases/20261020_old3_sym3/agent_p{i}.pth' for i in (0,1))]
    def identity():return {'source':source_identity(ROOT,PY,plans),'weights':hashes(protected)}
    frozen=identity()
    OUT.mkdir()
    receipt={'status':'running','started_utc':now(),'identity':frozen,'jobs':jobs,'completed_games':0,'rows':[],'pid':os.getpid()}
    def save():(OUT/'manifest.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    save()
    deadline=time.time()+1200
    try:
        import torch
        from luxai_s3.wrappers import LuxAIS3GymEnv
        from agents.sherlock.main import Agent_x
        from scripts.experiment import limit_threads
        from scripts.common import make_opponent,play_game
        from scripts.par_eval import build_cfg
        from scripts.night_train_pilot import tensor_sha256
        limit_threads()
        checkpoint=torch.load(weights,map_location='cpu',weights_only=True)
        expected=[tensor_sha256(s) for s in [checkpoint['q'],*checkpoint['ensemble']]]
        for mode,seed,side in jobs:
            assert time.time()<deadline and identity()==frozen
            power=subprocess.check_output(['pmset','-g','batt'],text=True)
            if 'AC Power' not in power:assert int(re.search(r'(\d+)%',power)[1])>25
            cfg=build_cfg(str(weights),[f'{k}={str(v).lower()}' for k,v in modes[mode].items()])
            a=Agent_x('player_0',agent_path=str(weights),cfg=cfg,train=False,seed=0)
            a.set_to_eval_mode();a.autosave_on_terminate=False
            nets=[a.q,*a.extra_q]
            assert len(nets)==36 and a.feat_dim==79 and a.n_actions==6 and not a.training and a.epsilon==0
            assert [tensor_sha256(n.state_dict()) for n in nets]==expected
            learn_steps=a.learn_steps
            opp=make_opponent('solution92','player_1' if side=='player_0' else 'player_0')
            env=LuxAIS3GymEnv(numpy_output=True)
            original=env.step;digest=hashlib.sha256()
            def step(actions):
                digest.update(action_bytes(actions))
                return original(actions)
            env.step=step
            try:row=play_game(env,a,opp,seed,side,train=False)
            finally:env.close()
            assert row['steps']==303 and row['point_counting_version']==2 and a.caught_errors==0
            assert a.learn_steps==learn_steps and [tensor_sha256(n.state_dict()) for n in nets]==expected
            assert cfg.art_move_guard==modes[mode].get('art_move_guard',False)
            assert cfg.point_pair_swap==modes[mode].get('point_pair_swap',False)
            entry={'mode':mode,'seed':seed,'side':side,'row':row,'config':cfg.to_dict(),
                   'action_sha256':digest.hexdigest(),'stats':dict(a.ep_stats),'tensors_unchanged':True}
            if mode=='off':
                ref=old[seed,side]
                entry['baseline_checks']={k:row[k]==ref[k] for k in ('steps','point_counting_version','result','our_wins','opp_wins','our_points','opp_points')}
                entry['baseline_checks']['action_sha256']=entry['action_sha256']==ref['action_sha256']
                assert all(entry['baseline_checks'].values()),entry['baseline_checks']
            receipt['rows'].append(entry);receipt['completed_games']+=1;save()
            print(f'complete {mode} {seed} {side}',flush=True)
        assert len(receipt['rows'])==24 and identity()==frozen
        counts={m:sum(int(r['stats'].get('art_move_kept' if m=='art' else 'point_pair_swaps',0)) for r in receipt['rows'] if r['mode']==m) for m in ('art','swap')}
        assert counts['art']>0 and counts['swap']>0,counts
        receipt.update(status='complete',finished_utc=now(),trigger_counts=counts,inputs_unchanged=True)
        save()
    except BaseException as exc:
        receipt.update(status='incomplete/rejected',finished_utc=now(),error=f'{type(exc).__name__}: {exc}');save();raise

if __name__=='__main__':main()
