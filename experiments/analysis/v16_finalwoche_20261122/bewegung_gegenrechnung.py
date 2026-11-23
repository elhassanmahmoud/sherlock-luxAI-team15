"""Audit a finished 1,040-game movement trial and its qualified comparison family."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
STARTS = {"zugnutzen": 160365000, "sichtlernen": 160370000}
OPPONENTS = ("solution92", "kaggle3")
ARMS = ("original", "adviser")
FIELDS = ("game_win", "our_wins", "opp_wins", "our_points", "opp_points", "changes")
V16 = "0c59706b6af1c2cd74819a4b13269b69cb55786e07e3daaa2d6e6547a6b86099"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def completed_selection_family():
    members = []
    for name in ("doppelziel", *STARTS):
        path = HERE / name
        result = json.loads((path / "auswahl_ergebnis.json").read_text())
        require(result["actual_games"] == 400 and result["raw_sha256"] == digest(path / "auswahl_partien.jsonl.gz"),
                f"Selection archive {name}")
        require(result["qualifies"] == all(result["gates"].values()), f"Selection qualification {name}")
        if result["qualifies"]:
            members.append(name)
    require(set(members) == set(STARTS), "Different family of independent trials")
    return members


def verify(name):
    members = completed_selection_family()
    folder = HERE / name
    # Open only completed reports and their compressed archives. Never scan per-seat intermediates.
    report = json.loads((folder / "bestaetigung_ergebnis.json").read_text())
    path = folder / "bestaetigung_partien.jsonl.gz"
    require(report["games"] == 1040 and report["maps"] == 120 and digest(path) == report["evidence_sha256"],
            "Missing or incorrect sealed evidence")
    contract = report["source"]
    require(contract.get("agent.zip") == V16, "Release hash")
    for filename, stamp in contract.items():
        if filename != "agent.zip":
            source = HERE / filename if filename == "BEWEGUNG_BESTAETIGEN.md" else folder / filename
            require(digest(source) == stamp, f"Frozen source {filename}")
    version = sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest()
    cube = np.full((120, 2, 2, 2, len(FIELDS)), -1, dtype=int)
    direct = np.full((40, 2), -1, dtype=int)
    with gzip.open(path, "rt") as stream:
        for line in stream:
            row = json.loads(line)
            index, side = row["seed"] - STARTS[name], row["team"]
            require(0 <= index < 120 and side in (0, 1) and row["source"] == version, "Map, seat or source")
            values = [row[f] for f in FIELDS]
            require(min(values) >= 0 and row["steps"] == 303 and row["point_counting_version"] == 2
                    and row["our_wins"] + row["opp_wins"] == 3 and row["game_win"] == int(row["our_wins"] >= 2),
                    "Invalid 303-step course result")
            if row["opponent"] == "v16":
                require(index < 40 and row["arm"] == "adviser" and direct[index, side] == -1, "Unexpected duel")
                direct[index, side] = row["game_win"]
            else:
                opp, arm = OPPONENTS.index(row["opponent"]), ARMS.index(row["arm"])
                target = cube[index, side, opp, arm]
                require(target[0] == -1 and (arm == 1 or row["changes"] == 0), "Duplicate or changed reference")
                target[:] = values
    require(np.min(cube) >= 0 and np.min(direct) >= 0, "Missing games")
    unchanged = cube[:, :, :, 1, -1] == 0
    require(np.array_equal(cube[:, :, :, 0, :-1][unchanged], cube[:, :, :, 1, :-1][unchanged]), "No-change seat mismatch")
    card = (cube[:, :, :, 1, 0] - cube[:, :, :, 0, 0]).mean(axis=1)
    primary = card.mean(axis=1) if name == "zugnutzen" else card[:, 0]
    rng = np.random.default_rng(231150)
    draws = np.empty((20000, 3))
    whole_cards = np.column_stack((primary, card))
    for i in range(len(draws)):
        weights = np.bincount(rng.choice(120, 120), minlength=120)
        draws[i] = 100 * weights @ whole_cards / 120
    standard = np.quantile(draws, [.025, .975], axis=0)
    tail = .025 / len(members)
    adjusted = np.quantile(draws[:, 0], [tail, 1 - tail])
    np.testing.assert_allclose([primary.mean()*100, *standard[:, 0], *adjusted],
                               [report["primary_delta_pp"], *report["primary_ci95"], *report["family_intervals"]["2"]])
    games = {}
    for j, opponent in enumerate(OPPONENTS):
        stats = report["external"][opponent]
        actual = cube[:, :, j].sum(axis=(0, 1))
        for a, arm in enumerate(ARMS):
            for f in ("game_win", "our_wins", "our_points", "opp_points", "changes"):
                require(actual[a, FIELDS.index(f)] == stats["arms"][arm][f], f"External totals {opponent} {arm} {f}")
        games[opponent] = dict(zip(ARMS, map(int, actual[:, 0])))
        np.testing.assert_allclose([100*card[:, j].mean(), *standard[:, j+1]], [stats["delta_pp"], *stats["ci95"]])
    direct_distribution = direct.mean(axis=1)[rng.choice(40, (20000, 40))].mean(axis=1)
    direct_ci = 100*np.quantile(direct_distribution, [.025, .975])
    np.testing.assert_allclose([direct.sum(), *direct_ci], [report["direct"]["wins"], *report["direct"]["ci95"]])
    gates = dict(primary=bool(standard[0, 0] > 0), solution=bool(card[:, 0].sum() >= 0),
                 kaggle=bool(card[:, 1].sum() >= 0), direct=bool(direct.sum() >= 40))
    require(gates == report["gates"] and all(gates.values()) == report["all_gates"], "Prespecified decision")
    return dict(verified=True, study=name, games=1040, maps=120, compared_family=members,
                primary="equally weighted game-win difference vs both opponents" if name == "zugnutzen"
                else "game-win difference vs Solution", favourable_direction="positive",
                primary_delta_pp=float(primary.mean()*100), primary_ci95_pp=standard[:, 0].tolist(),
                bonferroni_ci97_5_pp=adjusted.tolist(), external_wins_per_240=games,
                direct_wins_per_80=int(direct.sum()), direct_ci95_percent=direct_ci.tolist(), gates=gates,
                qualified_after_family_correction=bool(all(gates.values()) and adjusted[0] > 0),
                archive_sha256=digest(path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", choices=STARTS)
    print(json.dumps(verify(parser.parse_args().study), indent=2))
