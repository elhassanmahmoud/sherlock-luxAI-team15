"""Close the passive stage, independently audit all tours and apply the registered decision."""
import argparse
from collections import Counter, defaultdict
import gzip
import json

from audit import PublicModel, cells, independent_routes
from studie import HERE, SCRATCH, SINGLE, digest, read_zip, source


def stored(path, rows):
    raw = "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n" for r in rows).encode()
    if path.exists():
        assert gzip.decompress(path.read_bytes()) == raw
    else:
        path.write_bytes(gzip.compress(raw, mtime=0))


def encoded(rows):
    return json.dumps(rows, indent=2, sort_keys=True, allow_nan=False) + "\n"


def audit_game(raw, singles, record):
    groups = record["groups"]
    first = {}
    candidate_times = defaultdict(set)
    group_tests = set()
    checks = Counter(record["checks"])
    frames = record["frames"]
    for data, policy, hidden, f, base in zip(raw["public"], raw["policy"], raw["referee"], frames, singles["frames"], strict=True):
        t = f["t"]
        actual = cells(hidden)
        current = cells(f["groups"])
        for g in current:
            assert actual.intersection(groups[g])
            first.setdefault(g,t)
        confirmed = cells(base["p"]) | cells(f.get("extra_single", "0"))
        assert confirmed <= actual
        witnesses = {(g, uid) for g,uid,_ in f["complete"]}
        independent = independent_routes(data, policy, [(i,groups[i]) for i in current], confirmed)
        assert independent == witnesses, (raw["seed"], raw["team"], t, sorted(independent ^ witnesses))
        assert f["singleton_route"] == bool(int(base.get("strict_four", "0"), 16))
        for g, _ in independent:
            group_tests.add(g)
            for key in groups[g]:
                candidate_times[key].add(t)
        checks["independent_route_frames"] += 1
    query_cells = set(candidate_times)
    cache = {}
    def possible(t, keys):
        if t not in cache:
            cache[t] = PublicModel(raw["public"], t, query_cells)
        checks["public_integer_queries"] += 1
        return cache[t].zero_possible(keys)
    for g in sorted(group_tests):
        assert not possible(first[g], groups[g]), (raw["seed"], raw["team"], groups[g], first[g])
        checks["group_zero_rejected_at_first_proof"] += 1
    # Feasibility of zero is a nonincreasing function of time for each monotone point variable.
    possible_until = {}
    for key in sorted(candidate_times):
        ordered = sorted(candidate_times[key])
        lo, hi = -1, len(ordered)
        while hi - lo > 1:
            mid = (lo+hi)//2
            if possible(ordered[mid], [key]):
                lo = mid
            else:
                hi = mid
        possible_until[key] = ordered[lo] if lo >= 0 else -1
    decisions = []
    for f in frames:
        t = f["t"]
        strict = [[g, uid, path] for g,uid,path in f["complete"] if all(possible_until[k] >= t for k in groups[g])]
        if strict:
            decisions.append(dict(t=t, singleton_route=f["singleton_route"], tours=strict))
    return dict(seed=raw["seed"], team=raw["team"], possible_until=possible_until,
                first_public_certificates={g:first[g] for g in sorted(group_tests)}, decisions=decisions, checks=checks)


