"""Prüft die addierte öffentliche Punktschranke für ein vollständig geklärtes erstes Reliktpaar."""
import argparse
import gzip
import hashlib
from importlib.metadata import distribution
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent / "solution/frueh/wissenssprung.json.gz"
ENV_SHA = "cc1b2657e1b56df21ec890bc78eab75539575e16529b8b8e5a1e8d1b4865a469"
STATE_SHA = "8b658ed767ff0fd9f9cfbec681d57157f2702826979e611fba392fb183d503d5"
ARCHIVE_DIGEST = "e1dc834220e8b6aebaf1dae91b8b37f85f5456211e627a3f6a2d7b8b28300319"
CORNERS = frozenset((0, 23*24+23))


def joint_cap(confirmed, unresolved):
    possible = set(confirmed) | set(unresolved)
    return len(possible) + len(possible & CORNERS)


def inspect(frames):
    opening = frames[0]
    pair = opening["remembered_relic"]
    if not (opening["match"] == 2 and opening["turn"] == 0 and len(pair) == 2):
        raise ValueError("Erwartet bereits zu Matchbeginn ein bekanntes Paar")
    x,y = pair[0]
    if pair[1] != [23-y,23-x]:
        raise ValueError("Reliktsymmetrie unklar")
    eligible, hits, opponent_only = [], [], []
    for prev, now in zip(frames,frames[1:]):
        if (prev["match"] != 2 or now["match"] != 2 or now["turn"] != prev["turn"]+1
                or not 50 <= now["turn"] <= 100):
            continue
        if (prev["remembered_relic"] != pair or now["remembered_relic"] != pair
                or prev["candidate_n"] != 0 or now["candidate_n"] != 0
                or prev["known"] != now["known"]):
            continue
        values = now["known"]
        if len(values) != len(set(values)):
            raise ValueError("Mehrdeutige Feldidentität")
        cap = joint_cap(values, ())
        gains=[b-a for a,b in zip(prev["public_points"],now["public_points"],strict=True)]
        if len(gains)!=2 or min(gains)<0:
            raise ValueError("Reset oder ungültiger Teamstand")
        t=now["turn"]
        eligible.append(t)
        if gains[1]>len(values):
            opponent_only.append(t)
        if sum(gains)>cap:
            hits.append({"turn":t, "scores_before":prev["public_points"], "scores_after":now["public_points"],
                         "gains":gains,"possible_fields":len(values),
                         "possible_corners":sorted(CORNERS.intersection(values)), "cap":cap})
    return {"eligible":len(eligible),"joint_count":len(hits),"joint_first":hits[0] if hits else None,
            "joint_turns":[r["turn"] for r in hits],"opponent_only_count":len(opponent_only),
            "opponent_only_first":opponent_only[0] if opponent_only else None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    local=distribution("luxai-s3")
    engine=Path(local.locate_file("luxai_s3/env.py"))
    state=Path(local.locate_file("luxai_s3/state.py"))
    if (local.version!="0.2.1" or hashlib.sha256(engine.read_bytes()).hexdigest()!=ENV_SHA
            or hashlib.sha256(state.read_bytes()).hexdigest()!=STATE_SHA):
        raise ValueError("Die gemessene Kurs-Engine wurde nicht gefunden")
    if (joint_cap({2,3},set())!=2 or joint_cap({0,2},{575,5})!=6
            or joint_cap({0,2},{0,2})!=3 or joint_cap(set(),{575})!=2):
        raise AssertionError("Obergrenzen an zwei Ecken oder bei offenen Feldern fehlerhaft")
    raw=ARCHIVE.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ARCHIVE_DIGEST:
        raise ValueError("Abweichendes Beobachtungsarchiv")
    inputs=json.loads(gzip.decompress(raw))
    data={arm:{s:inspect(r["frames"]) for s,r in games.items()} for arm,games in inputs.items()}
    output={"luxai_s3":local.version,"env_py_sha256":ENV_SHA,"state_py_sha256":STATE_SHA,"archive_sha256":hashlib.sha256(raw).hexdigest(),
            "thesis":"sum_public_gains_exceeds_single_solved_pair_capacity","arms":data}
    body=json.dumps(output,indent=2)+"\n"
    if args.out:args.out.write_text(body)
    else:print(body,end="")


if __name__=="__main__":
    main()
