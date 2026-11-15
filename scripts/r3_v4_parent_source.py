"""Rebuild R3 from its pinned Git tree under a private Python import name."""
import argparse
from hashlib import sha256
import io
from pathlib import Path
import re
import subprocess
import tarfile

R3_REF = "0105658188b2ec5eaf5c3a4b0ef477be9a1412f8"
ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(rb"(?m)^(\s*from[ \t]+)(agents|scripts)(?=[. \t])")


def relocate(code):
    # Rewrite only absolute from-imports within the two project packages; all algorithms are copied.
    if re.search(rb"(?m)^\s*import (agents|scripts)(?=[. ,\n])", code):
        raise ValueError("Unexpected bare project import; inspect before using another tree")
    return PATTERN.sub(rb"\1r3_native.\2", code)


def materialize(repo, dest):
    blob = subprocess.check_output(["git","-C",str(repo),"archive",R3_REF,"agents/sherlock","scripts"])
    with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
        for member in archive:
            if not member.isfile() or not member.name.endswith(".py"):
                continue
            p = dest / "r3_native" / member.name
            p.parent.mkdir(parents=True, exist_ok=True)
            raw = archive.extractfile(member).read()
            try:
                actual = relocate(raw)
            except ValueError:
                # Standalone tools outside the import graph have no role in either policy.
                if member.name.startswith("agents/") or member.name.split("/")[-1] in USED_SCRIPTS:
                    raise
                continue
            if p.exists() and p.read_bytes() != actual:
                raise ValueError(f"Existing different source {p}")
            p.write_bytes(actual)


USED_SCRIPTS = ("selective_advice_agent.py", "combat_teacher_counterfactual.py", "collect_combat_advice.py",
                "imitate.py", "par_eval.py", "common.py", "experiment.py", "variants.py", "protocol.py",
                "scoring.py", "fetch_kaggle3.py")


def verify(repo_sources, historical):
    src = {}
    for f in sorted((ROOT / "r3_native/agents/sherlock").glob("*.py")):
        rel = str(f.relative_to(ROOT / "r3_native"))
        if rel not in historical:
            raise ValueError(f"Unregistered old policy module {rel}")
    for rel in sorted(k for k in repo_sources if k.startswith("agents/sherlock/") or
                      (k.startswith("scripts/") and k.split("/")[-1] in USED_SCRIPTS)):
        raw = repo_sources[rel]
        if rel in historical and sha256(raw).hexdigest() != historical[rel]:
            raise ValueError(f"Wrong R3 parent {rel}")
        path = ROOT / "r3_native" / rel
        if path.read_bytes() != relocate(raw):
            raise ValueError(f"Different source after rebasing imports in {rel}")
        src["r3_native/"+rel] = sha256(path.read_bytes()).hexdigest()
    if "r3_native/scripts/selective_advice_agent.py" not in src:
        raise ValueError("Missing legacy parent")
    return src


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", required=True, type=Path)
    materialize(p.parse_args().repo, ROOT)
