"""Select at most one candidate from the completed, paired November 15 screening games."""
import argparse
import hashlib
import json
from pathlib import Path

CANDIDATES = ("pressure", "contact", "learned")
OPPONENTS = ("kaggle3", "solution92")
SEATS = ("player_0", "player_1")
SEEDS = range(7163000, 7163012)


def checked_games(directory, name, seeds, opponents=OPPONENTS):
    games, manifest, _ = checked_run_files(directory, name, seeds, opponents)
    return games, manifest


def checked_run_files(directory, name, seeds, opponents):
    raw_manifest = (directory / "manifest.json").read_bytes()
    manifest = json.loads(raw_manifest)
    if name is None:
        name = manifest["candidate"]
    finished = json.loads((directory / "completed.json").read_text())
    raw = (directory / "games.jsonl").read_bytes()
    if (hashlib.sha256(raw).hexdigest() != finished["rows_sha256"]
            or manifest["candidate"] != name or manifest["first"] != seeds.start
            or manifest["maps"] != len(seeds) or sorted(manifest["opponents"]) != sorted(opponents)):
        raise ValueError(f"Inconsistent screen in {directory}")
    expected = {(o, s, side) for o in opponents for s in seeds for side in SEATS}
    games = {}
    for line in raw.splitlines():
        row = json.loads(line)
        key = row["opponent"], row["seed"], row["side"]
        if (key in games or row["candidate"] != name or type(row["steps"]) is not int or row["steps"] != 303
                or any(type(row[k]) is not int for k in ("seed", "wins", "losses"))
                or row["wins"] not in range(4) or row["wins"] + row["losses"] != 3
                or type(row["result"]) not in (int, float)
                or row["result"] != int(row["wins"] > row["losses"])):
            raise ValueError(f"Invalid game in {directory}: {key}")
        games[key] = row
    if games.keys() != expected:
        raise ValueError(f"Missing or unexpected keys in {directory}")
    reconstructed = {}
    for opp in opponents:
        subset = [row for (o, _, _), row in games.items() if o == opp]
        reconstructed[opp] = dict(played=len(subset), wins=sum(r["result"] for r in subset),
                                  matches=sum(r["wins"] for r in subset))
    if finished.get("summary") != reconstructed:
        raise ValueError(f"Completion summary differs from games in {directory}")
    return games, manifest, {"manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
                             "games_sha256": finished["rows_sha256"]}


def combat_arms(diagnosis):
    aim = diagnosis["all"]["aim"]["counts"]
    fire = diagnosis["all"]["fire"]["counts"]
    names = []
    if aim["aim_changes"] >= 30 and aim["deployed_target_hits"] > aim["base_target_hits"]:
        names.append("aim")
        if fire["new_saps"] >= 30 and fire["new_teacher_saps"] >= 0.75 * fire["new_saps"]:
            names.append("fire")
    return names


def summarize(root, diagnosis, combat=False):
    if combat:
        seeds = range(7271100, 7271116)
        names = combat_arms(diagnosis)
    else:
        seeds = SEEDS
        names = CANDIDATES if diagnosis["screen_gate"] else CANDIDATES[:2]
    baseline, reference = checked_games(root / "v14", "v14", seeds)
    results, eligible = {}, []
    for name in ("v14", *names):
        games, manifest = checked_games(root / name, name, seeds)
        if (manifest["weights"] != reference["weights"] or manifest["engine"] != reference["engine"]
                or any(manifest["sources"].get(k) != v for k, v in reference["sources"].items())):
            raise ValueError(f"Reference inputs differ for {name}")
        if combat and name != "v14" and manifest["model"] != diagnosis["model_sha256"]:
            raise ValueError(f"Screened a different combat model: {name}")
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
            qualifies = (k3 >= 1 and sol >= -1) or (sol >= 1 and k3 >= 0)
            if combat:
                qualifies = k3 + sol >= 2 and sol >= 0
            if qualifies:
                eligible.append((k3 + sol, sum(s["matches"] for s in score.values()), -names.index(name), name))
    return dict(results=results, nominee=max(eligible)[-1] if eligible else None)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--diagnosis", type=Path, required=True)
    parser.add_argument("--combat", action="store_true", help="Use the prespecified combat-advice screen")
    args = parser.parse_args()
    diagnosis = json.loads(args.diagnosis.read_text())
    print(json.dumps(summarize(args.root, diagnosis, args.combat), indent=2))
