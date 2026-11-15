from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from scripts import final_battle_assess as audit


EXT = ("kaggle3", "solution92")
MODEL = "b" * 64


def write_run(directory, name, first, count, opponents, winner, model=MODEL):
    directory.mkdir()
    sources = {p: "a" * 64 for p in audit.CORE}
    if name == "stack_reserve":
        sources["scripts/stack_reserve.py"] = audit.STACK_RESERVE_SHA
        sources["scripts/combat_teacher_counterfactual.py"] = "c" * 64
        model = None
    elif name != "v14":
        sources["scripts/selective_advice_agent.py"] = "c" * 64
        for path in ("combat_teacher_counterfactual.py", "collect_combat_advice.py", "imitate.py"):
            sources["scripts/" + path] = "c" * 64
    if "kaggle3" in opponents:
        for path in ("agent/base.py", "agent/agent.py"):
            sources[audit.KAGGLE + path] = "d" * 64
        sources.update({audit.KAGGLE + k: v for k,v in audit.WEIGHT_SHA256.items()})
    m = dict(candidate=name, first=first, maps=count, opponents=opponents, weights=audit.V14_SHA,
             model=None if name == "v14" else model, sources=sources,
             engine={k:"e"*64 for k in ("params.py", "env.py", "wrappers.py")})
    (directory / "manifest.json").write_text(json.dumps(m))
    rows = []
    for seed in range(first, first+count):
        for opp in opponents:
            for side in audit.SEATS:
                won = int(winner(seed, opp, side))
                rows.append(dict(candidate=name, seed=seed, side=side, opponent=opp, steps=303,
                                 result=float(won), wins=2 if won else 1, losses=1 if won else 2))
    save_rows(directory, rows)
    return directory


def save_rows(directory, rows):
    raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
    summary = {}
    for row in rows:
        group = summary.setdefault(row["opponent"], dict(played=0, wins=0, matches=0))
        group["played"] += 1
        group["wins"] += row["result"]
        group["matches"] += row["wins"]
    (directory / "games.jsonl").write_bytes(raw)
    (directory / "completed.json").write_text(json.dumps(dict(rows_sha256=sha256(raw).hexdigest(), summary=summary)))


def test_complete_screen_and_confirmation_with_separate_direct_blocks(tmp_path):
    def before(seed, opp, side): return False
    def after(seed, opp, side): return opp == "v14" or side == "player_1"
    name = "selective_movement"
    args = SimpleNamespace(stage="confirm", model_sha256=MODEL, screen_first=10, screen_maps=2,
                           screen_direct_first=None, confirm_first=20, confirm_maps=3, confirm_direct_first=30,
                           screen_reference=write_run(tmp_path/"s_ref","v14",10,2,EXT,before),
                           screen_candidate=write_run(tmp_path/"s_new",name,10,2,(*EXT,"v14"),after),
                           screen_direct=None, reference=write_run(tmp_path/"c_ref","v14",20,3,EXT,before),
                           candidate=write_run(tmp_path/"c_new",name,20,3,EXT,after),
                           direct=write_run(tmp_path/"c_duel",name,30,3,("v14",),after))
    report = audit.assess(args)
    assert report["selection"]["game_gates_pass"] and report["game_gates_pass"]
    assert report["external"]["difference_ci95"] == [.5, .5]
    assert report["direct"]["wins"] == 6 and report["direct"]["winrate_ci95"] == [1, 1]
    assert report["by_opponent"]["solution92"]["gained"] == 3 and report["by_opponent"]["solution92"]["lost"] == 0
    args.confirm_direct_first = 10
    with pytest.raises(ValueError, match="overlap"):
        audit.assess(args)
    args.confirm_direct_first = 30
    m = json.loads((args.direct / "manifest.json").read_text())
    m["model"] = "1" * 64
    (args.direct / "manifest.json").write_text(json.dumps(m))
    with pytest.raises(ValueError, match="checkpoint"):
        audit.assess(args)


