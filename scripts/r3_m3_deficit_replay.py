"""Replay the 17 tied R3 games with original commands. No policy is loaded."""
import argparse
import base64
from collections import Counter
from hashlib import sha256
from importlib import metadata, util
import json
from pathlib import Path
import tarfile
import zlib

import numpy as np

from scripts.scoring import match_points_after_step

PARENT = Path("experiments/analysis/r3_v4_wl_20261115/solution_scope")
SOURCES = {
    "partien.tar.gz": "2584974de981b64b71d01f9d5728471660bea5d4cecff9c6bca6c1232b8e1ab4",
    "completed.json": "1f2e6d17128aee5dd3c3b67655a5dfe2d16b12c0ab8d716376b3d70a32d62321",
    "protocol.json": "303df3a969e608fbbf62ca1e9bf713240518a896f9b6ba4990ad2dff044e0ce9",
}
SEATS = ("player_0", "player_1")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def trigger(match_step, wins, points, own):
    return (tuple(wins) == (1, 1) and 50 <= match_step <= 100
            and points[own] < points[1 - own])


def original_commands(row):
    stored = row["orders"]
    shape = (303, 2, 16, 3)
    require(stored["format"] == "zlib-base64-int16le" and list(shape) == stored["shape"],
            "Unknown command layout")
    raw = zlib.decompress(base64.b64decode(stored["data"], validate=True))
    require(sha256(raw).hexdigest() == stored["raw_sha256"], "Command bytes differ")
    commands = np.frombuffer(raw, dtype="<i2").reshape(shape).astype("<i8")
    for n, field in [(202, "prefix_sha256"), (303, "commands_sha256")]:
        for team, seat in enumerate(SEATS):
            require(sha256(commands[:n, team].tobytes()).hexdigest() == row[field][seat],
                    f"Different original {seat} command sequence at step {n}")
    return commands


def archive(folder):
    for name, expected in SOURCES.items():
        require(sha256((folder / name).read_bytes()).hexdigest() == expected, f"Changed {name}")
    files = json.loads((folder / "completed.json").read_bytes())["files_sha256"]
    rows = {}
    with tarfile.open(folder / "partien.tar.gz") as stream:
        members = stream.getmembers()
        require(len(members) == len(files) == 61 and {f.name for f in members} == set(files),
                "Unexpected archive contents")
        for member in members:
            require(member.isfile(), "Non-file member")
            raw = stream.extractfile(member).read()
            require(sha256(raw).hexdigest() == files[member.name], "Changed archived game")
            row = json.loads(raw)
            key = (row["seed"], row["side"], row["arm"])
            require(key not in rows, "Duplicate archived seat and arm")
            rows[key] = row
    controls = [r for r in rows.values() if r["arm"] == "control"]
    require(Counter(r["sequence"] for r in controls) == {"WWL":29,"WLW":11,"WLL":4,"LWW":2},
            "All 46 original close controls are required")
    tied = [r for r in controls if r["matches"][0]["winner"] != r["matches"][1]["winner"]]
    require(len(tied) == 17, "Expected exactly 17 tied seats")
    return [(r, rows.get((r["seed"], r["side"], "switch"))) for r in tied]


def bind_engine(folder):
    protocol = json.loads((folder / "protocol.json").read_bytes())
    source = protocol["source"]["engine"]
    root = Path(util.find_spec("luxai_s3").origin).parent
    require({p.name:sha256(p.read_bytes()).hexdigest() for p in root.glob("*.py")} == source["lux_modules"],
            "Different Lux engine")
    for name in ("luxai-s3", "jax", "jaxlib", "numpy"):
        require(metadata.version(name) == source["versions"][name], f"Different {name} version")
    require(sha256(Path(__file__).with_name("scoring.py").read_bytes()).hexdigest()
            == protocol["files_sha256"]["scoring"], "Different terminal score measurement")


def replay(env, row, old_switch):
    commands = original_commands(row)
    seat = row["side"]
    team = SEATS.index(seat)
    obs, _ = env.reset(seed=row["seed"])
    first = None
    matches = []
    for step, orders in enumerate(commands):
        before = obs[seat]
        t = int(before["match_steps"])
        require(t == step % 101, "Unexpected public match clock")
        wins = before["team_wins"]
        points = before["team_points"]
        if first is None and trigger(t, wins, points, team):
            first = dict(global_step=step, match_step=t, points=int(points[team]),
                         opponent_points=int(points[1 - team]))
        obs, _, term, trunc, info = env.step(dict(zip(SEATS, orders, strict=True)))
        require(all((bool(term[s]) or bool(trunc[s])) == (step == 302) for s in SEATS),
                "Episode ended on a different step")
        after = obs[seat]
        award = np.asarray(after["team_wins"]) - np.asarray(wins)
        if t == 100:
            require(award.tolist() in ([1, 0], [0, 1]), "Missing official match award")
            scores = match_points_after_step(before, after, info).tolist()
            matches.append({"world_points":scores, "winner":SEATS[int(np.argmax(award))]})
        else:
            require(not np.any(award), "Unexpected match award")
    require(row["matches"] == matches, "Archived match scores or winners differ")
    won = sum(m["winner"] == seat for m in matches)
    scores = [sum(m["world_points"][i] for m in matches) for i in (team, 1 - team)]
    final = dict(result=int(won >= 2), wins=won, losses=3-won, points=scores[0],
                 opp_points=scores[1], steps=len(commands))
    require(row["game"] == final, "Archived totals differ")
    return dict(seed=row["seed"], side=seat, original_sequence=row["sequence"],
                original_game_win=bool(final["result"]), trigger=first, original_matches=matches,
                original_game=final, original_commands_sha256=row["commands_sha256"],
                earlier_switch_game_win=bool(old_switch["game"]["result"]) if old_switch else None)


def summarize(rows):
    result = {}
    for won, label in [(False, "old_losses"), (True, "protected_wins")]:
        group = [r for r in rows if r["original_game_win"] == won]
        result[label] = dict(total=len(group), triggered=sum(r["trigger"] is not None for r in group))
    times = sorted({r["trigger"]["match_step"] for r in rows if not r["original_game_win"] and r["trigger"]})
    result["cumulative_at_loss_triggers"] = []
    for t in times:
        already = [r for r in rows if r["trigger"] and r["trigger"]["match_step"] <= t]
        result["cumulative_at_loss_triggers"].append(dict(match_step=t,
            triggered_losses=sum(not r["original_game_win"] for r in already),
            triggered_protected_wins=sum(r["original_game_win"] for r in already)))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    require(not args.out.exists(), "Output already exists")
    folder = args.project / PARENT
    rows = archive(folder)
    bind_engine(folder)
    from luxai_s3.wrappers import LuxAIS3GymEnv
    env = LuxAIS3GymEnv(numpy_output=True)
    try:
        results = []
        for row, old_switch in sorted(rows, key=lambda item:(item[0]["seed"], item[0]["side"])):
            results.append(replay(env, row, old_switch))
            print(f"{len(results)}/17 verified", flush=True)
    finally:
        env.close()
    stats = summarize(results)
    require(stats["protected_wins"]["total"] == 13 and stats["old_losses"]["total"] == 4,
            "Different opportunities")
    result = dict(archive_sha256=SOURCES, script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                  original_frames_replayed=303*len(results), games=results, summary=stats)
    with args.out.open("x") as out:
        json.dump(result, out, indent=2, allow_nan=False)
        out.write("\n")
    print(json.dumps(stats), flush=True)


if __name__ == "__main__":
    main()
