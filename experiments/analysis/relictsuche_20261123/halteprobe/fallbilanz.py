"""Compare the new public decision to the 16 historically identified opportunities."""
from collections import Counter
import gzip
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def rows(path):
    return [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]


def main():
    history = rows(HERE.parent / "feldbindung/fenster.jsonl.gz")
    archive = rows(HERE / "mechanik_partien.jsonl.gz")
    earlier = {(r["seed"], r["side"], r["opponent"]): r for r in history}
    result = json.loads((HERE / "mechanik.json").read_bytes())
    current = {(r["seed"], r["team"], r["opp"]): r for r in result["cases"]}
    assert len(archive) == len(earlier) == len(current) == 56
    table = Counter()
    details = []
    for pair in archive:
        key = tuple(pair["key"])
        record, event = earlier[key], current[key]
        follow = pair["original"]["follow"]
        eligible = bool(follow and follow["eligible"])
        selected = bool(follow and follow["selected"])
        assert record["initial"] == event["initial"]
        assert [eligible, selected] == [event["eligible"], event["selected"]]
        table[key[2], record["initial"], record["eligible_to_hold"], eligible, selected] += 1
        if not (record["eligible_to_hold"] or eligible):
            continue
        fields = ("own1", "own4", "foe1", "foe4", "target1", "target4")
        details.append({
            "key": list(key),
            "step": record["start"],
            "target": record["target"],
            "initial": record["initial"],
            "historical_hold": record["eligible_to_hold"],
            "eligible": eligible,
            "selected": selected,
            "public_gain": follow["signal_gain"] if follow else None,
            "probability_extra": follow["probability"][2] if eligible else None,
            "probability_loss": follow["probability"][0] if eligible else None,
            "result": {k: event[k] for k in fields} if selected else None,
        })
    output = {
        "population": len(archive),
        "summary_order": ["opponent", "initial_score", "historical_hold", "eligible", "selected", "n"],
        "summary": [[*k, n] for k, n in sorted(table.items())],
        "details": details,
    }
    (HERE / "fallbilanz.json").write_text(json.dumps(output, indent=2) + "\n")
    for k, n in sorted(table.items()):
        print(*k, n)


if __name__ == "__main__":
    main()
