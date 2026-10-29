"""agent.zip fuer die Abgabe bauen (Vorgaben laut Kursfolie 51).

    python -m scripts.build_submission
    python -m scripts.build_submission --team-name sherlock --group 15
    python -m scripts.build_submission --from-run experiments/runs/20261010_full_s1
    python -m scripts.build_submission --battle          # Gruppe15.zip im Projektordner

Inhalt von dist/agent.zip:

    <team_name>/
        __init__.py          leer
        main.py              Klasse Agent_x (act, update, set_to_eval_mode,
                             set_env_cfg, save_agent, load_agent)
        *.py                 Belief, Features, Netz, Reward, ...
        weights/agent_p0.pth, weights/agent_p1.pth
        agents.yaml          Import-Pfad + Lade-Pfade
    paths.csv                Moodle-Gruppe;Import_Path;Load_Path_P0;Load_Path_P1

--battle folgt der Mail des Profs zum Battle (erhalten 29.10.2026): Gruppe<N>.zip
mit Ordner Gruppe<N>/, Import-Pfad 'Gruppe<N>.main.Agent_x' und Gewichten direkt im
Ordner. Gleiche Gewichte fuer beide Seiten stehen einmal als agent.pth darin, sonst
als agent_0.pth und agent_1.pth. Dazu LIESMICH.txt mit den Pfaden fuer den Prof.

--from-run liest die Gewichte eines Experiment-Laufs direkt ins Zip.
agents/sherlock/weights/ bleibt unveraendert. Danach prueft das Skript
das entpackte Zip: Import ueber lux/runner.load_class_from_path, Pflichtmethoden,
Laden beider Seiten und ein Aktionsschritt auf einer echten Beobachtung. Das
Battle-Zip wird zweimal geprueft: Ordner unter agents/ und in der Projektwurzel.
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
from scripts.output_paths import checked_output

SRC = ROOT / "agents" / "sherlock"
REQUIRED = ["act", "update", "set_to_eval_mode", "set_env_cfg", "save_agent", "load_agent"]


def run_weights(run_dir: Path) -> list[Path]:
    w = run_dir / "weights"
    if (w / "agent.pth").is_file():
        p0 = p1 = w / "agent.pth"
    else:
        p0, p1 = w / "agent_p0.pth", w / "agent_p1.pth"
    for src in (p0, p1):
        if not src.is_file():
            raise SystemExit(f"Gewichte fehlen: {src}")
    return [p0, p1]


def sources(out: Path, from_run: Path | None) -> tuple[list[Path], list[Path], Path]:
    """Quelldateien, Gewichte beider Seiten und geprueftes Ausgabeziel."""
    files = sorted(p for p in SRC.glob("*.py") if p.name != "__init__.py")
    weights = (run_weights(from_run) if from_run is not None else
               [SRC / "weights" / "agent_p0.pth", SRC / "weights" / "agent_p1.pth"])
    for w in weights:
        if not w.is_file():
            raise SystemExit(f"{w} fehlt - erst trainieren oder --from-run nutzen.")
    try:
        out = checked_output(out, SRC / "weights")
        if any(out == w.resolve() or (out.exists() and out.samefile(w)) for w in weights):
            raise ValueError(f"Zip-Ausgabe darf keine Eingabe-Gewichte ersetzen: {out}")
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    out.parent.mkdir(parents=True, exist_ok=True)
    return files, weights, out


def yaml_text(imp: str, lp0: str, lp1: str) -> str:
    return (f"%YAML 1.2\n---\n\nIMPORT_PATH: '{imp}'\n"
            f"LOAD_PATH_P0: '{lp0}'\nLOAD_PATH_P1: '{lp1}'\n")


def build(team: str, group: int, out: Path, from_run: Path | None = None) -> Path:
    files, weights, out = sources(out, from_run)
    imp = f"agents.{team}.main.Agent_x"
    lp0, lp1 = f"agents/{team}/weights/agent_p0.pth", f"agents/{team}/weights/agent_p1.pth"
    csv = f"Moodle Gruppe;Import_Path;Load_Path_P0;Load_Path_P1\n{group};{imp};{lp0};{lp1}\n"

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{team}/__init__.py", "")
        for f in files:
            z.write(f, f"{team}/{f.name}")
        for i, w in enumerate(weights):
            z.write(w, f"{team}/weights/agent_p{i}.pth")
        z.writestr(f"{team}/agents.yaml", yaml_text(imp, lp0, lp1))
        z.writestr("paths.csv", csv)
    return out


def battle_paths(group: int, same: bool) -> tuple[str, str, str]:
    pkg = f"Gruppe{group}"
    if same:
        return f"{pkg}.main.Agent_x", f"{pkg}/agent.pth", f"{pkg}/agent.pth"
    return f"{pkg}.main.Agent_x", f"{pkg}/agent_0.pth", f"{pkg}/agent_1.pth"


def net_count(path: Path) -> int | None:
    """Anzahl Netze im Checkpoint (Hauptnetz + Ensemble); None, wenn nicht lesbar."""
    try:
        import torch
        ck = torch.load(path, map_location="cpu", weights_only=True)
        return 1 + len(ck.get("ensemble", []))
    except Exception:
        return None


def readme_text(group: int, imp: str, lp0: str, lp1: str, nets: int | None = None) -> str:
    pth = (f"Pfad zum trainierten Agenten:  {lp0}   (gleiche Datei fuer Player 0 und Player 1)"
           if lp0 == lp1 else f"Pfad Player 0:  {lp0}\nPfad Player 1:  {lp1}")
    return (f"Gruppe {group} - Agent Sherlock\n\n"
            f"Pfad zur Agent-Klasse (act, update):  {imp}\n{pth}\n\n"
            f"Zeile fuer Paths.csv:\n{group};{imp};{lp0};{lp1}\n\n"
            "Hinweise:\n"
            f"- Den Ordner Gruppe{group} nach agents/ oder in die Projektwurzel legen, beides geht.\n"
            "  Findet der Agent den Gewichte-Pfad vom Arbeitsverzeichnis aus nicht, laedt er die\n"
            "  gleichnamige .pth-Datei direkt neben main.py.\n"
            "- Fuer das Battle am besten mit train=False spielen (nur dann schreibt der Runner Replays).\n"
            "  Die Battle-Version ist eingefroren: Auch mit train=True spielt Sherlock in voller Staerke,\n"
            "  lernt nicht weiter und ueberschreibt seine .pth-Datei nicht.\n"
            "- Benoetigt nur die Kurs-Pakete (torch, numpy); CPU reicht.\n"
            + (f"- Beim Start erscheint: [Sherlock Agent_X] geladen: ... Ensemble={nets} Netze\n" if nets else
               "- Beim Start erscheint: [Sherlock Agent_X] geladen: ...\n"))


def frozen_bytes(path: Path, half: bool = False) -> bytes:
    """Checkpoint mit cfg.frozen = True (29.10.2026): Der Kurs-Runner startet Agenten mit train=True,
    wenn man es nicht abschaltet; eingefroren spielt Sherlock dann trotzdem wie mit train=False.
    Gewichte und alle anderen Eintraege bleiben gleich. Dateien ohne Config unveraendert.

    half=True (29.10.2026, nur fuer eine Moodle-Groessengrenze): Netzgewichte als float16 und ohne
    Optimierer-Zustand, die Datei wird etwa halb so gross (36 Netze 24 statt 12 MB). Der Agent rechnet
    weiter in float32, load_state_dict wandelt beim Laden um. Auf 50.000 Zustaenden aus einem Replay-Buffer
    aenderte das die beste erlaubte Aktion von mix36 in 0,008 % der Faelle (mix54 0,006 %)."""
    import io
    from collections import OrderedDict

    import torch
    try:
        ck = torch.load(path, map_location="cpu", weights_only=True)
    except Exception:
        return path.read_bytes()
    if not isinstance(ck, dict) or not isinstance(ck.get("cfg"), dict):
        return path.read_bytes()
    ck["cfg"] = {**ck["cfg"], "frozen": True}
    if half:
        def to_half(sd):
            out = OrderedDict((k, v.half() if v.is_floating_point() else v) for k, v in sd.items())
            if hasattr(sd, "_metadata"):
                out._metadata = sd._metadata
            return out
        for key in ("q", "target_q"):
            if key in ck:
                ck[key] = to_half(ck[key])
        ck["ensemble"] = [to_half(sd) for sd in ck.get("ensemble", [])]
        ck.pop("opt", None)
    buf = io.BytesIO()
    torch.save(ck, buf)
    return buf.getvalue()


def build_battle(group: int, out: Path, from_run: Path | None = None,
                 half: bool = False) -> tuple[Path, tuple[str, str, str]]:
    files, weights, out = sources(out, from_run)
    pkg = f"Gruppe{group}"
    same = weights[0].read_bytes() == weights[1].read_bytes()
    imp, lp0, lp1 = battle_paths(group, same)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{pkg}/__init__.py", "")
        for f in files:
            z.write(f, f"{pkg}/{f.name}")
        for w, lp in ([(weights[0], lp0)] if same else [(weights[0], lp0), (weights[1], lp1)]):
            z.writestr(lp, frozen_bytes(w, half))
        z.writestr(f"{pkg}/agents.yaml", yaml_text(imp, lp0, lp1))
        z.writestr(f"{pkg}/LIESMICH.txt", readme_text(group, imp, lp0, lp1, net_count(weights[0])))
    return out, (imp, lp0, lp1)


CHECK = r'''
import sys, numpy as np
sys.path.insert(0, sys.argv[1])
import agents  # wie beim Prof: agents/__init__.py importiert alle Unterpakete
from lux.runner import load_class_from_path
from luxai_s3.wrappers import LuxAIS3GymEnv
imp, p0, p1 = sys.argv[2:5]
cls = load_class_from_path(imp)
missing = [m for m in sys.argv[5].split(",") if not callable(getattr(cls, m, None))]
assert not missing, f"Pflichtmethoden fehlen: {missing}"
env = LuxAIS3GymEnv(numpy_output=True)
obs, info = env.reset(seed=1)
for side, path in (("player_0", p0), ("player_1", p1)):
    a = cls(side, agent_path=path)
    a.set_to_eval_mode(); a.set_env_cfg(info["params"])
    act = a.act(0, obs[side])
    assert np.asarray(act).shape == (16, 3), act.shape
    assert a.env_steps > 0, "Gewichte nicht geladen (env_steps == 0)"
    print(f"  {side}: {a.name} geladen, env_steps={a.env_steps}, Netze={1 + len(a.extra_q)}")
if sys.argv[6] == "frozen":
    # Runner mit train=True: kein set_to_eval_mode, save_agent() vor dem Spiel, update() bis Spielende
    for side, path in (("player_0", p0), ("player_1", p1)):
        b = cls(side, agent_path=path)
        data = open(b.agent_path, "rb").read()
        b.set_env_cfg(info["params"]); b.save_agent()
        act = b.act(0, obs[side])
        b.update(0, obs[side], 0.0, act, True, obs[side])
        assert b.cfg.frozen and not b.training and b.epsilon == 0.0, "train=True schaltet die Abgabe um"
        assert open(b.agent_path, "rb").read() == data, "train=True hat die .pth ueberschrieben"
        print(f"  {side}: train=True eingefroren ok (Netze={1 + len(b.extra_q)}, .pth unveraendert)")
print("Check ok")
'''


def project_copy(tmp: Path) -> None:
    """Frische Kursvorlage nachbauen: lux/, agents/__init__.py (Auto-Import), default."""
    skip = shutil.ignore_patterns("__pycache__")
    shutil.copytree(ROOT / "lux", tmp / "lux", ignore=skip)
    shutil.copytree(ROOT / "agents" / "default", tmp / "agents" / "default", ignore=skip)
    shutil.copy(ROOT / "agents" / "__init__.py", tmp / "agents" / "__init__.py")


def run_check(tmp: Path, imp: str, lp0: str, lp1: str, frozen: bool = False) -> None:
    subprocess.run([sys.executable, "-c", CHECK, str(tmp), imp, lp0, lp1, ",".join(REQUIRED),
                    "frozen" if frozen else "-"], cwd=tmp, check=True)


def check(zip_path: Path, team: str) -> None:
    """Zip in eine frische Projektkopie (nur lux/ + agents/<team>) entpacken und laden."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        project_copy(tmp)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tmp / "agents")
        row = (tmp / "agents" / "paths.csv").read_text().splitlines()[1].split(";")
        run_check(tmp, row[1], row[2], row[3])


