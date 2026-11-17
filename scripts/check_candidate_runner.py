"""Check a candidate with the unchanged course runner in a temporary workspace.

No training, no replacement of release weights. Uses already consumed development
seeds 500720/500721. Timing includes only Agent.act, not loading or environment.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

if __package__:
    from .xversion_replay import guard_course_calls
else:
    from xversion_replay import guard_course_calls

ROOT = Path(__file__).resolve().parent.parent
SEEDS = (500720, 500721)


def prepare_workspace(root: Path, weights: Path, destination: Path) -> None:
    root, weights, destination = root.resolve(), weights.resolve(), destination.resolve()
    if not weights.is_file():
        raise FileNotFoundError(weights)
    destination.mkdir(parents=True, exist_ok=False)
    copy = destination / "candidate.pth"
    shutil.copyfile(weights, copy)
    (destination / "agents").symlink_to(root / "agents", target_is_directory=True)
    with (root / "Paths.csv").open(encoding="cp1252", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        columns, rows = reader.fieldnames, list(reader)
    selected = [r for r in rows if r["Moodle Gruppe"] == "15"]
    if len(selected) != 1:
        raise ValueError("Expected exactly one group 15 in Paths.csv")
    selected[0]["Load_Path_P0"] = selected[0]["Load_Path_P1"] = str(copy)
    with (destination / "Paths.csv").open("w", encoding="cp1252", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def validate_actions(actions, max_units: int) -> None:
    a = np.asarray(actions)
    if (a.shape != (max_units, 3) or not np.isfinite(a).all()
            or not np.equal(a, np.floor(a)).all()
            or not ((a[:, 0] >= 0) & (a[:, 0] <= 5)).all()):
        raise ValueError("Invalid action shape, numeric value, or action type")


def write_report(out: Path, report: dict) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x") as f:
        json.dump(report, f, indent=2)
        f.write("\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_proxy(seeds) -> SimpleNamespace:
    values = iter(seeds)
    rng = SimpleNamespace(integers=lambda *a, **kw: next(values))
    return SimpleNamespace(random=SimpleNamespace(default_rng=lambda: rng))


def verify_loaded(agent, checkpoint: dict) -> None:
    """A playable randomly initialized fallback must never pass this check."""
    import torch
    from agents.sherlock.config import AgentConfig
    from agents.sherlock.features import FEATURE_DIM
    if isinstance(checkpoint, dict) and checkpoint.get("kind") == "hybrid" and "v14_ckpt" in checkpoint:
        # 15.11.2026: gepackter Hybrid (V14 + nachgeahmte Policy). V14-Teil wie jeder DQN-Checkpoint pruefen,
        # Schuelergewichte, Modus und Schuelerschalter bitgenau gegen die Datei.
        hybrid = getattr(agent, "_imitation", None)
        if hybrid is None or not hasattr(hybrid, "v14"):
            raise ValueError("Hybrid checkpoint was not delegated to a HybridAgent")
        verify_loaded(hybrid.v14, checkpoint["v14_ckpt"])
        expected = checkpoint["student_ckpt"]["policy"]
        loaded = hybrid.student.net.state_dict()
        if loaded.keys() != expected.keys() or any(not torch.equal(loaded[k].cpu(), expected[k].cpu()) for k in expected):
            raise ValueError("Loaded student weights differ")
        if hybrid.mode != checkpoint.get("mode", "points") or hybrid.combat_radius != int(checkpoint.get("combat_radius", 5)):
            raise ValueError("Hybrid mode differs")
        for key, value in checkpoint.get("student_overrides", {}).items():
            if getattr(hybrid.student.cfg, key) != value:
                raise ValueError(f"Student switch {key} differs")
        return
    if isinstance(checkpoint, dict) and checkpoint.get("kind") == "imitation":
        # 17.11.2026: reiner Schueler (nachgeahmte Policy, auch als Ensemble), von Agent_x an einen ImitationAgent
        # delegiert. Alle Netze bitgenau und die Spielschalter gegen die Datei pruefen.
        student = getattr(agent, "_imitation", None)
        if student is None or hasattr(student, "v14"):
            raise ValueError("Imitation checkpoint was not delegated to an ImitationAgent")
        nets = [student.net, *student.extra_nets]
        states = [checkpoint["policy"], *[m["policy"] for m in checkpoint.get("imitation_ensemble", [])]]
        if len(nets) != len(states):
            raise ValueError("Loaded student ensemble size differs")
        for net, state in zip(nets, states):
            loaded = net.state_dict()
            if loaded.keys() != state.keys() or any(not torch.equal(loaded[k].cpu(), state[k].cpu()) for k in state):
                raise ValueError("Loaded student weights differ")
        # PPOAgent setzt buffer_capacity=1 (kein Replay Buffer fuer eine reine Policy); sonst muss alles gleich sein
        loaded_cfg = dict(student.cfg.to_dict(), buffer_capacity=None)
        if loaded_cfg != dict(AgentConfig.from_dict(checkpoint["cfg"]).to_dict(), buffer_capacity=None):
            raise ValueError("Loaded student config differs")
        return
    if (not isinstance(checkpoint, dict) or "q" not in checkpoint
            or checkpoint.get("feature_dim", FEATURE_DIM) != agent.feat_dim
            or checkpoint.get("n_actions", agent.n_actions) != agent.n_actions):
        raise ValueError("Unsupported or incompatible checkpoint architecture")
    if agent.cfg.to_dict() != AgentConfig.from_dict(checkpoint["cfg"]).to_dict():
        raise ValueError("Loaded checkpoint config differs")
    expected = [checkpoint["q"], *checkpoint.get("ensemble", [])]
    actual = [agent.q, *agent.extra_q]
    if len(expected) != len(actual):
        raise ValueError("Loaded ensemble size differs")
    for model, state in zip(actual, expected):
        loaded = model.state_dict()
        if (loaded.keys() != state.keys()
                or any(not torch.equal(loaded[k].cpu(), state[k].cpu()) for k in state)):
            raise ValueError("Loaded model weights differ")
    if "cnn_policy" in checkpoint:
        raise ValueError("Mixed CNN/DQN checkpoints are not supported by this probe")


def run_check(weights: Path) -> dict:
    import torch
    import lux.runner as runner
    from agents.sherlock.main import Agent_x
    from luxai_s3.params import EnvParams

    if EnvParams().match_count_per_episode != 3:
        raise ValueError("Set the course match count to 3 first")
    torch.set_num_threads(1)
    protected = [ROOT / "agents/sherlock/weights" / f"agent_p{i}.pth" for i in (0, 1)]
    protected += [weights, ROOT / "Paths.csv", ROOT / "lux/runner.py"]
    hashes = {str(p): sha256(p) for p in protected}
    checkpoint = torch.load(weights, map_location="cpu", weights_only=False)
    records = []
    timings = []
    opponent = None

    class ObservedAgent(Agent_x):
        def __init__(self, player, agent_path=None):
            super().__init__(player, agent_path=agent_path)
            verify_loaded(self, checkpoint)
            clean = (not self.belief.relic_positions
                     and not self.belief.point_tiles.any()
                     and not self.belief.explored_ever.any()
                     and not self.belief.dead_tiles.any())
            if not clean:
                raise AssertionError("New agent retained game knowledge")
            self.probe = {"side": player, "opponent": opponent,
                          "seed": SEEDS[len(records) % len(SEEDS)],
                          "fresh_belief": clean, "loaded_model_verified": True, "steps": 0}
            self.probe_times = []
            records.append(self.probe)
            timings.append(self.probe_times)

        def act(self, step, obs):
            if self.probe["steps"] == 0 and step != 0:
                raise AssertionError("First step must be zero")
            if self.training:
                raise AssertionError("Runner did not select evaluation mode")
            started = time.perf_counter()
            actions = super().act(step, obs)
            self.probe_times.append(time.perf_counter() - started)
            validate_actions(actions, int(self.env_cfg["max_units"]))
            self.probe["steps"] += 1
            return actions

    loader = runner.load_class_from_path

    def load(path):
        cls = ObservedAgent if path == "agents.sherlock.main.Agent_x" else loader(path)

        class Guarded:
            """Erzeugt die echte Klasse mit Fehlerprüfung nach act/update (guard_course_calls). 17.11.2026: Der
            Kursrunner entscheidet über inspect.signature(Klasse.__init__), ob er agent_path übergibt; eine einfache
            Fabrikfunktion verdeckte diese Signatur, sodass die Gewichte des Kandidaten nicht übergeben wurden."""
            def __new__(klass, *args, **kwargs):
                return guard_course_calls(cls(*args, **kwargs))
        Guarded.__init__ = cls.__init__  # nur für die Signaturprüfung; __new__ liefert eine echte Instanz von cls
        return Guarded

    initial_cwd = Path.cwd()
    try:
        with tempfile.TemporaryDirectory(prefix="sherlock-runner-") as temp:
            workspace = Path(temp) / "workspace"
            prepare_workspace(ROOT, weights, workspace)
            os.chdir(workspace)
            with patch.object(runner, "_base_dir", str(workspace)), \
                    patch.object(runner, "load_class_from_path", load):
                for group, opponent in ((1, "default"), (2, "solution92")):
                    for side in (0, 1):
                        # Patch only the runner's RNG reference. Environment and agents
                        # retain their normal numpy modules and RNG implementations.
                        with patch.object(runner, "np", seed_proxy(SEEDS)):
                            pair = (15, group) if side == 0 else (group, 15)
                            runner.run_agents(*pair, games_to_play=2, train=False)
    finally:
        os.chdir(initial_cwd)
        for p in protected:
            if sha256(p) != hashes[str(p)]:
                raise AssertionError(f"Protected source changed: {p}")
    if len(records) != 8 or any(r["steps"] != 303 for r in records):
        raise AssertionError("Expected eight complete three-match games")
    for record, seconds in zip(records, timings):
        record["act_ms"] = {
            "median": float(np.median(seconds) * 1000),
            "p95": float(np.percentile(seconds, 95) * 1000),
            "max": float(max(seconds) * 1000),
        }
    return {
        "status": "passed", "games": records, "unchanged_sha256": hashes,
        "course_time_limit": "unknown; timings measured, no limit certified",
        "max_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "notes": [
            "Unchanged course runner; only workspace, class instrumentation and seed source patched.",
            "Solution_92 class-global state is not reset here, matching course runner behavior.",
            "Fresh Sherlock instance per game, as created by the course runner.",
            "Action check covers shape, integer values and type 0..5, not all game rules.",
            "Eight games on two reused development seeds are an integration test, not a winrate estimate.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    report = run_check(args.weights.resolve())
    write_report(args.out, report)
    print(f"Passed: {len(report['games'])} course-runner games; {args.out}")


if __name__ == "__main__":
    main()
