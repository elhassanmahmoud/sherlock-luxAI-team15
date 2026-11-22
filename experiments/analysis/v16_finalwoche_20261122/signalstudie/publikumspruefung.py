"""Prüft Vollständigkeit, identische Ausgangssituationen und die vorab fixierten Grenzen."""
import argparse
import json

import numpy as np

from bestaetigen import HERE, panel, frozen


def summarize(rows, target):
    external=[r for r in rows if r["opponent"]==target]
    games={(r["seed"],r["side"],r["arm"]):r for r in external}
    by_key=sorted(k[:2] for k in games if k[2]=="v16")
    results=[]
    for seed,side in by_key:
        old=games[seed,side,"v16"]
        new=games[seed,side,"signal"]
        if old["first"]!=new["first"] or (not new["changes"] and any(
            old[key]!=new[key] for key in ("our_wins","opp_wins","our_points","opp_points","match_winners",
                                          "game_win","known_second","fields_step0","fields_step1"))):
            raise ValueError(f"Widersprüchliches Paar vor dem Auslöser auf {seed}/{side}")
        delta=new["game_win"]-old["game_win"]
        results.append(dict(seed=seed,side=side,baseline=old["game_win"],candidate=new["game_win"],delta=delta,
                            old_matches=old["our_wins"],matches=new["our_wins"],
                            score_diff=(new["our_points"]-new["opp_points"])-(old["our_points"]-old["opp_points"]),
                            changes=len(new["changes"]), first=new["first"]["turn"] if new["first"] else None,
                            old_sight=old["known_second"],sight=new["known_second"],
                            old_fields_3=old["fields_step0"],fields_3=new["fields_step0"]))
    def stats(sub):
        return dict(sides=len(sub),maps=len({r["seed"] for r in sub}),baseline_wins=sum(r["baseline"] for r in sub),
                    candidate_wins=sum(r["candidate"] for r in sub),added=sum(r["delta"]==1 for r in sub),
                    lost=sum(r["delta"]==-1 for r in sub),baseline_matches=sum(r["old_matches"] for r in sub),
                    candidate_matches=sum(r["matches"] for r in sub),score_diff=sum(r["score_diff"] for r in sub),
                    altered_sides=sum(r["changes"]>0 for r in sub),altered_maps=len({r["seed"] for r in sub if r["changes"]}),
                    changed_actions=sum(r["changes"] for r in sub),
                    earlier=sum((r["sight"] if r["sight"] is not None else 101)<(r["old_sight"] if r["old_sight"] is not None else 101) for r in sub),
                    later=sum((r["sight"] if r["sight"] is not None else 101)>(r["old_sight"] if r["old_sight"] is not None else 101) for r in sub))
    seeds=sorted({r["seed"] for r in results})
    if len(results)!=2*len(seeds): raise ValueError("Es fehlen Startseiten")
    d=np.asarray([sum(r["delta"] for r in results if r["seed"]==seed)/2 for seed in seeds])
    rng=np.random.default_rng(221123)
    means=d[rng.integers(0,len(d),size=(20000,len(d)))].mean(axis=1)
    ci=np.quantile(means,[0.025,0.975],method="linear").tolist()
    return dict(total=stats(results),by_side={s:stats([r for r in results if r["side"]==s]) for s in ("player_0","player_1")},
                mean=float(d.mean()),ci95=ci,changed_outcomes=[r for r in results if r["delta"]])


def head_to_head(rows):
    direct=[r for r in rows if r["opponent"]=="v16"]
    def stats(part):
        return dict(games=len(part),wins=sum(r["game_win"] for r in part),matchwins=sum(r["our_wins"] for r in part),
                    changed_sides=sum(bool(r["changes"]) for r in part),changed_wins=sum(r["game_win"] for r in part if r["changes"]),
                    changed_maps=len({r["seed"] for r in part if r["changes"]}),quiet_wins=sum(r["game_win"] for r in part if not r["changes"]))
    pure=0
    mixed=[]
    both_active=0
    contradictory=[]
    for seed in sorted({r["seed"] for r in direct}):
        duo=[r for r in direct if r["seed"]==seed]
        if len(duo)!=2: raise ValueError("Fehlender Direktsitz")
        quiet=[r for r in duo if not r["changes"]]
        if len(quiet)==2:
            pure+=1
            if quiet[0]["match_winners"]!=quiet[1]["match_winners"]: contradictory.append(seed)
        elif len(quiet)==1:
            mod=next(r for r in duo if r["changes"])
            b=quiet[0]["match_winners"].count(int(mod["side"][-1]))
            mixed.append(dict(seed=seed,side=mod["side"],baseline_matchwins=b,matchwins=mod["our_wins"],
                              baseline_game_win=b>=2,game_win=mod["game_win"]))
        else: both_active+=1
    return dict(total=stats(direct),by_side={s:stats([r for r in direct if r["side"]==s]) for s in ("player_0","player_1")},
                both_quiet_maps=pure,both_active_maps=both_active,single_active_reference=mixed,quiet_inconsistency=contradictory)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("phase",choices=("haupt","kaggle"))
    phase=ap.parse_args().phase
    directory=HERE/phase
    hashes=frozen(phase)
    rows=[]
    for shard in (0,1):
        if json.loads((directory/f"quellen_{shard}.json").read_bytes())!=hashes:
            raise ValueError("Eine Quellenbindung stimmt nicht mehr")
        rows.extend(map(json.loads,(directory/f"worker_{shard}.jsonl").read_text().splitlines()))
    expected=set(panel(phase))
    actual=[(r["seed"],r["side"],r["opponent"],r["arm"]) for r in rows]
    if len(actual)!=len(expected) or set(actual)!=expected: raise ValueError("Prüfsatz noch unvollständig")
    for r in rows:
        w=r["our_wins"]
        if r["steps"]!=303 or w+r["opp_wins"]!=3 or w!=r["match_winners"].count(int(r["side"][-1])) or r["game_win"]!=int(w>=2):
            raise ValueError("Widersprüchlicher Endzustand")
    s=summarize(rows,"solution92" if phase=="haupt" else "kaggle3")
    if phase=="haupt":
        direct=head_to_head(rows)
        gate=s["ci95"][0]>0 and direct["total"]["wins"]>=50
    else:
        direct=None
        t=s["total"]
        gate=t["candidate_wins"]>=t["baseline_wins"] and t["candidate_matches"]>=t["baseline_matches"]
    report=dict(n=len(rows),external=s,direct=direct,gate=gate)
    (directory/"ergebnis.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(dict(n=len(rows),external=s["total"],ci95=s["ci95"],direct=direct["total"] if direct else None,gate=gate),indent=2))


if __name__=="__main__":
    main()
