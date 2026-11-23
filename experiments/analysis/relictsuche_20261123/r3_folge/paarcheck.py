"""Independently sum scored tiles and check all transfer and earlier full-game anchors from stored rows."""
import gzip
import json
from pathlib import Path


def rows(file):
    return [json.loads(line) for line in gzip.decompress(file.read_bytes()).splitlines()]


def main():
    here=Path(__file__).resolve().parent;out=here/'paartransfer';arms={r['mode']:r for r in rows(out/'verlaeufe.jsonl.gz')}
    known=next(r for r in rows(here/'ursachen/wertungen.jsonl.gz') if r['rival']=='solution')
    original={r['arm']:r for r in rows(here/'pilotpruefung/spiele.jsonl.gz') if r['seed']==known['seed'] and r['team']==known['team']}
    summary=json.loads((out/'ergebnis.json').read_text());assert set(arms)==set(summary['arms'])
    checks={}
    for mode,arm in arms.items():
        native=mode in ('native','plus')
        anchor=original['reference' if native else 'solution'];old=known['control' if native else 'active'];reference=arms['native' if native else 'advice']
        assert arm['matches'][:2]==anchor['matches'][:2] and reference['trace']==old['action_trace']==anchor['trace']
        assert arm['boundary']==reference['boundary'] and arm['boundary']['finished_matches']==arm['matches'][:2]
        assert arm['turns'][-1]['score']==arm['matches'][2]['points']
        change=set(arm['intervention']['before']['points'])^set(arm['intervention']['after']['points'])
        assert change==({290,515} if mode in ('plus','minus') else set())
        assert [r['turn'] for r in arm['turns']]==list(range(101))
        totals=[[sum(r['occupied'][j][team] for r in arm['turns']) for team in (0,1)] for j in (0,1)]
        assert totals==arm['field_credit']==summary['arms'][mode]['credit_on_pair']
        if mode in ('native','advice'):
            prev=[[old['credits'][f'2-{t}'].get(str(i),0) for t in (0,1)] for i in (290,515)]
            assert totals==prev and arm['matches']==old['matches']
        checks[mode]=dict(reconciled_m3_field_credits=totals,prefix=arm['boundary']['all_202_commands'],m3=arm['matches'][2]['points'])
    result=dict(all_modes=checks,all_m3_field_team_turn_indicators=4*2*2*101,complete_original_prefixes=2)
    dest=out/'nachrechnung.json'
    if dest.exists():assert json.loads(dest.read_text())==result
    else:dest.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('All M3 tile credits match each recorded indicator and both earlier full reference traces')


if __name__=='__main__':main()
