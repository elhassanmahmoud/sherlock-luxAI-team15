"""Read the two Sherlock DAgger archives. Example: python history.py REPO LOCAL_IMITATION RESULTS.json."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np


SHAPE = (6, 3, 4, 10, 4)
GROUPS = int(np.prod(SHAPE))
DELTA = np.array([(0, 0), (0, -1), (1, 0), (0, 1), (-1, 0), (0, 0)])
RANGES = {"original": (range(7271000, 7271032), range(7271032, 7271040)),
          "dagger": (range(7272000, 7272120), range(7272200, 7272224))}
DIRECTIONS = ("kaggle3", "solution92", "v14")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index(root, local):
    files = []
    for name, (train, val) in RANGES.items():
        if name == "original":
            source = root / "experiments/analysis/combat_advice_20261115/v14_advice_audit.json"
            raw = json.loads(source.read_text())["map_sides"]
            rows = [{**r["metadata"], "sha256": r["input_sha256"]} for r in raw]
            dirname = "final_20261115_v14_advice"
        else:
            source = root / "experiments/analysis/movement_dagger_20261115/corpus.json"
            rows = json.loads(source.read_text())["games"]
            dirname = "final_20261115_movement_dagger"
        keys = {(int(r["seed"]), r["side"]): r for r in rows}
        if len(keys) != len(rows) or set(keys) != {(s, p) for s in (*train, *val) for p in ("player_0", "player_1")}:
            raise ValueError(f"Incomplete map-seat roster in {source}")
        for (seed, side), r in sorted(keys.items()):
            path = local / dirname / f'g{seed}_{side}_{r["opponent"]}.npz'
            if r["opponent"] not in DIRECTIONS or sha(path) != r["sha256"]:
                raise ValueError(f"Archive changed or unexpected opponent {path}")
            files.append((name, seed in train, seed, side, r["opponent"], path))
    return files


def extract(name, seed, side, opponent, path):
    with np.load(path, allow_pickle=False) as z:
        meta = json.loads(z["meta"].item())
        if [meta[k] for k in ("seed", "side", "opponent")] != [seed, side, opponent]:
            raise ValueError(f"Mismatched identity in {path}")
        step = z["global_step"][z["step"]].astype(int)
        ms = z["mstep"]
        uid = z["uid"].astype(int)
        pos = z["pos"].astype(int)
        base = z["base_act"].astype(int)
        played = base if name == "original" else z["played_act"].astype(int)
        y = z["act"].astype(int)
        f = z["feats"].astype(np.float32)
    n = len(step)
    if not np.array_equal(step % 101, ms) or np.any((ms == 0) | (step > 302) | (step < 1)):
        raise ValueError("Unexpected match steps")
    if np.any((uid < 0) | (uid >= 16)) or np.unique(step * 16 + uid).size != n:
        raise ValueError("Invalid unit or duplicate time/UID")
    if np.any((np.stack((played, y, base)) < 0) | (np.stack((played, y, base)) > 5)):
        raise ValueError("Unexpected action encoding")
    # Lookup can refer only to the previous step in this one map/seat file, with the same UID.
    lookup = np.full((303, 16), -1, int)
    lookup[step, uid] = np.arange(n)
    prev = lookup[step - 1, uid]
    matched = (prev >= 0) & (ms > 1)
    idx = np.flatnonzero(matched)
    prev = prev[idx]
    away = pos[idx].any(1) & pos[prev].any(1)
    idx, prev = idx[away], prev[away]
    displacement = pos[idx] - pos[prev]
    valid = (displacement == 0).all(1) | (displacement == DELTA[played[prev]]).all(1)
    idx, prev = idx[valid], prev[valid]
    if not np.array_equal(step[idx], step[prev] + 1) or not np.array_equal(ms[idx], ms[prev] + 1):
        raise ValueError("Cross-match history")
    f = f[idx]
    # FEATURE_NAMES: 2=self_energy, 3=self_low_energy, 7=cfg_sap_cost,
    # 30,31,33=assigned_dx/dy/exists, 34=on_point, 38=redundant_here.
    energy, sap = np.rint(f[:, 2] * 400), np.rint(f[:, 7] * 50)
    egroup = np.select([f[:, 3] > 0.5, energy < sap, energy < 2 * sap], [0, 1, 2], 3)
    role = 2 * (f[:, 34] > 0.5).astype(int) + (f[:, 38] > 0.5)
    goal = np.where(f[:, 33] > 0.5, (1 + np.sign(f[:, 30])) * 3 + 1 + np.sign(f[:, 31]), 9).astype(int)
    g = np.ravel_multi_index((base[idx], step[idx] // 101, role, goal, egroup), SHAPE)
    audit = dict(archive_rows=n, no_consecutive_live_uid=int(n - matched.sum()),
                 spawn_excluded=int((~away).sum()), motion_inconsistent=int((~valid).sum()),
                 kept=len(idx), previous_actual_different_from_v14=int((played[prev] != base[prev]).sum()))
    return g, played[prev], base[idx], y[idx], audit


def scores(y, prev, v14, pb, ph):
    pred_b, pred_h = pb.argmax(1), ph.argmax(1)
    b, h = pred_b == y, pred_h == y
    move, step = y < 5, (y > 0) & (y < 5)
    both_move = move & (v14 < 5)
    ids = np.arange(len(y))
    return dict(rows=len(y), basic_right=int(b.sum()), history_right=int(h.sum()),
                corrected=int((~b & h).sum()), damaged=int((b & ~h).sum()), v14_right=int((v14 == y).sum()),
                previous_right=int((prev == y).sum()), teacher_moves=int(move.sum()),
                basic_move_right=int((b & move).sum()), history_move_right=int((h & move).sum()),
                teacher_moves_without_stay=int(step.sum()), basic_nonstay_right=int((b & step).sum()),
                history_nonstay_right=int((h & step).sum()), both_movement=int(both_move.sum()),
                basic_both_movement_right=int((b & both_move).sum()), history_both_movement_right=int((h & both_move).sum()),
                loss_basic_sum=float(-np.log(pb[ids, y]).sum()), loss_history_sum=float(-np.log(ph[ids, y]).sum()))


def report(maps):
    keys = sorted(maps)
    tot = sum((Counter(maps[k]) for k in keys), Counter())
    n = np.array([maps[k]["rows"] for k in keys])
    g = np.array([maps[k]["history_right"] - maps[k]["basic_right"] for k in keys])
    loss = np.array([maps[k]["loss_history_sum"] - maps[k]["loss_basic_sum"] for k in keys])
    rng = np.random.default_rng(2711)
    draws = rng.integers(0, len(keys), (10000, len(keys)))
    den = n[draws].sum(axis=1)
    return dict(maps=len(keys), **tot, delta_accuracy_pp=float(100 * g.sum() / n.sum()),
                delta_accuracy_pp_ci95=np.quantile(100 * g[draws].sum(1) / den, [0.025, 0.975]).tolist(),
                delta_loss_nats=float(loss.sum() / n.sum()),
                delta_loss_ci95=np.quantile(loss[draws].sum(1) / den, [0.025, 0.975]).tolist(),
                maps_higher_accuracy=int((g > 0).sum()), maps_lower_accuracy=int((g < 0).sum()),
                maps_lower_loss=int((loss < 0).sum()), maps_higher_loss=int((loss > 0).sum()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("repo", "local", "output"):
        parser.add_argument(arg, type=Path)
    a = parser.parse_args()
    files = index(a.repo, a.local)
    extcnt = np.zeros((GROUPS, 6, 6), dtype=np.int64)
    audits = defaultdict(Counter)
    preds = defaultdict(lambda: defaultdict(Counter))
    map_records = []
    for name, train, seed, side, opp, path in files:
        if train:
            g, last, base, y, audit = extract(name, seed, side, opp, path)
            np.add.at(extcnt, (g, last, y), 1)
            audits[name + "/train"].update(audit)
    cnt = extcnt.sum(axis=1)
    by_act = cnt.reshape(6, -1, 6).sum(1)
    prior = (by_act + .5) / (by_act.sum(1, keepdims=True) + 3)
    pb = (cnt + 12 * np.repeat(prior, GROUPS // 6, axis=0)) / (cnt.sum(1, keepdims=True) + 12)
    ph = (extcnt + 24 * pb[:, None, :]) / (extcnt.sum(2, keepdims=True) + 24)
    if not np.allclose(ph.sum(2), 1) or not np.allclose(pb.sum(1), 1):
        raise ValueError("Invalid conditional probabilities")
    for name, train, seed, side, opp, path in files:
        if not train:
            g, last, base, y, audit = extract(name, seed, side, opp, path)
            audits[name + "/validation"].update(audit)
            stats = scores(y, last, base, pb[g], ph[g, last])
            map_records.append(dict(cohort=name, seed=seed, side=side, opponent=opp, **stats))
            for group in ("all", name, name + "/" + opp, "opponent/" + opp):
                preds[group][seed].update(stats)
    out = dict(source_sha256=sha(Path(__file__)), audits=dict(audits),
               held_out_tables={key:report(maps) for key,maps in preds.items()},
               held_out_game_seats=map_records, verified_archives=len(files))
    with a.output.open("x") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")
    for group, r in sorted(out["held_out_tables"].items()):
        print(group, r["rows"], r["basic_right"], r["history_right"], r["corrected"],r["damaged"],
              round(r["delta_accuracy_pp"], 3), round(r["delta_loss_nats"], 4), r["maps_higher_accuracy"],
              r["maps_lower_loss"], r["maps"])
    print(out["audits"])


if __name__ == "__main__":
    main()
