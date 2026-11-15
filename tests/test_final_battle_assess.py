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


R2_MODEL = "23fa6208d76e81940916388b9ee56c1d290693e8febfa53622442b64b0d33f96"
R3_MODEL = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
R4_EXAMPLE = "9" * 64
MOVEMENT_PANELS = {"distill": (7273000, 7273100, 7273200),
                   "previous_enemy": (7275000, 7275100, 7275200)}


def movement_fixture(tmp_path, protocol, *, r2_extra_win=False, model=None, shift=0):
    """Write fully paired synthetic selection runs with intentional swaps of the winning seat."""
    model = model or (R3_MODEL if protocol == "distill" else R4_EXAMPLE)
    first, confirm_first, confirm_direct = MOVEMENT_PANELS[protocol]
    first += shift

    def make_run(dirname, role, start, count, opponents, winner):
        base = role == "v14"
        name = "v14" if base else "selective_movement"
        path = write_run(tmp_path / dirname, name, start, count, opponents, winner,
                         model=R2_MODEL if role == "control" else model)
        mf = path / "manifest.json"
        manifest = json.loads(mf.read_text())
        for file, digest in audit.MOVEMENT_SOURCES[protocol].items():
            if not base or file == "scripts/final_battle_compare.py":
                manifest["sources"][file] = digest
        mf.write_text(json.dumps(manifest))
        return path

    def lost(*args):
        return False

    def candidate(seed, opponent, seat):
        return opponent == "v14" or seat == "player_0"

    def control(seed, opponent, seat):
        return seat == "player_1" or (r2_extra_win and seed == first and opponent == "kaggle3")

    reference = make_run("selection_v14", "v14", first, 16, EXT, lost)
    study = make_run("selection_new", "candidate", first, 16, (*EXT, "v14"), candidate)
    r2 = make_run("selection_r2", "control", first, 16, EXT, control)
    args = SimpleNamespace(protocol=protocol, stage="screen", model_sha256=model,
                           screen_first=first, screen_maps=16, screen_direct_first=None,
                           confirm_first=confirm_first, confirm_maps=60, confirm_direct_first=confirm_direct,
                           reference=reference, candidate=study, direct=None, selection_control=r2,
                           screen_reference=reference, screen_candidate=study, screen_direct=None)
    return args, make_run


def use_movement_confirmation(args, make_run):
    args.stage = "confirm"
    args.reference = make_run("confirm_v14", "v14", args.confirm_first, 60, EXT, lambda *_: False)
    args.candidate = make_run("confirm_new", "candidate", args.confirm_first, 60, EXT, lambda *_: True)
    args.direct = make_run("confirm_direct", "candidate", args.confirm_direct_first, 60,
                           ("v14",), lambda *_: True)


@pytest.mark.parametrize("protocol", ["distill", "previous_enemy"])
def test_new_movement_screen_preserves_r2_tie_and_map_pairs_in_confirmation(tmp_path, protocol):
    args, make_run = movement_fixture(tmp_path, protocol)
    screen = audit.assess(args)
    vs_r2 = screen["selection_control"]
    assert (vs_r2["candidate_wins"], vs_r2["r2_wins"], vs_r2["net_wins"]) == (32, 32, 0)
    # Both seats swap winners on every map, but the paired per-map difference never changes.
    assert list(vs_r2["difference_ci95"]) == [0, 0]
    assert screen["gates"]["external_at_least_r2"] and screen["game_gates_pass"]

    use_movement_confirmation(args, make_run)
    result = audit.assess(args)
    assert result["selection"]["selection_control"] == vs_r2
    assert result["selection"]["gates"]["external_at_least_r2"] and result["game_gates_pass"]


@pytest.mark.parametrize("protocol", ["distill", "previous_enemy"])
def test_new_movement_screen_refuses_confirmation_one_external_game_below_r2(tmp_path, protocol):
    args, make_run = movement_fixture(tmp_path, protocol, r2_extra_win=True)
    report = audit.assess(args)
    assert report["selection_control"]["net_wins"] == -1
    assert not report["gates"]["external_at_least_r2"] and not report["game_gates_pass"]
    assert all(value for k, value in report["gates"].items() if k != "external_at_least_r2")
    use_movement_confirmation(args, make_run)
    with pytest.raises(ValueError):
        audit.assess(args)


@pytest.mark.parametrize("model", [audit.FIRST_MOVEMENT_MODEL, R2_MODEL, R3_MODEL])
def test_previous_enemy_rejects_an_older_checkpoint_even_if_run_matches_requested_hash(tmp_path, model):
    args, _ = movement_fixture(tmp_path, "previous_enemy", model=model)
    with pytest.raises(ValueError):
        audit.assess(args)


@pytest.mark.parametrize("fault", ["missing_control", "r2_model", "rehashed_control_rows", "registered_sources", "panel"])
def test_learning_selection_requires_actual_control_and_registered_inputs(tmp_path, fault):
    args, _ = movement_fixture(tmp_path, "distill", shift=int(fault == "panel"))
    if fault == "missing_control":
        args.selection_control = None
    elif fault == "r2_model":
        mf = args.selection_control / "manifest.json"
        manifest = json.loads(mf.read_text())
        manifest["model"] = R3_MODEL
        mf.write_text(json.dumps(manifest))
    elif fault == "rehashed_control_rows":
        rows = [json.loads(line) for line in (args.selection_control / "games.jsonl").read_text().splitlines()]
        rows[0]["seed"] += 10000
        save_rows(args.selection_control, rows)
    elif fault == "registered_sources":
        # Two agreeing but unregistered advisor implementations must still be rejected.
        for d in (args.selection_control, args.candidate):
            mf = d / "manifest.json"
            manifest = json.loads(mf.read_text())
            manifest["sources"]["scripts/selective_advice_agent.py"] = "0" * 64
            mf.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        audit.assess(args)


def test_previous_enemy_requires_explicit_training_hash(tmp_path):
    args, _ = movement_fixture(tmp_path, "previous_enemy")
    args.model_sha256 = None
    with pytest.raises(ValueError, match="model-sha256"):
        audit.assess(args)
