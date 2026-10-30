"""Wie entscheidet die Abgabe? Netz-Stimmen, Maske und Regeln je Unit und Step.

    python -m scripts.decision_trace --seeds 690000-690004 --opponent solution92 \
        --out experiments/analysis/decision_trace_20261026.json

Reine Diagnose fuer die Praesentation (26.10.2026, Fragen aus der Review): kein Training,
Gewichte werden nur gelesen. Pro Unit und Step wird festgehalten:
  raw        argmax des Ensemble-Mittels OHNE Maske (was die Netze am liebsten taeten)
  greedy     argmax des Ensemble-Mittels MIT Maske (was das Netz waehlt)
  final      Aktion nach allen Regeln (was wirklich gespielt wird)
  agree      wie viele der Netze einzeln (mit Maske) dieselbe Aktion wie das Mittel waehlen
  rules      Regeln, die die Aktion in diesem Step geaendert haben
Dazu je Kategorie ein echtes Beispiel mit Merkmalen und den Q-Werten aller Netze.
Kein Leistungsnachweis: die Spiele dienen nur der Beschreibung des Ablaufs.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import torch

ACTION_NAMES = ["stay", "up", "right", "down", "left", "sap"]
WEIGHTS = "agents/sherlock/weights/agent_p0.pth"

# Methode des Agenten -> (Name der Regel, hat sie etwas geaendert?)
RULE_HOOKS = {
    "_explore_action": ("scripted_explore", lambda args, out: out != args[1]),
    "_path_fix": ("path_fix", lambda args, out: out != args[1]),
    "_soft_nebula": ("nebula_soft", lambda args, out: out != args[1]),
    "_leave_nebula": ("nebula_exit", lambda args, out: out is not None),
    "_artillery_ok": ("art_sap", lambda args, out: bool(out)),
    "_sap_still": ("pt_sap", lambda args, out: bool(out)),  # letzte Bedingung von pt_sap
    "_overkill": ("no_overkill", lambda args, out: bool(out)),
}


def _group(a: int) -> str:
    return "move" if 1 <= a <= 4 else ACTION_NAMES[a]


def example_kind(r: dict, n_units: int, n_nets: int = 18) -> str | None:
    """Kategorie eines Datensatzes fuer die Beispielsammlung (None: kein Beispiel). Schwellen fuer 18 Netze
    (alle, mindestens 9, hoechstens 8), seit 30.10.2026 anteilig fuer andere Ensemblegroessen (V11: 36)."""
    late = r["match"] >= 1
    if r["agree"] == n_nets and 1 <= r["greedy"] <= 4 and r["n_legal"] >= 5 and not r["rules"] and late:
        return "einig"
    if r["masked_raw"] and 1 <= r["raw"] <= 4 and not r["rules"] and r["agree"] >= n_nets // 2 and late:
        return "maske"
    if "pt_sap" in r["rules"] and r["on_point"]:
        return "regel_pt_sap"
    if "path_fix" in r["rules"]:
        return "regel_path_fix"
    if r["agree"] <= n_nets * 8 // 18 and not r["rules"] and late and n_units >= 4:
        return "uneinig"
    return None


def summarize(rec: list[dict], n_nets: int) -> dict:
    """Anteile je Unit-Step (alle Werte zwischen 0 und 1, ausser mean_*)."""
    n = max(1, len(rec))
    changed = [r for r in rec if r["final"] != r["greedy"]]
    return dict(
        unit_steps=len(rec), nets=n_nets,
        mean_legal=float(np.mean([r["n_legal"] for r in rec])) if rec else 0.0,
        sap_legal_frac=sum(r["sap_legal"] for r in rec) / n,
        masked_raw_frac=sum(r["masked_raw"] for r in rec) / n,
        masked_raw_by_action={ACTION_NAMES[k]: v / n for k, v in
                              sorted(Counter(r["raw"] for r in rec if r["masked_raw"]).items())},
        all_agree_frac=sum(r["agree"] == n_nets for r in rec) / n,
        mean_agree=float(np.mean([r["agree"] for r in rec])) if rec else 0.0,
        majority_is_choice_frac=sum(r["agree"] == r["top_vote"] for r in rec) / n,
        agree_below_half_frac=sum(r["agree"] < n_nets / 2 + 1 for r in rec) / n,
        net_alone_frac=sum(not r["rules"] and r["final"] == r["greedy"] for r in rec) / n,
        rule_changed_frac=len(changed) / n,
        rule_change_kinds={k: v / n for k, v in Counter(
            f"{_group(r['greedy'])}->{_group(r['final'])}" for r in changed).most_common()},
        rule_fired_frac={k: v / n for k, v in Counter(x for r in rec for x in r["rules"]).most_common()},
        greedy_dist={ACTION_NAMES[k]: v / n for k, v in sorted(Counter(r["greedy"] for r in rec).items())},
        final_dist={ACTION_NAMES[k]: v / n for k, v in sorted(Counter(r["final"] for r in rec).items())},
    )


def trace(seeds: list[int], opponent: str = "solution92", weights: str = WEIGHTS) -> dict:
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.features import FEATURE_NAMES
    from agents.sherlock.main import Agent_x
    from scripts.common import make_opponent, play_game

    agent = Agent_x("player_0", agent_path=weights, train=False)
    agent.set_to_eval_mode()
    nets = [agent.q] + agent.extra_q
    rec: list[dict] = []
    examples: dict = {}
    fired: dict[int, list[str]] = {}
    game = {"seed": None, "side": None}

    for name, (label, changed) in RULE_HOOKS.items():
        def hook(ctx, uid, *args, _f=getattr(agent, name), _label=label, _changed=changed):
            out = _f(ctx, uid, *args)
            if _changed(args, out):
                fired.setdefault(int(uid), []).append(_label)
            return out
        setattr(agent, name, hook)

    original_act = agent._act

    def traced_act(step, obs):
        fired.clear()
        actions = original_act(step, obs)
        if int(np.asarray(obs["match_steps"])) == 0 or agent._cache is None:
            return actions
        _, ctx, ids, feats, masks, saps = agent._cache
        if not ids:
            return actions
        t = torch.as_tensor(np.stack([feats[u] for u in ids]), dtype=torch.float32)
        with torch.no_grad():
            per = torch.stack([m(t[:, :m.feat_dim]) for m in nets]).numpy()  # Netze x Units x 6
        mean = per.mean(0)
        mk = np.stack([masks[u] for u in ids])
        raw = mean.argmax(1)
        greedy = np.where(mk, mean, -np.inf).argmax(1)
        per_choice = np.where(mk[None], per, -np.inf).argmax(2)
        for k, u in enumerate(ids):
            votes = Counter(per_choice[:, k].tolist())
            x, y = int(ctx["ally_pos"][u][0]), int(ctx["ally_pos"][u][1])
            r = dict(step=int(ctx["step"]), match=int(ctx["match_idx"]), uid=int(u),
                     n_legal=int(mk[k].sum()), sap_legal=bool(mk[k][5]),
                     raw=int(raw[k]), greedy=int(greedy[k]), final=int(agent._prev_actions[u]),
                     agree=int(votes[int(greedy[k])]), top_vote=int(votes.most_common(1)[0][1]),
                     masked_raw=bool(not mk[k][raw[k]]), rules=list(fired.get(int(u), [])),
                     on_point=bool(ctx["point_tiles"][x, y]))
            rec.append(r)
            kind = example_kind(r, len(ids), len(nets))
            if kind and kind not in examples:
                examples[kind] = dict(
                    seed=game["seed"], side=game["side"], step=r["step"], match=r["match"] + 1,
                    uid=int(u), pos=[x, y], energy=float(ctx["ally_ene"][u]),
                    assigned=list(ctx["assigned"].get(int(u)) or []),
                    visible_enemies=int(len(ctx["enemy_coords"])), on_point=r["on_point"],
                    features={n: round(float(v), 3) for n, v in zip(FEATURE_NAMES, feats[u]) if abs(v) > 1e-6},
                    mask={ACTION_NAMES[a]: bool(mk[k][a]) for a in range(6)},
                    q_per_net=[[round(float(v), 3) for v in per[j, k]] for j in range(len(nets))],
                    q_mean=[round(float(v), 3) for v in mean[k]],
                    choice_per_net=[ACTION_NAMES[int(a)] for a in per_choice[:, k]],
                    raw=ACTION_NAMES[r["raw"]], greedy=ACTION_NAMES[r["greedy"]],
                    final=ACTION_NAMES[r["final"]], agree=r["agree"], rules=r["rules"],
                    sap_target=list(saps[u] or []))
        return actions

    agent._act = traced_act
    env = LuxAIS3GymEnv(numpy_output=True)
    games = []
    try:
        for s in seeds:
            for side in ("player_0", "player_1"):
                game.update(seed=s, side=side)
                opp = make_opponent(opponent, "player_1" if side == "player_0" else "player_0")
                res = play_game(env, agent, opp, s, side, train=False)
                games.append(dict(seed=s, side=side, our_wins=int(res["our_wins"]),
                                  opp_wins=int(res["opp_wins"])))
                print(f"  seed {s} als {side}: {res['our_wins']}-{res['opp_wins']}", flush=True)
    finally:
        env.close()
    return dict(weights=weights, opponent=opponent, seeds=seeds, games=games,
                **summarize(rec, len(nets)), examples=examples)


def _seed_list(text: str) -> list[int]:
    if "-" in text:
        a, b = (int(v) for v in text.split("-"))
        return list(range(a, b + 1))
    return [int(v) for v in text.split(",")]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", default="690000-690004")
    ap.add_argument("--opponent", default="solution92")
    ap.add_argument("--weights", default=WEIGHTS)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = trace(_seed_list(args.seeds), args.opponent, args.weights)
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "examples"}, indent=1))


if __name__ == "__main__":
    main()
