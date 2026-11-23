"""Independently reconcile every sight, intervention and sensor attribution with archived command streams."""
import base64
from collections import Counter
import gzip
from hashlib import sha256
import json
from pathlib import Path
import zlib

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "sicht1_wiederholung"


def archive(file):
    return [json.loads(line) for line in gzip.decompress(file.read_bytes()).splitlines()]


def main():
    rows = archive(HERE/"sitze.jsonl.gz")
    games = {tuple(x["key"]): x for x in archive(OLD/"partien.jsonl.gz")}
    published = {(v["seed"], v["team"]): v for v in json.loads((OLD/"ergebnis.json").read_bytes())["seats"]}
    total, full, isolated, counts = 0, 0, 0, Counter()
    for r in rows:
        seed, side = r["seed"], r["side"]
        new, base = [games[seed, side, arm, "solution92"] for arm in ("ortundflotte", "v16")]
        assert new["sight"] == r["sight"] and base["sight"] == r["original"] and r["digest"] == new["digest"]
        assert published[seed, side]["diverged"] == r["first_raw_change"]
        assert published[seed, side]["sight"] == r["original"] - r["sight"]
        if r["uid"] is not None:
            t = r["first_raw_change"]
            segments = [zlib.decompress(base64.b64decode(rec["tape"])) for rec in (new, base)]
            assert segments[0][:t*96] == segments[1][:t*96]
            off = 96*t + 48*side
            different = [u for u in range(16) if segments[0][off+3*u:off+3*u+3] != segments[1][off+3*u:off+3*u+3]]
            assert different == [r["uid"]]
        category = r["kind"]
        if r["sight"] == 101:
            assert category == "kein_fund" and not r["visible_nodes"]
        else:
            full += 1
            if r["first_raw_change"] is None or r["first_raw_change"] >= r["sight"]:
                assert category == "vor_eingriff"
            else:
                isolated += 1
                assert r["visible_nodes"]
                one = any(n["ship"] for n in r["visible_nodes"])
                rest = any(n["rest"] for n in r["visible_nodes"])
                assert all((r["uid"] in n["individual_uids"]) == n["ship"] for n in r["visible_nodes"])
                assert all(not any(i != r["uid"] for i in n["individual_uids"]) or n["rest"] for n in r["visible_nodes"])
                assert one == r["ship_alone"] and rest == r["rest_alone"]
                assert category == {(True, False): "nur_schiff", (False, True): "nur_rest",
                                    (True, True): "beide_allein", (False, False): "nur_gemeinsam"}[one, rest]
        timing = "frueher" if new["sight"] < base["sight"] else "spaeter" if new["sight"] > base["sight"] else "gleich"
        counts[timing, category] += 1
        total += 1
    assert total == len(published) == 192
    agg = json.loads((HERE/"ergebnis.json").read_bytes())
    assert agg["archive_sha"] == sha256((HERE/"sitze.jsonl.gz").read_bytes()).hexdigest()
    assert counts == Counter({(g,k):n for g,row in agg["groups"].items() for k,n in row.items() if k!="seats"})
    result = {"seats":total, "full_masks_with_sight":full, "isolated_and_reconciled":isolated,
              "source_sha256":sha256((OLD/"partien.jsonl.gz").read_bytes()).hexdigest()}
    (HERE/"gegenpruefung.json").write_text(json.dumps(result, indent=2)+"\n")
    print(result)


if __name__ == "__main__":
    main()
