"""One fixed offline Fog influence diagnosis; no games, fitting or promotion.

Balanced trained-on replay ns/next_mask rows are descriptive, correlated data.
Neural proposals cannot establish action quality, Fog attribution or final rules.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time

import numpy as np
import torch

from agents.sherlock.config import AgentConfig
from agents.sherlock.model import QNet
from scripts import fog_reward_compare as F
from scripts import fog_reward_eval as E
from scripts import ensemble_diversity_eval_supervisor as S
from scripts.early_curriculum_study import digest
from scripts.experiment import limit_threads, state_sha256
from scripts.night_train_pilot import tensor_sha256

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('experiments/analysis/fog_influence_20261108/run_v1')
ARMS=('control41','neutral41','control42','neutral42')
NEW_MEMBERS=('control41','control42','neutral41','neutral42')
AUDIT=Path('experiments/analysis/fog_reward_20261108/operations/final-independent-audit.json')
AUDIT_SHA='cf563a0ac4c8ee890ee33800cc00e189d3d9104e11becca99e51c91441b49198'
PLANS=[ROOT/f'docs/superpowers/{kind}/2026-11-08-fog-influence.md' for kind in ('specs','plans')]
STOP=Path('/tmp').resolve()/'sherlock-fog-influence-20261108'/'STOP'
LIMIT=2500
require=F.require


def sample_buffer(path,sha256,rng):
    require(digest(path)==sha256,'Accepted replay buffer hash changed')
    with np.load(path,allow_pickle=False) as source:
        ns,mask,done=source['ns'],source['mask'],source['done']
        require(ns.ndim==2 and ns.shape[1]==79 and ns.dtype==np.float32
            and mask.shape==(len(ns),6) and mask.dtype==np.bool_
            and done.shape==(len(ns),) and np.isfinite(ns).all() and np.isfinite(done).all()
            and np.isin(done,(0,1)).all(),'Invalid finite79-feature ns/next_mask/done replay schema')
        eligible=np.flatnonzero((done==0)&mask.any(axis=1))
        indices=rng.choice(eligible,min(LIMIT,len(eligible)),replace=False)
        result=dict(ns=ns[indices].copy(),mask=mask[indices].copy(),indices=indices,
                    eligible_rows=len(eligible),source_rows=len(ns))
    require(digest(path)==sha256,'Replay changed while sampling')
    return result


def unique_rows(ns,mask):
    # Exact typed bytes, including the stored mask; no independence assumption.
    raw=np.concatenate((np.ascontiguousarray(ns).view(np.uint8).reshape(len(ns),-1),mask.view(np.uint8)),axis=1)
    keys=np.ascontiguousarray(raw).view(np.dtype((np.void,raw.shape[1]))).ravel()
    return len(np.unique(keys))


def sample_bank(buffers,check=lambda:None):
    require(tuple(buffers)==ARMS,'Fixed four replay arms/order required')
    rng=np.random.Generator(np.random.PCG64(0));parts=[];metadata={}
    for index,arm in enumerate(ARMS):
        check();item=buffers[arm];row=sample_buffer(item['path'],item['sha256'],rng)
        parts.append(dict(ns=row['ns'],mask=row['mask'],row_indices=row['indices'],
                          arm_indices=np.full(len(row['indices']),index,np.uint8)))
        metadata[arm]=dict(path=str(item['path']),sha256=item['sha256'],eligible_rows=row['eligible_rows'],
            source_rows=row['source_rows'],sampled_rows=len(row['indices']))
    bank={key:np.concatenate([p[key] for p in parts]) for key in parts[0]}
    require(0<len(bank['ns'])<=10000,'No eligible replay rows or bank exceeds fixed cap')
    return bank,dict(arms=metadata,sampled_rows=len(bank['ns']),unique_ns_mask_rows=unique_rows(bank['ns'],bank['mask']),
        uniqueness='byte-exact(ns,mask); no replacement within each arm; duplicates across arms retained',
        rng='PCG64 seed0, sequential arms control41/neutral41/control42/neutral42',limit_per_arm=LIMIT)


def persist_bank(out,bank,metadata,member_hashes):
    out=Path(out)
    with (out/'bank.npz').open('xb') as stream: np.savez(stream,**bank)
    proof=dict(metadata,bank_sha256=digest(out/'bank.npz'),bank_content_sha256=state_sha256(bank),
        ordered_member_hashes=member_hashes,forward_started=False)
    S.exclusive_json(out/'bank_manifest.json',proof)
    return proof


def legal_argmax(q,mask):
    q=np.asarray(q);mask=np.asarray(mask)
    require(q.ndim==2 and q.shape==mask.shape and q.shape[1]==6 and mask.dtype==np.bool_
            and np.isfinite(q).all() and mask.any(axis=1).all(),'Finite Q and nonempty legal six-action masks required')
    winners=np.where(mask,q,np.float32(-1e9)).argmax(axis=1)
    require(mask[np.arange(len(mask)),winners].all(),'Minus1e9 masking produced an illegal winner')
    return winners


def ensemble_means(members):
    require(members.shape[0]==40 and members.ndim==3 and members.shape[2]==6
            and members.dtype==torch.float32 and torch.isfinite(members).all(),'Exactly40 finite float32 member outputs required')
    return dict(V14=torch.stack(list(members[:36])).mean(0),
        CONTROL38=torch.stack([*members[:36],*members[36:38]]).mean(0),
        NEUTRAL38=torch.stack([*members[:36],*members[38:40]]).mean(0))


def check_reproduction(assembled,independent):
    require(assembled.shape==independent.shape and assembled.dtype==independent.dtype==torch.float32
        and torch.isfinite(assembled).all() and torch.isfinite(independent).all()
        and torch.allclose(assembled,independent,rtol=1e-6,atol=1e-6),'Independent38-member candidate mean mismatch')
    return dict(passed=True,max_absolute_error=float((assembled-independent).abs().max()),atol=1e-6,rtol=1e-6)


def distribution(values):
    values=np.asarray(values,dtype=np.float64).reshape(-1)
    require(np.isfinite(values).all(),'Nonfinite descriptive values')
    if not len(values): return dict(count=0)
    return dict(count=len(values),mean=float(values.mean()),std=float(values.std()),min=float(values.min()),
        max=float(values.max()),quantiles={str(q):float(np.quantile(values,q)) for q in (0,.05,.25,.5,.75,.95,1)})


def changes(base,candidate):
    changed=base!=candidate
    return dict(rows=len(base),changed=int(changed.sum()),to_sap=int(((base!=5)&(candidate==5)).sum()),
                from_sap=int(((base==5)&(candidate!=5)).sum()))


def gap(q,mask):
    eligible=mask.sum(1)>=2
    selected=q[eligible];legal=mask[eligible].copy()
    winners=legal_argmax(selected,legal)
    legal[np.arange(len(legal)),winners]=False
    runners=legal_argmax(selected,legal)
    return eligible,winners,runners,selected[np.arange(len(selected)),winners]-selected[np.arange(len(selected)),runners]


def summarize(members,mask,arm_indices):
    means=ensemble_means(members);raw=members.numpy();base=means['V14'].numpy()
    winner=legal_argmax(base,mask);multi,best,runner,_=gap(base,mask);rows=np.arange(len(base))
    report=dict(rows=len(base),rows_with_two_legal=int(multi.sum()),candidates={},members=[],parent18={})
    for index,q in enumerate(raw):
        proposals=legal_argmax(q,mask)
        report['members'].append(dict(index=index,q=distribution(q),legal_action_gap=distribution(gap(q,mask)[3]),
            proposals_vs_v14=changes(winner,proposals)))
    for role,start in (('CONTROL38',36),('NEUTRAL38',38)):
        full=means[role].numpy();candidate=legal_argmax(full,mask)
        pair=torch.stack(list(members[start:start+2])).mean(0).numpy()
        raw_delta=pair-base;delta=np.float32(2/38)*raw_delta
        changed=winner!=candidate;changed_rows=rows[changed]
        report['candidates'][role]=dict(proposal_changes=changes(winner,candidate),
            per_bank_arm={arm:changes(winner[arm_indices==i],candidate[arm_indices==i]) for i,arm in enumerate(ARMS)},
            pair_minus_base_all_q=distribution(raw_delta),full_mean_delta_all_q=distribution(delta),
            pair_minus_base_at_v14_winner=distribution(raw_delta[rows,winner]),
            pair_minus_base_at_candidate_winner=distribution(raw_delta[rows,candidate]),
            full_mean_delta_at_v14_winner=distribution(delta[rows,winner]),
            full_mean_delta_at_candidate_winner=distribution(delta[rows,candidate]),
            v14_fixed_margin_change=distribution(delta[multi][np.arange(len(best)),best]-delta[multi][np.arange(len(best)),runner]),
            changed_candidate_vs_v14_margin_contribution=distribution(delta[changed_rows,candidate[changed]]-delta[changed_rows,winner[changed]]),
            changed_candidate_vs_v14_original_margin=distribution(base[changed_rows,candidate[changed]]-base[changed_rows,winner[changed]]),
            changed_candidate_vs_v14_full_margin=distribution(full[changed_rows,candidate[changed]]-full[changed_rows,winner[changed]]),
            float32_decomposition_max_error=float(np.abs((full-base)-delta).max()))
    parent=raw[18];parent_winner=legal_argmax(parent,mask)
    for offset,arm in enumerate(NEW_MEMBERS):
        q=raw[36+offset];proposals=legal_argmax(q,mask)
        report['parent18'][arm]=dict(proposal_changes=changes(parent_winner,proposals),q_minus_parent=distribution(q-parent),
            per_bank_arm={a:changes(parent_winner[arm_indices==i],proposals[arm_indices==i]) for i,a in enumerate(ARMS)})
    return report


def inspect_models(root,admission,accepted):
    """Read/strict-load checkpoints only; never construct an Agent or environment."""
    checkpoints={role:torch.load(root/path,map_location='cpu',weights_only=True) for role,path in F.ROLE_PATHS.items()}
    for arm in ARMS:
        path=F.historical_path(root,accepted['root'],accepted['arms'][arm]['checkpoint_path'])
        checkpoints[arm]=torch.load(path,map_location='cpu',weights_only=True)
    cfg=AgentConfig.from_dict(checkpoints['V14']['cfg']).to_dict()
    for label,cp in checkpoints.items():
        require(cp.get('cnn_policy') is None,'CNN policy unsupported; stop rather than claim full neural inference')
        count=36 if label=='V14' else (38 if label in F.CANDIDATES else 1)
        effective,_=F.checked_checkpoint(cp,count)
        require(effective['hidden']==cfg['hidden'] and effective['dueling']==cfg['dueling'],'Different hidden/dueling structure')
        require(all(t.dtype==torch.float32 and torch.isfinite(t).all() for state in F._states(cp) for t in state.values()),
                'All actual member weights must be finite float32')
    states=[*F._states(checkpoints['V14']),*(checkpoints[a]['q'] for a in NEW_MEMBERS)]
    hashes=[tensor_sha256(s) for s in states]
    for role,start in (('CONTROL38',36),('NEUTRAL38',38)):
        require([tensor_sha256(s) for s in F._states(checkpoints[role])]==hashes[:36]+hashes[start:start+2]
            and AgentConfig.from_dict(checkpoints[role]['cfg']).to_dict()==admission['inference_config'],
                'Actual candidate order/config differs from accepted original36+pair')
    return states,checkpoints,cfg,hashes


def forward(states,ns,cfg,check):
    outputs=[]
    with torch.no_grad():
        for state in states:
            check()
            model=QNet(79,6,hidden=cfg['hidden'],dueling=cfg['dueling']).to(device='cpu',dtype=torch.float32)
            model.load_state_dict(state,strict=True);model.eval();batches=[]
            for start in range(0,len(ns),512):
                check();q=model(torch.from_numpy(ns[start:start+512]))
                require(q.dtype==torch.float32 and torch.isfinite(q).all(),'Nonfinite/wrong-dtype model output')
                batches.append(q)
            outputs.append(torch.cat(batches))
    return torch.stack(outputs)


def run(expected_head,usage_file,*,stop_file=STOP):
    """Exactly one process/one fresh destination; failure preserves partial evidence."""
    h=S.helpers();stop_file=h.safe_path(stop_file);out=h.safe_path(ROOT/OUT)
    require(not out.exists(),'Offline output already exists; no overwrite/retry')
    interrupted=[];state=None
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP)}
    with h.compute_lock(ROOT):
        try:
            for sig in handlers: signal.signal(sig,lambda *_:interrupted.append(True))
            accepted,bindings=F.historical_acceptance(ROOT)
            audit_path=S.repo_path(ROOT,str(AUDIT));require(digest(audit_path)==AUDIT_SHA,'Independent audit trust-anchor changed')
            audit=F.C._load_json(audit_path)
            require(audit.get('status')=='PASS','Replay audit not accepted')
            buffers={}
            for arm in ARMS:
                suffix=f'/20261108_fog_reward_{arm}/weights/agent.buffer.npz'
                candidates=[(p,sha) for p,sha in audit['artifact_files'].items() if p.endswith(suffix)]
                require(len(candidates)==1,'Missing/ambiguous fixed arm replay binding')
                old,sha=candidates[0];path=F.historical_path(ROOT,accepted['root'],old)
                require(digest(path)==sha,'Replay buffer differs from independent audit')
                buffers[arm]=dict(path=path,sha256=sha);bindings[str(path)]=sha
            admission_path=ROOT/F.CANDIDATE_DIR/'admission.json'
            bindings.update({str(audit_path):AUDIT_SHA,str(admission_path):digest(admission_path),
                **{str(ROOT/p):digest(ROOT/p) for p in F.ROLE_PATHS.values()}})
            source=h.source_identity(ROOT,sys.executable,PLANS)
            require(source['head']==expected_head and F.C._hex(expected_head,40),'Expected current source HEAD changed')
            protected={str(F.historical_path(ROOT,accepted['root'],p,protected=True)):sha for p,sha in accepted['protected'].items()}
            state=dict(schema_version=1,status='prepared',root=str(ROOT),out=str(out),python=sys.executable,
                expected_head=expected_head,source=source,plans=list(map(str,PLANS)),inputs=bindings,protected=protected,
                usage_file=str(h.safe_path(usage_file)),max_used_percent=100,stop_file=str(stop_file),owner_pid=os.getpid(),
                argv=sys.argv,model_processes=1)
            last=[0.]
            def check(force=False):
                require(not interrupted and not stop_file.exists(),'Signal/STOP requested')
                if force or time.time()-last[0]>=10:
                    E.guard(state,{});last[0]=time.time()
            check(True)
            admission,admission_bindings=F.validate_admission(admission_path,root=ROOT)
            state['inputs'].update(admission_bindings)
            states,checkpoints,cfg,member_hashes=inspect_models(ROOT,admission,accepted)
            check(True);out.parent.mkdir(parents=True,exist_ok=True);out.mkdir()
            state['status']='sampling';h.save_state(state)
            bank,metadata=sample_bank(buffers,check)
            proof=persist_bank(out,bank,metadata,member_hashes)
            state['inputs'].update(h.hashes([out/'bank.npz',out/'bank_manifest.json']))
            state.update(status='forward',bank_sha256=proof['bank_sha256']);h.save_state(state)
            check(True);limit_threads()
            member_q=forward(states,bank['ns'],cfg,check);means=ensemble_means(member_q)
            reproduction={};independent_means={}
            for role in F.CANDIDATES:
                independently_loaded=torch.load(ROOT/F.ROLE_PATHS[role],map_location='cpu',weights_only=True)
                independent=forward(F._states(independently_loaded),bank['ns'],cfg,check).mean(0)
                reproduction[role]=check_reproduction(means[role],independent)
                independent_means[role]=independent
            check(True)
            with (out/'outputs.npz').open('xb') as stream:
                np.savez(stream,member_q=member_q.numpy(),**{r+'_mean_q':q.numpy() for r,q in means.items()},
                    **{r+'_independent_mean_q':q.numpy() for r,q in independent_means.items()},
                    row_indices=bank['row_indices'],arm_indices=bank['arm_indices'],
                    ordered_member_hashes=np.asarray(member_hashes),
                    member_labels=np.asarray([f'original{i}' for i in range(36)]+list(NEW_MEMBERS)))
            summary=dict(schema_version=1,status='complete',bank=proof,reproduction=reproduction,
                descriptive=summarize(member_q,bank['mask'],bank['arm_indices']),
                outputs_sha256=digest(out/'outputs.npz'),source=source,
                limits='Balanced pooled trained-on, trajectory-dependent replay rows; not independent observations. '
                    'No inferential confidence intervals, action-quality labels, Fog attribution, final-rule claim or strength/promotion evidence.',
                arithmetic='P=mean(new pair);B=mean(original36);raw=P-B;full deltaQ=(2/38)*(P-B). '
                    'Fixed V14 best/runnerup deltaMargin for all rows with at least2legal actions; changed-winner margins separately.')
            state['inputs'].update(h.hashes([out/'outputs.npz']))
            check(True);summary['input_sha256']=dict(state['inputs'])
            S.exclusive_json(out/'summary.json',summary)
            state.update(status='complete',finished_at=time.time(),outputs_sha256=summary['outputs_sha256']);h.save_state(state)
            return summary
        except BaseException as exc:
            if state is not None and out.is_dir():
                state.update(status='incomplete',error=f'{type(exc).__name__}: {exc}');h.save_state(state)
            raise
        finally:
            for sig,handler in handlers.items(): signal.signal(sig,handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--expected-head',required=True)
    parser.add_argument('--usage-file',type=Path,required=True)
    parser.add_argument('--stop-file',type=Path,default=STOP)
    args=parser.parse_args();result=run(args.expected_head,args.usage_file,stop_file=args.stop_file)
    print(json.dumps(dict(status=result['status'],rows=result['bank']['sampled_rows'])))


if __name__=='__main__': main()
