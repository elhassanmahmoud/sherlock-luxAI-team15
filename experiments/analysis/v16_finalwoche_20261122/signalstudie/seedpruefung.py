"""Durchsucht beide relevanten Kopien einschließlich komprimierter Versuchs- und Replaydaten."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
OWN = "experiments/analysis/v16_finalwoche_20261122/signalstudie/"
IDS = re.compile(rb"(?<![\w.])(?:160343[01][0-9][0-9]|160344[0-3][0-9][0-9])(?![\w.])")
TEXT = {".csv",".tsv",".md",".py",".json",".jsonl",".sh",".txt",".yml",".yaml",".log",".gz"}
GZIP_LABELS = (".json.gz", ".jsonl.gz", ".csv.gz", ".tsv.gz", ".txt.gz", ".log.gz")
AREAS = ("agents","docs","experiments","scripts")

def contains(path):
    use_gzip = path.name.endswith(GZIP_LABELS)
    with (gzip.open(path, "rb") if use_gzip else path.open("rb")) as source:
        previous=b""
        while True:
            block=source.read(512*1024)
            if not block:
                return bool(IDS.search(previous))
            data=previous+block
            if b"16034" in data and any(m.end() < len(data)-32 for m in IDS.finditer(data)):
                return True
            previous=data[-64:]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("roots",nargs="+",type=Path)
    args=ap.parse_args()
    result=[]
    for root in args.roots:
        counts=Counter()
        matches=[]
        command=["git","-C",str(root),"ls-files","-co","--exclude-standard","-z","--",*AREAS]
        paths=subprocess.check_output(command).decode().split("\0")
        for name in sorted(set(paths)):
            if not name or name.startswith(OWN): continue
            path=root/name
            if path.suffix not in TEXT or not path.is_file(): continue
            if path.suffix==".gz" and not path.name.endswith(GZIP_LABELS): continue
            if contains(path): matches.append(name)
            counts[path.suffix]+=1
        result.append(dict(root=root.name,formats=dict(counts),matches=matches))
    (HERE/"seedpruefung.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print([(sum(r["formats"].values()),r["matches"]) for r in result])
    if any(r["matches"] for r in result): raise SystemExit(1)


if __name__=="__main__":
    main()
