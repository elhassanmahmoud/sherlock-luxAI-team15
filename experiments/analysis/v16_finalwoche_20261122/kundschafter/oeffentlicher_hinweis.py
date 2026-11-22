"""Prüft eine nach dem Experiment formulierte Suchhypothese, allein aus zwei öffentlichen Archivverläufen."""
import argparse
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "solution/frueh/wissenssprung.json.gz"


def public_evidence(frames):
    opening_pair = frames[0]["remembered_relic"]
    a, b = opening_pair
    assert [23 - a[1], 23 - a[0]] == b and frames[0]["match"] == 2 and frames[0]["turn"] == 0
    eligible = []
    for prev, cur in zip(frames, frames[1:]):
        if (prev["match"] != 2 or cur["match"] != 2 or not 50 <= cur["turn"] <= 100
                or cur["turn"] != prev["turn"] + 1):
            continue
        # Beide Zeitstempel tragen dasselbe, schon bei Matchbeginn bekannte alte Paar.
        if prev["remembered_relic"] != opening_pair or cur["remembered_relic"] != opening_pair:
            continue
        # Konservativ ganz ausgeklärte, unveränderte bekannte Zone.
        if prev["candidate_n"] or cur["candidate_n"] or prev["known"] != cur["known"]:
            continue
        prior, after = prev["public_points"][1], cur["public_points"][1]
        bound = len(cur["known"])  # beide Spieler teilen sich die Punktefelder
        assert after >= prior
        eligible.append({"turn": cur["turn"], "opponent_points_before": prior, "opponent_points_after": after,
                         "gain": after-prior, "bound": bound, "over": after-prior>bound})
    hits = [r for r in eligible if r["over"]]
    return {"eligible_turns": len(eligible), "flagged_turns": [r["turn"] for r in hits],
            "first_signal": hits[0] if hits else None}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    raw = json.loads(gzip.decompress(DATA.read_bytes()))
    result = {arm: {seed: public_evidence(report["frames"]) for seed, report in games.items()}
              for arm, games in raw.items()}
    body = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.write_text(body)
    else:
        print(body, end="")


if __name__ == "__main__":
    main()
