"""agent.zip fuer die Abgabe bauen (Vorgaben laut Kursfolie 51).

    python -m scripts.build_submission
    python -m scripts.build_submission --team-name sherlock --group 15
    python -m scripts.build_submission --from-run experiments/runs/20261010_full_s1

Inhalt von dist/agent.zip:

    <team_name>/
        __init__.py          leer
        main.py              Klasse Agent_x (act, update, set_to_eval_mode,
                             set_env_cfg, save_agent, load_agent)
        *.py                 Belief, Features, Netz, Reward, ...
        weights/agent_p0.pth, weights/agent_p1.pth
        agents.yaml          Import-Pfad + Lade-Pfade
    paths.csv                Moodle-Gruppe;Import_Path;Load_Path_P0;Load_Path_P1

--from-run kopiert vorher die Gewichte eines Experiment-Laufs nach
agents/sherlock/weights/ (die Pfade aus Paths.csv). Danach prueft das Skript
das entpackte Zip: Import ueber lux/runner.load_class_from_path, Pflichtmethoden,
Laden beider Seiten und ein Aktionsschritt auf einer echten Beobachtung.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from scripts.common import ROOT

SRC = ROOT / "agents" / "sherlock"
REQUIRED = ["act", "update", "set_to_eval_mode", "set_env_cfg", "save_agent", "load_agent"]


def install_weights(run_dir: Path) -> None:
    w = run_dir / "weights"
    dst = SRC / "weights"
    if (w / "agent.pth").is_file():
        p0 = p1 = w / "agent.pth"
    else:
        p0, p1 = w / "agent_p0.pth", w / "agent_p1.pth"
    for src, name in ((p0, "agent_p0.pth"), (p1, "agent_p1.pth")):
        if not src.is_file():
            raise SystemExit(f"Gewichte fehlen: {src}")
        shutil.copyfile(src, dst / name)
    print(f"Gewichte aus {run_dir} -> {dst}")


def build(team: str, group: int, out: Path) -> Path:
    files = sorted(p for p in SRC.glob("*.py") if p.name != "__init__.py")
    weights = [SRC / "weights" / "agent_p0.pth", SRC / "weights" / "agent_p1.pth"]
    for w in weights:
        if not w.is_file():
            raise SystemExit(f"{w} fehlt - erst trainieren oder --from-run nutzen.")
    imp = f"agents.{team}.main.Agent_x"
    lp0, lp1 = f"agents/{team}/weights/agent_p0.pth", f"agents/{team}/weights/agent_p1.pth"
    yaml = (f"%YAML 1.2\n---\n\nIMPORT_PATH: '{imp}'\n"
            f"LOAD_PATH_P0: '{lp0}'\nLOAD_PATH_P1: '{lp1}'\n")
    csv = f"Moodle Gruppe;Import_Path;Load_Path_P0;Load_Path_P1\n{group};{imp};{lp0};{lp1}\n"

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{team}/__init__.py", "")
        for f in files:
            z.write(f, f"{team}/{f.name}")
        for w in weights:
            z.write(w, f"{team}/weights/{w.name}")
        z.writestr(f"{team}/agents.yaml", yaml)
        z.writestr("paths.csv", csv)
    return out


CHECK = r'''
import sys, numpy as np
sys.path.insert(0, sys.argv[1])
import pandas as pd
from lux.runner import load_class_from_path
from luxai_s3.wrappers import LuxAIS3GymEnv
row = pd.read_csv(sys.argv[2], sep=";").iloc[0]
cls = load_class_from_path(row["Import_Path"])
missing = [m for m in sys.argv[3].split(",") if not callable(getattr(cls, m, None))]
assert not missing, f"Pflichtmethoden fehlen: {missing}"
env = LuxAIS3GymEnv(numpy_output=True)
obs, info = env.reset(seed=1)
for side, col in (("player_0", "Load_Path_P0"), ("player_1", "Load_Path_P1")):
    a = cls(side, agent_path=row[col])
    a.set_to_eval_mode(); a.set_env_cfg(info["params"])
    act = a.act(0, obs[side])
    assert np.asarray(act).shape == (16, 3), act.shape
    assert a.env_steps > 0, "Gewichte nicht geladen (env_steps == 0)"
    print(f"  {side}: {a.name} geladen, env_steps={a.env_steps}")
print("Check ok")
'''


def check(zip_path: Path, team: str) -> None:
    """Zip in eine frische Projektkopie (nur lux/ + agents/<team>) entpacken und laden."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copytree(ROOT / "lux", tmp / "lux", ignore=shutil.ignore_patterns("__pycache__"))
        (tmp / "agents").mkdir()
        (tmp / "agents" / "__init__.py").write_text("")
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tmp / "agents")
        subprocess.run([sys.executable, "-c", CHECK, str(tmp), str(tmp / "agents" / "paths.csv"),
                        ",".join(REQUIRED)], cwd=tmp, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--team-name", default="sherlock", help="Ordnername im Zip (= Teamname)")
    ap.add_argument("--group", type=int, default=15, help="Moodle-Gruppennummer")
    ap.add_argument("--from-run", default=None, help="Gewichte aus diesem Run-Ordner uebernehmen")
    ap.add_argument("--out", default=str(ROOT / "dist" / "agent.zip"))
    ap.add_argument("--no-check", action="store_true")
    args = ap.parse_args()

    if args.from_run:
        install_weights(Path(args.from_run))
    out = build(args.team_name, args.group, Path(args.out))
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
    print(f"{out} ({out.stat().st_size / 1e6:.1f} MB):")
    for n in names:
        print("  ", n)
    if not args.no_check:
        check(out, args.team_name)


if __name__ == "__main__":
    main()
