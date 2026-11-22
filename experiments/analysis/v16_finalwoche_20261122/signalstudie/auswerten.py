"""Vollständig abgeschlossene unveränderte V16-Partien beurteilen, mit beiden Sitzen je Karte."""
import json

from messen import HERE, SEEDS, source_hashes


def count(rows):
    early = [r for r in rows if r["early"]]
    opportunities = [r for r in rows if r["opportunity"]]
    late = [r for r in rows if r["first"] is not None and not r["early"]]
    negative = [r for r in rows if r["true_second_spawn"] is None]
    missed = [r for r in opportunities if not r["early"]]
    return dict(sides=len(rows),maps=len({r["seed"] for r in rows}),
        whole_wins=sum(r["game_win"] for r in rows),match2_wins=sum(r["match2_win"] for r in rows),
        no_pair_sides=len(negative),no_pair_maps=len({r["seed"] for r in negative}),
        eligible_team_turns_on_no_pair_maps=sum(r["eligible_turns"] for r in negative),
        false_alarm_sides=sum(bool(r["false_turns"]) for r in rows),
        any_signal_sides=sum(r["first"] is not None for r in rows),
        early_sides=len(early),early_maps=len({r["seed"] for r in early}),
        early_lost_game=sum(not r["game_win"] for r in early), early_lost_match2=sum(not r["match2_win"] for r in early),
        late_or_false_sides=len(late),opportunity_sides=len(opportunities),opportunity_maps=len({r["seed"] for r in opportunities}),
        missed_sides=len(missed),missed_maps=len({r["seed"] for r in missed}),
        missed_with_opening_pair=sum(r["opening_pair"] for r in missed),
        missed_with_qualified_turn=sum(r["eligible_turns"]>0 for r in missed),
        missed_with_positive_candidate_count_t50=sum(r["state_50"]["unresolved"]>0 for r in missed),
        missed_lost_game=sum(not r["game_win"] for r in missed),missed_lost_match2=sum(not r["match2_win"] for r in missed),
        knowledge_precedes_truth=sum(r.get("knowledge_precedes_truth",False) for r in rows))


def main():
    folder = HERE/"beobachtung"
    rows = []
    sources=source_hashes()
    for shard in (0,1):
        if json.loads((folder/f"quellen_{shard}.json").read_bytes())!=sources:
            raise ValueError("Abweichende Version")
        rows.extend(map(json.loads,(folder/f"worker_{shard}.jsonl").read_text().splitlines()))
    keys = [(r["seed"],r["side"]) for r in rows]
    if len(keys)!=96 or set(keys)!={(seed,side) for seed in SEEDS for side in ("player_0","player_1")}:
        raise ValueError("Erst nach allen unveränderten 96 Spielen auswerten")
    for seed in SEEDS:
        both=[r for r in rows if r["seed"]==seed]
        if len({r["true_second_spawn"] for r in both})!=1: raise ValueError("Seed mit zwei verschiedenen Reliktaktivierungen")
    for r in rows:
        witness=r["first"]
        if witness:
            if (r["joint_turns"][0]!=witness["turn"] or sum(witness["gains"])<=witness["cap"]
                    or witness["cap"]!=witness["possible_fields"]+len(witness["possible_corners"])):
                raise ValueError("Falsche erste Summenüberschreitung")
        if (r["steps"]!=303 or r["our_wins"]+r["opp_wins"]!=3 or r["our_wins"]!=r["match_winners"].count(int(r["side"][-1]))
                or r["game_win"]!=int(r["our_wins"]>=2) or (r["early"] and not r["opportunity"])):
            raise ValueError("Inkonsistente Rohwerte")
    totals=count(rows)
    summary=dict(all=totals,
        by_side={side:count([r for r in rows if r["side"]==side]) for side in ("player_0","player_1")},
        actual_early=[dict(seed=r["seed"],side=r["side"],turn=r["first"]["turn"],seen=r["known_second"],
                       lead=r["public_lead"],game_win=r["game_win"],match2_win=r["match2_win"])
                      for r in sorted(rows,key=lambda r:(r["seed"],r["side"])) if r["early"]],
        gate=not totals["false_alarm_sides"] and totals["early_maps"]>=3 and
             any(r["early"] and (not r["match2_win"] or not r["game_win"]) for r in rows))
    (folder/"ergebnis.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(summary["all"],ensure_ascii=False,indent=2))
    print("Aktionsprüfung",summary["gate"])


if __name__=="__main__":
    main()
