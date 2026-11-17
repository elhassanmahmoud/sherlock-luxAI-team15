"""Kurspaket "reiner Schüler" bauen (17.11.2026).

Gleiches Format wie das R3-Finalpaket: `paths.csv`, Ordner `sherlock/` mit dem Agentencode (Kopie von
agents/sherlock/*.py, Klasse `agents.sherlock.main.Agent_x`) und genau einer Gewichtsdatei `sherlock/weights/agent.pth`
für beide Seiten. Die Gewichtsdatei ist der Imitations-Checkpoint (kind "imitation", auch als Ensemble) mit den
Spielschaltern in seiner Config (Standard wie in den Messungen: imit_stay_bias 1.5, imit_unstack true) und
`frozen: true`. Agent_x erkennt den Checkpoint und spielt die nachgeahmte Policy; update() und save_agent() tun dann
nichts. Pfade aus dem Training (Daten, Startnetz) werden nicht mitverpackt.

    python -m scripts.build_student_package --student ens9 --out experiments/candidates/deve_20261117/agent_ens9.zip

Schreibt nie auf die Abgabedateien (`dist/agent.zip`, `Gruppe15.zip`) oder in das R3-Releaseverzeichnis.
"""
from __future__ import annotations

import argparse
import io
import keyword
import zipfile
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "agents" / "sherlock"
R3_DIR = ROOT / "experiments/releases/20261116_r3_finale"
PROTECTED = {ROOT / "dist/agent.zip", ROOT / "Gruppe15.zip"}
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
DEFAULT_SWITCHES = {"imit_stay_bias": 1.5, "imit_unstack": True}
DROP_KEYS = ("data", "init")  # lokale Trainingspfade
IMPORT = "agents.sherlock.main.Agent_x"
LOAD = "agents/sherlock/weights/agent.pth"


def packed_checkpoint(student: Path, switches: dict) -> bytes:
    from dataclasses import fields

    import torch

    from agents.sherlock.config import AgentConfig

    ck = torch.load(student, map_location="cpu", weights_only=False)
    if not isinstance(ck, dict) or ck.get("kind") != "imitation" or not isinstance(ck.get("cfg"), dict):
        raise ValueError(f"{student} ist kein Imitations-Checkpoint mit Config")
    unknown = set(switches) - {f.name for f in fields(AgentConfig)}
    if unknown:
        raise ValueError(f"Unbekannte Schalter: {sorted(unknown)}")
    ck = {k: v for k, v in ck.items() if k not in DROP_KEYS}
    if isinstance(ck.get("members"), list):  # Ensemble: nur Dateinamen der Mitglieder, keine lokalen Pfade
        ck["members"] = [Path(str(m)).name for m in ck["members"]]
    ck["cfg"] = {**ck["cfg"], **switches, "frozen": True}
    ck["source_sha256"] = sha256(student.read_bytes()).hexdigest()
    buf = io.BytesIO()
    torch.save(ck, buf)
    return buf.getvalue()


def build(student: str, out: Path, switches: dict | None = None) -> str:
    from agents.sherlock_r3t.agent import STUDENTS

    switches = dict(DEFAULT_SWITCHES if switches is None else switches)
    src = Path(STUDENTS.get(student, student)).resolve()
    out = out.resolve()
    if out in PROTECTED or R3_DIR.resolve() in out.parents or SRC.resolve() in out.parents:
        raise SystemExit(f"Geschützte Datei oder Verzeichnis: {out}")
    if out.exists():
        raise SystemExit(f"{out} existiert schon")
    weights = packed_checkpoint(src, switches)
    files = sorted(p for p in SRC.glob("*.py")
                   if p.name != "__init__.py" and p.stem.isidentifier() and not keyword.iskeyword(p.stem))
    yaml = f"%YAML 1.2\n---\n\nIMPORT_PATH: '{IMPORT}'\nLOAD_PATH_P0: '{LOAD}'\nLOAD_PATH_P1: '{LOAD}'\n"
    csv = f"Moodle Gruppe;Import_Path;Load_Path_P0;Load_Path_P1\n15;{IMPORT};{LOAD};{LOAD}\n"
    out.parent.mkdir(parents=True, exist_ok=True)

    def put(z, name, data):
        info = zipfile.ZipInfo(name, FIXED_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, data)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        put(z, "paths.csv", csv)
        put(z, "sherlock/__init__.py", b"")
        put(z, "sherlock/agents.yaml", yaml)
        for f in files:
            put(z, f"sherlock/{f.name}", f.read_bytes())
        put(z, "sherlock/weights/agent.pth", weights)
    return sha256(out.read_bytes()).hexdigest()


def main() -> None:
    from scripts.par_eval import parse_value

    ap = argparse.ArgumentParser()
    ap.add_argument("--student", required=True, help="Name aus agents/sherlock_r3t/agent.py STUDENTS oder Pfad")
    ap.add_argument("--out", required=True)
    ap.add_argument("--set", action="append", default=None, metavar="KEY=VALUE",
                    help="Spielschalter statt der Standardwerte (imit_stay_bias=1.5, imit_unstack=true)")
    ap.add_argument("--no-check", action="store_true", help="ohne Ladeprüfung des Kursrunners")
    a = ap.parse_args()
    switches = None if a.set is None else {k: parse_value(v) for k, v in (kv.split("=", 1) for kv in a.set)}
    out = Path(a.out)
    print(f"{out}: SHA-256 {build(a.student, out, switches)}")
    if not a.no_check:
        from scripts.build_submission import check
        check(out.resolve(), "sherlock")


if __name__ == "__main__":
    main()
