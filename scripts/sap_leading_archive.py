#!/usr/bin/env python3
"""Fixed public-only SAP-leading archive geometry; real archive run awaits Root review."""
import argparse
from collections import Counter
import copy
import gzip
import hashlib
from itertools import chain
import json
import math
from pathlib import Path
import sys

MANIFEST_SHA = "90324b008945da4a054a0559a108ee0023cf572d754b20af844160dfe4ebc435"
BASE = Path("experiments/analysis/continuation_20261102")
FIXED = [(831006, "player_1"), (831029, "player_0"), (831042, "player_0"),
         (831042, "player_1"), (831043, "player_0"), (831043, "player_1"),
         (831000, "player_0"), (831000, "player_1"), (831001, "player_0"),
         (831001, "player_1"), (831002, "player_0"), (831002, "player_1")]
STAGES = ["sap_total", "assigned_current", "previous_visible", "moved", "energy", "legal", "eligible"]
FACTORS = {"0": 0.0, "0.25": 0.25, "0.5": 0.5, "1": 1.0}


def need(ok, message):
    if not ok: raise ValueError(message)


def distance(a, b):
    return max(abs(a[0]-b[0]), abs(a[1]-b[1]))


def visible(frame):
    p = frame["public"]
    ids, positions, energies = (p[k] for k in ("enemy_vis_ids", "enemy_coords", "enemy_energies"))
    need(len(ids) == len(positions) == len(energies) and len(ids) == len(set(ids)), "Enemy arrays/UIDs differ")
    return {u: (pos, energy) for u, pos, energy in zip(ids, positions, energies)}


def consecutive(a, b):
    if a is None or b is None or a["status"] != "decision" or b["status"] != "decision": return False
    x, y = a["key"], b["key"]
    return (all(x[k] == y[k] for k in ("seed", "side", "match_idx"))
            and x["obs_step"]+1 == y["obs_step"] and x["match_step"]+1 == y["match_step"])


def self_test():
    checks = 0
    def check(value):
        nonlocal checks
        assert value
        checks += 1
    def frame(step, pos, energy=20, side="player_0"):
        return dict(status="decision", key=dict(seed=1, side=side, match_idx=0,
                    obs_step=step, match_step=step), public=dict(W=6, H=6,
                    enemy_vis_ids=[7], enemy_coords=[pos], enemy_energies=[energy],
                    sap_range=4, sap_cost=10, move_cost=2,
                    sensor_mask=[[True]*6 for _ in range(6)], passable=[[True]*6 for _ in range(6)]),
                    units=[dict(uid=0, position=[1, 2], energy=20, final_action=[5, 2, 0])],
                    posthoc={"never_use": "hidden truth"})
    prev, cur, nxt = frame(1, [2, 2]), frame(2, [3, 2]), frame(3, [4, 2])
    event = analyze_frame(prev, cur, nxt)[0]
    check(event["passed"] == STAGES)
    check(event["outcome"] == "keep" and event["distance_old"] == 1 and event["distance_new"] == 0)
    check(event["geometry"]["0.25"] == dict(old=0.25, new=1.0, delta=0.75))
    for pos, outcome in (([3, 3], "turn"), ([3, 2], "stay"), ([5, 5], "other")):
        check(analyze_frame(prev, cur, frame(3, pos))[0]["outcome"] == outcome)
    check(analyze_frame(prev, cur, None)[0]["outcome"] == "unknown")
    for field, value in (("match_idx", 1), ("obs_step", 4)):
        bad = copy.deepcopy(nxt); bad["key"][field] = value
        check(analyze_frame(prev, cur, bad)[0]["outcome"] == "unknown")
    missing = copy.deepcopy(nxt)
    for name in ("enemy_vis_ids", "enemy_coords", "enemy_energies"): missing["public"][name] = []
    check(analyze_frame(prev, cur, missing)[0]["unknown_reason"] == "next_uid_not_visible")
    negative = analyze_frame(prev, cur, frame(3, [4, 2], -1))[0]
    check(negative["outcome"] == "keep" and negative["next_energy_sign"] == "negative")
    for field in ("sensor_mask", "passable"):
        bad = copy.deepcopy(cur); bad["public"][field][4][2] = False
        check("eligible" not in analyze_frame(prev, bad, nxt)[0]["passed"])
    transpose = copy.deepcopy(cur); transpose["public"]["sensor_mask"][2][4] = False
    check("eligible" in analyze_frame(prev, transpose, nxt)[0]["passed"])
    for change in ("own_energy", "enemy_energy", "range", "stack", "old_illegal"):
        bad = copy.deepcopy(cur)
        if change == "own_energy": bad["units"][0]["energy"] = 9
        if change == "enemy_energy": bad["public"]["enemy_energies"] = [1]
        if change == "range": bad["public"]["sap_range"] = 2
        if change == "old_illegal": bad["public"]["sap_range"] = 1
        if change == "stack":
            bad["public"]["enemy_vis_ids"].append(8)
            bad["public"]["enemy_coords"].append([3, 2]); bad["public"]["enemy_energies"].append(20)
        check("eligible" not in analyze_frame(prev, bad, nxt)[0]["passed"])
    check("energy" not in analyze_frame(frame(1, [2, 2], -1), cur, nxt)[0]["passed"])
    check("moved" not in analyze_frame(frame(1, [1, 2]), cur, nxt)[0]["passed"])
    check("previous_visible" not in analyze_frame(frame(0, [2, 2]), cur, nxt)[0]["passed"])
    edge = frame(2, [5, 2]); edge["units"][0]["final_action"] = [5, 4, 0]
    check("eligible" not in analyze_frame(frame(1, [4, 2]), edge, nxt)[0]["passed"])
    mirrored = [copy.deepcopy(f) for f in (prev, cur, nxt)]
    for f in mirrored: f["key"]["side"] = "player_1"
    check(analyze_frame(*mirrored)[0]["predicted_target"] == [4, 2])
    two = copy.deepcopy(cur); extra = copy.deepcopy(two["units"][0]); extra["uid"] = 1; two["units"].append(extra)
    stats = summarize(analyze_frame(prev, two, nxt))
    check(stats["unique_events"] == 2 and stats["unique_enemy_frames_by_stage"]["eligible"] == 1)
    check(stats["events"]["outcomes"]["keep"] == 2 and stats["enemy_frames"]["outcomes"]["keep"] == 1)
    check(summarize([negative])["events"]["observed_energy_signs"] == {"negative": 1})
    print(json.dumps(dict(status="PASS_SYNTHETIC", checks=checks, archive_files_read=0)))