def test_joint_bootstrap_keeps_both_opponents_and_seats_of_each_map(tmp_path):
    def before(seed, opp, side): return (opp == "kaggle3") == (seed % 2 == 0)
    def after(seed, opp, side): return side == "player_0" if opp == "v14" else not before(seed, opp, side)
    ref = write_run(tmp_path/"ref","v14",0,4,EXT,before)
    cand = write_run(tmp_path/"new","selective_movement",0,4,EXT,after)
    direct = write_run(tmp_path/"direct","selective_movement",100,4,("v14",),after)
    p = audit.load_phase(ref, cand, direct, range(4), range(100,104))
    report = audit.summarize(p, "screen")
    assert report["by_opponent"]["kaggle3"]["difference_ci95"] == [-1, 1]
    assert report["external"]["difference_ci95"] == [0, 0]
    assert report["by_opponent"]["kaggle3"]["gained"] == report["by_opponent"]["kaggle3"]["lost"] == 4
    assert report["direct"]["winrate_ci95"] == [.5, .5] and not report["gates"]["direct_majority"]
    assert not report["game_gates_pass"]


@pytest.mark.parametrize("fault", ["unclosed", "hash", "duplicate", "missing_seat", "bad_result",
                                    "summary", "engine", "weights", "rival_weights", "adapter"])
def test_rejects_incomplete_or_incompatible_runs(tmp_path, fault):
    fn = lambda *args: True
    ref = write_run(tmp_path/"ref", "v14", 0, 2, EXT, fn)
    cand = write_run(tmp_path/"new", "selective_movement", 0, 2, (*EXT,"v14"), fn)
    closed = cand / "completed.json"
    rowsfile = cand / "games.jsonl"
    if fault == "unclosed":
        closed.unlink()
    elif fault == "hash":
        rowsfile.write_bytes(rowsfile.read_bytes() + b"\n")
    elif fault in ("duplicate", "missing_seat", "bad_result"):
        rows = [json.loads(line) for line in rowsfile.read_text().splitlines()]
        if fault == "duplicate": rows[-1] = rows[0]
        if fault == "missing_seat": rows.pop()
        if fault == "bad_result": rows[0]["result"] = 0
        save_rows(cand, rows)
    elif fault == "summary":
        c = json.loads(closed.read_text())
        c["summary"]["v14"]["wins"] = 0
        closed.write_text(json.dumps(c))
    else:
        manifest = cand / "manifest.json"
        m = json.loads(manifest.read_text())
        if fault == "engine": m["engine"]["params.py"] = "1"*64
        if fault == "weights": m["weights"] = "1"*64
        if fault == "adapter": m["sources"]["scripts/kaggle3_opponent.py"] = "1"*64
        if fault == "rival_weights": m["sources"][audit.KAGGLE + next(iter(audit.WEIGHT_SHA256))] = "1"*64
        manifest.write_text(json.dumps(m))
    with pytest.raises((OSError, ValueError)):
        audit.load_phase(ref, cand, None, range(2), range(2))



def test_stack_protocol_requires_registered_rule_and_consistent_correction_helper(tmp_path):
    def lost(*_): return False
    def won(*_): return True
    name = "stack_reserve"
    args = SimpleNamespace(protocol=name, stage="confirm", model_sha256=None,
                           screen_first=10, screen_maps=2, screen_direct_first=None,
                           confirm_first=20, confirm_maps=2, confirm_direct_first=30,
                           screen_reference=write_run(tmp_path/"s_ref","v14",10,2,EXT,lost),
                           screen_candidate=write_run(tmp_path/"s_new",name,10,2,(*EXT,"v14"),won),
                           screen_direct=None, reference=write_run(tmp_path/"c_ref","v14",20,2,EXT,lost),
                           candidate=write_run(tmp_path/"c_new",name,20,2,EXT,won),
                           direct=write_run(tmp_path/"c_direct",name,30,2,("v14",),won))
    result = audit.assess(args)
    assert result["policy_sha256"] == result["selection"]["policy_sha256"] == audit.STACK_RESERVE_SHA
    assert result["model"] is None and result["game_gates_pass"]
    args.protocol = "dagger"
    with pytest.raises(ValueError):
        audit.assess(args)
    args.protocol = name
    path = args.direct / "manifest.json"
    original = json.loads(path.read_text())
    for field, value, reason in (
            ("scripts/stack_reserve.py", "f"*64, "policy SHA"),
            ("scripts/combat_teacher_counterfactual.py", None, "Missing source"),
            ("scripts/combat_teacher_counterfactual.py", "f"*64, "implementation")):
        modified = {**original, "sources": dict(original["sources"])}
        if value is None:
            del modified["sources"][field]
        else:
            modified["sources"][field] = value
        path.write_text(json.dumps(modified))
        with pytest.raises(ValueError, match=reason):
            audit.assess(args)
    path.write_text(json.dumps({**original, "model": MODEL}))
    with pytest.raises(ValueError, match="checkpoint"):
        audit.assess(args)
