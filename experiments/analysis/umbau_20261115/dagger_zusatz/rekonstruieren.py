"""Rebuild the optional collection from Git and locally installed Kaggle files, without loading networks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
COMMIT = "d609183ea6d0ceb416687418613970a8ca2e53e3"
FREEZE = "adeb0c096fc025f8ced1abbbff55b2f2d651147b48d4161f8708de07b6055521"
PROTOCOL = "bdbc249aeb9831b8f83eaf2144da3f361ac983e20d6cd16f46b955ec2bd34290"
PATCH = "105a1ef7753c6df32feddea44d5287bb71dac21bdc824452a7a3e93e715b2b00"
FIXTURE = "3c61cf8e05b4e491c5183f02f8d072cba5a5ddfdc8c431d5801b0710ca38f8cb"
TEACHER = "experiments/opponents/kaggle3_lux3_048fn/"
TOOLS = {"scripts/optional_v4_dagger.py": "optional_v4_dagger.py", "run.sh": "run.sh"}


def verify(path, expected):
    with path.open("rb") as source:
        h = hashlib.sha256()
        for block in iter(lambda: source.read(1048576), b""):
            h.update(block)
    if h.hexdigest() != expected:
        raise ValueError(f"Unexpected SHA-256 for {path}")


def extract_git_files(project, dest, names):
    # Copy only the individually pinned regular files, not any mutable checkout contents.
    with tempfile.TemporaryDirectory() as work:
        archive = Path(work) / "original.tar"
        subprocess.run(["git", "-C", project, "archive", "--format=tar", "-o", archive, COMMIT,
                        "--", *sorted(names)], check=True)
        with tarfile.open(archive) as source:
            for name in sorted(names):
                entry = source.getmember(name)
                if not entry.isfile():
                    raise ValueError(f"Expected a regular Git file: {name}")
                file = dest / name
                file.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(entry) as reader, file.open("xb") as writer:
                    shutil.copyfileobj(reader, writer)


def rebuild(project, dest, check_runtime):
    manifest = HERE / "freeze.json"
    historical = HERE / "laufprotokoll.json"
    verify(manifest, FREEZE)
    verify(historical, PROTOCOL)
    verify(HERE / "sammler.patch", PATCH)
    verify(HERE / "verify_fixture.py", FIXTURE)
    freeze = json.loads(manifest.read_bytes())
    protocol = json.loads(historical.read_bytes())
    if freeze["source"] != COMMIT or protocol["source"] != COMMIT or protocol["freeze_sha256"] != FREEZE:
        raise ValueError("Source and runtime protocol disagree")
    files = freeze["files"]
    external = {p for p in files if p.startswith(TEACHER)}
    original = set(files) - external - TOOLS.keys()
    for item in external:
        verify(project / item, files[item])
    if dest.is_relative_to(project) or HERE.is_relative_to(dest):
        raise ValueError("Choose a new directory outside the project")
    dest.mkdir(exist_ok=False)
    try:
        extract_git_files(project, dest, original)
        collector = dest / "scripts/imitate.py"
        verify(collector, freeze["upstream_collector"])
        # Only this single upstream file is patched. Its full postimage is verified below.
        with (HERE / "sammler.patch").open("rb") as patch:
            subprocess.run(["patch", "-p1", "-f"], cwd=dest, stdin=patch, check=True)
        for name in sorted(external):
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(project / name, target)
        for name, source in TOOLS.items():
            shutil.copyfile(HERE / source, dest / name)
        (dest / "run.sh").chmod(0o755)
        shutil.copyfile(manifest, dest / "freeze.json")
        shutil.copyfile(HERE / "verify_fixture.py", dest / "verify_fixture.py")
        for name, expected in files.items():
            verify(dest / name, expected)
        verify(dest / "freeze.json", FREEZE)
        verify(dest / "verify_fixture.py", FIXTURE)
        if check_runtime:
            # Use the project's actual interpreter and the reconstructed collector's own metadata routines.
            # These functions hash sources and load existing score tables; they never instantiate agents or Gym.
            program = """from pathlib import Path
import sys
from scripts import optional_v4_dagger as collection
observed = collection.provenance()
observed["robustness_assessment_sha256"] = collection.prerequisites(Path(sys.argv[1]))
if collection.encoded(observed) != Path(sys.argv[2]).read_bytes():
    raise SystemExit("Runtime, roster, sources or robustness report differ from the original protocol")
if 'torch' in sys.modules or 'luxai_s3.env' in sys.modules:
    raise SystemExit("Unexpected model/environment import")
"""
            subprocess.run([project / ".venv/bin/python", "-B", "-c", program, project, historical],
                           cwd=dest, check=True)
    except BaseException:
        # We acquired this previously absent directory above. Never clean up an existing destination.
        shutil.rmtree(dest)
        raise
    print(f"{len(files)} frozen files verified; {len(original)-1} original, 1 patched, "
          f"{len(TOOLS)} additional and {len(external)} Kaggle files.")
    if check_runtime:
        print(f"Original collection protocol reproduced byte-for-byte: {PROTOCOL}")
    print(dest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=os.environ.get("SHERLOCK_PROJECT"),
                        help="Project for Git, Kaggle resources and .venv; defaults to SHERLOCK_PROJECT")
    parser.add_argument("--out", required=True, type=Path, help="New directory with an existing parent")
    parser.add_argument("--check-runtime", action="store_true",
                        help="Also compare the exact runtime, full roster and 288 existing robustness results")
    args = parser.parse_args()
    if args.project is None:
        parser.error("Set SHERLOCK_PROJECT or pass --project")
    rebuild(args.project.resolve(), args.out.resolve(), args.check_runtime)
