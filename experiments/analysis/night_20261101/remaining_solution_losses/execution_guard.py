"""One authorized, bounded replay of the six frozen V14 selection losses."""
import csv
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

GUARD = Path(__file__).parent
STATE = GUARD / "state.json"
state = json.loads(STATE.read_text())
ROOT = Path(state["root"])
OUT = Path(state["out"])
sys.path.insert(0, str(ROOT))
from scripts.early_curriculum_study import source_identity, hashes, THREAD_ENV


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save():
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def identity():
    return {"runtime": source_identity(ROOT, sys.executable, []),
            "inputs": hashes(state["identity"]["inputs"])}


def check():
    if identity() != state["identity"]:
        raise RuntimeError("Frozen HEAD/runtime/engine/weights/opponent/CSV changed")
    if "AC Power" not in subprocess.check_output(["pmset", "-g", "batt"], text=True):
        raise RuntimeError("AC power disconnected")


def no_other_model_jobs():
    output = subprocess.check_output(["ps", "-axo", "pid=,command="], text=True)
    found = []
    for line in output.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        pid, command = parts
        if re.search(r"(?:^|\s)-m\s+scripts\.(par_eval|par_losses|mechanism_probe|finetune|experiment|night_train_pilot)(?:\s|$)", command):
            if "python" in command.split()[0].lower():
                found.append({"pid": int(pid), "command": command})
    if found:
        raise RuntimeError(f"Another model job is active: {found}")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_matches(path):
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = {(int(g["seed"]), g["side"], m, t)
                for g in state["losses"] for m in range(3) for t in range(2)}
    keys = [(int(r["seed"]), r["side"], int(r["match"]), int(r["team"])) for r in rows]
    assert len(rows) == 36 and len(set(keys)) == 36 and set(keys) == expected
    assert all(r["opponent"] == "solution92" and int(r["point_counting_version"]) == 2 for r in rows)
    reproduced = []
    for original in state["losses"]:
        seed, side = int(original["seed"]), original["side"]
        us = int(side[-1])
        game = [r for r in rows if int(r["seed"]) == seed and r["side"] == side]
        assert all(int(r["is_us"]) == int(int(r["team"]) == us) for r in game)
        teams = [[r for r in game if int(r["team"]) == team] for team in (us, 1 - us)]
        points = [sum(int(r["points"]) for r in group) for group in teams]
        wins = [sum(int(r["won_match"]) for r in group) for group in teams]
        assert points == [int(original["our_points"]), int(original["opp_points"])], (seed, side, "points", points)
        assert wins == [int(original["our_wins"]), int(original["opp_wins"])], (seed, side, "wins", wins)
        result = 1.0 if wins[0] > wins[1] else 0.0 if wins[0] < wins[1] else 0.5
        assert result == float(original["result"])
        reproduced.append({"seed": seed, "side": side, "points": points, "wins": wins, "result": result})
    return {"rows": len(rows), "unique_keys": len(set(keys)), "sha256": sha(path), "reproduced_games": reproduced}


def validate_mechanisms(path):
    games = json.loads(path.read_text())
    keys = [(int(g["seed"]), g["side"]) for g in games]
    expected = {(int(g["seed"]), g["side"]): g for g in state["losses"]}
    assert len(games) == 6 and len(set(keys)) == 6 and set(keys) == set(expected)
    matches = []
    for game in games:
        key = (int(game["seed"]), game["side"])
        original = expected[key]
        assert game["wins"] == [int(original["our_wins"]), int(original["opp_wins"])], (key, game["wins"])
        assert len(game["matches"]) == 3
        assert {int(m["match"]) for m in game["matches"]} == {0, 1, 2}
        for match in game["matches"]:
            assert "us" in match and "opp" in match
            matches.append((*key, int(match["match"])))
    assert len(matches) == 18 and len(set(matches)) == 18
    return {"games": len(games), "match_objects": len(matches), "sha256": sha(path),
            "final_wins_reproduced": True,
            "output_limit": "No emitted total steps, match-end points or per-match winners; not independently verified for this tool."}


assert state["status"] == "preflight_complete_waiting_measurement_evidence_decision"
with (GUARD / "active.lock").open("x") as lock:
    lock.write(f"{os.getpid()}\n")
state.update(status="running", pid=os.getpid(), supervisor_command=[sys.executable, "-B", str(Path(__file__))],
             started_utc=stamp(), supervisor_sha256=sha(Path(__file__)),
             receipt_amendment={"authorized_by": "Root before first replay", "recorded_utc": stamp(),
               "scope": "No hook/instrumentation/source changes; CLI unchanged; max six games per tool, twelve total.",
               "validation": "CSV exact 6N keys, match points/wins and original game totals; JSON exact 3N match objects, game keys and original final wins.",
               "limitations": "Existing tools do not emit a total step counter; mechanism JSON also lacks end points/per-match winners. Do not claim these missing fields as independently checked. Original benchmark already has 303 steps/v2."})
save()
(OUT / "diagnosis_receipt.json").write_text(json.dumps(state, indent=2) + "\n")
overall_deadline = min(time.time() + 1200, datetime(2026, 11, 2, 4, 0, tzinfo=timezone.utc).timestamp())
state["hard_deadline_utc"] = datetime.fromtimestamp(overall_deadline, timezone.utc).isoformat()
child = None


def stop(sig, frame):
    raise SystemExit(f"Signal {sig}")


signal.signal(signal.SIGTERM, stop)
try:
    check()
    for module, filename, validator in (("scripts.par_losses", "matches.csv", validate_matches),
                                         ("scripts.mechanism_probe", "mechanisms.json", validate_mechanisms)):
        no_other_model_jobs()
        check()
        target = OUT / filename
        assert not target.exists()
        command = [sys.executable, "-B", "-m", module, "--weights", state["weights"],
                   "--games", state["games"], "--opponent", "solution92", "--which", "lost",
                   "--limit", "8", "--workers", "1", "--out", str(target)]
        record = {"module": module, "command": command, "started_utc": stamp(), "status": "running"}
        state["jobs"].append(record)
        save()
        print(f"{stamp()} START {module}", flush=True)
        deadline = min(time.time() + 600, overall_deadline)
        assert time.time() < deadline
        with (OUT / f"{module.rsplit('.', 1)[-1]}.log").open("x") as log:
            child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                     env={**os.environ, **THREAD_ENV}, start_new_session=True)
            record.update(pid=child.pid, process_group=child.pid)
            save()
            while child.poll() is None:
                check()
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError(f"Hard budget reached for {module}")
                try:
                    child.wait(timeout=min(10, remaining))
                except subprocess.TimeoutExpired:
                    pass
        record.update(exit_code=child.returncode, finished_utc=stamp())
        assert child.returncode == 0, (module, child.returncode)
        assert time.time() <= deadline, "Part finished after admitted deadline"
        check()
        record["validation"] = validator(target)
        record["status"] = "complete_and_reproduced"
        save()
        print(f"{stamp()} COMPLETE {module}; reproduction verified", flush=True)
        child = None
    check()
    assert time.time() <= overall_deadline
    state.update(status="complete_and_reproduced", finished_utc=stamp(), inputs_unchanged=True)
except BaseException as exc:
    state.update(status="stopped_incomplete_or_not_reproduced", error=f"{type(exc).__name__}: {exc}", finished_utc=stamp())
    raise
finally:
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
    save()
    (OUT / "diagnosis_receipt.json").write_text(json.dumps(state, indent=2) + "\n")
