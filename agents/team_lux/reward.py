"""Reward Shaping pro Einheit.

Das Env liefert nur ein Team-Signal und nur am Matchende (Slide 45). Das ist fuer
DQN viel zu spaerlich, deshalb formen wir pro Einheit und pro Step:

  r = w_point     * steht auf bewiesenem Punkte-Tile (und ist dort "Eigentuemer")
    - w_stack     * steht redundant auf einem bereits besetzten Punkte-Tile
    + w_shape     * (gamma * phi(s') - phi(s))        <- potentialbasiert
    + w_explore   * neu gesehene Tiles   (geteilt im Team)
    + w_discovery * neu bewiesene Punkte-Tiles (geteilt im Team)
    + w_energy    * Energieaenderung / 400
    - w_death     * Einheit verloren
    + w_sap_hit   * getroffene Gegner beim Sap (bzw. Strafe bei Fehlschuss)
    + w_match     * Env-Reward (Matchsieg/-niederlage)

Mit cfg.use_shaping = False (Ablation no_shaping) bleibt nur
  r = w_point * (Eigentuemer eines bewiesenen Punkte-Tiles) + w_match * Env-Reward

phi(s) = -SHAPE_SCALE * dist(unit, zugewiesenes Ziel) / (W + H)

Potentialbasiertes Shaping nach Ng, Harada & Russell (1999) aendert die optimale
Policy nicht, solange phi nur vom Zustand abhaengt. phi haengt hier ueber die
Zielzuweisung vom Belief ab - der Belief ist Teil unseres Zustands und die
Zielzuweisung steckt auch in den Features ("assigned_*"), damit das Shaping
markovsch bleibt.
"""
from __future__ import annotations

import numpy as np

from agents.team_lux import geometry as geo

SHAPE_SCALE = 10.0


def _phi(ctx: dict, uid: int) -> float:
    tgt = ctx["assigned"].get(int(uid))
    if tgt is None:
        return 0.0
    x = int(ctx["ally_pos"][uid][0])
    y = int(ctx["ally_pos"][uid][1])
    if x < 0 or y < 0:
        return 0.0
    dist = abs(tgt[0] - x) + abs(tgt[1] - y)
    return -SHAPE_SCALE * dist / float(ctx["W"] + ctx["H"])


def _on_owned_point_tile(next_ctx: dict, uid: int) -> int:
    """+1 Eigentuemer eines bewiesenen Punkte-Tiles, -1 redundant dort, 0 sonst."""
    nx = int(next_ctx["ally_pos"][uid][0])
    ny = int(next_ctx["ally_pos"][uid][1])
    if not (0 <= nx < next_ctx["W"] and 0 <= ny < next_ctx["H"]):
        return 0
    if not next_ctx["point_tiles"][nx, ny]:
        return 0
    owner = next_ctx["first_on_tile"].get((nx, ny), uid)
    return 1 if owner == uid else -1


def _sparse_rewards(cfg, alive_now, alive_next, next_ctx, env_reward) -> dict[int, float]:
    out: dict[int, float] = {}
    for uid in alive_now:
        r = cfg.w_match * float(env_reward)
        if uid in alive_next and _on_owned_point_tile(next_ctx, uid) == 1:
            r += cfg.w_point
        out[uid] = float(r)
    return out


def unit_rewards(cfg, ctx: dict, next_ctx: dict, env_reward: float,
                 actions: dict[int, int], sap_hits: dict[int, int]) -> dict[int, float]:
    """Reward je Unit, die im Ausgangszustand `ctx` gelebt hat."""
    alive_now = set(int(u) for u in ctx["ally_ids"].tolist())
    alive_next = set(int(u) for u in next_ctx["ally_ids"].tolist())
    n = max(1, len(alive_now))

    belief = next_ctx["belief"]
    team_bonus = (
        cfg.w_explore * min(belief.newly_explored / 20.0, 1.0)
        + cfg.w_discovery * belief.newly_proven
    ) / n

    if not cfg.use_shaping:
        return _sparse_rewards(cfg, alive_now, alive_next, next_ctx, env_reward)

    out: dict[int, float] = {}
    for uid in alive_now:
        r = team_bonus + cfg.w_match * float(env_reward)

        if uid in alive_next:
            on_point = _on_owned_point_tile(next_ctx, uid)
            if on_point == 1:
                r += cfg.w_point
            elif on_point == -1:
                r -= cfg.w_stack
            de = float(next_ctx["ally_ene"][uid]) - float(ctx["ally_ene"][uid])
            r += cfg.w_energy * de / 400.0
            r += cfg.w_shape * (cfg.gamma * _phi(next_ctx, uid) - _phi(ctx, uid))
        else:
            r -= cfg.w_death

        if actions.get(uid) == geo.SAP:
            hits = sap_hits.get(uid, 0)
            r += cfg.w_sap_hit * (1.0 if hits > 0 else -1.0) * max(1, hits)

        out[uid] = float(r)
    return out
