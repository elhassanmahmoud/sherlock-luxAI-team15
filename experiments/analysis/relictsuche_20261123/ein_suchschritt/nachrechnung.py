"""Reconstruct the five-arm development study from the published whole-game records."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ARMS = [("v16", "solution92"), ("eins", "solution92"), ("voll", "solution92"), ("eins", "v16"), ("voll", "v16")]
RESULT_FIELDS = ("matches", "sight", "credit", "after_70", "win", "points")


def check(value, explanation):
    if not value:
        raise ValueError(explanation)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def design():
    import jax
    from jax import numpy as jnp
    from luxai_s3.params import env_params_ranges

    spec = json.loads((HERE / "karten.json").read_bytes())
    for name, digest in spec["sources"].items():
        check(sha((HERE.parent / name).read_bytes()) == digest, f"Frozen source changed {name}")
    nomination = json.loads((HERE.parent / "abschlusspruefung/nominierung.json").read_bytes())
    for name, digest in (nomination["sources"] | nomination["base"]["support"]).items():
        check(sha((ROOT / name).read_bytes()) == digest, f"Nominated dependency changed {name}")
    package = ROOT / "experiments/releases/20261117_sherlock_v16/agent.zip"
    check(sha(package.read_bytes()) == nomination["base"]["release"], "Original package changed")
    names = list(env_params_ranges)
    index = names.index("unit_sensor_range")
    choices = jnp.array(env_params_ranges[names[index]])

    def selected(seed):
        key = jax.random.split(jax.random.key(seed))[0]
        for _ in range(index + 1):
            key, draw = jax.random.split(key)
        return jax.random.choice(draw, choices) == 1

    pool = np.arange(166200000, 166201000, dtype=np.int32)
    cards = pool[np.asarray(jax.jit(jax.vmap(selected))(pool))][:32].tolist()
    check(cards == spec["cards"] and len(set(cards)) == 32, "Map selection mismatch")
    return cards, sha(json.dumps(spec, sort_keys=True, separators=(",", ":")).encode())


def inspect(row):
    ms = row["matches"]
    check(len(ms) == 3 and row["steps"] == 303 and row["actions_checked"] == [303,303]
          and row["caught_errors"] == [0,0] and row["point_counting_version"] == 2, "Invalid game control")
    check(row["phase"] == "test" and row["sensor"] == 1, "Wrong population")
    check(re.fullmatch("[a-f0-9]{64}",row["action_hash"]), "Invalid action digest")
    for m in ms:
        own, their = m["points"]
        check(min(own,their) >= 0 and m["win"] in (0,1) and (own == their or m["win"] == int(own > their)), "Invalid match score")
    check(row["wins"] == sum(m["win"] for m in ms) and row["win"] == (row["wins"] >= 2), "Invalid whole-game outcome")
    check(row["points"] == np.sum([m["points"] for m in ms],axis=0).tolist(), "Wrong score sum")
    check(all(0 <= a <= b for a,b in zip(row["after_70"],ms[0]["points"],strict=True)), "Wrong turn 70")
    check(all(0 <= row[f] <= 101 for f in ("sight","credit")) and ((row["credit"]==101) == (ms[0]["points"][0]==0)), "Wrong first signal")
    events = row["events"]
    check(row["id"] != "v16" or not events, "Modified original")
    check(row["id"] != "eins" or len(events) <= 1, "Second single-step override")
    check(len({e[1] for e in events}) <= 1 and [e[0] for e in events] == sorted({e[0] for e in events}), "Changed ship or duplicated action")
    for step, uid, before, after in events:
        check(16 <= step <= 83 and step < row["sight"] and step <= row["credit"] and 0 <= uid < 16
              and 0 <= before <= 4 and 1 <= after <= 4 and after != before, "Illegal known-scout override")


def identities(left, right, expected_same):
    same = left["action_hash"] == right["action_hash"]
    check(same == expected_same, "Mismatch between event history and full-game command fingerprints")
    if same:
        check(all(left[k] == right[k] for k in RESULT_FIELDS), "Identical command fingerprints, different scoreboard")
    return same


def bootstrap(sums):
    n = len(sums)
    draws = np.random.default_rng(231123)
    replications = np.concatenate([sums[draws.integers(n,size=(250,n))].sum(axis=1) for _ in range(80)]) / (2*n)
    return np.percentile(replications,[2.5,97.5],axis=0).T.tolist()


def audit(cards, source):
    # The generator publishes ergebnis.json before the archive. Wait for both and require exactly 320 rows.
    archive = HERE/"partien.jsonl.gz"
    public = json.loads((HERE/"ergebnis.json").read_bytes())
    blob = archive.read_bytes()
    lines = gzip.decompress(blob).splitlines()
    check(len(lines) == 320 and public["source"] == source and public["arms"] == [list(a) for a in ARMS], "Incomplete published set")
    by_id = {}
    expected = {(s,t,*a) for s in cards for t in (0,1) for a in ARMS}
    for line in lines:
        r = json.loads(line)
        key = (r["seed"],r["team"],r["id"],r["opponent"])
        check(key in expected and key not in by_id and r["source"] == source, "Duplicate or foreign game")
        inspect(r)
        by_id[key] = r
    check(set(by_id) == expected, "Missing arm")
    stats = []
    scores = Counter()
    comparison = Counter()
    changed_winners = []
    for s in cards:
        for t in (0,1):
            rows = [by_id[s,t,*arm] for arm in ARMS]
            ref,one,full,d1,df = rows
            for i,r in enumerate(rows):
                scores[i,t,"game"] += r["win"]
                for m,match in enumerate(r["matches"]):
                    scores[i,t,m] += match["win"]
            for label, single, original in (("solution",one,full),("direct",d1,df)):
                check(single["events"] == original["events"][:1], "Shortened policy changed its first executed override")
                same = identities(single,original,len(original["events"]) <= 1)
                comparison[label,"identical"] += int(same)
                comparison[label,"activated"] += bool(single["events"])
                if not same:
                    divergence = original["events"][1][0]
                    for field,bound in (("sight",divergence+1),("credit",divergence)):
                        if min(original[field],single[field]) < bound:
                            check(original[field] == single[field], "Signal differed before separation")
                    if divergence > 70:
                        check(original["after_70"] == single["after_70"], "Score differed before separation")
                if original["win"] != single["win"]:
                    changed_winners.append(dict(seed=s,team=t,opponent=label,full=original["win"],one=single["win"]))
            identities(ref,one,not one["events"])
            identities(ref,full,not full["events"])
            stats.append([*[r["win"] for r in rows],*[r["sight"] for r in rows[:3]],*[r["credit"] for r in rows[:3]]])
    data = np.array(stats).reshape(32,2,11)
    totals = data.sum((0,1))[:5].tolist()
    means = (data.sum((0,1))[5:]/64).tolist()
    metrics = np.stack([data[:,:,1]-data[:,:,0],data[:,:,1]-data[:,:,2],data[:,:,7]-data[:,:,6],data[:,:,3]],axis=-1)
    intervals = bootstrap(metrics.sum(axis=1))
    gates = dict(whole_game_at_least_both=totals[1] >= max(totals[0],totals[2]), direct_at_least_half=totals[3]>=32,
                 sight_strictly_earlier_than_full=means[1]<means[2])
    check(public["wins"] == totals and public["times"] == means and public["ci"] == intervals, "Published endpoints disagree")
    check(public["changed"] == 64-comparison["solution","identical"] and public["passed"] == all(gates.values()), "Published outcome disagrees")
    per_seat = [dict(arm=list(a),seat=t,wins=scores[i,t,"game"],matches=[scores[i,t,m] for m in range(3)])
                for i,a in enumerate(ARMS) for t in (0,1)]
    return dict(source=source,archive_sha256=sha(blob),games=320,matches=960,turns=96960,
                gates=gates,passed=all(gates.values()),arms=[list(a) for a in ARMS],wins=totals,mean_times=means,
                intervals=intervals,activated={k:comparison[k,"activated"] for k in ("solution","direct")},
                identical_short_full={k:comparison[k,"identical"] for k in ("solution","direct")},
                whole_game_swaps_short_full=changed_winners,by_seat=per_seat,
                match_points_ties=sum(m["points"][0] == m["points"][1] for r in by_id.values() for m in r["matches"]))


if __name__ == "__main__":
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--design",action="store_true")
    args = arg.parse_args()
    cards, token = design()
    if args.design:
        print(f"Verified 32 new sensor-one maps {cards[0]}–{cards[-1]} and sealed sources")
    else:
        report = audit(cards, token)
        text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n"
        dest = HERE/"nachrechnung.json"
        if dest.exists():
            check(dest.read_text() == text, "Previous independent score differs")
        else:
            dest.write_text(text)
        print(json.dumps({k:report[k] for k in ("wins","mean_times","intervals","gates","passed")}))
