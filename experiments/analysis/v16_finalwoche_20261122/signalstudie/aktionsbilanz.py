"""Aktions- und Spielergebnisse der festgelegten 48 Entwicklungskarten, mit ihren V16-Paarungen."""
import json

from aktion import HERE, SEEDS, baseline_data, bound_sources


def load_selection():
    rows=[]
    directory=HERE/"aktion"
    hashes=bound_sources()
    for shard in (0,1):
        if json.loads((directory/f"quellen_{shard}.json").read_bytes())!=hashes:
            raise ValueError("Abweichende Aktionsquelle")
        rows.extend(map(json.loads,(directory/f"worker_{shard}.jsonl").read_text().splitlines()))
    wanted={(s,p,o) for s in SEEDS for p in ("player_0","player_1") for o in ("solution92","v16")}
    if len(rows)!=192 or {(r["seed"],r["side"],r["opponent"]) for r in rows}!=wanted:
        raise ValueError("Erst nach den vollständigen 192 Spielen auswerten")
    return rows


def visibility(t):
    return 101 if t is None else t


def group(rows, base):
    sol=[]
    direct=[]
    for r in rows:
        key=r["seed"],r["side"]
        if r["opponent"]=="v16":
            direct.append(r)
            continue
        b=base[key]
        new=r["game_win"]>b["game_win"]
        lost=r["game_win"]<b["game_win"]
        if new and lost: raise ValueError("Ungültiger Vergleich")
        sol.append(dict(seed=r["seed"],side=r["side"],new=new,lost=lost,started=r["start"] is not None,
                        changed=bool(r["changes"]),actions=len(r["changes"]),first=r["first"],
                        old_wins=b["game_win"],wins=r["game_win"],old_matches=b["our_wins"],matches=r["our_wins"],
                        old_score=b["our_points"]-b["opp_points"],score=r["our_points"]-r["opp_points"],
                        earlier=visibility(r["known_second"])<visibility(b["known_second"]),
                        later=visibility(r["known_second"])>visibility(b["known_second"]),
                        old_second=b["known_second"],second=r["known_second"],
                        fields_match3_step0=r["fields_match3_step0"],fields_match3_step1=r["fields_match3_step1"]))
    def count(key): return sum(r[key] for r in sol)
    def direct_sum(key): return sum(r[key] for r in direct)
    summary=dict(solution_games=len(sol),solution_baseline_wins=count("old_wins"),solution_candidate_wins=count("wins"),
                 solution_new_wins=count("new"),solution_lost_wins=count("lost"),solution_baseline_matchwins=count("old_matches"),
                 solution_candidate_matchwins=count("matches"),solution_score_delta=count("score")-count("old_score"),
                 first_scheduled=sum(bool(r["first"]) for r in sol),actually_assigned=count("started"),
                 changed_solution_games=count("changed"),changed_solution_maps=len({r["seed"] for r in sol if r["changed"]}),
                 changed_solution_actions=count("actions"),earlier_solution_sightings=count("earlier"),later_solution_sightings=count("later"),
                 direct_games=len(direct),direct_wins=direct_sum("game_win"),direct_matchwins=direct_sum("our_wins"),
                 direct_opponent_matchwins=direct_sum("opp_wins"),direct_changed_games=sum(bool(r["changes"]) for r in direct),
                 direct_changed_maps=len({r["seed"] for r in direct if r["changes"]}),
                 direct_changed_actions=sum(len(r["changes"]) for r in direct),
                 direct_changed_wins=sum(r["game_win"] for r in direct if r["changes"]))
    # In einem unveränderten Sitz des Direktduells spielen beide Seiten die
    # Originalpolicy. Seine festen Team-Sieger liefern eine Kontrolle für
    # den zweiten Sitz derselben Karte, sofern sein Gegenstück aktiv wurde.
    inferred=[]
    contradictory=[]
    for seed in sorted({r["seed"] for r in direct}):
        pair=[r for r in direct if r["seed"]==seed]
        if len(pair)!=2: continue
        quiet=[r for r in pair if not r["changes"]]
        if len(quiet)==2 and quiet[0]["match_winners"]!=quiet[1]["match_winners"]:
            contradictory.append(seed)
        if len(quiet)==1:
            changed=next(r for r in pair if r["changes"])
            team=int(changed["side"][-1])
            base_match=quiet[0]["match_winners"].count(team)
            inferred.append(dict(seed=seed,side=changed["side"],reference_matchwins=base_match,
                                 candidate_matchwins=changed["our_wins"],reference_game_win=base_match>=2,
                                 candidate_game_win=changed["game_win"]))
    if len(rows)==192:
        summary["direct_asymmetric_reference"]=inferred
        summary["direct_quiet_maps_inconsistent"]=contradictory
    return summary,sorted([s for s in sol if s["changed"]],key=lambda s:(s["seed"],s["side"]))


def main():
    base=baseline_data()
    rows=load_selection()
    for r in rows:
        if (r["steps"]!=303 or r["our_wins"]+r["opp_wins"]!=3 or
                r["our_wins"]!=r["match_winners"].count(int(r["side"][-1]))): raise ValueError("Unausgewertetes Match")
    total,affected=group(rows,base)
    byside={side:group([r for r in rows if r["side"]==side],base)[0] for side in ("player_0","player_1")}
    gate=(total["solution_new_wins"]>total["solution_lost_wins"]
          and total["solution_candidate_matchwins"]>=total["solution_baseline_matchwins"]
          and total["direct_wins"]>=48)
    artifact=dict(all=total,by_side=byside,affected=affected,gate=gate)
    (HERE/"aktion"/"ergebnis.json").write_text(json.dumps(artifact,indent=2)+"\n")
    print(json.dumps(total,indent=2))
    print("Bestätigung eröffnen",gate)


if __name__=="__main__":
    main()
