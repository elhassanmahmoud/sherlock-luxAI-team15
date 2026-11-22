"""Prüft den vollständigen Vier-Sitz-Test oder das unabhängige 16-Karten-Panel."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(path):
    file = json.loads(path.read_text())
    for key, name in (("rules_sha256", "PLAN.md"), ("source_sha256", "kandidat.py")):
        if sha256((HERE/name).read_bytes()).hexdigest() != file[key]:
            raise ValueError(f"Abweichende Fassung: {name}")
    rows=file["rows"]
    tech=file["phase"]=="technik"
    if file["v16_sha256"]!="0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099":
        raise ValueError("Falsche Abgabe")
    seeds=(7261020,7267071) if tech else range(94651000,94651016)
    opps=("solution92",) if tech else ("solution92","kaggle3","v16")
    lookup={(r["seed"],r["side"],r["opponent"],r["arm"]): r for r in rows}
    expected={(seed,side,opp,arm) for seed in seeds for side in ("player_0","player_1")
              for opp in opps for arm in (("scout",) if opp=="v16" else ("v16","scout"))}
    if len(rows)!=len(expected) or set(lookup)!=expected:
        raise ValueError("Fehlende oder doppelte Sitze")
    for r in rows:
        if r["steps"]!=303 or r["our_wins"]+r["opp_wins"]!=3 or r["game_win"]!=int(r["our_wins"]>r["opp_wins"]):
            raise ValueError("Ungültiger Spielausgang")
        if r["changes"]:
            times=[t for t,*_ in r["changes"]]
            if (len({uid for _,uid,*_ in r["changes"]})!=1 or times!=sorted(set(times))
                   or min(times)<50 or max(times)>79 or max(times)-min(times)>=20
                   or any(a==5 or d==5 or a==d for _,_,a,d,_,_ in r["changes"])):
                raise ValueError("Unzulässige Aktivität")
    for opponent in opps:
        selected=[r for r in rows if r["arm"]=="scout" and r["opponent"]==opponent]
        print(opponent,"Kandidat")
        for side in (None, "player_0", "player_1"):
            group=[r for r in selected if side is None or r['side']==side]
            counts=Counter()
            per_seed=defaultdict(int)
            for r in group:
                active = bool(r["changes"])
                counts.update(active_wins=int(active)*r["game_win"],active_matches=int(active)*r["our_wins"],
                              inactive_wins=int(not active)*r["game_win"],games=1,wins=r['game_win'],matches=r['our_wins'],
                              points_margin=r['our_points']-r['opp_points'],
                              active_games=int(bool(r['changes'])),changed_actions=len(r['changes']),
                              monitor='confirmed_far_goal' in r,confirmed_far_goal=len(r.get('confirmed_far_goal',[])))
                if opponent!='v16':
                    b=lookup[r['seed'],r['side'],opponent,'v16']
                    changed=r['game_win']-b['game_win']
                    if not r['changes'] and any(r[k]!=b[k] for k in ('our_points','opp_points','our_wins','opp_wins')):
                        raise ValueError("Unterschiedliches Spiel ohne geänderte Aktion")
                    counts.update(baseline_wins=b['game_win'],baseline_matches=b['our_wins'],
                                  gained=int(changed==1),lost=int(changed==-1),
                                  points_margin_delta=r['our_points']-r['opp_points']-b['our_points']+b['opp_points'],
                                  earlier=int((r['pair_turn'] if r['pair_turn'] is not None else 101) <
                                              (b['pair_turn'] if b['pair_turn'] is not None else 101)))
                    per_seed[r['seed']]+=changed
            counts["maps_with_changes"]=len({r["seed"] for r in group if r["changes"]})
            if opponent=='v16':
                by_seed=defaultdict(int)
                for r in group:
                    by_seed[r['seed']]+=r['game_win']
                counts["direct_wins_per_map"]=dict(sorted(Counter(by_seed.values()).items()))
            if opponent!='v16':
                nonzero=[v for v in per_seed.values() if v]
                obs=abs(sum(nonzero))
                distribution=[abs(sum(s*v for s,v in zip(signs,nonzero))) for signs in product((-1,1),repeat=len(nonzero))]
                counts["n_maps_nonzero"]=len(nonzero)
                counts["p_seed_signflip_2s"] = sum(v>=obs for v in distribution)/len(distribution)
            print(side or "beide",json.dumps(dict(counts),sort_keys=True))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("daten",type=Path)
    run(parser.parse_args().daten)
