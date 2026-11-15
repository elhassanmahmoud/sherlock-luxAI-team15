"""Audit complete fixed sets of v4 sole-holder games and the registered phase transitions."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
from types import SimpleNamespace

from agents.sherlock.geometry import mirror_xy
from scripts.final_battle_assess import bounds, external_comparison
from scripts.final_battle_compare import digest
from scripts.scoring import POINT_COUNTING_VERSION
from scripts.train_combat_advice import publish_json
from scripts.v4_holder_replay import MODE, SIDES, TARGETS, binding, filename, plan


def check(condition, message):
    if not condition:
        raise ValueError(message)


def integer(x, lo, hi):
    return type(x) is int and lo <= x <= hi


def validate_events(events, arm, side):
    seen = set()
    for e in events:
        t, uid = e["step"], e["uid"]
        xy = tuple(e["world"])
        check(integer(t, 0, 302) and integer(uid, 0, 15) and (t, uid) not in seen, "Event key")
        seen.add((t, uid))
        check((e["match"], e["match_step"]) == (t // 101 + 1, t % 101), "Event match")
        check(len(xy) == 2 and all(integer(n, 0, 23) for n in xy), "Event position")
        canonical = mirror_xy(*xy) if side == "player_1" else xy
        check(tuple(e["canonical"]) == canonical, "Incorrect player-oriented coordinates")
        check(e["tile_confirmed"] is True and e["enemy_within_five"] is True and
              integer(e["occupants"], 1, 16) and integer(e["energy"], 0, 1000000), "Invalid holder")
        check(len(e["v14"]) == len(e["student"]) == len(e["final"]) == 3 and
              e["student"] != e["v14"], "Missing proposed actions")
        for field in ("v14_end", "student_end", "planned_end"):
            check(len(e[field]) == 2 and all(integer(n, 0, 23) for n in e[field]), "Invalid endpoint")
        can = (e["occupants"] == 1 and e["student_chosen"] is True and
               tuple(e["v14_end"]) == xy and tuple(e["student_end"]) != xy)
        check(e["can_hold"] is can and (not e["eligible"] or can), "Inconsistent holder qualification")
        check(not e["eligible"] or e["other_planned_final"] == 0, "Handover at protected field")
        check(e["restored"] is (e["eligible"] and arm == "guard"), "Wrong routing intervention")
        use_v14 = e["restored"] or not e["student_chosen"]
        check(e["final"] == e["v14" if use_v14 else "student"] and
              e["planned_end"] == e["v14_end" if use_v14 else "student_end"], "Wrong final row")
        n = e["observed_count_after"]
        check((n is None if t % 101 == 100 else integer(n, 0, 16)), "Missing observed occupancy")
        lapse = e["observed_empty_step_ends"]
        check(integer(lapse, 0, 100 - t % 101) and
              e["censored_at_match_boundary"] is (lapse == 100 - t % 101) and
              (n is None or (n == 0) == (lapse > 0)), "Inconsistent vacancy duration")
        for field in ("points_before", "points_after"):
            check(len(e[field]) == 2 and all(integer(x, 0, 1000000) for x in e[field]), "Points")
    check(not arm.startswith("native_") or not events, "Uninstrumented runs have event data")


def check_rows(stage, out, stamp, history):
    keys = plan(stage)
    expected = {filename(out, stage, k).name for k in keys if filename(out, stage, k).parent == out / stage}
    present = {p.name for p in (out / stage).glob("*.json") if p.name != "assessment.json"}
    check(present == expected and len(set(keys)) == len(keys) == {"tech":6, "directed":20, "screen":160}[stage],
          f"{stage}: missing, extra or repeated games")
    rows, hashes = {}, {}
    for key in keys:
        seed, side, foe, arm = key
        path = filename(out, stage, key)
        r = json.loads(path.read_bytes())
        check(tuple(r[k] for k in ("seed", "side", "opponent", "arm")) == key and r["source"] == stamp,
              f"Source or identity mismatch in {path}")
        g, m = r["game"], r["matches"]
        check(g["steps"] == 303 and g["point_counting_version"] == POINT_COUNTING_VERSION and
              [i["match"] for i in m] == [1, 2, 3] and all(integer(i["won"], 0, 1) for i in m),
              f"Incomplete game {key}")
        check(all(integer(i[k], 0, 1000000) for i in m for k in ("our_points", "opp_points")) and
              all(sum(i[k] for i in m) == g[k] for k in ("our_points", "opp_points")) and
              sum(i["won"] for i in m) == g["our_wins"] == 3 - g["opp_wins"] and
              g["game_win"] == int(g["our_wins"] >= 2), f"Inconsistent end score {key}")
        historic = history[MODE[arm]].get((seed, side)) if arm != "guard" and foe == "solution92" else None
        if historic is None:
            check(r["reproduces_archive"] is None, "Unexpected historical reproduction claim")
        else:
            check(g == historic and r["reproduces_archive"] is True, "Different historical outcome")
        check(len(r["orders_sha256"]) == 2 and
              all(re.fullmatch("[0-9a-f]{64}", h) for h in r["orders_sha256"]), "Missing seat orders")
        validate_events(r["events"], arm, side)
        rows[key] = r
        hashes[str(path.relative_to(out))] = digest(path)
    return rows, hashes


def activity(r):
    events = r["events"]
    return dict(source_disagreements=len(events), qualified=sum(e["eligible"] for e in events),
                restored=sum(e["restored"] for e in events),
                vacant_immediately=sum(e["eligible"] and e["observed_count_after"] == 0 for e in events))


def tech(rows):
    parity = {}
    for arm in ("mixed", "points"):
        k = (7150068, "player_1", "solution92")
        observed, native = rows[*k, arm], rows[*k, "native_" + arm]
        parity[arm] = (observed["orders_sha256"] == native["orders_sha256"] and
                       observed["matches"] == native["matches"] and observed["game"] == native["game"])
    controls = {f"{side}/{arm}": dict(matches=r["matches"], actions_sha256=r["orders_sha256"], **activity(r))
                for (_, side, _, arm), r in rows.items() if arm in ("mixed", "points")}
    mixed_vacancy = any(i["vacant_immediately"] > 0 for k, i in controls.items() if k.endswith("/mixed"))
    return dict(archive_reproductions=len(rows), actual_player1_parity=parity, controls=controls,
                eligible_mixed_departure_caused_observed_vacancy=mixed_vacancy,
                passes=all(parity.values()) and mixed_vacancy)


def directed(rows):
    cases = []
    for seed, s in TARGETS:
        k = (seed, f"player_{s}", "solution92")
        case = dict(seed=seed, side=k[1])
        for arm in ("mixed", "guard"):
            r = rows[*k, arm]
            case[arm] = dict(game=r["game"], matches=r["matches"], **activity(r))
        cases.append(case)
    gain = sum(c["guard"]["game"]["game_win"] - c["mixed"]["game"]["game_win"] for c in cases)
    matches = sum(c["guard"]["game"]["our_wins"] - c["mixed"]["game"]["our_wins"] for c in cases)
    changed = sum(c["guard"]["restored"] for c in cases)
    return dict(cases=cases, net_game_wins=gain, net_match_wins=matches, restored_orders=changed,
                passes=changed > 0 and gain > 0 and matches >= 0)


def screen(rows):
    seeds = range(7170200, 7170216)
    def scores(arm):
        return SimpleNamespace(games={(foe, seed, seat): {"result": r["game"]["game_win"]}
                                      for (seed, seat, foe, a), r in rows.items() if a == arm})
    before, after = scores("mixed"), scores("guard")
    versus, both = external_comparison(before, after, seeds, "mixed_wins")
    by_map = [sum(after.games["mixed", seed, seat]["result"] for seat in SIDES) / 2 for seed in seeds]
    wins = int(2 * sum(by_map))
    both.update(gained=sum(t["gained"] for t in versus.values()), lost=sum(t["lost"] for t in versus.values()),
                mixed_wins=sum(t["mixed_wins"] for t in versus.values()),
                candidate_wins=sum(t["candidate_wins"] for t in versus.values()))
    direct = dict(wins=wins, losses=32-wins, games=32, winrate=wins/32,
                  winrate_ci95=bounds(by_map), wins_by_map=[int(x * 2) for x in by_map])
    return dict(vs_external=versus, combined=both, direct=direct,
                passes=both["net_wins"] >= 2 and versus["solution92"]["net_wins"] >= 0 and wins > 16,
                decision_scope="nomination only")


def assess(out, stage):
    stamp, history = binding()
    rows, files = check_rows(stage, out, stamp, history)
    analysis = {"tech":tech, "directed":directed, "screen":screen}[stage](rows)
    return dict(stage=stage, source=stamp, assessor_sha256=digest(Path(__file__)), files=files, **analysis)


def require_predecessor(out, stage):
    for dep in (("tech",) if stage == "directed" else ("tech", "directed") if stage == "screen" else ()):
        p = out / dep / "assessment.json"
        report = assess(out, dep)
        check(p.exists() and json.loads(p.read_bytes()) == report and report["passes"],
              f"Missing, stale or negative {dep} assessment")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("tech", "directed", "screen"))
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    out = a.out.resolve()
    require_predecessor(out, a.stage)
    report = assess(out, a.stage)
    dst = out / a.stage / "assessment.json"
    if dst.exists():
        check(report == json.loads(dst.read_bytes()), f"Different prior report at {dst}")
    else:
        publish_json(dst, report)
    print(json.dumps({k:v for k,v in report.items() if k not in ("source", "files")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