def summarize(records, audits):
    categories = ("open", "partial", "partial_without_full", "full", "also_single", "separate", "ambiguous", "primary")
    acc = {k: dict(maps=set(), seats=set(), pairs=set(), seat_groups=set(), turns=0, group_ticks=0,
                   by_match=[0, 0, 0], sizes=Counter()) for k in categories}
    checks = Counter(); streaks = set(); examples = []
    for r,a in zip(records, audits, strict=True):
        s, team = r["seed"], r["team"]
        checks.update(a["checks"])
        robust = {f["t"]:f["tours"] for f in a["decisions"]}
        previous = set()
        example = None
        for f in r["frames"]:
            t = f["t"]
            tours = robust.get(t, [])
            full = {g for g,_,_ in f["complete"]}
            partial = cells(f["partial"])
            ambiguous = {g for g,_,_ in tours}
            primary = ambiguous if not f["singleton_route"] else set()
            current = {(g,uid) for g,uid,_ in tours if g in primary}
            if previous & current:
                streaks.add((s, team))
            previous = current
            for g,uid,path in tours:
                if g in primary and (example is None or len(path) < len(example["path"])):
                    example = dict(seed=s,team=team,step=t,group=r["groups"][g],uid=uid,path=path)
            values = dict(open=cells(f["open"]), partial=partial, partial_without_full=partial-full, full=full,
                          also_single=full if f["singleton_route"] else set(),
                          separate=full if not f["singleton_route"] else set(), ambiguous=ambiguous, primary=primary)
            for k, items in values.items():
                if not items:
                    continue
                c = acc[k]
                c["maps"].add(s); c["seats"].add((s,team)); c["turns"] += 1; c["group_ticks"] += len(items)
                c["by_match"][t//101] += len(items)
                for g in items:
                    identity = tuple(r["groups"][g])
                    c["pairs"].add((s,identity)); c["seat_groups"].add((s,team,identity)); c["sizes"][len(identity)] += 1
        if example: examples.append(example)
    bins = {}
    for k,c in acc.items():
        bins[k] = dict(maps=len(c["maps"]), seats=len(c["seats"]), sides=[sum(t==i for _,t in c["seats"]) for i in (0,1)],
                       map_groups=len(c["pairs"]), seat_groups=len(c["seat_groups"]), decision_times=c["turns"],
                       group_ticks=c["group_ticks"], ticks_by_match=c["by_match"], ticks_by_size=dict(c["sizes"]))
    p = bins["primary"]
    gates = dict(eight_maps=p["maps"]>=8, twelve_seats=p["seats"]>=12, three_per_side=min(p["sides"])>=3,
                 eight_repeated_seats=len(streaks)>=8)
    return dict(categories=bins, consecutive_seats=sorted(streaks), checks=checks, primary_examples=examples,
                gates=gates, pass_all=all(gates.values()))


def run(group):
    games = read_zip(SINGLE / group / "beobachtungen.jsonl.gz")
    singles = read_zip(SINGLE / group / "beweise.jsonl.gz")
    expected = {f"{r['seed']}_{r['team']}.json.gz" for r in games}
    assert expected == {p.name for p in (SCRATCH / group).glob("*.json.gz")}
    folder = HERE / group
    folder.mkdir(exist_ok=True)
    records, audits = [], []
    binding = source(group)
    for raw, controls in zip(games, singles, strict=True):
        key = raw["seed"], raw["team"]
        r = json.loads(gzip.decompress((SCRATCH / group / f"{key[0]}_{key[1]}.json.gz").read_bytes()))
        assert r["source"] == binding and (r["seed"],r["team"]) == key and raw["action_hash"] == r["action_hash"] == controls["action_hash"]
        audits.append(audit_game(raw, controls, r)); records.append(r)
    stored(folder / "gruppen.jsonl.gz", records)
    stored(folder / "nachrechnung.jsonl.gz", audits)
    result = summarize(records, audits)
    result.update(group=group, games=len(games), maps=len(games)//2, gate_applies=group=="frisch", sources=binding,
                  evidence_sha256=digest(folder / "gruppen.jsonl.gz"), audit_sha256=digest(folder / "nachrechnung.jsonl.gz"),
                  evaluation={n:digest(HERE/n) for n in ("audit.py", "auswerten.py", "pruefen.py")})
    path=folder / "ergebnis.json"
    if path.exists():
        assert json.loads(path.read_text()) == json.loads(encoded(result))
    else:
        path.write_text(encoded(result))
    print(group, len(games), 'audited games', flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=("archiv", "frisch"))
    run(parser.parse_args().group)
