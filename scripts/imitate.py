"""Imitation Learning (15.11.2026): Sherlock lernt die Zuege des Kaggle-Platz-3-Agenten.

    # 1) Lehrer-Daten: der Lehrer spielt, ein Schatten-Sherlock baut fuer seine Seite die Netzeingaben
    python -m scripts.imitate collect --out experiments/imitation/k3_v1 --games 400 --workers 12
    # 2) Nachahmen: PolicyNet lernt die Lehrer-Aktion je Unit (maskierte Kreuzentropie)
    python -m scripts.imitate train --data experiments/imitation/k3_v1 --out experiments/imitation/k3_v1/student.pth
    # 3) Spielen/Messen: par_eval laedt Checkpoints mit kind="imitation" als ImitationAgent

Der Lehrer (scripts/kaggle3_opponent.py) ist nur Lehrer und Testgegner, nie Teil der Abgabe. Trainings-Seeds
ab 7200000 (getrennt von Dev A/B 7150000/7151000 und der Bestaetigung 7158000). Ausgaben nur unter
experiments/imitation/ (die Abgabe-Gewichte werden nie geschrieben).
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import random
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
V14 = ROOT / "agents" / "sherlock" / "weights" / "agent_p0.pth"
OUT_BASE = ROOT / "experiments" / "imitation"
PLANE_SCALE = 127.0
TRAIN_SEED0 = 7_200_000


def _check_out(path: Path) -> Path:
    path = path.resolve()
    weights = (ROOT / "agents" / "sherlock" / "weights").resolve()
    if weights == path or weights in path.parents:
        raise SystemExit("Ausgabe darf nicht im Abgabe-Gewichteordner liegen")
    return path


def v14_cfg():
    from agents.sherlock.main import Agent_x
    return Agent_x._cfg_from_checkpoint(str(V14))


def make_shadow(side: str, cfg):
    """Sherlock ohne eigenes Netz, nur fuer Gedaechtnis und Netzeingaben auf der Seite des Lehrers."""
    from agents.sherlock.imitation_agent import ImitationAgent
    shadow = ImitationAgent(side, agent_path=None, cfg=cfg, train=False, seed=0)
    shadow.set_to_eval_mode()
    return shadow


def make_player(kind: str, side: str):
    from scripts.common import make_opponent
    if kind == "v14":
        from agents.sherlock.main import Agent_x
        from scripts.par_eval import build_cfg
        p = Agent_x(side, agent_path=str(V14), cfg=build_cfg(str(V14), []), train=False, seed=0)
        p.set_to_eval_mode()
        p.autosave_on_terminate = False
        return p
    return make_opponent(kind, side)


class SideRecord:
    """Lehrer-Daten einer Seite eines Spiels."""

    def __init__(self) -> None:
        self.planes, self.step, self.pos, self.uid = [], [], [], []
        self.feats, self.mask, self.act, self.sdx, self.sdy, self.mstep = [], [], [], [], [], []

    def add(self, fz, teacher_actions, mirrored: bool) -> None:
        from agents.sherlock.imitation_agent import canonical_action
        ctx, ids, feats, masks, _, planes, pos = fz
        si = len(self.planes)
        self.planes.append(np.round(planes * PLANE_SCALE).astype(np.int8))
        for k, u in enumerate(ids):
            a, dx, dy = canonical_action(teacher_actions[u], mirrored)
            self.step.append(si)
            self.pos.append(pos[k])
            self.uid.append(u)
            self.feats.append(feats[k])
            self.mask.append(masks[k])
            self.act.append(a)
            self.sdx.append(dx)
            self.sdy.append(dy)
            self.mstep.append(int(ctx["match_step"]))

    def save(self, path: Path, meta: dict) -> int:
        if not self.act:
            return 0
        np.savez_compressed(
            path, planes=np.stack(self.planes), step=np.array(self.step, np.int32),
            pos=np.array(self.pos, np.int8), uid=np.array(self.uid, np.int8),
            feats=np.array(self.feats, np.float16), mask=np.array(self.mask, bool),
            act=np.array(self.act, np.int8), sdx=np.array(self.sdx, np.int8), sdy=np.array(self.sdy, np.int8),
            mstep=np.array(self.mstep, np.int16), meta=json.dumps(meta))
        return len(self.act)


def _collect_worker(job) -> list[dict]:
    games, out_dir = job
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv
    from scripts.kaggle3_opponent import Kaggle3Opponent

    env = LuxAIS3GymEnv(numpy_output=True)
    cfg = v14_cfg()
    done_meta = []
    for seed, tside, opp_kind in games:
        oside = "player_1" if tside == "player_0" else "player_0"
        players = {tside: Kaggle3Opponent(tside), oside: make_player(opp_kind, oside)}
        teacher_sides = [tside] + ([oside] if opp_kind == "kaggle3" else [])
        shadows = {s: make_shadow(s, cfg) for s in teacher_sides}
        for s_, p in list(players.items()) + list(shadows.items()):
            if hasattr(p, "new_game"):
                p.new_game(s_)
        obs, info = env.reset(seed=seed)
        for p in list(players.values()) + list(shadows.values()):
            if hasattr(p, "set_env_cfg"):
                p.set_env_cfg(info["params"])
        recs = {s: SideRecord() for s in teacher_sides}
        step, done = 0, False
        while not done:
            fzs = {s: featurize_safe(shadows[s], obs[s]) for s in teacher_sides}
            acts = {s: np.asarray(players[s].act(step, obs[s])) for s in players}
            for s, fz in fzs.items():
                if fz is not None:
                    recs[s].add(fz, acts[s], shadows[s].belief.mirrored)
            obs, _, term, trunc, info = env.step(acts)
            done = bool(np.asarray(term[tside])) or bool(np.asarray(trunc[tside]))
            step += 1
        wins = np.asarray(obs[tside]["team_wins"]).tolist()
        for s in teacher_sides:
            team = 0 if s == "player_0" else 1
            meta = dict(seed=seed, side=s, opponent=opp_kind, teacher_wins=int(wins[team]),
                        opp_wins=int(wins[1 - team]), sap_range=int(info["params"]["unit_sap_range"])
                        if "params" in info else None)
            n = recs[s].save(Path(out_dir) / f"g{seed}_{s}_{opp_kind}.npz", meta)
            done_meta.append({**meta, "samples": n})
    env.close()
    return done_meta


def _dagger_worker(job) -> list[dict]:
    """DAgger: der Schueler spielt selbst, ein Schatten-Lehrer auf seiner Seite sagt fuer genau diese Lagen,
    was er getan haette. So lernt das Netz auch Zustaende, in die nur seine eigenen Fehler fuehren."""
    games, out_dir, student_path = job[:3]
    overrides = job[3] if len(job) > 3 else []
    from scripts.experiment import limit_threads
    limit_threads()
    from luxai_s3.wrappers import LuxAIS3GymEnv

    from agents.sherlock.imitation_agent import ImitationAgent
    from scripts.kaggle3_opponent import Kaggle3Opponent

    env = LuxAIS3GymEnv(numpy_output=True)
    done_meta = []
    for seed, sside, opp_kind in games:
        oside = "player_1" if sside == "player_0" else "player_0"
        if overrides:
            from scripts.par_eval import build_cfg
            student = ImitationAgent(sside, agent_path=student_path, train=False,
                                     cfg=build_cfg(student_path, overrides))
        else:
            student = ImitationAgent(sside, agent_path=student_path, train=False)
        student.set_to_eval_mode()
        opp = make_player(opp_kind, oside)
        teacher = Kaggle3Opponent(sside)
        for s_, p in ((sside, student), (oside, opp)):
            if hasattr(p, "new_game"):
                p.new_game(s_)
        obs, info = env.reset(seed=seed)
        for p in (student, opp, teacher):
            if hasattr(p, "set_env_cfg"):
                p.set_env_cfg(info["params"])
        rec = SideRecord()
        step, done = 0, False
        while not done:
            label = np.asarray(teacher.act(step, obs[sside]))
            acts = {sside: np.asarray(student.act(step, obs[sside])), oside: np.asarray(opp.act(step, obs[oside]))}
            if student.last_fz is not None:
                rec.add(student.last_fz, label, student.belief.mirrored)
            obs, _, term, trunc, info = env.step(acts)
            teacher.remember_played_actions(acts[sside])
            done = bool(np.asarray(term[sside])) or bool(np.asarray(trunc[sside]))
            step += 1
        wins = np.asarray(obs[sside]["team_wins"]).tolist()
        team = 0 if sside == "player_0" else 1
        meta = dict(seed=seed, side=sside, opponent=opp_kind, dagger=True, student=str(student_path),
                    teacher_history="played_student_actions",
                    student_wins=int(wins[team]), opp_wins=int(wins[1 - team]))
        n = rec.save(Path(out_dir) / f"g{seed}_{sside}_{opp_kind}_dagger.npz", meta)
        done_meta.append({**meta, "samples": n})
    env.close()
    return done_meta


def cmd_dagger(a) -> None:
    out = _check_out(Path(a.out))
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed0)
    mix = [(k, float(v)) for k, v in (kv.split(":") for kv in a.mix.split(","))]
    kinds, weights = zip(*mix)
    games = [(a.seed0 + i, rng.choice(["player_0", "player_1"]), rng.choices(kinds, weights)[0])
             for i in range(a.games)]
    chunks = [games[i::a.workers] for i in range(a.workers) if games[i::a.workers]]
    t0 = time.time()
    student = str(Path(a.student).resolve())
    with mp.get_context("spawn").Pool(len(chunks)) as pool:
        metas = [m for part in pool.map(_dagger_worker, [(c, str(out), student, a.set) for c in chunks]) for m in part]
    (out / "collect.json").write_text(json.dumps(dict(
        games=a.games, seed0=a.seed0, mix=a.mix, dagger=True, student=student, student_set=a.set,
        teacher="kaggle3 lux3-bot 0.4.8_fn",
        samples=sum(m["samples"] for m in metas), secs=round(time.time() - t0)), indent=1))
    by = {}
    for m in metas:
        w, n = by.get(m["opponent"], (0, 0))
        by[m["opponent"]] = (w + int(m["student_wins"] > m["opp_wins"]), n + 1)
    print(f"DAgger: {len(metas)} Spiele, {sum(m['samples'] for m in metas)} Entscheidungen in {time.time() - t0:.0f}s; "
          "Schueler gewinnt " + ", ".join(f"{k} {w}/{n}" for k, (w, n) in by.items()))


def featurize_safe(shadow, obs):
    from agents.sherlock.imitation_agent import featurize
    return featurize(shadow, obs)


def cmd_collect(a) -> None:
    out = _check_out(Path(a.out))
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed0)
    mix = [(k, float(v)) for k, v in (kv.split(":") for kv in a.mix.split(","))]
    kinds, weights = zip(*mix)
    games = []
    for i in range(a.games):
        seed = a.seed0 + i
        games.append((seed, rng.choice(["player_0", "player_1"]), rng.choices(kinds, weights)[0]))
    chunks = [games[i::a.workers] for i in range(a.workers) if games[i::a.workers]]
    t0 = time.time()
    with mp.get_context("spawn").Pool(len(chunks)) as pool:
        metas = [m for part in pool.map(_collect_worker, [(c, str(out)) for c in chunks]) for m in part]
    (out / "collect.json").write_text(json.dumps(dict(
        games=a.games, seed0=a.seed0, mix=a.mix, teacher="kaggle3 lux3-bot 0.4.8_fn", shadow_cfg="V14 agent_p0.pth",
        samples=sum(m["samples"] for m in metas), files=len(metas), secs=round(time.time() - t0)), indent=1))
    tw = sum(m["teacher_wins"] > m["opp_wins"] for m in metas if m["opponent"] != "kaggle3")
    nk = sum(1 for m in metas if m["opponent"] != "kaggle3")
    print(f"{len(metas)} Lehrer-Seiten, {sum(m['samples'] for m in metas)} Unit-Entscheidungen in "
          f"{time.time() - t0:.0f}s; Lehrer gewinnt {tw}/{nk} Spiele gegen andere Gegner")


# ------------------------------------------------------------------ Training
def concat_games(files, *, with_base=False):
    columns = ("pos", "feats", "mask", "act", "sdx", "sdy") + (("base_act",) if with_base else ())
    planes, rows = [], {k: [] for k in ("step", *columns)}
    off = 0
    for path in files:
        with np.load(path, allow_pickle=False) as z:
            board = z["planes"]
            planes.append(board)
            rows["step"].append(z["step"].astype(np.int64) + off)
            off += len(board)
            for k in columns:
                rows[k].append(z[k])
    return np.concatenate(planes), {k: np.concatenate(v) for k, v in rows.items()}


def partition_files(dirs: list[str], val_frac: float, seed: int):
    files = sorted(f for d in dirs for f in Path(d).glob("g*.npz"))
    rng = random.Random(seed)
    games = sorted({f.name.split("_")[0] for f in files})
    val_games = set(rng.sample(games, max(1, int(len(games) * val_frac))))
    parts = {"train": [], "val": []}
    for f in files:
        parts["val" if f.name.split("_")[0] in val_games else "train"].append(f)

    return parts


def load_data(dirs: list[str], val_frac: float, seed: int):
    parts = partition_files(dirs,val_frac,seed)
    return concat_games(parts["train"]), concat_games(parts["val"]), len(parts["train"]), len(parts["val"])


def selective_data(dirs):
    """Nutze exakt die pruefsummengebundenen Karten/Sitze der Kampfspezialisten-Diagnose."""
    from scripts.train_combat_advice import input_index, make_plan

    plan = make_plan(7271000, 32, 7271032, 8)
    records = input_index(dirs, plan)
    train, val = (concat_games([r["path"] for r in records[k]], with_base=True) for k in ("train","val"))
    identities = {k: [{name: r[name] for name in ("seed","side","sha256")} for r in group]
                  for k, group in records.items()}
    return train, val, len(records["train"]), len(records["val"]), identities


def action_loss(logits, teachers, base_actions=None):
    import torch.nn.functional as F

    if base_actions is None:
        return F.cross_entropy(logits, teachers)
    per_row = F.cross_entropy(logits, teachers, reduction="none")
    weights = 1 + 2 * ((base_actions == 5) | (teachers == 5)).to(per_row.dtype)
    return (per_row * weights).sum() / weights.sum()


def movement_distillation_loss(student, teacher, legal, temperature):
    """T² KL(teacher || student) over the legal movement classes of the selected rows."""
    import torch
    import torch.nn.functional as F

    teacher_logp = F.log_softmax((teacher / temperature).masked_fill(~legal, -torch.inf), dim=1)
    student_logp = F.log_softmax((student / temperature).masked_fill(~legal, -torch.inf), dim=1)
    # Exactly zero contribution and gradient off the legal support; avoid (-inf) - (-inf).
    difference = teacher_logp.masked_fill(~legal, 0) - student_logp.masked_fill(~legal, 0)
    return temperature ** 2 * (teacher_logp.exp() * difference).sum() / max(1, len(student))


def prepare_labels(rows, width, height):
    """Rekonstruiert die Spielmaske aus ganzzahligen Spielwerten im Float16-Archiv.

    Die Demonstration wird erst danach auf Lernbarkeit geprueft. Beide Zielkoordinaten
    vor dem Abflachen pruefen, damit ein Randueberlauf kein anderes Feld bezeichnet.
    """
    import torch

    rows["act"], rows["pos"] = rows["act"].long(), rows["pos"].long()
    feats = rows["feats"].float()
    rows["mask"][:, 5] = torch.round(feats[:, 2] * 400) >= torch.round(feats[:, 7] * 50)
    rows["rng"] = torch.round(feats[:, 8] * 7).long()
    dx, dy = rows["sdx"].long(), rows["sdy"].long()
    tx, ty = rows["pos"][:, 0] + dx, rows["pos"][:, 1] + dy
    on_board = (tx >= 0) & (tx < width) & (ty >= 0) & (ty < height)
    in_range = torch.maximum(dx.abs(), dy.abs()) <= rows["rng"]
    action_ok = rows["mask"].gather(1, rows["act"][:, None]).squeeze(1)
    shot = rows["act"] == 5
    rows["sap_label"] = shot & action_ok & on_board & in_range
    rows["admitted"] = action_ok & (~shot | rows["sap_label"])
    rows["tgt"] = tx * height + ty


def agreement(action_logits, labels, valid_shots, shot_logits, targets, height):
    """Vollstaendig richtige Befehle; Zielgenauigkeit separat fuer legale Lehrer-Schuesse."""
    actions = action_logits.argmax(1)
    joint = ((labels != 5) & (actions == labels)).sum()
    if shot_logits is None:
        return joint, 0, 0
    pred = shot_logits.argmax(1)
    exact = pred == targets
    near = ((pred // height - targets // height).abs().maximum(
        (pred % height - targets % height).abs()) <= 1)
    joint += ((actions[valid_shots] == 5) & exact).sum()
    return joint, exact.sum(), near.sum()


def add_previous_enemy_input(net):
    """Append one trainable zero channel to the already initialized R2 convolution."""
    import torch
    conv = net.stem[0]
    if conv.in_channels != 16 or conv.groups != 1:
        raise ValueError("Expected the original 16-channel student stem")
    w = conv.weight.detach()
    conv.weight = torch.nn.Parameter(torch.cat((w, torch.zeros_like(w[:, :1])), dim=1))
    conv.in_channels = 17
    net.arch["in_ch"] = 17


def verify_initial_history_outputs(net):
    """Check the actual freshly seeded student before any optimizer update, using no labels or RNG."""
    import torch
    board = torch.linspace(-1., 1., 2*16*24*24).reshape(2,16,24,24)
    positions = torch.tensor([[0,0],[10,8],[23,23]])
    features = torch.linspace(-1., 1., 3*net.arch["feat_dim"]).reshape(3,-1)
    args = (torch.tensor([0,1,1]), positions, features)
    with torch.no_grad():
        original = net.forward_all(board,*args)
        add_previous_enemy_input(net)
        # First decision of a match and a later frame with observed enemy occupancy.
        lag = torch.zeros_like(board[:,:1])
        lag[1,0,7:12,3:5] = 32/127
        wider = net.forward_all(torch.cat((board,lag),dim=1),*args)
        differences = []
        for old, new in zip(original,wider):
            torch.testing.assert_close(new,old,rtol=1e-5,atol=1e-6)
            differences.append(float((new-old).abs().max()))
    return dict(device="cpu", rtol=1e-5, atol=1e-6, max_abs_by_head=differences)


def train_student(train, val, a, log):
    import torch
    import torch.nn.functional as F

    from agents.sherlock.features import FEATURE_DIM
    from agents.sherlock.imitation_net import ImitationNet, masked_sap_logits

    dev = torch.device(a.device if a.device != "auto" else ("mps" if torch.backends.mps.is_available() else "cpu"))
    torch.manual_seed(a.seed)
    net = ImitationNet(feat_dim=FEATURE_DIM, n_actions=6, ch=a.ch, blocks=a.blocks, hidden=a.hidden,
                       detach_value=True, sap_head=True)
    if getattr(a, "previous_enemy", False):
        if getattr(a, "movement_distillation", None) is not None:
            raise ValueError("Soft movement targets and previous enemy history are separate experiments")
        a.previous_enemy_initial_parity = verify_initial_history_outputs(net)
        log(f"Fresh seeded CPU network, before/after adding input 17: {a.previous_enemy_initial_parity}")
    net = net.to(dev)
    if train[0].shape[1] != net.arch["in_ch"] or val[0].shape[1] != net.arch["in_ch"]:
        raise ValueError("Wrong number of input board channels")

    if getattr(a, "own_command_input", False):
        from scripts.own_command_study import widen_and_check
        a.initial_parity = widen_and_check(net)
        log(f"Before the first update, own-command input parity: {a.initial_parity}")
    low_memory = getattr(a, "low_memory", False)
    selective = "base_act" in train[1]
    step_rng = np.random.default_rng(a.seed) if selective else np.random

    def to_dev(planes, rows):
        if low_memory:
            return torch.from_numpy(planes), {k:torch.from_numpy(v) for k,v in rows.items()}
        # Beim kleinen Fokuslauf bleiben die kompakten int8-Karten im Hauptspeicher.
        return (torch.as_tensor(planes, device="cpu" if selective else dev),
                {k: torch.as_tensor(v.astype(np.float32) if k == "feats" else v).to(dev) for k, v in rows.items()})

    P, R = to_dev(*train)
    Pv, Rv = to_dev(*val)
    if P.shape[-2:] != Pv.shape[-2:]:
        raise ValueError("Training und Validierung haben unterschiedliche Kartengroessen")
    width, height = P.shape[-2:]
    for name, rows in (("Training", R), ("Validierung", Rv)):
        if not low_memory:
            prepare_labels(rows, width, height)
        shot = rows["act"] == 5
        center = rows["sap_label"] & (rows["sdx"] == 0) & (rows["sdy"] == 0)
        log(f"{name}: {int(rows['admitted'].sum())}/{len(shot)} Befehle im Spiel ausfuehrbar, "
            f"{int(rows['sap_label'].sum())}/{int(shot.sum())} legale Schusslabels, "
            f"davon {int(center.sum())} auf das eigene Feld")
    train_idx = torch.where(R["admitted"])[0]
    n = len(train_idx)
    if n == 0:
        raise ValueError("Keine ausfuehrbaren Lehrerbefehle im Training")
    counts = torch.bincount(R["act"][train_idx].long().cpu(), minlength=6).float()
    if selective:
        focused = ((R["act"][train_idx] == 5) | (R["base_act"][train_idx] == 5)).sum().item()
        log(f"Aktionsverlust: {int(focused)}/{n} ausfuehrbare Zeilen mit V14- oder Lehrer-SAP erhalten Gewicht 3")
    log(f"Trainingsdaten: {n} Unit-Entscheidungen, Verteilung " +
        ", ".join(f"{nm} {100 * c / n:.1f} %" for nm, c in zip(("stay", "up", "right", "down", "left", "sap"), counts.tolist())))
    opt = torch.optim.AdamW(net.parameters(), lr=a.lr, weight_decay=1e-4)
    train_step_np = train[1]["step"][train_idx.cpu().numpy()]
    val_step_np = val[1]["step"]
    n_steps = len(np.unique(train_step_np))
    k_steps = max(8, int(round(a.mb * n_steps / max(1, n))))
    steps_total = a.epochs * ((n_steps + k_steps - 1) // k_steps)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=steps_total, pct_start=0.1)

    def step_batches(Rt_step_np, k, shuffle):
        """Minibatches aus k Spielschritten mit allen Units (Zeilen eines Schritts liegen zusammen).
        Liefert (Zeilenindex, Schritte, inverse Zuordnung Zeile -> Schritt im Batch)."""
        steps_all = np.unique(Rt_step_np)
        starts = np.searchsorted(Rt_step_np, steps_all, side="left")
        ends = np.searchsorted(Rt_step_np, steps_all, side="right")
        order = step_rng.permutation(len(steps_all)) if shuffle else np.arange(len(steps_all))
        for b in range(0, len(order), k):
            sel = order[b:b + k]
            counts = ends[sel] - starts[sel]
            idx = np.repeat(starts[sel] - np.concatenate([[0], np.cumsum(counts)[:-1]]), counts) + np.arange(counts.sum())
            inv = np.repeat(np.arange(len(sel)), counts)
            index_device = "cpu" if low_memory else dev
            yield (torch.as_tensor(idx, device=index_device), torch.as_tensor(steps_all[sel], device=index_device),
                   torch.as_tensor(inv, device=index_device))

    def batch_logits(Pt, Rt, idx, uniq, inv, model, target_device):
        planes = Pt[uniq.to(Pt.device)].to(target_device, dtype=torch.float32) / PLANE_SCALE
        pos = Rt["pos"][idx].to(target_device, dtype=torch.long)
        feats = Rt["feats"][idx].to(target_device, dtype=torch.float32)
        inv = inv.to(target_device)
        logits, _, smap = model.forward_all(planes, inv, pos, feats)
        logits = logits.masked_fill(~Rt["mask"][idx].to(target_device), -torch.inf)
        sel = Rt["sap_label"][idx].to(target_device)
        s_logits = s_tgt = None
        if bool(sel.any()):
            radius = Rt["rng"][idx].to(target_device, dtype=torch.long)
            s_logits = masked_sap_logits(smap, inv[sel], pos[sel], radius[sel])
            s_tgt = Rt["tgt"][idx].to(target_device, dtype=torch.long)[sel]
        return logits, sel, s_logits, s_tgt

    def evaluate(start=0, stop=None):
        # Keep optimizer parameters and moments on the training device. Only validation uses a CPU copy.
        if low_memory and dev.type != "cpu":
            from copy import deepcopy
            eval_net = deepcopy(net).to("cpu").eval()
        else:
            eval_net = net.eval()
        eval_device = torch.device("cpu") if low_memory else dev
        correct = torch.zeros(6, device=eval_device)
        total = torch.zeros(6, device=eval_device)
        stop = len(val_step_np) if stop is None else stop
        joint_correct = 0
        sap_n = sap_hit = sap_near = 0
        with torch.no_grad():
            for idx, uniq, inv in step_batches(val_step_np[start:stop], 32 if selective or low_memory else 512, False):
                if start:
                    idx = idx + start
                lg, sel, s_lg, s_tgt = batch_logits(Pv, Rv, idx, uniq, inv, eval_net, eval_device)
                pred = lg.argmax(1)
                y = Rv["act"][idx].to(eval_device, dtype=torch.long)
                joint, hit, near = agreement(lg, y, sel, s_lg, s_tgt, height)
                joint_correct += int(joint)
                sap_n += int(sel.sum())
                sap_hit += int(hit)
                sap_near += int(near)
                for c in range(6):
                    sel = y == c
                    total[c] += sel.sum()
                    correct[c] += (pred[sel] == c).sum()
        net.train()
        acc = float(correct.sum() / total.sum())
        per = [float(correct[c] / total[c]) if total[c] > 0 else float("nan") for c in range(6)]
        exact = sap_hit / sap_n if sap_n else float("nan")
        near = sap_near / sap_n if sap_n else float("nan")
        return acc, per, joint_correct / (stop - start), exact, near

    log(f"Minibatch: {k_steps} Spielschritte (im Mittel etwa {a.mb} Unit-Entscheidungen), Geraet {dev}")
    distill = getattr(a, "movement_distillation", None)
    for ep in range(a.epochs):
        tot, cnt, t0 = 0.0, 0, time.time()
        used_soft = 0
        for idx, uniq, inv in step_batches(train_step_np, k_steps, True):
            idx = train_idx[idx]
            lg, _, s_lg, s_tgt = batch_logits(P, R, idx, uniq, inv, net, dev)
            loss = action_loss(lg, R["act"][idx].to(dev, dtype=torch.long), R["base_act"][idx] if selective else None)
            if s_lg is not None:
                loss = loss + a.sap_weight * F.cross_entropy(s_lg, s_tgt)
            if distill is not None:
                selected = torch.where(R["distill_ok"][idx])[0]
                if selected.numel():
                    soft_rows = idx[selected]
                    soft_loss = movement_distillation_loss(lg[selected, :5], R["movement_scores"][soft_rows],
                                                          R["mask"][soft_rows, :5], distill["temperature"])
                    loss = loss + distill["weight"] * soft_loss
                    used_soft += selected.numel()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            opt.step()
            sched.step()
            tot += loss.item() * len(idx)
            cnt += len(idx)
        if distill is not None:
            if used_soft != distill["eligible_train_rows"]:
                raise ValueError("Soft movement rows used differ from the eligible training rows")
            distill["used_train_rows_per_epoch"].append(used_soft)
            log(f"Epoche {ep+1}: {used_soft}/{cnt} Trainingszeilen mit Bewegungs-KL "
                f"(T={distill['temperature']}, Gewicht {distill['weight']})")
        acc, per, joint_acc, s_acc, s_near = evaluate()
        log(f"Epoche {ep + 1}/{a.epochs}: Loss {tot / cnt:.4f} | Validierung Aktion {100 * acc:.1f} % "
            f"| vollstaendiger Befehl {100 * joint_acc:.1f} % | je Aktion " +
            " ".join(f"{nm} {100 * p:.0f}" for nm, p in zip(("stay", "up", "right", "down", "left", "sap"), per)) +
            f" | Ziel bei legalem Lehrerschuss exakt {100 * s_acc:.0f} %, +-1 Feld {100 * s_near:.0f} % | {time.time() - t0:.0f}s")
    for cohort, start, stop in getattr(a, "validation_groups", ()):
        acc, _, joint, exact, _ = evaluate(start, stop)
        log(f"Fixe letzte Epoche, {cohort}: {stop-start} Zeilen | Aktion {100*acc:.2f} % "
            f"| voller Befehl {100*joint:.2f} % | Ziel bei legalem Lehrerschuss {100*exact:.2f} %")
    return net.to("cpu").eval()


def cmd_train(a) -> None:
    from contextlib import ExitStack
    from agents.sherlock.ppo_agent import save_policy

    out = _check_out(Path(a.out))
    if out.exists():
        raise SystemExit(f"{out} existiert schon")
    out.parent.mkdir(parents=True, exist_ok=True)
    log_path = out.with_suffix(".log")

    def log(msg):
        print(msg, flush=True)
        with open(log_path, "a") as fh:
            fh.write(msg + "\n")

    t0 = time.time()
    extra = {}
    with ExitStack() as resources:
        if getattr(a, "selective", False):
            train, val, nt, nv, inputs = selective_data(a.data)
            extra["selective_training"] = dict(inputs=inputs, combat_action_weight=3, other_action_weight=1,
                                               target_weight=a.sap_weight, mb=a.mb, seed=a.seed, lr=a.lr,
                                               lr_schedule="OneCycleLR", optimizer="AdamW")
        elif getattr(a, "low_memory", False):
            import tempfile
            from scripts.imitation_storage import store_partition
            parts = partition_files(a.data, a.val_frac, a.seed)
            nt, nv = len(parts["train"]), len(parts["val"])
            tmp = Path(resources.enter_context(tempfile.TemporaryDirectory(prefix=".imitation-data-",dir=out.parent)))
            train, val = (store_partition(parts[k],tmp/k,prepare_labels) for k in ("train","val"))
            disk_bytes = sum(f.stat().st_size for f in tmp.glob("*/*"))
            log(f"Temporärer Plattenspeicher {disk_bytes / 2**30:.2f} GiB; Validierung auf CPU")
        else:
            train, val, nt, nv = load_data(a.data, a.val_frac, a.seed)
        log(f"Dateien: {nt} Training, {nv} Validierung (getrennt nach Spiel), geladen in {time.time() - t0:.0f}s")
        net = train_student(train, val, a, log)
        del train, val
    cfg = v14_cfg()
    save_policy(str(out), net, cfg, extra={"kind": "imitation", "teacher": "kaggle3 lux3-bot 0.4.8_fn",
                                           "data": a.data, "epochs": a.epochs,
                                           # Zielkopf mit dem eigenen Feld als legalem Ziel trainiert (masked_sap_logits)
                                           "sap_own_tile": True, **extra})
    log(f"gespeichert: {out} ({sum(p.numel() for p in net.parameters())} Parameter)")


def cmd_ensemble(a) -> None:
    """Mehrere Schueler zu einem Checkpoint buendeln (erster = Hauptnetz, Rest = imitation_ensemble)."""
    import torch
    out = _check_out(Path(a.out))
    if out.exists():
        raise SystemExit(f"{out} existiert schon")
    cks = [torch.load(p, map_location="cpu", weights_only=False) for p in a.students]
    main_ck = dict(cks[0])
    main_ck["imitation_ensemble"] = [{"arch": c["arch"], "policy": c["policy"]} for c in cks[1:]]
    main_ck["members"] = [str(p) for p in a.students]
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(main_ck, out)
    print(f"Ensemble mit {len(cks)} Schuelern: {out}")


def cmd_hybrid(a) -> None:
    """Kleine Beschreibungsdatei fuer einen Hybrid aus V14 und einem Schueler (agents/sherlock/hybrid_agent.py)."""
    import torch
    out = _check_out(Path(a.out))
    if out.exists():
        raise SystemExit(f"{out} existiert schon")
    from agents.sherlock.main import Agent_x
    cfg = Agent_x._cfg_from_checkpoint(str(V14))
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"kind": "hybrid", "v14": str(V14), "student": str(Path(a.student).resolve()), "mode": a.mode,
                "combat_radius": a.combat_radius, "cfg": cfg.to_dict()}, out)
    print(f"Hybrid {a.mode}: {out}")


def cmd_pack_hybrid(a) -> None:
    """Hybrid fuer die Kursabgabe in EINE Datei packen (V14- und Schueler-Checkpoint eingebettet).
    Ausgabe z. B. <run>/weights/agent.pth, dann scripts.build_submission --battle --from-run <run> --out ..."""
    import torch

    from scripts.par_eval import build_cfg, parse_value
    out = _check_out(Path(a.out))
    if out.exists():
        raise SystemExit(f"{out} existiert schon")
    overrides = {k: parse_value(v) for k, v in (kv.split("=", 1) for kv in a.set)}
    build_cfg(a.student, a.set)  # Schalter frueh pruefen
    v14 = torch.load(V14, map_location="cpu", weights_only=False)
    student = torch.load(a.student, map_location="cpu", weights_only=False)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"kind": "hybrid", "mode": a.mode, "combat_radius": a.combat_radius, "v14_ckpt": v14,
                "student_ckpt": student, "student_overrides": overrides, "cfg": dict(v14["cfg"]),
                "sources": {"v14": str(V14), "student": str(Path(a.student).resolve())}}, out)
    print(f"Gepackter Hybrid ({a.mode}, Schueler-Schalter {overrides}): {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--out", required=True)
    c.add_argument("--games", type=int, default=200)
    c.add_argument("--workers", type=int, default=12)
    c.add_argument("--seed0", type=int, default=TRAIN_SEED0)
    c.add_argument("--mix", default="kaggle3:0.5,v14:0.25,solution92:0.25")
    d = sub.add_parser("dagger")
    d.add_argument("--student", required=True)
    d.add_argument("--out", required=True)
    d.add_argument("--games", type=int, default=200)
    d.add_argument("--workers", type=int, default=12)
    d.add_argument("--seed0", type=int, default=TRAIN_SEED0 + 50_000)
    d.add_argument("--mix", default="kaggle3:0.5,v14:0.25,solution92:0.25")
    d.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                   help="Schalter fuer den spielenden Schueler (z. B. imit_stay_bias=1.5)")
    e = sub.add_parser("ensemble")
    e.add_argument("--students", nargs="+", required=True)
    e.add_argument("--out", required=True)
    h = sub.add_parser("hybrid")
    h.add_argument("--student", required=True)
    h.add_argument("--mode", choices=("points", "combat", "sap", "mixed"), default="points")
    h.add_argument("--combat-radius", type=int, default=5)
    h.add_argument("--out", required=True)
    ph = sub.add_parser("pack-hybrid")
    ph.add_argument("--student", required=True)
    ph.add_argument("--mode", choices=("points", "combat", "sap", "mixed"), default="points")
    ph.add_argument("--combat-radius", type=int, default=5)
    ph.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ph.add_argument("--out", required=True)
    t = sub.add_parser("train")
    t.add_argument("--data", nargs="+", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--epochs", type=int, default=4)
    t.add_argument("--mb", type=int, default=2048)
    t.add_argument("--lr", type=float, default=2e-3)
    t.add_argument("--ch", type=int, default=64)
    t.add_argument("--blocks", type=int, default=6)
    t.add_argument("--hidden", type=int, default=256)
    t.add_argument("--low-memory", action="store_true",
                   help="Dateigruppen auf Platte halten, nur Trainingsbatches auf das Gerät laden, auf CPU validieren")
    t.add_argument("--val-frac", type=float, default=0.08)
    t.add_argument("--seed", type=int, default=0)
    t.add_argument("--device", default="auto")
    t.add_argument("--sap-weight", type=float, default=0.5)
    focused = sub.add_parser("train-selective", help="6 Aktionsklassen; feste Kampfkarten und SAP-Gewichtung")
    focused.add_argument("--data", nargs="+", required=True)
    focused.add_argument("--out", required=True)
    focused.add_argument("--device", choices=("auto","mps","cpu"), default="auto")
    focused.set_defaults(selective=True, epochs=5, mb=256, lr=0.001, ch=32, blocks=3, hidden=128,
                         seed=2711, sap_weight=0.5)
    a = ap.parse_args()
    commands = {"collect": cmd_collect, "dagger": cmd_dagger, "ensemble": cmd_ensemble, "hybrid": cmd_hybrid, "pack-hybrid": cmd_pack_hybrid,
                "train": cmd_train, "train-selective": cmd_train}
    commands[a.cmd](a)


if __name__ == "__main__":
    main()