def check_battle(zip_path: Path, paths: tuple[str, str, str]) -> None:
    """Battle-Zip so pruefen, wie der Prof es nutzen kann: unter agents/ und in der Wurzel."""
    for place in ("agents", "."):
        print(f"Ordner in {'agents/' if place == 'agents' else 'Projektwurzel'}:")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            project_copy(tmp)
            with zipfile.ZipFile(zip_path) as z:
                z.extractall(tmp / place)
            run_check(tmp, *paths, frozen=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--team-name", default="sherlock", help="Ordnername im Zip (= Teamname)")
    ap.add_argument("--group", type=int, default=15, help="Moodle-Gruppennummer")
    ap.add_argument("--from-run", default=None, help="Gewichte dieses Runs direkt verpacken; Abgabe-Dateien unveraendert lassen")
    ap.add_argument("--battle", action="store_true", help="Format aus der Battle-Mail: Gruppe<N>.zip")
    ap.add_argument("--out", default=None, help="Standard: dist/agent.zip bzw. Gruppe<N>.zip im Projektordner")
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--half", action="store_true",
                    help="nur --battle: Netzgewichte als float16, halbe Dateigroesse (fuer eine Moodle-Grenze)")
    args = ap.parse_args()
    if args.half and not args.battle:
        ap.error("--half gibt es nur mit --battle")

    from_run = Path(args.from_run).expanduser() if args.from_run else None
    if args.battle:
        out, paths = build_battle(args.group, Path(args.out or ROOT / f"Gruppe{args.group}.zip"), from_run,
                                  args.half)
    else:
        out = build(args.team_name, args.group, Path(args.out or ROOT / "dist" / "agent.zip"), from_run)
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
    print(f"{out} ({out.stat().st_size / 1e6:.1f} MB):")
    for n in names:
        print("  ", n)
    if args.battle:
        print("Fuer den Prof:\n  Agent-Klasse: {}\n  Gewichte P0:  {}\n  Gewichte P1:  {}".format(*paths))
    if not args.no_check:
        if args.battle:
            check_battle(out, paths)
        else:
            check(out, args.team_name)


if __name__ == "__main__":
    main()
