"""Select at most one candidate from the completed, paired November 15 screening games."""
import argparse
import hashlib
import json
from pathlib import Path

CANDIDATES = ("pressure", "contact", "learned")
OPPONENTS = ("kaggle3", "solution92")
SEATS = ("player_0", "player_1")
SEEDS = range(7163000, 7163012)


def checked_games(directory, name):
    manifest = json.loads((directory / "manifest.json").read_text())
    finished = json.loads((directory / "completed.json").read_text())
    raw = (directory / "games.jsonl").read_bytes()
    if (hashlib.sha256(raw).hexdigest() != finished["rows_sha256"]
            or manifest["candidate"] != name or manifest["first"] != SEEDS.start
            or manifest["maps"] != len(SEEDS) or tuple(manifest["opponents"]) != OPPONENTS):
        raise ValueError(f"Inconsistent screen in {directory}")
    expected = {(o, s, side) for o in OPPONENTS for s in SEEDS for side in SEATS}
    games = {}
    for line in raw.splitlines():
        row = json.loads(line)
        key = row["opponent"], row["seed"], row["side"]
        if (key in games or row["candidate"] != name or row["steps"] != 303
                or row["wins"] not in range(4) or row["wins"] + row["losses"] != 3
                or row["result"] != int(row["wins"] > row["losses"])):
            raise ValueError(f"Invalid game in {directory}: {key}")
        games[key] = row
    if games.keys() != expected:
        raise ValueError(f"Missing or unexpected keys in {directory}")
    return games, manifest


def summarize(root, include_learned):
    baseline, reference = checked_games(root / "v14", "v14")
    names = CANDIDATES if include_learned else CANDIDATES[:2]
    results, eligible = {}, []
    for name in ("v14", *names):
        games, manifest = checked_games(root / name, name)
        if (manifest["weights"] != reference["weights"] or manifest["engine"] != reference["engine"]
                or any(manifest["sources"].get(k) != v for k, v in reference["sources"].items())):
            raise ValueError(f"Reference inputs differ for {name}")
        score = {}
        for o in OPPONENTS:
            pairs = [(games[k], base) for k, base in baseline.items() if k[0] == o]
            score[o] = dict(games=len(pairs), wins=sum(r["result"] for r, _ in pairs),
                            matches=sum(r["wins"] for r, _ in pairs),
                            gained=sum(r["result"] > b["result"] for r, b in pairs),
                            lost=sum(r["result"] < b["result"] for r, b in pairs))
        results[name] = score
        if name != "v14":
            k3, sol = (score[o]["wins"] - results["v14"][o]["wins"] for o in OPPONENTS)
            if (k3 >= 1 and sol >= -1) or (sol >= 1 and k3 >= 0):
                eligible.append((k3 + sol, sum(s["matches"] for s in score.values()), -names.index(name), name))
    return dict(results=results, nominee=max(eligible)[-1] if eligible else None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--diagnosis", type=Path, required=True)
    args = parser.parse_args()
    diagnosis = json.loads(args.diagnosis.read_text())
    include = diagnosis["screen_gate"]
    print(json.dumps(summarize(args.root, include), indent=2))
