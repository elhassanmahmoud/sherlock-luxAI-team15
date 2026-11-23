"""Cross two agents' authentic public histories into the same live world at the decisive match reset."""
import argparse
import gzip
import json
import random
from pathlib import Path
import numpy as np
from luxai_s3.wrappers import LuxAIS3GymEnv
from experiments.analysis.relictsuche_20261123.abschlusspruefung.nachrechnen import decode
from experiments.analysis.relictsuche_20261123.abschlusspruefung.vergleich import make
from experiments.analysis.relictsuche_20261123.vergleich.spielen import Monitor,sha,write_once
from scripts.experiment import limit_threads
from scripts.par_eval import require_no_agent_errors
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'abschlusspruefung/partien.jsonl.gz'
CASES=((164300150,0,101),(164300158,0,202),(164300158,1,202))
CROSS=((0,0,0),(1,1,1),(1,0,0),(0,1,0),(1,1,0))


def play(envs,case,arms,bank):
    seed,t,cut=case;own,foe,world=arms
    side=f'player_{t}';other=f'player_{1-t}'
    players=make(('v16','ortundflotte')[own],side),make('solution92',other)
    for player,s in zip(players,(side,other),strict=True):
        if hasattr(player,'new_game'):player.new_game(s)
    random.seed(seed);np.random.seed(seed)
    monitors=[Monitor(e,t,'discovery') for e in envs]
    resets=[m.reset(seed=seed) for m in monitors]
    observations=[v[0] for v in resets]
    for player in players:
        if hasattr(player,'set_env_cfg'):player.set_env_cfg(resets[world][1]['params'])
    comparison=[bank[seed,t,a,'solution92'] for a in ('v16','ortundflotte')]
    tapes=[decode(r) for r in comparison]
    before=None
    for step in range(303):
        if step==cut:
            assert step in (101,202)
            before=[m.digest.hexdigest() for m in monitors]
            assert all(len(m.matches)==cut//101 for m in monitors)
            assert sum(x['win'] for x in monitors[0].matches)==sum(x['win'] for x in monitors[1].matches)
        src=(own,foe) if step<cut else (world,world)
        cmd={s:p.act(step=step,obs=observations[view][s]) for p,s,view in zip(players,(side,other),src,strict=True)}
        if step<cut:
            for i,s,view in zip((t,1-t),(side,other),src,strict=True):
                assert np.array_equal(cmd[s],tapes[view][step,i]),(case,arms,step,i)
            for k in (0,1):
                observed={f'player_{i}':tapes[k][step,i].astype(np.int32) for i in (0,1)}
                observations[k]=monitors[k].step(observed)[0]
        else:
            observations[world]=monitors[world].step(cmd)[0]
    require_no_agent_errors(*players)
    m=monitors[world]
    assert m.turn==303 and m.matches[:cut//101]==comparison[world]['matches'][:cut//101]
    if own==foe==world:
        assert m.digest.hexdigest()==comparison[world]['digest'] and m.matches==comparison[world]['matches']
    return dict(own=own,foe=foe,world=world,matched_prefix_commands=[cut,cut],prefixes=before,
                digest=m.digest.hexdigest(),matches=m.matches,win=int(sum(v['win'] for v in m.matches)>=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path);p.add_argument('op',choices=('play','score'));p.add_argument('index',type=int,nargs='?',default=0)
    a=p.parse_args();limit_threads()
    if a.op=='play':
        with gzip.open(SOURCE,'rt') as f:bank={tuple(v['key']):v for v in map(json.loads,f) if any(v['key'][:2]==list(c[:2]) for c in CASES)}
        envs=[LuxAIS3GymEnv(numpy_output=True) for _ in (0,1)]
        try:
            c=CASES[a.index]
            for arms in CROSS:
                dest=a.folder/f"{a.index}_{''.join(map(str,arms))}.json"
                if not dest.exists():write_once(dest,play(envs,c,arms,bank))
        finally:
            for e in envs:e.close()
        return
    out=[]
    for i,c in enumerate(CASES):
        rows=[json.loads((a.folder/f"{i}_{''.join(map(str,v))}.json").read_bytes()) for v in CROSS]
        assert len({tuple(r['prefixes']) for r in rows})==1 and rows[0]['win']==0 and rows[1]['win']==1
        out.append(dict(seed=c[0],team=c[1],boundary=c[2],rows=rows))
    write_once(HERE/'ergebnis.json',dict(source=sha(SOURCE),cases=out))


if __name__=='__main__':main()
