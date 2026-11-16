"""Independently check the frozen blend study and print its German report or JSON."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SEATS = ('player_0', 'player_1')
FRESH = range(7151000, 7151040)
DIRECT = range(7173400, 7173416)
FIELDS = ('game_win', 'our_wins', 'opp_wins', 'our_points', 'opp_points', 'steps')
REF_FIELDS = ('win', 'matches_won', 'matches_lost', 'points', 'opp_points', 'steps')
JOINED = 'experiments/analysis/movement_soft_20261115/shared_400/sitzvergleich/joined.csv'
DEV_B = 'experiments/analysis/kaggle3_20261115/devB_hyb_v4_mixed.csv'
PINS = {JOINED: '9589b3d5b1b4e9634aca85c91984a987ca32228c03db27736df740e0b1ae7ec6',
        DEV_B: 'c636616ec829532fad74605d13fcfc4d813dfee7b96b453d5eda219f45d8ec26'}
SOURCES = {'PLAN.md': 'f52f63e6093a6c277df1982a638c1b025c604c046c8760c6745f90c92f355134',
           'REGEL.md': 'add0e39012709dcae73484d88f2102b97fe305671a764e52323a7642c0400231',
           'kombination.py': '46b8c35d8acbfd0126fa4d37c2bff9485121fb8fca8aa982535e2b78cb774468',
           'spiele.py': '155fa15c4b0da30dfb5fe1b9d5a4239c9da4836ed3d171fb4b3e4f84a200c863'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def full(seeds):
    return {(s, p) for s in seeds for p in SEATS}


def checked_score(values):
    require(len(values) == 6 and all(type(x) is int and x >= 0 for x in values),
            'Invalid outcome fields')
    won, a, b, _, _, steps = values
    require(a+b == 3 and won == int(a>b) and steps == 303, f'Invalid terminal score {values}')
    return tuple(values)


def references(repo):
    for name, expected in PINS.items():
        require(sha(repo/name) == expected, f'Changed reference {name}')
    with (repo/JOINED).open(newline='') as stream:
        both = {}
        for row in csv.DictReader(stream):
            key = (row['opponent'], int(row['seed']), row['side'])
            require(key not in both, f'Duplicate published key {key}')
            both[key] = {a: checked_score([int(row[a+'_'+f]) for f in REF_FIELDS])
                         for a in ('r3', 'v14', 'v15')}
    require(set(both) == {(o,s,p) for o in ('solution92','kaggle3')
                         for s,p in full(range(7158000,7158400))}, 'Incomplete shared panel')
    original = {(s,p): v for (o,s,p),v in both.items() if o=='solution92'}
    dev = {}
    with (repo/DEV_B).open(newline='') as stream:
        for row in csv.DictReader(stream):
            k = row['opponent'], int(row['seed']), row['side']
            score = checked_score([int(row[f]) for f in FIELDS])
            require(k not in dev and int(row['point_counting_version']) == 2
                    and float(row['result']) == score[0], f'Invalid V15 reference at {k}')
            require(float(row['point_win']) == (1 if score[3]>score[4] else .5 if score[3]==score[4] else 0),
                    f'Invalid point result at {k}')
            dev[k] = score
    opponents = ('solution92','kaggle3','self:agents/sherlock/weights/agent_p0.pth')
    require(set(dev) == {(o,s,p) for o in opponents for s,p in full(range(7151000,7151100))},
            'Incomplete V15 Dev B reference')
    return original, {(s,p): dev['solution92',s,p] for s,p in full(FRESH)}


def load_phase(study, name, schedule):
    path = study/name/'games.jsonl'
    seal = read(path.with_name('complete.json'))
    raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==seal['sha256'] and seal['n']==len(schedule), f'Invalid {name} completion')
    groups = {}
    for line in raw.splitlines():
        r=json.loads(line)
        k = r['arm'],r['opponent'],r['seed'],r['seat']
        require(k in schedule and k not in groups, f'Unexpected or repeated {name} key {k}')
        score=checked_score([r[f] for f in FIELDS])
        counts=r.get('routing',{})
        if k[0] in ('blend','contact'):
            keys=({'contact','early_outside','early_different','early_add_shot'} if k[0]=='blend'
                  else {'near_unit_turns','far_unit_turns','different_near','different_far'})
            require(set(counts)==keys and all(type(v) is int and v>=0 for v in counts.values()),
                    f'Invalid routing counters {k}')
            if k[0]=='blend':
                require(counts['early_add_shot']<=counts['early_different']<=counts['early_outside']
                        <= 2*25*16 and counts['contact']+counts['early_outside']<=303*16,
                        f'Impossible early window {k}')
            else:
                require(counts['different_near']<=counts['near_unit_turns'] and
                        counts['different_far']<=counts['far_unit_turns'] and
                        counts['near_unit_turns']+counts['far_unit_turns']<=303*16, f'Impossible contact {k}')
        groups[k]=(score,counts)
    require(groups.keys()==schedule, f'Incomplete {name} schedule')
    return groups,seal


def diagnosis_refs(study, original, keys):
    diag=study/'diagnose'
    report=read(diag/'summary.json')
    evidence=report['raw_sha256']
    files={f'{a}-{s}-{p}.json.gz' for a in ('r3','v15') for s,p in keys}
    require(set(evidence)==files and {p.name for p in (diag/'roh').glob('*.gz')}==files, 'Parent replay scope')
    require(report['rows']==72 and report['steps_per_arm']==3636, 'Parent match count')
    for name in sorted(files):
        path=diag/'roh'/name
        require(sha(path)==evidence[name], f'Changed parent replay {name}')
        r=json.loads(gzip.decompress(path.read_bytes()))
        a,s,p=r['arm'],r['seed'],r['side']
        ref=original[s,p][a]
        require(name==f'{a}-{s}-{p}.json.gz' and checked_score(r['actual'])==ref==checked_score(r['expected']),
                f'Parent terminal result {name}')
        fs=r['frames']
        require([f['step'] for f in fs]==list(range(303)) and sum(f['after'][0] for f in fs[100::101])==ref[3]
                and sum(f['after'][1] for f in fs[100::101])==ref[4] and tuple(fs[-1]['next_wins'])==ref[1:3],
                f'Parent clock/score {name}')
        for tag,side in [('own_orders',p),('opp_orders',SEATS[1-SEATS.index(p)])]:
            mats=np.asarray([f[tag] for f in fs])
            require(mats.shape==(303,16,3) and mats.dtype.kind in 'iu' and
                    hashlib.sha256(mats.astype('<i8').tobytes()).hexdigest()==r['command_sha256'][side],
                    f'Parent command stream {name} {side}')
    return sha(diag/'summary.json')


def totals(group):
    return dict(games=len(group),wins=sum(x[0] for x in group.values()),
                match_wins=sum(x[1] for x in group.values()))


def paired(a,b=None):
    require(b is None or a.keys()==b.keys(),'Unpaired comparison')
    keys=sorted(a)
    require(set(keys)==full({s for s,_ in keys}),'Both seats required for map bootstrap')
    panel=np.array([a[k][0]-(b[k][0] if b is not None else 0) for k in keys]).reshape(-1,2).mean(axis=1)
    indices=np.random.default_rng(2711).integers(0,len(panel),size=(10000,len(panel)))
    r=dict(maps=len(panel),games=len(keys),value=float(panel.mean()),
           ci95=np.percentile(panel[indices].mean(axis=1),[2.5,97.5]).tolist())
    if b is not None:
        r.update(gained=sum(a[k][0]>b[k][0] for k in keys),lost=sum(a[k][0]<b[k][0] for k in keys))
    return r


def assess(repo,study,runs=None):
    runs=runs or study
    for name,digest in SOURCES.items():
        require(sha(study/name)==digest,f'Changed frozen study source {name}')
    runtime=read(study/'laufzeit.json')
    require(sha(study/'laufzeit.json')=='0f1d82ee28801175562b78d8aff5ebb64aa6a19e42e8c5f5c9e472e361cd72f0'
            and runtime['point_counting_version']==2, 'Unexpected game runtime or scoring version')
    original,dev_v15=references(repo)
    losses={k for k,v in original.items() if v['r3'][0]==0}
    require(len(losses)==12 and sum(original[k]['v15'][0] for k in losses)==9, 'Wrong diagnosis cases')
    parent_digest=diagnosis_refs(study,original,losses)
    def schedule(arm,opp,seats):
        return {(arm,opp,s,p) for s,p in seats}
    plans={'smoke':set().union(*(schedule(a,'solution',full([7158000])) for a in ('r3','v15'))),
           'control':schedule('r3','solution',full(FRESH))|schedule('r3','v15',full(DIRECT))}
    for a,phase in [('blend','candidate'),('contact','contact')]:
        plans[phase]=schedule(a,'solution',full(FRESH))|schedule(a,'r3',full(DIRECT))|schedule(a,'v15',full(DIRECT))
        plans['diagnosis_'+a]=schedule(a,'solution',losses)
    seals,groups={},{}
    for name,keys in plans.items():
        groups[name],seals[name]=load_phase(runs,name,keys)
    for (a,_,s,p),(score,_) in groups['smoke'].items():
        require(score==original[s,p][a],f'Failed original smoke comparison {a}/{s}/{p}')
    def arm(phase,who,opp):
        return {(s,p): row[0] for (a,o,s,p),row in groups[phase].items() if a==who and o==opp}
    groups_sol={'r3':arm('control','r3','solution'),'v15':dev_v15,
                'blend':arm('candidate','blend','solution'),'contact':arm('contact','contact','solution')}
    sol={a:paired(groups_sol['blend'],groups_sol[a]) for a in ('r3','v15','contact')}
    direct={}
    for opp in ('r3','v15'):
        blend=arm('candidate','blend',opp)
        contact=arm('contact','contact',opp)
        d=dict(blend=totals(blend),contact=totals(contact),blend_winrate=paired(blend),
               contact_winrate=paired(contact),blend_minus_contact=paired(blend,contact))
        if opp=='v15':
            control=arm('control','r3','v15')
            d.update(original_r3=totals(control),blend_minus_r3=paired(blend,control))
        direct[opp]=d
    diagnoses={a:{k:original[k][a] for k in losses} for a in ('r3','v15')}
    diagnoses.update({a:arm('diagnosis_'+a,a,'solution') for a in ('blend','contact')})
    per_seat=[dict(seed=s,seat=p,**{a:g[s,p] for a,g in diagnoses.items()}) for s,p in sorted(losses)]
    def flipped(a,b):
        return {name:[list(k) for k in sorted(losses) if (diagnoses[a][k][0]-diagnoses[b][k][0])==sign]
                for name,sign in [('gained',1),('lost',-1)]}
    changes={f'{a}_minus_{b}':flipped(a,b) for a,b in (
        ('blend','r3'),('blend','v15'),('blend','contact'),('contact','r3'),('contact','v15'))}
    activity={}
    for phase in ('candidate','diagnosis_blend'):
        for opp in ('solution','r3','v15'):
            use=[(k[3],counter) for k,(_,counter) in groups[phase].items() if k[1]==opp]
            if use:
                activity[phase+'/'+opp]={p:{c:sum(n[c] for side,n in use if side==p) for c in use[0][1]}
                                        for p in SEATS}
    gates=dict(solution_improves=sol['r3']['value']>0,
               majority_vs_r3=direct['r3']['blend_winrate']['value']>.5,
               majority_vs_v15=direct['v15']['blend_winrate']['value']>.5,
               better_than_r3_against_v15=direct['v15']['blend_minus_r3']['value']>0)
    return dict(sources=SOURCES,references=PINS,completions=seals,runtime_sha256=sha(study/'laufzeit.json'),
                parent_diagnosis_sha256=parent_digest,point_counting_version=2,
                solution={a:totals(g) for a,g in groups_sol.items()},solution_deltas=sol,
                direct=direct,diagnosis={a:totals(g) for a,g in diagnoses.items()},diagnosis_seats=per_seat,
                diagnosis_pair_changes=changes,window=activity,gates=gates,positive_screen=all(gates.values()),
                bootstrap='10,000 draws of whole paired maps, both seats together, PCG64(2711)')


def percent(x,signed=False):
    return format(100*x, '+.2f' if signed else '.2f').replace('-','−').replace('.',',')


def effect(r,difference=True):
    unit='Prozentpunkte' if difference else '%'
    text=f"{percent(r['value'],difference)} {unit} (95-%-Intervall {percent(r['ci95'][0],difference)} bis {percent(r['ci95'][1],difference)})"
    if difference:
        text+=f", {r['gained']} hinzugewonnen, {r['lost']} verloren"
    return text


def record(r):
    return f"{r['wins']}/{r['games']} Spiele, {r['match_wins']}/{3*r['games']} Matches"


def markdown(r):
    lines=['# R3 und V15 mit einem frühen V15-Fenster', '',
           '**'+('Das Ergebnis rechtfertigt eine unabhängige Bestätigung.' if r['positive_screen'] else
                 'Die Kombination verfehlt das vorab festgelegte Ziel für eine unabhängige Bestätigung.')+'**',
           (f"Auf den 80 Solution-Sitzen gewinnt die Kombination {r['solution']['blend']['wins']} Spiele, "
            f"Original-R3 {r['solution']['r3']['wins']} und V15 {r['solution']['v15']['wins']}. "
            f"Direkt gewinnt sie {r['direct']['r3']['blend']['wins']}/32 gegen R3 und "
            f"{r['direct']['v15']['blend']['wins']}/32 gegen V15. Original-R3 ist die freigegebene Finaleversion."),
           '', '## Solution auf 40 Entwicklungskarten','']
    for name,g in r['solution'].items():
        lines.append(f"- {name}: {record(g)}.")
    lines+=['','Differenz der Kombination in ganzen Spielsiegen, gepaart auf denselben 80 Sitzen.','']
    for name,comparison in r['solution_deltas'].items():
        lines.append(f'- Gegenüber {name}: {effect(comparison)}.')
    lines+=['','## Direktduelle auf 16 anderen Karten','']
    for name,d in r['direct'].items():
        lines += [f"- Gegner {name}: Kombination {record(d['blend'])}, Siegquote {effect(d['blend_winrate'],False)}.",
                  f"- Kontaktroute gegen {name}: {record(d['contact'])}. Unterschied durch das Zusatzfenster: {effect(d['blend_minus_contact'])}."]
        if 'original_r3' in d:
            lines.append(f"- Original-R3 gegen V15: {record(d['original_r3'])}. Kombination minus R3 gegen denselben Gegner V15: {effect(d['blend_minus_r3'])}.")
    lines+=['','## Die zwölf bekannten R3-Niederlagen','',
            'Die Fälle wurden nach dem ursprünglichen R3-Ergebnis gewählt. Sie bleiben außerhalb der Entwicklungswertung.','',
            '| Sitz | R3 | V15 | Kontakt | Kombination |','|---|---:|---:|---:|---:|']
    for row in r['diagnosis_seats']:
        cells=[':'.join(map(str,row[a][1:3])) for a in ('r3','v15','contact','blend')]
        lines.append(f"| {row['seed']} / {row['seat']} | "+' | '.join(cells)+' |')
    lines+=['','Jede Tabellenzelle enthält die Matchsiege beider Teams im betreffenden ganzen Spiel.','']
    for a,g in r['diagnosis'].items():
        lines.append(f'- {a}: {record(g)}.')
    def seats(xx):
        return ', '.join(f'{s}/P{p[-1]}' for s,p in xx) or 'keine'
    for name,d in r['diagnosis_pair_changes'].items():
        arm,other=name.split('_minus_')
        lines.append(f"- {arm} gegenüber {other}: gerettet {len(d['gained'])} ({seats(d['gained'])}), neu verloren {len(d['lost'])} ({seats(d['lost'])}).")
    lines+=['','## Tatsächliche Befehlsänderungen','',
            '| Stichprobe/Gegner | Spieler 0 | Spieler 1 |','|---|---:|---:|']
    for name,activity in r['window'].items():
        lines.append(f"| {name} | {activity['player_0']['early_different']} | {activity['player_1']['early_different']} |")
    lines+=['','Gezählt sind abweichende vollständige Elternbefehle außerhalb der Kontaktroute in den ersten 25 Zügen von Match 2 und 3. Der Effekt der gesamten Regel ergibt sich aus den gepaarten Spielen der Kombination und der sonst identischen Kontaktroute.','',
            'Die Intervalle resampeln 10.000-mal ganze Karten einschließlich beider Sitze (Seed 2711). Für die vier vorab genannten Auswahlbedingungen zählen Punktschätzer. Die Intervalle zeigen deren Unsicherheit.','',
            '| Auswahlbedingung | Erfüllt |','|---|---|']
    names={'solution_improves':'Mehr Solution-Siege als Original-R3','majority_vs_r3':'Mehrheit direkt gegen R3',
           'majority_vs_v15':'Mehrheit direkt gegen V15','better_than_r3_against_v15':'Mehr Siege als R3 im direkten Spiel gegen V15'}
    lines += [f"| {names[k]} | {'Ja' if v else 'Nein'} |" for k,v in r['gates'].items()]
    lines+=['','Der Vergleich umfasst 400 neue Entwicklungsspiele und 80 wiederverwendete V15-Referenzspiele. Separat wurden vier technische Kontrollen sowie 24 Elternwiederholungen und 24 Partien der beiden Kombinationsregeln auf den zwölf bekannten Diagnosesitzen geprüft.',
            '', '[Vorabplan](PLAN.md) · [Regel und Kontrollarm](REGEL.md) · [Elterndiagnose](diagnose/ERGEBNIS.md) · [Laufzeitnachweis](laufzeit.json)']
    return '\n'.join(lines)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=ROOT)
    parser.add_argument('--study',type=Path,default=HERE)
    parser.add_argument('--runs',type=Path,help='Alternative directory containing the six finished game phases')
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    report=assess(args.repo,args.study,args.runs)
    print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False) if args.json else markdown(report))
