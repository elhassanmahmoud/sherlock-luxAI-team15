"""Build the candidate's tested course ZIP in the separate Gruppe15 layout."""
import argparse
from hashlib import sha256
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from scripts.build_submission import battle_paths, check_battle, yaml_text

VERIFIED = {
    "fc4061619542169bd7197bec857ff91408297bcb2c2f2f1151c03b362ba23bfe": ("Bewegungsberater", "wertberater.npz"),
    "45970b09f22c5312ceda84d8bfb74ad50d5d2ca72223e5a37879a5892d08dc50": ("Sichtberater", "sichtwert.json"),
}


def build(source, target):
    src, dst = source.resolve(), target.resolve()
    checksum = sha256(src.read_bytes()).hexdigest()
    if checksum not in VERIFIED:
        raise ValueError("Expected a separately verified candidate")
    description, extra = VERIFIED[checksum]
    if any(dst.is_relative_to((ROOT/folder).resolve()) for folder in ("dist", "agents", "experiments/releases")):
        raise ValueError("Choose a separate research output")
    paths = battle_paths(15, True)
    with ZipFile(src) as z:
        files = {}
        for name in z.namelist():
            if not name.startswith("sherlock/") or name.endswith(("/", "/agents.yaml")):
                continue
            rel = name.removeprefix("sherlock/")
            dest = paths[1] if rel == "weights/agent.pth" else "Gruppe15/" + rel
            files[dest] = z.read(name)
    required = {"Gruppe15/main.py", "Gruppe15/v16_main.py", "Gruppe15/agent.pth", f"Gruppe15/{extra}"}
    if not required <= files.keys():
        raise ValueError("Incomplete candidate source archive")
    files["Gruppe15/agents.yaml"] = yaml_text(*paths).encode()
    files["Gruppe15/LIESMICH.txt"] = (
        f"Team 15 – Sherlock mit {description}\n\n"
        "Klasse: Gruppe15.main.Agent_x\n"
        "Gewichte Spieler 0 und 1: Gruppe15/agent.pth\n"
        f"Die Datei {extra} liegt im selben Ordner wie main.py.\n"
        "Benötigt die Kursumgebung mit NumPy, SciPy und PyTorch.\n"
    ).encode()
    dst.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(dst, "x") as z:
        for name, data in sorted(files.items()):
            attr = ZipInfo(name, (2026,11,23,0,0,0))
            attr.compress_type = ZIP_DEFLATED
            attr.external_attr = 0o644 << 16
            z.writestr(attr, data)
    with ZipFile(dst) as z:
        if z.testzip() or any(z.read(name) != value for name, value in files.items()):
            raise ValueError("Copied policy or weights differ")
    return paths


if __name__ == "__main__":
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("course", type=Path)
    arg.add_argument("out", type=Path)
    a = arg.parse_args()
    paths = build(a.course, a.out)
    check_battle(a.out, paths)
    print(sha256(a.out.read_bytes()).hexdigest())
