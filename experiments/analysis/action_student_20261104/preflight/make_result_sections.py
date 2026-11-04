"""Format already audited complete measurements; no candidate selection."""
import argparse,json
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--audit',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
d=json.loads(args.audit.read_text());assert d['integrity']=='complete' and d['games']==1400;assert not args.out.exists()
def wdl(item):return f"{item['wins']}–{item['draws']}–{item['losses']}"
def contrast(item):
    lo,hi=item['percentile_95_ci_percentage_points']
    return f"{item['score_difference_percentage_points']:+.2f} pp [{lo:+.2f}; {hi:+.2f}]"
lines=['## Ergebnisse auf neuen Karten','','W–R–N = Siege–Remis–Niederlagen. Je Gegner und Rolle 40 Spiele auf 20 Karten, beide Seiten. Die Direktduelle verwenden 20 andere Karten.','','| Variante | Netze | Solution W–R–N | default W–R–N | V13 W–R–N | Direkt gegen V14 W–R–N |','|---|---:|---:|---:|---:|---:|']
for role,s in d['summaries'].items():
    o=s['by_opponent'];v13=next(v for k,v in o.items() if k.startswith('self:'));direct=wdl(d['direct_against_V14'][role]) if role!='V14' else '–';nets=36 if role=='V14' else 2 if role in ('CONTROL2','SAP02') else 1
    lines.append(f"| {role} | {nets} | {wdl(o['solution92'])} | {wdl(o['default'])} | {wdl(v13)} | {direct} |")
lines+=['','### Änderungen gegenüber V14','','Panel = gleich gewichteter Vergleich gegen Solution, default und V13. Remis zählen halb. Werte sind Differenzen in Prozentpunkten mit 95-%-Intervall aus ganzen Karten.','','| Variante | Paneländerung gegenüber V14 | Solution-Änderung gegenüber V14 |','|---|---:|---:|']
for role,c in d['comparisons_against_V14'].items():
    if role!='V14':lines.append(f"| {role} | {contrast(c['pooled_three_opponent_panel'])} | {contrast(c['by_opponent']['solution92'])} |")
lines+=['','### Welche Änderung hilft?','','| Vorab festgelegter Vergleich | Paneländerung | Solution-Änderung |','|---|---:|---:|']
pairs=[('A2 gegenüber S30',d['A2_against_S30'])]
pairs += [(f'SAP0 gegenüber Kontrolle, Start {seed}',value) for seed,value in d['reward_comparisons'].items()]
pairs += [(f'{ensemble} gegenüber {member}',value) for ensemble,items in d['ensemble_against_constituents'].items() for member,value in items.items()]
for label,c in pairs:lines.append(f"| {label} | {contrast(c['pooled_three_opponent_panel'])} | {contrast(c['by_opponent']['solution92'])} |")
lines+=['','Auch diese Intervalle sind explorativ und nicht für die vielen Vergleiche korrigiert. Einzelergebnisse der zwei Trainingsstarts werden nicht als große Zahl unabhängiger Trainingswiederholungen behandelt. Die vollständigen Direktintervalle und Werte je Startseite stehen im [unabhängigen Auswertungsbericht](../experiments/analysis/action_student_20261104/diagnostic/diagnostic_review.md).','']
args.out.write_text('\n'.join(lines))
