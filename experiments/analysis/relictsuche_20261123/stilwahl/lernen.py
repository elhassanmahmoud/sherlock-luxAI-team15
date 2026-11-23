"""Out-of-fold risk-sensitive decisions on the complete, outcome-unselected archived cards."""
from collections import Counter

import numpy as np

from daten import GAMES, HERE, compact, extract, save, sha
from modell import STYLE_NAMES, fit, predict


def folds(rows):
    result={};rng=np.random.default_rng(231123)
    for opp in ('solution92','v16'):
        for side in (0,1):
            keys=sorted(r['seed'] for r in rows if r['opponent']==opp and r['team']==side)
            assert len(keys)==40
            for i,s in enumerate(rng.permutation(keys)):result[int(s)]=i%4
    return result


def model_from(rows):
    allowed=[r for r in rows if r['eligible'] and r['observable']]
    return fit([r['input'] for r in allowed],[r['style'] for r in allowed],[r['target'] for r in allowed])


def summarize(rows,field):
    out={}
    for group in ('both','solution92','v16'):
        population=[r for r in rows if group=='both' or r['opponent']==group]
        chosen=[r for r in population if r[field]]
        value=np.asarray([r['target'] if r[field] else 0 for r in population],dtype=int)
        rng=np.random.default_rng(163710);boot=np.mean(value[rng.integers(0,len(value),(20000,len(value)))],axis=1)
        gains=[r for r in chosen if r['delta']>0];losses=[r for r in chosen if r['delta']<0]
        out[group]=dict(maps=len(population),switched=len(chosen),gains=len(gains),losses=len(losses),
             gain_seeds=[r['seed'] for r in gains],loss_seeds=[r['seed'] for r in losses],gain_folds=sorted({r['fold'] for r in gains}),
             whole_wins=sum(r['switch'] if r[field] else r['original'] for r in population),
             native_wins=sum(r['original'] for r in population),risk_total=int(value.sum()),risk_mean=float(value.mean()),
             risk_lower90=float(np.quantile(boot,.1)),risk_ci95=np.quantile(boot,[.025,.975]).tolist())
    return out


def main():
    rows=extract();allocation=folds(rows);fit_sizes=[]
    for r in rows:r['fold']=allocation[r['seed']]
    for i in range(4):
        train=[r for r in rows if r['fold']!=i];test=[r for r in rows if r['fold']==i]
        assert len(train)==120 and len(test)==40 and not {r['seed'] for r in train}&{r['seed'] for r in test}
        spec=model_from(train);fit_sizes.append(sum(r['eligible'] and r['observable'] for r in train))
        for r in test:
            for label,is_extended in (('base21',False),('extended',True)):
                s=predict(spec,r['input'],r['style'],is_extended) if r['eligible'] and r['observable'] else None
                r[label+'_score']=s;r[label]=s is not None and s>.05
            r['native_pick']=False;r['always_pick']=r['eligible']
    names=('native_pick','always_pick','old_pick','base21','extended')
    totals={k:summarize(rows,k) for k in names};sel=totals['extended'];pooled=sel['both']
    gates=dict(eight_real_switches=pooled['switched']>=8,two_gains_in_two_folds=pooled['gains']>=2 and len(pooled['gain_folds'])>=2,
        risk_better_than_native_and_base=pooled['risk_total']>max(0,totals['base21']['both']['risk_total']),
        nonnegative_risk_lower90=pooled['risk_lower90']>=0,
        neither_opponent_loses_net=all(sel[k]['whole_wins']>=sel[k]['native_wins'] for k in ('solution92','v16')))
    diagnostics={}
    for grp in ('both','solution92','v16'):
        pop=[r for r in rows if grp=='both' or r['opponent']==grp];eligible=[r for r in pop if r['eligible']]
        supported=[r for r in eligible if r['observable']]
        diagnostics[grp]=dict(maps=len(pop),m1_wins=len(eligible),supported=len(supported),
            observation_counts={k:int(sum(r['tracks'][k] for r in eligible)) for k in ('moving','consecutive')},
            true_gains_all=sum(r['delta']>0 for r in eligible),true_gains_supported=sum(r['delta']>0 for r in supported),
            true_losses_all=sum(r['delta']<0 for r in eligible),true_losses_supported=sum(r['delta']<0 for r in supported),
            true_gains_without_contact_support=[r['seed'] for r in eligible if r['delta']>0 and not r['observable']])
    compact(HERE/'kreuzkarten.jsonl.gz',rows);save(HERE/'modell.json',dict(names=STYLE_NAMES,fit=model_from(rows)))
    save(HERE/'ergebnis.json',dict(passed=all(gates.values()),gates=gates,models=totals,support=diagnostics,technical=dict(
        maps=160,archived_games=275,test_per_fold=40,train_supported_per_fold=fit_sizes,outcome_identifiers_in_model=False,
        reproduced_original_features=160*21,mirror_checks=160,uid_permutation_checks=160,never_opened_valid_maps=48,
        archived_scores_sha=sha(GAMES),input_rows_sha=sha(HERE/'kreuzkarten.jsonl.gz'),plan_sha=sha(HERE/'PLAN.md'))))
    print('Passed:',all(gates.values()),'extended:',pooled,'coverage:',diagnostics)


if __name__=='__main__':main()
