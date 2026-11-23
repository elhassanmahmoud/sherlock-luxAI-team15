"""Independently verify the frozen 15-turn estimator and held-out measurements."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def check_panel(archive_path, initial_seed, size, raw_directory, omissions=()):
    with gzip.open(archive_path, "rt") as stream:
        archive = [json.loads(line) for line in stream]
    rows = {item["case"][0]: item for item in archive}
    expected = set(range(initial_seed, initial_seed + size)).difference(omissions)
    require(len(archive) == len(expected) and set(rows) == expected, "Map coverage")
    for seed in sorted(expected):
        i = seed - initial_seed
        row = rows[seed]
        seat = i % 2
        rival = ["solution92", "kaggle3"][(i // 2) % 2]
        first = [26, 40, 54][i % 3]
        require(row["case"] == [seed, seat, rival, first], f"Wrong case {seed}")
        if raw_directory:
            raw_file = raw_directory / f"{seed}.json"
            require(digest(raw_file) == row["sha256"], f"Raw hash {seed}")
            raw = json.loads(raw_file.read_text())
            require(raw["case"] == row["case"], f"Raw assignment {seed}")
            left, right = raw["original"], raw["alternative"]
            require((left is None) == (right is None) == (row["x"] is None), f"Missing arm {seed}")
            if left:
                require(left["event"] == right["event"] and left["pivot"] == right["pivot"], f"Branch identity {seed}")
                difference = np.subtract(right["gains"], left["gains"]).tolist()
                require(row["delta"] == difference and row["x"] == left["event"]["x"], f"Raw gain or input {seed}")
        if row["x"] is None:
            require(row["delta"] is None, f"Missing observation {seed}")
        else:
            x = np.asarray(row["x"])
            require(x.shape == (13,) and np.isfinite(x).all(), f"Input width {seed}")
            require(first <= row["step"] - 101 <= 75 and row["direction"] in range(5), f"Time or direction {seed}")
            require(abs(x[-3] * 100 - (row["step"] - 101)) < 1e-6 and -1 <= x[-2] <= 0, f"Time or margin {seed}")
            require(np.asarray(row["delta"]).shape == (3, 2), f"Point deltas {seed}")
    return [rows[seed] for seed in sorted(rows)]


def outcome(row):
    own, opponent = row["delta"][-1]
    return own - opponent


def audit(study, raw):
    train_file = study / "trainingskarten.jsonl.gz"
    test_file = study / "pruefkarten.jsonl.gz"
    model_file = study / "folgemodell.json"
    model = json.loads(model_file.read_text())
    result = json.loads((study / "pruefung.json").read_text())
    require(digest(model_file) == result["frozen_estimator"] and digest(test_file) == result["map_archive"], "Test inputs")
    require(digest(train_file) == model["train_data"] and digest(study / "lernen.py") == model["fit_code"], "Fit inputs")
    for rel, original_sha in model["sources"].items():
        require(digest(study.parent / rel) == original_sha, f"Frozen source {rel}")
    exclusion = study / "trainingsausfall.json"
    require(digest(exclusion) == "7c0c09ee16ac33d2c6724b4649a9df5575065c9f917c6c2223222724be8f9f41",
            "Technical training exclusion")
    failed = json.loads(exclusion.read_text())
    require((failed["seed"], failed["team"], failed["opponent"], failed["arm"]) == (160390154, 0, "kaggle3", "original")
            and model["technical_exclusion"] == [160390154] and model["planned_maps"] == 160, "Excluded map identity")
    if raw:
        require(not (raw / "train/160390154.json").exists(), "Unexpected scoring row for excluded training map")
        for log in failed["records"]:
            require(digest(raw / log["file"]) == log["sha256"], "Original opponent failure log")
    train = check_panel(train_file, 160390000, 160, raw / "train" if raw else None, omissions=(160390154,))
    test = check_panel(test_file, 160391000, 80, raw / "test" if raw else None)
    actual = [r for r in train if r["x"] is not None]
    require(model["n_proposals"] == len(actual) and model["n_maps"] == len(train), "Train sample")
    require(model["lambda_ridge"] == 32 and model["threshold"] == 1, "Frozen controls")
    x = np.array([r["x"] for r in actual])
    target = np.array([outcome(r) for r in actual])
    clipped = np.clip(target, -30, 30)
    means, scales = x.mean(axis=0), x.std(axis=0)
    scales[scales < 1e-7] = 1
    np.testing.assert_allclose(means, model["mean"])
    np.testing.assert_allclose(scales, model["scale"])
    require(model["clipped_targets"] == int((target != clipped).sum()), "Clipped labels")
    beta = np.array(model["coefficients"])
    z = (x - means) / scales
    residual = z @ beta + model["intercept"] - clipped
    # Check the original coefficients by first-order optimality without fitting a new model.
    np.testing.assert_allclose(z.T @ residual + 32 * beta, 0, atol=1e-8)
    np.testing.assert_allclose(residual.sum(), 0, atol=1e-8)
    decisions = []
    effects = np.zeros((len(test), 2))
    for i, row in enumerate(test):
        if row["x"] is None:
            continue
        prediction = model["intercept"] + sum(
            coefficient * (value - average) / spread
            for coefficient, value, average, spread in zip(beta, row["x"], means, scales)
        )
        accept = bool(prediction >= 1)
        np.testing.assert_allclose(prediction, row["prediction"], atol=1e-10)
        require(accept == row["accept"], f"Threshold decision {row['case'][0]}")
        decisions.append(accept)
        if accept:
            effects[i, 0] = outcome(row)
        else:
            effects[i, 1] = -outcome(row)
    require([sum(decisions), len(decisions) - sum(decisions)] == [result["accepted"], result["rejected"]], "Decision counts")
    require(result["maps"] == 80 and result["proposals"] == len(decisions)
            and result["no_proposal"] == 80 - len(decisions), "Unobserved opportunities")
    for rival in ("solution92", "kaggle3"):
        subset = [i for i, row in enumerate(test) if row["case"][2] == rival]
        np.testing.assert_allclose(effects[subset].mean(axis=0), result["descriptive_by_opponent"][rival], atol=1e-12)
    rng = np.random.default_rng(231115)
    means_per_draw = np.empty((20000, 2))
    for i in range(len(means_per_draw)):
        multiplicity = np.bincount(rng.choice(80, 80), minlength=80)
        means_per_draw[i] = multiplicity @ effects / 80
    ci = np.quantile(means_per_draw, [.025, .975], axis=0)
    gains = {}
    for j, key in enumerate(("versus_v16", "versus_always")):
        m = result["gains"][key]
        np.testing.assert_allclose([m["total"], m["mean"], *m["ci95"]],
                                   [effects[:, j].sum(), effects[:, j].mean(), *ci[:, j]])
        gains[key] = m
    gates = dict(training=len(actual) >= 40, accepted=sum(decisions) >= 10,
                 rejected=len(decisions) - sum(decisions) >= 10, v16=bool(ci[0, 0] > 0),
                 instant=bool(ci[0, 1] > 0))
    require(result["gates"] == gates and result["eligible"] == all(gates.values()), "Admission decision")
    return dict(verified=True, checked_original_game_records=239 if raw else 0, train_maps=159, test_maps=80,
                technical_training_exclusion=160390154,
                train_proposals=len(actual), test_proposals=len(decisions), accepted=sum(decisions),
                rejected=len(decisions) - sum(decisions), gains=gains, gates=gates,
                eligible=all(gates.values()), model_sha256=digest(model_file), archive_sha256=digest(test_file))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("study", type=Path)
    p.add_argument("--raw", type=Path, help="Directory containing the 160 train and 80 test original paired traces")
    a = p.parse_args()
    print(json.dumps(audit(a.study, a.raw), indent=2))
