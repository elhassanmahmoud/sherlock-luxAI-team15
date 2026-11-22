"""Bind one immutable nominee using completed development panels only."""
import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
CONTROL="5b200d5a7fadfffb86ccb6c3e74324e49fe4c1e27510581ae810e6a452b2a67b"


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def choose(out):
    control=PARENT/"kontrollkopf"
    scout=PARENT/"kundschafter"
    spec=importlib.util.spec_from_file_location("control_screen",control/"auswertung.py")
    audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
    control_report=audit.summarize(control/"partien.jsonl")
    if not control_report["passed"] or control_report!=json.loads((control/"ergebnis.json").read_text()):
        raise ValueError("Control screen incomplete or not qualified")
    panel=json.loads((scout/"frisch.json").read_text())
    if (panel["phase"]!="frisch" or panel["source_sha256"]!=sha(scout/"kandidat.py")
            or panel["rules_sha256"]!=sha(scout/"PLAN.md")):
        raise ValueError("Scout development source mismatch")
    rows=panel["rows"]
    keys={(s,p,o,a) for s in range(94651000,94651016) for p in ("player_0","player_1")
          for o in ("solution92","kaggle3","v16") for a in ("v16","scout") if a=="scout" or o!="v16"}
    if (len(rows)!=160 or {tuple(r[k] for k in ("seed","side","opponent","arm")) for r in rows}!=keys
            or any(r["steps"]!=303 or r["our_wins"]+r["opp_wins"]!=3 or r["game_win"]!=int(r["our_wins"]>=2) for r in rows)):
        raise ValueError("Incomplete or invalid scout panel")
    def count(arm,opponent,k):
        return sum(r[k] for r in rows if r["arm"]==arm and r["opponent"]==opponent)
    tests=dict(solution_more_games=count("scout","solution92","game_win")>count("v16","solution92","game_win"),
               kaggle_at_least_games=count("scout","kaggle3","game_win")>=count("v16","kaggle3","game_win"),
               kaggle_at_least_matches=count("scout","kaggle3","our_wins")>=count("v16","kaggle3","our_wins"),
               direct_at_least_half=count("scout","v16","game_win")>=16)
    passed=all(tests.values())
    record=dict(name="scout" if passed else "kontrolle",candidate_sha256=sha(scout/"kandidat.py") if passed else CONTROL,
                control_passed=True,scout_passed=passed,scout_gates=tests,
                control_panel_sha256=sha(control/"partien.jsonl"),scout_panel_sha256=sha(scout/"frisch.json"),
                control_plan_sha256=sha(control/"PLAN.md"),scout_plan_sha256=sha(scout/"PLAN.md"))
    content=json.dumps(record,indent=2)+"\n"
    if out.exists():
        if out.read_text()!=content: raise ValueError("Different existing nomination")
    else:
        with out.open("x") as f: f.write(content)
    print(content)


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("destination",type=Path)
    choose(ap.parse_args().destination)