def analyze_frame(prev, cur, nxt):
    if cur["status"] != "decision": return []
    p, enemies, events = cur["public"], visible(cur), []
    for u in cur["units"]:
        a = u["final_action"]
        if a[0] != 5: continue
        own = u["position"]; old = [own[0]+a[1], own[1]+a[2]]
        e = dict(key=dict(cur["key"]), shooter_uid=u["uid"], own_position=own,
                 own_energy=u["energy"], sap_cost=p["sap_cost"], sap_range=p["sap_range"],
                 move_cost=p["move_cost"], final_action=a, old_target=old,
                 passed=["sap_total"], rejection=None)
        events.append(e)
        matches = [uid for uid, (pos, _) in enemies.items() if pos == old]
        e["target_visible_uids"] = matches
        if len(matches) != 1:
            e["rejection"] = "no_visible_target" if not matches else "ambiguous_current_stack"; continue
        uid = matches[0]; e.update(enemy_uid=uid, current_enemy_energy=enemies[uid][1])
        e["passed"].append("assigned_current")
        if not consecutive(prev, cur): e["rejection"] = "previous_frame_unavailable"; continue
        previous = visible(prev)
        if uid not in previous: e["rejection"] = "previous_uid_not_visible"; continue
        before, before_energy = previous[uid]
        e.update(previous_position=before, previous_enemy_energy=before_energy)
        e["passed"].append("previous_visible")
        delta = [old[0]-before[0], old[1]-before[1]]; e["last_delta"] = delta
        if abs(delta[0])+abs(delta[1]) != 1: e["rejection"] = "not_one_cardinal_step"; continue
        e["passed"].append("moved")
        failures = []
        if before_energy < 0: failures.append("previous_enemy_negative")
        if enemies[uid][1] < 0: failures.append("current_enemy_negative")
        if enemies[uid][1] < p["move_cost"]: failures.append("enemy_below_move_cost")
        if u["energy"] < p["sap_cost"]: failures.append("own_below_sap_cost")
        if failures: e.update(rejection="energy", failed_conditions=failures); continue
        e["passed"].append("energy")
        new = [old[0]+delta[0], old[1]+delta[1]]; e["predicted_target"] = new
        inside = lambda pos: 0 <= pos[0] < p["W"] and 0 <= pos[1] < p["H"]
        failures = []
        if not inside(old): failures.append("old_off_board")
        if distance(own, old) > p["sap_range"]: failures.append("old_out_of_sap_range")
        if not inside(new): failures.append("predicted_off_board")
        else:
            if not p["sensor_mask"][new[0]][new[1]]: failures.append("predicted_not_currently_visible")
            if not p["passable"][new[0]][new[1]]: failures.append("predicted_not_passable")
        if distance(own, new) > p["sap_range"]: failures.append("predicted_out_of_sap_range")
        if failures: e.update(rejection="legal", failed_conditions=failures); continue
        e["passed"].extend(["legal", "eligible"])
        # Selection ends here. Only now inspect the subsequent public observation.
        if not consecutive(cur, nxt):
            e.update(outcome="unknown", unknown_reason="next_frame_unavailable"); continue
        following = visible(nxt)
        if uid not in following:
            e.update(outcome="unknown", unknown_reason="next_uid_not_visible"); continue
        pos, energy = following[uid]; nd = [pos[0]-old[0], pos[1]-old[1]]
        outcome = ("keep" if nd == delta else "stay" if nd == [0, 0]
                   else "turn" if abs(nd[0])+abs(nd[1]) == 1 else "other")
        d_old, d_new = distance(old, pos), distance(new, pos)
        e.update(outcome=outcome, next_position=pos, next_enemy_energy=energy,
                 next_energy_sign="negative" if energy < 0 else "nonnegative",
                 next_delta=nd, distance_old=d_old, distance_new=d_new, geometry={})
        for name, factor in FACTORS.items():
            weight = lambda d: 1.0 if d == 0 else factor if d == 1 else 0.0
            x, y = weight(d_old), weight(d_new)
            e["geometry"][name] = dict(old=x, new=y, delta=y-x)
    return events


