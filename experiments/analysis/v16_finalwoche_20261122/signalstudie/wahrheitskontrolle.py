"""Wertet die öffentliche Frühwarnung auf dem fertigen unabhängigen Referenzsatz extern aus."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from messen import HERE, SEEDS, source_hashes


def activation(env,seed):
    # Die Kurs-Engine bildet die neue Maske im Übergang aus dem vorherigen
    # globalen Zugzähler. Das erste sichtbare Ergebnisdatum ist schedule+1.
    env.reset(seed=seed)
    schedule=np.asarray(env.state.relic_spawn_schedule,dtype=int)
    if schedule.shape!=(6,) or not np.array_equal(schedule[:3],schedule[3:]):
        raise ValueError("Unerwartete Zuordnung der beiden Spiegelseiten")
    return int(schedule[1])+1-101 if schedule[1]>=0 else None


def observed(folder):
    return [r for i in (0,1) for r in map(json.loads,(folder/f"worker_{i}.jsonl").read_text().splitlines())]


def analyze(rows,truth):
    counts=dict(sides=len(rows),maps=len({r["seed"] for r in rows}),no_second_pair_sides=0,
                no_second_pair_maps=len({r["seed"] for r in rows if truth[r["seed"]] is None}),
                genuine_opportunities=0,signaled=0,early=0,short_lead=0,false_alarms=0,missed_opportunities=0,
                early_lost_whole=0,missed_lost_whole=0,whole_losses=0)
    early_maps=set()
    lead_turns=[]
    for r in rows:
        seed=r["seed"]
        spawn=truth[seed]
        sight=r["known_second"]
        if sight is not None and (spawn is None or sight < spawn): raise ValueError("Sicht vor Existenz des Paares")
        end=100 if sight is None else sight
        counts["no_second_pair_sides"]+=spawn is None
        opportunity=spawn is not None and max(50,spawn)<=79 and end-max(50,spawn)>=5
        counts["genuine_opportunities"]+=opportunity
        counts["whole_losses"]+=not r["game_win"]
        event=r["first"]
        on_time=False
        if event:
            t=event["turn"]
            if not 50<=t<=79: raise ValueError("Unerwartetes öffentliches Auslösefenster")
            counts["signaled"]+=1
            if spawn is None or t<spawn:
                counts["false_alarms"]+=1
            elif end-t>=5:
                counts["early"]+=1
                early_maps.add(seed)
                counts["early_lost_whole"]+=not r["game_win"]
                lead_turns.append(end-t)
                on_time=True
            else:
                counts["short_lead"]+=1
        if opportunity and not on_time:
            counts["missed_opportunities"]+=1
            counts["missed_lost_whole"]+=not r["game_win"]
    counts["early_maps"]=len(early_maps)
    counts["true_lead_min_max"]=[min(lead_turns),max(lead_turns)] if lead_turns else []
    return counts


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("phase",choices=("haupt","kaggle"))
    phase=ap.parse_args().phase
    folder=HERE/phase
    outcome=json.loads((folder/"ergebnis.json").read_bytes())
    if outcome["n"]!=(900 if phase=="haupt" else 800): raise ValueError("Erst nach Vollständigkeit")
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.experiment import limit_threads
    limit_threads()
    env=LuxAIS3GymEnv(numpy_output=True)
    validation={s:activation(env,s) for s in SEEDS}
    old=observed(HERE/"beobachtung")
    if len(old)!=96 or any(validation[r["seed"]]!=r["true_second_spawn"] for r in old):
        raise ValueError("Kartenerzeugung reproduzierte die im Spiel beobachtete Spawnzeit nicht")
    opp="solution92" if phase=="haupt" else "kaggle3"
    rows=[r for r in observed(folder) if r["opponent"]==opp and r["arm"]=="v16"]
    seeds=sorted({r["seed"] for r in rows})
    if len(rows)!=400 or len(seeds)!=200: raise ValueError("Falsche Referenzkarten")
    truth={s:activation(env,s) for s in seeds}
    doc=dict(original_controls=48,original_seats=96,map_truth=truth,total=analyze(rows,truth),
             by_side={s:analyze([r for r in rows if r["side"]==s],truth) for s in ("player_0","player_1")},
             validation_sources=source_hashes(),result_digest=sha256((folder/"ergebnis.json").read_bytes()).hexdigest())
    (folder/"signalwahrheit.json").write_text(json.dumps(doc,indent=2)+"\n")
    print(json.dumps(doc["total"],indent=2))


if __name__=="__main__": main()
