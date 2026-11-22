"""Run only prespecified seed/seat jobs on one CPU or the first selected event of each match."""
from pathlib import Path
import argparse
import json
from messen import run_one

if __name__=='__main__':
    q=argparse.ArgumentParser()
    q.add_argument('mode',choices=('original','fork'))
    q.add_argument('folder',type=Path)
    q.add_argument('first',type=int);q.add_argument('last',type=int);q.add_argument('side',type=int,choices=(0,1))
    a=q.parse_args()
    for seed in range(a.first,a.last+1):
        if a.mode=='original':
            run_one(seed,a.side,a.folder)
        else:
            baseline=json.loads((a.folder/f'{seed}_{a.side}.json').read_text())
            for i,event in enumerate(baseline['selected']):
                if event['ms'] <= 93:
                    run_one(seed,a.side,a.folder,i)
