"""Fixed 16-map study of the published R3 and R2 students as points-mode HybridAgent.

    python -m scripts.points_hybrid_screen play v14 --out RESULTS/v14
    python -m scripts.points_hybrid_screen play points_r3 --out RESULTS/r3
    python -m scripts.points_hybrid_screen assess --v14 RESULTS/v14 --r3 RESULTS/r3

Only for a separately requested external R2 comparison, run play points_r2 and pass its
directory to assess --r2. All paths are local inputs or output directories. No packing.
"""
import argparse
from importlib import metadata, util
import json
import os
from pathlib import Path
import platform
from types import SimpleNamespace

from scripts import final_battle_compare as base
from scripts import final_battle_assess as audit
from scripts.final_battle_select import OPPONENTS, checked_run_files

SEEDS = range(7278000, 7278016)
MODELS = {
    "points_r2": ("r2.pth", "23fa6208d76e81940916388b9ee56c1d290693e8febfa53622442b64b0d33f96"),
    "points_r3": ("r3_soft.pth", "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"),
}
OVERRIDES = {"imit_stay_bias": 1.5, "imit_unstack": True}
STUDY_FILE = "scripts/points_hybrid_screen.py"


def settings(arm, root):
    if arm not in ("v14", *MODELS):
        raise ValueError(f"Unregistered arm {arm}")
    opponents = (*OPPONENTS, "v14") if arm == "points_r3" else OPPONENTS
    model = None if arm == "v14" else str((Path(root) / "experiments/candidates/movement_dagger_20261115"
                                          / MODELS[arm][0]).resolve())
    return SimpleNamespace(candidate=arm, model=model, first=SEEDS.start, maps=len(SEEDS),
                           opponents=",".join(opponents))


def environment():
    package = Path(util.find_spec("luxai_s3").origin).parent
    return {"python": platform.python_version(), "platform": platform.system(), "machine": platform.machine(),
            "runtime_flags": {k: os.environ.get(k) for k in ("JAX_PLATFORMS", "XLA_FLAGS", "CUDA_VISIBLE_DEVICES",
                                                              "PYTHONHASHSEED")},
            "versions": {k: metadata.version(k) for k in ("numpy", "scipy", "torch", "jax", "jaxlib", "luxai-s3")},
            "lux_modules": {p.name: base.digest(p) for p in sorted(package.glob("*.py"))}}


def validate_arm(manifest, arm):
    model = None if arm == "v14" else MODELS[arm][1]
    hybrid = None if arm == "v14" else {"mode": "points", "student_overrides": OVERRIDES}
    expected = settings(arm, base.ROOT)
    if ((manifest["first"], manifest["maps"]) != (expected.first, expected.maps)
            or manifest["opponents"] != expected.opponents.split(",")):
        raise ValueError(f"Unexpected {arm} opponent or map panel")
    if manifest["candidate"] != arm or manifest["model"] != model or manifest["weights"] != audit.V14_SHA:
        raise ValueError(f"Unexpected {arm} model or V14 weights")
    if manifest["hybrid"] != hybrid:
        raise ValueError(f"Unexpected {arm} policy or student switches")


def study_contract(a):
    # Both arms execute shipped agent modules, all of which the V14 contract already hashes.
    core = SimpleNamespace(**{**vars(a), "candidate": "v14"})
    m = base.contract(core)
    m["candidate"] = a.candidate
    m["hybrid"] = None if a.candidate == "v14" else {"mode": "points", "student_overrides": dict(OVERRIDES)}
    for path in (STUDY_FILE, "agents/__init__.py", "scripts/fetch_kaggle3.py", "scripts/protocol.py",
                 "scripts/variants.py"):
        m["sources"][path] = base.digest(base.ROOT / path)
    m["environment"] = environment()
    validate_arm(m, a.candidate)
    return m


def init_worker(arm, model):
    if arm == "v14":
        base.init_worker(arm, model)
        return
    from scripts.experiment import limit_threads
    limit_threads()
    import torch
    from agents.sherlock.hybrid_agent import HybridAgent
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.par_eval import build_cfg
    torch.manual_seed(0)
    cfg = build_cfg(model, [])
    for key, value in OVERRIDES.items():
        setattr(cfg, key, value)
    agent = HybridAgent("player_0", str(base.WEIGHTS), model, mode="points", student_cfg=cfg)
    if len(agent.v14.extra_q) != 35 or not agent.student.has_sap_head:
        raise ValueError("Expected the full V14 ensemble and the student's learned SAP head")
    base.evaluate.agent, base.evaluate.env = agent, LuxAIS3GymEnv(numpy_output=True)


def play(job):
    row = base.evaluate(job, metrics=("unit_steps", "wait_frac", "invalid_frac", "sap_attempts", "sap_hits",
                                      "stack_frac", "relics_seen", "point_counting_version"))
    if job[0] in MODELS:
        agent = base.evaluate.agent
        if agent.v14.caught_errors or agent.student.caught_errors:
            raise RuntimeError("Hybrid child caught a policy error")
        row["study"] = dict(agent.stats)  # Unit routing counts, including identical orders.
    return row


def read_arm(directory, arm):
    opponents = settings(arm, base.ROOT).opponents.split(",")
    rows, manifest, hashes = checked_run_files(Path(directory), arm, SEEDS, opponents)
    validate_arm(manifest, arm)
    return audit.Run(manifest, rows, hashes)


def paired_arm(directory, arm, reference):
    run = read_arm(directory, arm)
    audit.compatible(reference, run)
    if (run.manifest["sources"] != reference.manifest["sources"]
            or run.manifest["environment"] != reference.manifest["environment"]):
        raise ValueError(f"Different sources or runtime for paired {arm} games")
    return run


def assess(v14, r3, r2=None):
    reference = audit.load_run(v14, "v14", SEEDS, OPPONENTS)
    validate_arm(reference.manifest, "v14")
    if STUDY_FILE not in reference.manifest["sources"] or not reference.manifest["environment"]["lux_modules"]:
        raise ValueError("Required study runner or engine provenance missing")
    candidate = paired_arm(r3, "points_r3", reference)
    result = audit.summarize(audit.Phase(reference, candidate, candidate, SEEDS, SEEDS), "screen")
    if r2:
        control = paired_arm(r2, "points_r2", reference)
        paired = audit.summarize(audit.Phase(control, candidate, candidate, SEEDS, SEEDS), "screen")
        for group in paired["by_opponent"].values():
            group["r2_wins"] = group.pop("v14_wins")
        result["r3_vs_r2_external"] = {"r2_files": control.hashes, "r2_model": control.manifest["model"],
                                        "by_opponent": paired["by_opponent"], "external": paired["external"]}
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("play")
    run.add_argument("arm", choices=("v14", *MODELS))
    run.add_argument("--out", required=True, type=Path)
    run.add_argument("--workers", choices=(1, 2), type=int, default=1)
    report = sub.add_parser("assess")
    for name in ("v14", "r3", "r2"):
        report.add_argument("--" + name, required=name != "r2", type=Path)
    args = p.parse_args()
    if args.command == "assess":
        print(json.dumps(assess(args.v14, args.r3, args.r2), indent=2, allow_nan=False))
        return
    a = settings(args.arm, base.ROOT)
    a.out, a.workers = args.out, args.workers
    a.out.mkdir(exist_ok=True, parents=True)
    base.run(a, get_contract=study_contract, initializer=init_worker, play=play)


if __name__ == "__main__":
    main()
