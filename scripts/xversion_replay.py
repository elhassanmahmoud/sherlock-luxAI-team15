"""Battle-Zip in einer anderen Python-/torch-/numpy-Version pruefen (30.10.2026).

Der Prof startet die Agents auf seinem Laptop (README der Vorlage: Windows, Python 3.10+, Pakete ohne
Versionen). `record` spielt mit der Zip ein echtes Spiel Sherlock gegen Sherlock wie der Kurs-Runner
(train=True: kein set_to_eval_mode, update() nach jedem Schritt) und zeichnet Beobachtungen und Aktionen
beider Seiten auf. `replay` laedt dieselbe Zip in einer anderen Umgebung, spielt die Beobachtungen nach und
zaehlt abweichende Aktionen. Bewusst ohne Projekt-Importe, damit es mit jedem Interpreter laeuft, der nur
torch und numpy hat (replay) bzw. zusaetzlich luxai_s3 (record).

    python scripts/xversion_replay.py record Gruppe15.zip spiel.pkl --seed 4242
    /pfad/zu/python3.10 -I scripts/xversion_replay.py replay Gruppe15.zip spiel.pkl
"""
import argparse
import atexit
import os
import pickle
import shutil
import sys
import tempfile
import zipfile

import numpy as np


def unpack(zip_path):
    """Zip wie beim Prof unter agents/ entpacken; Gewichte-Pfad bleibt relativ (Rueckfall neben main.py)."""
    base = tempfile.mkdtemp(prefix="xversion_")
    atexit.register(shutil.rmtree, base, True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(os.path.join(base, "agents"))
        group = next(n.split("/")[0] for n in z.namelist() if n.endswith("/main.py"))
    sys.path.insert(0, os.path.join(base, "agents"))
    os.chdir(base)
    module = __import__(f"{group}.main", fromlist=["Agent_x"])
    return module.Agent_x, f"{group}/agent.pth"


def plain(x):
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if isinstance(x, np.generic):
        return x.item()
    if hasattr(x, "tolist") and not isinstance(x, np.ndarray):
        return np.asarray(x).tolist()
    return x


def arrays(obs):
    return {k: ({kk: np.asarray(vv) for kk, vv in v.items()} if isinstance(v, dict) else np.asarray(v))
            for k, v in obs.items()}


def record(args):
    agent_cls, weights = unpack(args.zip)
    from luxai_s3.wrappers import LuxAIS3GymEnv
    env = LuxAIS3GymEnv(numpy_output=True)
    obs, info = env.reset(seed=args.seed)
    cfg = plain(info["params"])
    agents = [agent_cls("player_0", agent_path=weights), agent_cls("player_1", agent_path=weights)]
    for a in agents:
        a.set_env_cfg(cfg)
    rec, step, done = [], 0, False
    while not done:
        acts = {a.player: a.act(step=step, obs=obs[a.player]) for a in agents}
        nxt, rew, term, trunc, _ = env.step(acts)
        done = bool(term["player_0"] or trunc["player_0"] or term["player_1"] or trunc["player_1"])
        rec.append(dict(step=step, obs={p: plain(obs[p]) for p in obs}, rew={p: float(rew[p]) for p in rew},
                        acts={p: np.asarray(v).tolist() for p, v in acts.items()}, done=done,
                        next_obs={p: plain(nxt[p]) for p in nxt}))
        for a in agents:
            a.update(step=step, obs=obs[a.player], reward=float(rew[a.player]), action=acts[a.player],
                     terminated=done, next_obs=nxt[a.player])
        step += 1
        obs = nxt
    wins = np.asarray(obs["player_0"]["team_wins"]).tolist()
    with open(args.pkl, "wb") as f:
        pickle.dump(dict(cfg=cfg, rec=rec, wins=wins, py=sys.version), f, protocol=4)
    print(f"aufgezeichnet: {len(rec)} Schritte, Matchsiege {wins}, Netze {1 + len(agents[0].extra_q)}")


def replay(args):
    import torch
    agent_cls, weights = unpack(args.zip)
    with open(args.pkl, "rb") as f:
        d = pickle.load(f)
    agents = [agent_cls("player_0", agent_path=weights), agent_cls("player_1", agent_path=weights)]
    for a in agents:
        a.set_env_cfg(d["cfg"])
    diff, first = 0, None
    for r in d["rec"]:
        for a in agents:
            obs = arrays(r["obs"][a.player])
            act = np.asarray(a.act(step=r["step"], obs=obs)).tolist()
            if act != r["acts"][a.player]:
                diff += 1
                first = first or (r["step"], a.player)
            a.update(step=r["step"], obs=obs, reward=r["rew"][a.player], action=act, terminated=r["done"],
                     next_obs=arrays(r["next_obs"][a.player]))
    print(f"Python {sys.version.split()[0]}, torch {torch.__version__}, numpy {np.__version__} "
          f"(aufgezeichnet mit Python {d['py'].split()[0]}): {len(d['rec'])} Schritte, "
          f"Netze {1 + len(agents[0].extra_q)}, eingefroren {agents[0].cfg.frozen}, "
          f"abweichende Aktionen {diff}" + (f", erste bei {first}" if first else ""))
    return 1 if diff else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["record", "replay"])
    ap.add_argument("zip")
    ap.add_argument("pkl")
    ap.add_argument("--seed", type=int, default=4242)
    args = ap.parse_args()
    args.zip, args.pkl = os.path.abspath(args.zip), os.path.abspath(args.pkl)
    return record(args) if args.mode == "record" else replay(args)


if __name__ == "__main__":
    raise SystemExit(main())
