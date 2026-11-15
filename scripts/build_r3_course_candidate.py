"""Prepare a separate R3 course candidate from immutable Git objects.

    python -m scripts.build_r3_course_candidate --repo . --out candidate/r3-final-candidate.zip

Inputs are the tested 0105658 implementation/V14 and the published bd202fb R3.
The bundle contains the two original checkpoint byte streams in one agent.pth.
"""
import argparse
import ast
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from scripts.build_submission import yaml_text
from scripts.r3_course_entry import KIND, check_payload

RESEARCH = "0105658188b2ec5eaf5c3a4b0ef477be9a1412f8"
PUBLICATION = "bd202fb26c5b6e919007760c62eb5830a1439191"
SOURCE = "agents/sherlock/"
HERE = Path(__file__).resolve().parent
IMPORT_PATH = "agents.sherlock.main.Agent_x"
WEIGHT_PATH = "agents/sherlock/weights/agent.pth"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def functions(source, names):
    nodes = {n.name: n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}
    return "\n\n\n".join(ast.get_source_segment(source, nodes[name]) for name in names) + "\n"


def runtime_sources(repo):
    def read(path):
        return git(repo, "show", f"{RESEARCH}:{path}").decode("utf-8")

    # Relative imports in the unmodified V14 package work in either course installation layout.
    names = git(repo, "ls-tree", "--name-only", f"{RESEARCH}:agents/sherlock").decode().splitlines()
    files = {"v14/" + n: read(SOURCE + n) for n in names if n.endswith(".py") and n != "residual.py"}
    adviser = read("scripts/selective_advice_agent.py")
    files["r3_adviser.py"] = (adviser.replace("from agents.sherlock", "from .v14")
                               .replace("from scripts.combat_teacher_counterfactual", "from .orders"))
    # Keep exactly the action validator and corrections, without collector, opponent or replay imports.
    orders = functions(read("scripts/combat_teacher_counterfactual.py"), ("native_order", "live_ids", "substitute"))
    files["orders.py"] = ('import numpy as np\nfrom .v14 import geometry as geo\n'
                          'from .v14.imitation_agent import canonical_action\n\nARMS = ("movement",)\n\n\n'
                          + orders.replace("from agents.sherlock", "from .v14"))
    files["main.py"] = (HERE / "r3_course_entry.py").read_text(encoding="utf-8")
    files["__init__.py"] = ""
    return files


def final_layout(sources, weights):
    # Same package, YAML schema and CSV columns as build_submission.build. Both seats
    # resolve to the same byte-identical V14/R3 bundle through the course loader.
    files = {"sherlock/" + filename: source for filename, source in sources.items()}
    files["sherlock/weights/agent.pth"] = weights
    files["sherlock/agents.yaml"] = yaml_text(IMPORT_PATH, WEIGHT_PATH, WEIGHT_PATH)
    files["paths.csv"] = ("Moodle Gruppe;Import_Path;Load_Path_P0;Load_Path_P1\n"
                          f"15;{IMPORT_PATH};{WEIGHT_PATH};{WEIGHT_PATH}\n")
    return files


def build(repo, output):
    import torch

    output = Path(output).expanduser().absolute()
    if output.name.casefold() in {"agent.zip", "gruppe15.zip"} or output.suffix.lower() != ".zip" or output.exists():
        raise ValueError("Choose a new candidate .zip outside the current submission")
    weights = (Path(repo) / SOURCE / "weights").resolve()
    if output.resolve().is_relative_to(weights):
        raise ValueError("Candidate output may not be in the released weights directory")
    files = runtime_sources(repo)
    bundle = {
        "kind": KIND,
        "v14": git(repo, "show", f"{RESEARCH}:{SOURCE}weights/agent_p0.pth"),
        "r3": git(repo, "show", f"{PUBLICATION}:experiments/candidates/movement_dagger_20261115/r3_soft.pth"),
    }
    check_payload(bundle)
    packed = BytesIO()
    torch.save(bundle, packed)
    files = final_layout(files, packed.getvalue())
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as tmp:
        stage = Path(tmp) / "candidate.zip"
        with ZipFile(stage, "x") as archive:
            for name, content in sorted(files.items()):
                info = ZipInfo(name)
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content, compress_type=ZIP_DEFLATED)
        os.link(stage, output)  # Publish complete bytes, never overwrite an existing package.
    return sha256(output.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=HERE.parent)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    print(build(args.repo, args.out), args.out)


if __name__ == "__main__":
    main()
