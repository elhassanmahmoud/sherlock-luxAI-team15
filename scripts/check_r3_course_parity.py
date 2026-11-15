"""Compare the extracted R3 course entrant with the original selective movement policy.

python -I scripts/check_r3_course_parity.py --zip r3-final-candidate.zip --research ARCHIVE_0105658 --v14 V14.pth --r3 r3_soft.pth --out NEW.json

The same historical map is played once per seat against native Solution_92. This
checks implementation parity on visited positions, without estimating win rate.
Use --diagonal for the fixed two-view candidate and its separate source snapshot.
"""
import argparse
from copy import deepcopy
import csv
import hashlib
from importlib.machinery import PathFinder
import io
import json
import multiprocessing as mp
import os
from pathlib import Path
import shutil
import sys
import tempfile
import traceback
import zipfile


COMMIT = "0105658188b2ec5eaf5c3a4b0ef477be9a1412f8"
SOURCES = "178af787fa828ac4b3572dfa7bbdd96cdf2f9c1c16b4b11eca3a80e1a61fa55e"
V14 = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
R3 = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"
DIAGONAL_COMMIT = "aa5cd60354014ac33ddc4d6b1013e1842ba27aa7"
DIAGONAL_SOURCES = "2ede35c0e544c06b079b7ef7eaf7d1c0f56dd0c92f33347c172f30f48245c736"
DIAGONAL_ZIP = "feaf20aa7058ad856634cd8a5a2daf56bfc6da4f6be296cff6d98fc55eefac25"
# Same diagnostic seed, original 606-step reference from candidate_package/parity.json.
STANDARD_ACTIONS = {
    "player_0": "e749bc4ba8fd124eea24627d60a03f7e430f3966ba4c032e33bc63f924fbbae7",
    "player_1": "1dbeaa80a5dd81ba168a9382d76eaff65aa3820b118158bdafc41425e9cb413d",
}
SEED = 7271000
IMPORT = "agents.sherlock.main.Agent_x"
WEIGHTS = "agents/sherlock/weights/agent.pth"
CSV_HEADER = ["Moodle Gruppe", "Import_Path", "Load_Path_P0", "Load_Path_P1"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def research_digest(root):
    # Same sorted path + NUL + blob SHA-256 + LF for every Python source in git ls-tree.
    h = hashlib.sha256()
    files = (p for group in ("agents", "scripts", "lux") for p in (root / group).rglob("*.py"))
    for p in sorted(files, key=lambda path: path.relative_to(root).as_posix()):
        h.update(f"{p.relative_to(root).as_posix()}\0{digest(p)}\n".encode())
    return h.hexdigest()


def extract_entrant(archive, folder, research, diagonal=False):
    support = {f"sherlock/v14/{p.name}": p for p in (research / "agents/sherlock").glob("*.py")
               if p.name != "residual.py"}
    team = ("__init__.py", "main.py", "r3_adviser.py", "orders.py", "weights/agent.pth", "agents.yaml")
    expected = {"paths.csv", *support} | {"sherlock/" + name for name in team}
    if diagonal:
        expected.add("sherlock/r3_diagonal.py")
    if sorted(archive.namelist()) != sorted(expected):
        raise ValueError("Unexpected final ZIP contents (files missing, duplicated or added)")
    for member, original in support.items():
        if archive.read(member) != original.read_bytes():
            raise ValueError(f"Bundled V14 source differs from 0105658: {member}")
    if archive.read("sherlock/__init__.py") != b"":
        raise ValueError("The final team package initializer must be empty")
    rows = list(csv.reader(io.StringIO(archive.read("paths.csv").decode("cp1252")), delimiter=";"))
    if rows != [CSV_HEADER, ["15", IMPORT, WEIGHTS, WEIGHTS]]:
        raise ValueError(f"Unexpected final paths.csv: {rows}")
    from scripts.build_submission import yaml_text
    if archive.read("sherlock/agents.yaml").decode() != yaml_text(*rows[1][1:]):
        raise ValueError("agents.yaml differs from the course YAML produced for this CSV row")
    (folder / "agents").mkdir()
    shutil.copyfile(research / "agents/__init__.py", folder / "agents/__init__.py")
    shutil.copytree(research / "lux", folder / "lux", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    archive.extractall(folder / "agents")


class NoResearchImports:
    def __init__(self, folder):
        self.folder = folder
        self.denied = []

    def find_spec(self, fullname, path=None, target=None):
        top = fullname.split(".", 1)[0]
        if top not in {"scripts", "sherlock", "agents", "lux"}:
            return None
        if top == "lux" or fullname in ("agents", "agents.sherlock") or fullname.startswith("agents.sherlock."):
            spec = PathFinder.find_spec(fullname, path)
            if spec and spec.origin and Path(spec.origin).resolve().is_relative_to(self.folder / top):
                return spec
        self.denied.append(fullname)
        raise ImportError(f"Final entrant tried to import a foreign module: {fullname}")


def course_process(pipe, folder, research, side):
    """Fresh interpreter: the unmodified course import, constructor and save/update lifecycle."""
    try:
        sys.dont_write_bytecode = True
        sys.path[:] = [p for p in sys.path if not Path(p).resolve().is_relative_to(research)]
        if any(name in sys.modules for name in ("scripts", "agents", "lux")):
            raise RuntimeError("Research modules already present in course interpreter")
        guard = NoResearchImports(folder)
        sys.meta_path.insert(0, guard)
        os.chdir(folder)
        sys.path.insert(0, str(folder))
        import torch
        torch.set_num_threads(1)
        torch.manual_seed(0)
        import pandas
        import agents  # runs the original course package discovery
        from lux.runner import _get_path_value, load_class_from_path
        paths = pandas.read_csv(folder / "agents/paths.csv", sep=";", encoding="cp1252")
        cls = load_class_from_path(_get_path_value(paths, 15, "Import_Path"))
        weights = _get_path_value(paths, 15, "Load_Path_P" + side[-1])
        if cls.__module__ != "agents.sherlock.main" or Path(sys.modules[cls.__module__].__file__).resolve() != folder / "agents/sherlock/main.py":
            raise RuntimeError("Wrong final course import")
        actor = cls(side, agent_path=weights)  # course run_agents(train=True) uses constructor defaults
        if Path(actor.agent_path).resolve() != folder / WEIGHTS:
            raise RuntimeError("Course entrant loaded a different weight file")
        while True:
            request = pipe.recv()
            if request is None:
                break
            method, args, kwargs = request
            value = getattr(actor, method)(*args, **kwargs)
            if guard.denied:
                raise ImportError(f"Course package requested research modules: {guard.denied}")
            if actor.caught_errors:
                raise RuntimeError(f"Course agent caught an error during {method}")
            if not any(m.startswith("agents.sherlock.v14.") for m in sys.modules):
                raise RuntimeError("Private packaged V14 was not imported")
            pipe.send((True, (value, dict(actor.selective_counts))))
    except Exception:
        pipe.send((False, traceback.format_exc()))
    finally:
        pipe.close()


class ComparedPlayer:
    """Adapter for the original play_game, which supplies the real transition to update."""
    def __init__(self, ref, pipe):
        self.ref, self.pipe = ref, pipe
        self.resets, self.match_wins = [], []
        self.movement = [0, 0, 0]
        self.sap_orders = self.nonzero_sap_offsets = 0
        self.actions = hashlib.sha256()
        self.updates = 0

    def remote(self, method, *args, **kwargs):
        self.pipe.send((method, args, kwargs))
        success, result = self.pipe.recv()
        if not success:
            raise RuntimeError(result)
        value, counts = result
        if self.ref.caught_errors or counts != dict(self.ref.selective_counts):
            raise ValueError(f"{method}, step {self.updates}: reference errors={self.ref.caught_errors}, "
                             f"counts reference={dict(self.ref.selective_counts)} course={counts}")
        return value

    def new_game(self, side):
        self.ref.new_game(side)  # course agent was freshly constructed in the other process

    def set_env_cfg(self, cfg):
        self.ref.set_env_cfg(cfg)
        self.remote("set_env_cfg", cfg)
        self.remote("save_agent")

    def act(self, step, obs):
        import numpy as np
        if int(obs["match_steps"]) == 0:
            self.resets.append(step)
            self.match_wins.append(np.asarray(obs["team_wins"]).astype(int).tolist())
        old = self.ref.selective_counts["movement"]
        want = np.asarray(self.ref.act(step=step, obs=deepcopy(obs)))
        actual = np.asarray(self.remote("act", step=step, obs=obs))
        if (actual.shape != (16, 3) or want.shape != (16, 3)
                or actual.dtype.kind not in "iu" or want.dtype.kind not in "iu"):
            raise ValueError(f"Invalid action matrix at step {step}")
        if not np.array_equal(actual, want):
            uid = int(np.flatnonzero(np.any(actual != want, axis=1))[0])
            raise ValueError(f"Step {step}, unit {uid}: reference={want[uid].tolist()} course={actual[uid].tolist()}")
        self.actions.update(actual.astype("<i8").tobytes())
        shots = actual[actual[:, 0] == 5, 1:]
        self.sap_orders += len(shots)
        self.nonzero_sap_offsets += int(np.any(shots != 0, axis=1).sum())
        self.movement[step // 101] += self.ref.selective_counts["movement"] - old
        return actual

    def update(self, **transition):
        self.remote("update", **transition)
        self.updates += 1


def run_side(folder, args, side):
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.common import make_opponent, play_game
    if args.diagonal:
        from scripts.r3_diagonal import DiagonalAgent as Adviser
    else:
        from scripts.selective_advice_agent import SelectiveAdviceAgent as Adviser
    ref = Adviser(side, agent_path=str(args.v14), advice_path=str(args.r3), mode="movement", train=False, seed=0)
    ref.set_to_eval_mode()
    rival = make_opponent("solution92", "player_1" if side == "player_0" else "player_0")
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe()
    proc = ctx.Process(target=course_process, args=(child, folder, args.research, side))
    env = LuxAIS3GymEnv(numpy_output=True)
    proc.start()
    child.close()
    player = ComparedPlayer(ref, parent)
    try:
        result = play_game(env, player, rival, SEED, side, train=True)
        parent.send(None)
        proc.join()
        counts = dict(ref.selective_counts)
        if (proc.exitcode or result["steps"] != 303 or player.updates != 303 or player.resets != [0, 101, 202]
                or result["our_wins"] + result["opp_wins"] != 3 or not sum(player.movement)
                or sum(player.movement) != counts.get("changed_unit_orders")
                or not counts.get("changed_steps")):
            raise ValueError(f"Incomplete parity run for {side}: steps={result['steps']}, resets={player.resets}, "
                             f"course updates={player.updates}, counts={counts}")
        return dict(seed=SEED, side=side, opponent="solution92", equal_action_matrices=result["steps"],
                    course_updates=player.updates, match_start_steps=player.resets,
                    team_wins_at_match_start=player.match_wins, final_wins=[result["our_wins"], result["opp_wins"]],
                    movements_per_match=player.movement, selective_counts=counts, caught_errors=0,
                    rejected_orders=counts.get("rejected_orders", 0), sap_orders=player.sap_orders,
                    nonzero_sap_offsets=player.nonzero_sap_offsets,
                    world_actions_int64_le_sha256=player.actions.hexdigest())
    finally:
        parent.close()
        if proc.is_alive():
            proc.terminate()
            proc.join()
        env.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagonal", action="store_true", help="Compare the registered diagonal course and research policies")
    for key in ("zip", "research", "v14", "r3", "out"):
        parser.add_argument("--" + key, type=lambda p: Path(p).resolve(), required=True)
    args = parser.parse_args()
    report = dict(format="final", import_path=IMPORT, load_paths=[WEIGHTS, WEIGHTS],
                  research_commit=COMMIT, games=[], result="failed")
    with args.out.open("x") as out:
        try:
            report.update(zip_sha256=digest(args.zip), v14_sha256=digest(args.v14), r3_sha256=digest(args.r3),
                          original_python_sources_sha256=research_digest(args.research), checker_sha256=digest(__file__))
            if args.diagonal:
                report.update(format="final_diagonal", diagonal_source_commit=DIAGONAL_COMMIT)
                if report["zip_sha256"] != DIAGONAL_ZIP:
                    raise ValueError("Different registered two-view ZIP")
            sources = DIAGONAL_SOURCES if args.diagonal else SOURCES
            if (report["original_python_sources_sha256"], report["v14_sha256"], report["r3_sha256"]) != (sources, V14, R3):
                raise ValueError("Research archive or input checkpoint differs from pinned sources")
            sys.dont_write_bytecode = True
            sys.path.insert(0, str(args.research))
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            os.environ["JAX_PLATFORMS"] = "cpu"
            import torch
            from luxai_s3 import env, params, wrappers
            torch.set_num_threads(1)
            torch.manual_seed(0)
            report["engine_sha256"] = {m.__name__: digest(m.__file__) for m in (env, params, wrappers)}
            with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(args.zip) as z:
                folder = Path(tmp).resolve()
                extract_entrant(z, folder, args.research, args.diagonal)
                report["course_weights_sha256"] = digest(folder / WEIGHTS)
                for side in ("player_0", "player_1"):
                    report["active_side"] = side
                    report["games"].append(run_side(folder, args, side))
                    if digest(folder / WEIGHTS) != report["course_weights_sha256"]:
                        raise ValueError(f"Course save/update changed weights on {side}")
                if args.diagonal:
                    for game in report["games"]:
                        original = STANDARD_ACTIONS[game["side"]]
                        game["standard_r3_actions_sha256"] = original
                        game["differs_from_standard_r3"] = original != game["world_actions_int64_le_sha256"]
                        if not game["nonzero_sap_offsets"]:
                            raise ValueError(f"No nonzero SAP offset observed on {game['side']}")
                    if not any(game["differs_from_standard_r3"] for game in report["games"]):
                        raise ValueError("Neither trajectory exercised a different final order than standard R3")
                del report["active_side"]
            if any(not Path(m.__file__).resolve().is_relative_to(args.research) for n, m in sys.modules.items()
                   if n.split(".", 1)[0] in ("agents", "scripts") and getattr(m, "__file__", None)):
                raise RuntimeError("Original policy imported foreign project sources")
            report["result"] = "passed"
        except Exception as exc:
            report["error"] = str(exc)
            raise
        finally:
            json.dump(report, out, indent=2, allow_nan=False)
            out.write("\n")


if __name__ == "__main__":
    main()