def identity(e, enemy=False):
    k = e["key"]
    return tuple(k[n] for n in ("seed", "side", "match_idx", "obs_step")) + (e["enemy_uid"] if enemy else e["shooter_uid"],)


def outcome_summary(events):
    observed = [e for e in events if e["outcome"] != "unknown"]
    result = dict(eligible=len(events), observed=len(observed),
        outcomes={k: sum(e["outcome"] == k for e in events) for k in ("keep", "turn", "stay", "other", "unknown")},
        unknown_reasons=dict(Counter(e["unknown_reason"] for e in events if e["outcome"] == "unknown")),
        observed_energy_signs=dict(Counter(e["next_energy_sign"] for e in observed)), geometry={})
    for name in FACTORS:
        result["geometry"][name] = dict(denominator=len(observed),
            **{field: sum(e["geometry"][name][field] for e in observed) for field in ("old", "new", "delta")})
    result["by_observed_energy_sign"] = {sign: dict(
        count=sum(e["next_energy_sign"] == sign for e in observed),
        outcomes=dict(Counter(e["outcome"] for e in observed if e["next_energy_sign"] == sign)),
        geometry_delta={name: sum(e["geometry"][name]["delta"] for e in observed if e["next_energy_sign"] == sign)
                        for name in FACTORS}) for sign in ("negative", "nonnegative")}
    return result


def summarize(events):
    need(len({identity(e) for e in events}) == len(events), "Duplicate shooter/frame event")
    eligible = [e for e in events if "eligible" in e["passed"]]; unique = {}
    for e in eligible:
        key = identity(e, True)
        if key in unique:
            for field in ("old_target", "predicted_target", "outcome", "next_position", "next_enemy_energy", "geometry", "unknown_reason"):
                need(e.get(field) == unique[key].get(field), "Inconsistent repeated enemy/frame")
        unique[key] = e
    return dict(unique_events=len(events), funnel={s: sum(s in e["passed"] for e in events) for s in STAGES},
        unique_enemy_frames_by_stage={s: len({identity(e, True) for e in events if s in e["passed"]}) for s in STAGES[1:]},
        rejections=dict(Counter(e["rejection"] for e in events if e["rejection"])),
        events=outcome_summary(eligible), enemy_frames=outcome_summary(list(unique.values())))


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for b in iter(lambda: stream.read(1024*1024), b""): h.update(b)
    return h.hexdigest()


def loads(text):
    def reject(value): raise ValueError("Nonfinite JSON: " + value)
    return json.loads(text, parse_constant=reject)


