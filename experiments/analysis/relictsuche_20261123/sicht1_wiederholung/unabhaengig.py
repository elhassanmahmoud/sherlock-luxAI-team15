"""Audit the published 96-map archive without importing the series scorer or playing games."""
import argparse
import base64
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import product
import json
from math import comb
from pathlib import Path
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CANDIDATE = "ortundflotte"
ARMS = (("v16", "solution92"), (CANDIDATE, "solution92"), (CANDIDATE, "v16"))


def check(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_design():
    import jax
    import jax.numpy as jnp
    from importlib.util import find_spec
    from luxai_s3.params import env_params_ranges

    design = json.loads((HERE / "karten.json").read_bytes())
    prior = HERE.parent / "abschlusspruefung"
    for key, path in {"policy": prior / "nominierung.json", "previous": prior / "nachrechnung.json",
                      "runner": HERE / "serie.py", "plan": HERE / "PLAN.md"}.items():
        check(sha(path.read_bytes()) == design[key], f"Frozen {key} changed")
    nomination = json.loads((prior / "nominierung.json").read_bytes())
    check(nomination["player"] == CANDIDATE, "Unexpected policy")
    for name, digest in (nomination["sources"] | nomination["base"]["support"]).items():
        check(sha((ROOT / name).read_bytes()) == digest, f"Changed source {name}")
    package = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
    check(sha(package.read_bytes()) == nomination["base"]["release"], "V16 package changed")
    engine = Path(find_spec("luxai_s3").origin).parent
    for name, digest in nomination["base"]["engine"].items():
        check(sha((engine / name).read_bytes()) == digest, f"Changed engine file {name}")

    # Same seeded parameter sequence as the frozen Lux wrapper. No game object is created.
    names = list(env_params_ranges)
    position = names.index("unit_sensor_range")
    choices = jnp.array(env_params_ranges["unit_sensor_range"])

    def range_for(seed):
        key = jax.random.split(jax.random.key(seed))[0]
        for _ in range(position + 1):
            key, draw = jax.random.split(key)
        return jax.random.choice(draw, choices)

    pool = np.arange(165300000, 165301500, dtype=np.int32)
    sensors = np.asarray(jax.jit(jax.vmap(range_for))(pool))
    maps = pool[sensors == 1][:96].tolist()
    check(maps == design["cards"] and len(set(maps)) == 96, "Incorrect map panel or order")
    token = sha(json.dumps(design, sort_keys=True, separators=(",", ":")).encode())
    return maps, token


def sign_tail(values):
    """Count exact assignments using binomial multiplicities for card amplitudes one and two."""
    values = [int(x) for x in values]
    counts = Counter(abs(x) for x in values)
    check(set(counts) <= {0, 1, 2}, "Unexpected map amplitude")
    a, b = counts[1], counts[2]
    threshold = sum(values)
    favorable = sum(comb(a, i) * comb(b, j) for i in range(a + 1) for j in range(b + 1)
                    if (2 * i - a) + 2 * (2 * j - b) >= threshold)
    return dict(observed=threshold, map_histogram=dict(sorted(Counter(values).items())),
                null_outcomes=2 ** (a + b), at_least_observed=favorable, p=float(Fraction(favorable, 2 ** (a + b))))


def check_sign_method():
    for sample in ([], [0, 0], [1, 1, -2, 2, 0, -1], [-1, -2], [2, 2, 2, 2], [1, 1, 1, 1, 1, 1, 1]):
        counts = sign_tail(sample)
        outcomes = [sum(abs(x) * s for x, s in zip(sample, signs)) for signs in product((-1, 1), repeat=len(sample))]
        reference = Fraction(sum(x >= sum(sample) for x in outcomes), len(outcomes))
        check(Fraction(counts["at_least_observed"], counts["null_outcomes"]) == reference, "Wrong sign arithmetic")


def read_archive(maps, token, public):
    data = (HERE / "partien.jsonl.gz").read_bytes()
    check(sha(data) == public["archive"] and public["source"] == token and public["games"] == 576,
          "Publication incomplete or not bound to these sources")
    lines = gzip.decompress(data).splitlines()
    check(len(lines) == 576, "Incomplete archive")
    games = {}
    expected = {(s, t, *arm) for s in maps for t in (0, 1) for arm in ARMS}
    for line in lines:
        row = json.loads(line)
        key = tuple(row["key"])
        check(key in expected and key not in games, f"Unexpected or repeated game {key}")
        check(row["source"] == token and row["sensor"] == 1, f"Invalid source/sensor {key}")
        tape = zlib.decompress(base64.b64decode(row["tape"], validate=True))
        commands = np.frombuffer(tape, dtype=np.int8).reshape(303, 2, 16, 3)
        check(sha(commands.astype("<i4").tobytes()) == row["digest"], f"Command digest mismatch {key}")
        check(np.isin(commands[..., 0], np.arange(6)).all(), f"Unknown action type {key}")
        matches = row["matches"]
        check(len(matches) == 3, f"Missing match {key}")
        for m in matches:
            own, other = m["points"]
            check(min(own, other) >= 0 and m["win"] in (0, 1), f"Invalid score {key}")
            check(own == other or m["win"] == int(own > other), f"Wrong winner by points {key}")
        check(row["win"] == int(sum(m["win"] for m in matches) >= 2), f"Wrong three-match winner {key}")
        check(all(0 <= row[f] <= 101 for f in ("sight", "credit")), f"Opening time {key}")
        games[key] = (row, commands)
    check(set(games) == expected, "Incomplete seat/arm grid")
    return games


def first_difference(a, b):
    indices = np.flatnonzero((a != b).any(axis=(1, 2, 3)))
    return int(indices[0]) if len(indices) else None


def move_changes(native, scout):
    units = np.flatnonzero((native != scout).any(axis=1))
    if len(units):
        check(len(units) == 1, "Multiple directly changed ships at first difference")
        i = units[0]
        check(0 <= native[i, 0] <= 4 and 1 <= scout[i, 0] <= 4
              and native[i, 0] != scout[i, 0] and not scout[i, 1:].any(), "Invalid first scout movement")
    return len(units)


def intervals(map_sums):
    # Sample whole maps, already summed over the two seats. Same declared bootstrap draws as publication.
    n = len(map_sums)
    rng = np.random.default_rng(231123)
    samples = []
    for _ in range(100):
        indices = rng.integers(n, size=(200, n))
        samples.append(map_sums[indices].sum(axis=1) / (2 * n))
    return np.percentile(np.concatenate(samples), (2.5, 97.5), axis=0).T


def check_small_examples():
    check_sign_method()
    bounds = intervals(np.array([[-2, 0, 8], [2, 2, 8]]))
    check(np.array_equal(bounds, [[-1, 1], [0, 1], [4, 4]]), "Wrong clustered intervals")
    original = np.zeros((303, 2, 16, 3), dtype=np.int8)
    changed = original.copy()
    changed[25, 1, 7, 0] = 2
    check(first_difference(original, original) is None, "False command divergence")
    check(first_difference(original, changed) == 25 and move_changes(original[25,1], changed[25,1]) == 1,
          "Wrong first changed unit")
    changed[25, 1, 3, 0] = 4
    try:
        move_changes(original[25,1], changed[25,1])
    except ValueError:
        return
    raise ValueError("Accepted different first movements from two ships")


def audit(maps, token, public):
    games = read_archive(maps, token, public)
    seats = []
    changed_games = []
    ties = []
    direct_same = []
    direct_diff = []
    totals = Counter()
    match_changes = [Counter() for _ in range(3)]
    time_changes = {f: Counter() for f in ("sight", "credit")}
    for s in maps:
        d0, d1 = [games[s, t, *ARMS[2]] for t in (0, 1)]
        j = first_difference(d0[1], d1[1])
        if j is None:
            for left, right in zip(d0[0]["matches"], d1[0]["matches"]):
                check(left["points"] == right["points"][::-1] and left["win"] + right["win"] == 1,
                      f"Identical seat-rotated direct tape has inconsistent scoreboard {s}")
            direct_same.append(s)
        else:
            check(16 <= j <= 83, f"Direct first change outside intervention {s}")
            n0 = move_changes(d1[1][j, 0], d0[1][j, 0])
            n1 = move_changes(d0[1][j, 1], d1[1][j, 1])
            if n0:
                check(j < d0[0]["sight"] and j <= d0[0]["credit"], "Invalid direct scout timing P0")
            if n1:
                check(j < d1[0]["sight"] and j <= d1[0]["credit"], "Invalid direct scout timing P1")
            direct_diff.append(s)
        for t in (0, 1):
            for n, arm in enumerate(ARMS):
                r, _ = games[s, t, *arm]
                totals[n, t, "game"] += r["win"]
                for i, m in enumerate(r["matches"], 1):
                    totals[n, t, i] += m["win"]
                    if m["points"][0] == m["points"][1]:
                        ties.append([s, t, *arm, i, m["points"], m["win"]])
            (ref, native), (new, scout), (direct, _) = [games[s, t, *arm] for arm in ARMS]
            first = first_difference(native, scout)
            if first is None:
                check(all(ref[k] == new[k] for k in ("matches", "sight", "credit", "win", "digest")), "Inconsistent identical tape")
            else:
                check(16 <= first <= 83 and first < ref["sight"] and first <= ref["credit"], "Invalid opening time")
                check(np.array_equal(native[first, 1 - t], scout[first, 1 - t]), "Rival diverged first")
                check(move_changes(native[first, t], scout[first, t]) == 1, "Scout did not move first")
            for i, (a, b) in enumerate(zip(ref["matches"], new["matches"])):
                match_changes[i][b["win"] - a["win"]] += 1
            for field, counts in time_changes.items():
                shift = ref[field] - new[field]
                counts["earlier" if shift > 0 else "later" if shift < 0 else "same"] += 1
                counts["original_censored"] += int(ref[field] == 101)
                counts["candidate_censored"] += int(new[field] == 101)
            gain = new["win"] - ref["win"]
            if gain:
                changed_games.append(dict(seed=s, team=t, gain=gain, original=ref["matches"], candidate=new["matches"],
                                          first_action=first, sight=[ref["sight"],new["sight"]], credit=[ref["credit"],new["credit"]]))
            seats.append(dict(seed=s, team=t, level=1, base=ref["win"], new=new["win"], direct=direct["win"], gain=gain,
                              sight=ref["sight"]-new["sight"], credit=ref["credit"]-new["credit"], changed=int(first is not None), diverged=first))
    published_seats = sorted(public["seats"], key=lambda r:(r["seed"],r["team"]))
    check(seats == published_seats, "Disagreement in seat effects")
    by_map = np.array([[v[k] for k in ("gain","direct","sight","credit")] for v in seats]).reshape(96,2,4).sum(axis=1)
    ci = intervals(by_map)
    sol = sign_tail(by_map[:,0])
    duel = sign_tail(by_map[:,1]-1)
    overall = dict(cards=len(maps), seats=len(seats), original=sum(v["base"] for v in seats), candidate=sum(v["new"] for v in seats),
                   direct=sum(v["direct"] for v in seats), gain_ci=ci[0].tolist(), direct_ci=ci[1].tolist(),
                   sight_ci=ci[2].tolist(), credit_ci=ci[3].tolist(), exact_p_solution=sol["p"], exact_p_direct=duel["p"])
    for name, col in (("gain",0),("sight_gain",2),("credit_gain",3)):
        overall[name] = float(by_map[:,col].sum()/192)
    overall.update(changed=sum(v["changed"] for v in seats), rescued=sum(v["gain"]>0 for v in seats),
                   lost=sum(v["gain"]<0 for v in seats), winning_cards=int((by_map[:,0]>0).sum()), losing_cards=int((by_map[:,0]<0).sum()))
    check(overall == public["panel"], "Published scores or intervals disagree with reconstruction")
    conditions = dict(solution_sign=sol["p"] <= .0125, solution_interval=ci[0,0] > 0,
                      direct_half=overall["direct"] >= 96, direct_interval=ci[1,0] >= .45)
    qualified = all(conditions.values())
    check(qualified == public["qualified"], "Published decision differs")
    arm_totals = [{"arm":list(arm),"seat":t,"matches":[totals[n,t,i] for i in (1,2,3)],"games":totals[n,t,"game"]}
                  for n,arm in enumerate(ARMS) for t in (0,1)]
    return dict(archive_sha256=public["archive"], source_sha256=token, design_sha256=sha((HERE/"karten.json").read_bytes()),
                games=len(games), matches=3*len(games), turns=303*len(games), public_panel=overall, decision=qualified,
                gates={k:bool(v) for k,v in conditions.items()}, solution_randomization=sol, direct_randomization=duel,
                whole_game_changes=changed_games, points_ties=ties, wins_by_arm_and_seat=arm_totals,
                identical_direct_maps=direct_same, different_direct_maps=direct_diff,
                match_changes_solution=[dict(improved=c[1], declined=c[-1], same=c[0]) for c in match_changes],
                opening_times={f:dict(c) for f,c in time_changes.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", action="store_true", help="Verify method, frozen sources and map selection only")
    args = parser.parse_args()
    check_small_examples()
    maps, token = checked_design()
    if args.design:
        print(f"Verified 96 sensor-one maps {maps[0]}–{maps[-1]} and frozen sources {token}")
        return
    path = HERE/"ergebnis.json"
    check(path.is_file(), "The final archive has not been published")
    result = audit(maps, token, json.loads(path.read_bytes()))
    output = HERE/"unabhaengig.json"
    content = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if output.exists():
        check(output.read_text() == content, "Existing independent result differs")
    else:
        output.write_text(content)
    print(json.dumps(result["public_panel"], sort_keys=True))
    print("qualified", result["decision"])


if __name__ == "__main__":
    main()
