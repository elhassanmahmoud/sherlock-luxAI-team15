"""Make a local source snapshot for the final round, with no release-path writes."""
import argparse
from pathlib import Path
from shutil import copy2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def freeze(out):
    out.mkdir(parents=True,exist_ok=False)
    sources = {p for name in ("scripts","agents","lux") for p in (ROOT/name).rglob("*.py")}
    kaggle = ROOT/"experiments/opponents/kaggle3_lux3_048fn"
    sources.update(p for p in kaggle.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    sources.update([ROOT/"experiments/releases/20261117_sherlock_v16/agent.zip",HERE/"PLAN.md",HERE/"festlauf.py",
                    HERE.parent/"kundschafter/kandidat.py"])
    for p in sorted(sources):
        dest=out/p.relative_to(ROOT); dest.parent.mkdir(parents=True,exist_ok=True); copy2(p,dest)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("destination",type=Path)
    freeze(p.parse_args().destination)