def frames(path, key):
    count = 0
    with gzip.open(path, "rt") as stream:
        for line in stream:
            raw = loads(line); k = raw["key"]
            need((k["seed"], k["side"]) == key and k["obs_step"] == count, "Frame key/order differs")
            need(raw["status"] in ("reset", "decision"), "Unusable archived frame")
            count += 1
            # No hidden fields enter the analysis object.
            f = {name: raw[name] for name in ("status", "key")}
            if raw["status"] == "decision":
                f.update(public=raw["public"], units=raw["units"])
                p = f["public"]
                need(p["config"]["canonical"] is True and p["step"] == k["obs_step"]
                     and p["match_idx"] == k["match_idx"] and p["match_step"] == k["match_step"], "Canonical context/time differs")
                need(len({u["uid"] for u in f["units"]}) == len(f["units"]), "Duplicate own UID")
                for u in f["units"]:
                    a = u["final_action"]; native = u["native_action"]
                    expected = ([5, -a[2], -a[1]] if a[0] == 5 else [[0, 2, 1, 4, 3][a[0]], 0, 0]) if key[1] == "player_1" else a
                    need(native == expected, "Final canonical/native action mismatch")
                    need(u["position"] == p["ally_pos"][u["uid"]] and u["energy"] == p["ally_ene"][u["uid"]], "Unit/public identity differs")
                need(all(math.isfinite(p[n]) and p[n] >= 0 for n in ("move_cost", "sap_cost", "sap_range")), "Invalid public costs/range")
            yield f
    need(count == 303, "Incomplete fixed trace")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.self_test:
        need(args.root is None and args.out is None, "Selfchecks do not accept archive/output paths")
        self_test(); return
    need(args.root is not None and args.out is not None, "--root and --out required")
    root = args.root.resolve(strict=True); out = args.out.resolve()
    need(out.is_relative_to(Path("/tmp").resolve()) and not out.exists() and out.parent.is_dir(), "Output must be a new /tmp file")
    inputs = {}
    def bind(path, expected=None):
        value = digest(path)
        need(expected is None or value == expected, "Input SHA differs: " + str(path))
        inputs[str(path)] = value
    manifest_path = root/BASE/"targeting/manifest.json"
    bind(manifest_path, MANIFEST_SHA); manifest = loads(manifest_path.read_text())
    need(manifest["status"] == "complete" and [(k["seed"], k["side"]) for k in manifest["keys"]] == FIXED, "Fixed manifest cohort differs")
    keys_path = root/BASE/"diagnostic_keys.json"; bind(keys_path, manifest["keys_sha256"])
    need(loads(keys_path.read_text())["keys"] == manifest["keys"], "Diagnostic keys differ")
    bind(Path(__file__).resolve())
    records = manifest["games"]
    need([(r["key"]["seed"], r["key"]["side"]) for r in records] == FIXED, "Fixed game records differ")
    all_events, per_game = [], []
    for i, r in enumerate(records):
        key = FIXED[i]; group = "loss" if i < 6 else "control"
        need(r["complete"] is True and r["key"]["group"] == group, "Incomplete/wrong group")
        filename = f"{key[0]}_{key[1]}.jsonl.gz"
        need(r["trace"]["path"] == filename, "Unexpected archive path")
        path = manifest_path.parent/filename; bind(path, r["trace"]["sha256"])
        stream = frames(path, key); prev, cur = None, next(stream); events = []
        for nxt in chain(stream, [None]):
            events.extend(analyze_frame(prev, cur, nxt)); prev, cur = cur, nxt
        for e in events: e["group"] = group
        per_game.append(dict(seed=key[0], side=key[1], group=group, summary=summarize(events)))
        all_events.extend(events)
    need(all(digest(Path(p)) == h for p, h in inputs.items()), "Input changed during read")
    report = dict(schema_version=1, status="COMPLETE_DESCRIPTIVE", manifest_sha256=MANIFEST_SHA,
        input_sha256=inputs, coordinate_order="canonical [x][y]; final_action delta, never sap_target",
        definitions=dict(turn="any other cardinal step, including reversal", other="displacement neither zero nor cardinal-one",
            unknown="no consecutive same-match public successor or UID not visible; never a stay/kill label",
            geometry="one target only: 1 at distance0, factor at Chebyshev distance1, else0; no physical damage",
            eligible="all public filters passed, including own SAP energy and old center legality"),
        summary=summarize(all_events), per_game=per_game,
        groups={g: summarize([e for e in all_events if e["group"] == g]) for g in ("loss", "control")},
        events=all_events, limitations=[
            "Selected old losses/qualitative controls, not representative frequencies or independent row samples.",
            "Same visible UID and nonnegative prior/current energies do not prove biological lifetime identity.",
            "Next visible negative energy is retained and separately described; missing visibility remains unknown.",
            "Survivor/visibility censoring limits motion labels. Other covers possible respawns or larger jumps without causal attribution.",
            "Fixed factors0/.25/.5/1 are geometry scenarios, not observed parameter estimates. No other targets, damage phases, enemy reactions or strength are evaluated.",
            "No posthoc selection or labels, games, tensor loads, project imports, training, policy changes or parameter selection."])
    payload = json.dumps(report, indent=2, allow_nan=False)+"\n"
    with out.open("x") as dest: dest.write(payload)
    print(json.dumps(dict(status=report["status"], output=str(out), sha256=digest(out))))


if __name__ == "__main__":
    main()
